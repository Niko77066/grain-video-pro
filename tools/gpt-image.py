#!/usr/bin/env python3
"""GPT-Image-2 静帧批量客户端（契约见 produce/references/image-motion.md）。

pixel-broll 与 collage-broll 的 Gate 2 共用。把两条易错契约固化成会报错的形状：
size 必须是 16 的倍数、output_format 禁 webp。响应 b64_json / url 两种形态都处理。

带 "ref" 的 job 走 /v1/images/edits（参考图编辑）——角色一致性问题必须在便宜的图像阶段
解决，不能拖到贵的视频阶段。B 型（角色动作）的尾帧姿态帧就该拿首帧当 ref 生成。

jobs.json:
{ "defaults": {"size":"1280x720","quality":"medium"},
  "jobs": [ {"name":"s01","prompt":"...","size":"720x1280"},
            {"name":"s01_last","prompt":"同角色，改姿态","ref":["anchors/s01_raw.png"]} ] }

用法:
  gpt-image.py --jobs jobs.json --out anchors/ [--state runs/img-state.json] [--dry-run]
"""
import argparse
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

MODEL = "gpt-image-2"
QUALITY = ("low", "medium", "high")
FORMATS = ("png", "jpeg")          # webp 会被 Azure 系部署 400 invalid_value
RETRIES = 3


def repo_root():
    for d in Path(__file__).resolve().parents:
        if (d / ".env").exists():
            return d
    sys.exit("找不到带 .env 的仓库根（worktree 里先 ln -sf <主仓库>/.env .env）")


def load_env(root):
    env = {}
    for line in (root / ".env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    # ⚠️ 用 ARK_* 这组（neodrop 网关）；.env 里的 OPENAI_* 是灵鲸，无 gpt-image-2 渠道
    base = env.get("ARK_VIDEO_API_BASE_URL") or os.environ.get("ARK_VIDEO_API_BASE_URL")
    key = env.get("ARK_VIDEO_API_KEY") or os.environ.get("ARK_VIDEO_API_KEY")
    if not base or not key:
        sys.exit("ARK_VIDEO_API_BASE_URL / ARK_VIDEO_API_KEY 未配置")
    return base.rstrip("/"), key


def multipart(fields, files):
    """手搓 multipart/form-data（edits 端点要 multipart，urllib 不自带）。"""
    boundary = f"----kuleshov{uuid.uuid4().hex}"
    buf = bytearray()
    for k, v in fields.items():
        buf += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n"
                f"{v}\r\n").encode()
    for path in files:
        p = Path(path)
        ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        buf += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image[]\"; "
                f"filename=\"{p.name}\"\r\nContent-Type: {ctype}\r\n\r\n").encode()
        buf += p.read_bytes() + b"\r\n"
    buf += f"--{boundary}--\r\n".encode()
    return bytes(buf), f"multipart/form-data; boundary={boundary}"


def post(url, key, payload, files=None):
    if files:
        body, ctype = multipart({k: v for k, v in payload.items() if k != "n"}, files)
    else:
        body, ctype = json.dumps(payload).encode(), "application/json"
    req = urllib.request.Request(
        url, data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": ctype,
                 "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
        method="POST")
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read().decode()), r.headers.get("x-oneapi-request-id")
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:600]
            # 520–524 是 Cloudflare 的上游异常，和 5xx 一样属于可重试（2026-07-28 实测撞到 520）
            if e.code in (429, 500, 502, 503, 504, 520, 521, 522, 523, 524) \
                    and attempt < RETRIES - 1:
                wait = 2 ** attempt * 5
                print(f"  HTTP {e.code}，{wait}s 后重试（{attempt + 1}/{RETRIES}）", flush=True)
                time.sleep(wait)
                continue
            sys.exit(f"HTTP {e.code}: {body}")
        except urllib.error.URLError as e:
            if attempt < RETRIES - 1:
                time.sleep(2 ** attempt * 5)
                continue
            sys.exit(f"网络错误: {e}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--jobs", required=True)
    p.add_argument("--out", required=True, help="静帧输出目录")
    p.add_argument("--state", help="留痕 JSON（request-id 进 ledger.costs 用）")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    root = repo_root()
    base, key = load_env(root)
    spec = json.loads(Path(a.jobs).read_text())
    dft = spec.get("defaults", {})
    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    sp = Path(a.state) if a.state else None
    if sp:
        sp.parent.mkdir(parents=True, exist_ok=True)
    state = (json.loads(sp.read_text()) if sp and sp.exists()
             else {"model": MODEL, "generated": []})

    def persist():
        # 每出一张就落盘：中途失败（网关 520、限流）不能丢已花钱的 request-id
        if sp:
            sp.write_text(json.dumps(state, ensure_ascii=False, indent=2))

    # 断点续跑：已在 state 里的条目不重复出图（重复出图 = 重复计费）
    done = {g["name"] for g in state.get("generated", [])}

    for job in spec["jobs"]:
        name = job["name"]
        if name in done and not a.dry_run:
            print(f"skip {name}（state 里已有，跳过以免重复计费）")
            continue
        size = job.get("size", dft.get("size"))
        quality = job.get("quality", dft.get("quality", "medium"))
        fmt = job.get("output_format", dft.get("output_format", "png"))
        if not size:
            sys.exit(f"[{name}] 必须显式给 size（省略=auto，画幅会失控）")
        w, h = (int(x) for x in size.lower().split("x"))
        if w % 16 or h % 16:
            sys.exit(f"[{name}] size {size} 不是 16 的倍数（image-motion.md 契约）")
        if quality not in QUALITY:
            sys.exit(f"[{name}] quality 只能是 {QUALITY}")
        if fmt not in FORMATS:
            sys.exit(f"[{name}] output_format 只能是 {FORMATS}（webp 会 400）")

        refs = job.get("ref") or []
        for r in refs:
            if not Path(r).exists():
                sys.exit(f"[{name}] 参考图不存在: {r}")
        if len(refs) > 16:
            sys.exit(f"[{name}] 参考图最多 16 张（image-motion.md 契约）")

        payload = {"model": MODEL, "prompt": job["prompt"], "quality": quality,
                   "output_format": fmt, "size": size, "n": 1}
        endpoint = "/v1/images/edits" if refs else "/v1/images/generations"
        if a.dry_run:
            print(json.dumps({name: {"endpoint": endpoint, "ref": refs, **payload}},
                             ensure_ascii=False, indent=2))
            continue

        print(f"[{name}] {size} / {quality}"
              + (f" / ref×{len(refs)}" if refs else "") + " …", flush=True)
        resp, rid = post(f"{base}{endpoint}", key, payload, files=refs or None)
        item = (resp.get("data") or [{}])[0]
        dst = outdir / f"{name}_raw.{fmt}"
        if item.get("b64_json"):
            dst.write_bytes(base64.b64decode(item["b64_json"]))
        elif item.get("url"):
            urllib.request.urlretrieve(item["url"], dst)
        else:
            sys.exit(f"[{name}] 响应里既无 b64_json 也无 url: {json.dumps(resp)[:600]}")
        print(f"  → {dst}  request-id={rid}")
        state["generated"].append({"name": name, "file": str(dst), "request_id": rid,
                                   "endpoint": endpoint, "ref": refs, "size": size,
                                   "quality": quality, "prompt": job["prompt"]})
        persist()

    if sp and not a.dry_run:
        print(f"\n留痕 → {sp}")


if __name__ == "__main__":
    main()
