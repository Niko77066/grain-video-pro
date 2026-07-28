#!/usr/bin/env python3
"""Seedance 2.0 首尾帧批量客户端（submit / poll / download + 留痕）。

契约源见 .claude/skills/produce/references/seedance.md，本脚本只是把它固化成
不会写错的形状：duration 必须在 metadata 内、ratio 不许省略、request-id 必留痕。

jobs.json:
{ "defaults": {"ratio":"16:9","resolution":"720p","duration":10},
  "jobs": [ {"name":"s03_pick","prompt":"...","first":"a/first.png","last":"a/last.png"} ] }

用法:
  seedance.py submit --jobs jobs.json --state runs/state.json [--dry-run]
  seedance.py poll   --state runs/state.json --out shots/ [--timeout-min 40]
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from http.client import RemoteDisconnected
from pathlib import Path

MODEL = "doubao-seedance-2-0-260128"   # 禁用不带日期的别名（default 分组无渠道 → 503）
DUR_MIN, DUR_MAX = 4, 15
RATIOS = ("16:9", "4:3", "1:1", "3:4", "9:16", "21:9")
POLL_EVERY_S = 20


def repo_root():
    here = Path(__file__).resolve()
    for d in here.parents:
        if (d / ".env").exists() and (d / "tools" / "oss-upload.sh").exists():
            return d
    sys.exit("找不到带 .env 与 tools/oss-upload.sh 的仓库根"
             "（worktree 里先 ln -sf <主仓库>/.env .env）")


def load_env(root):
    env = {}
    for line in (root / ".env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    base = env.get("ARK_VIDEO_API_BASE_URL") or os.environ.get("ARK_VIDEO_API_BASE_URL")
    key = env.get("ARK_VIDEO_API_KEY") or os.environ.get("ARK_VIDEO_API_KEY")
    if not base or not key:
        sys.exit("ARK_VIDEO_API_BASE_URL / ARK_VIDEO_API_KEY 未配置")
    return base.rstrip("/"), key


# 可重试的瞬时故障：网关 5xx、Cloudflare 52x、限流。其余 HTTP 码是契约错，立刻停。
RETRYABLE = (429, 500, 502, 503, 504, 520, 521, 522, 523, 524)
HTTP_RETRIES = 4


def http(url, key, data=None, timeout=120, soft_fail=False):
    """soft_fail=True 时瞬时故障返回 (None, None) 而不退出——轮询循环靠它撑过断连。"""
    req = urllib.request.Request(
        url, data=json.dumps(data).encode() if data is not None else None,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 # 网关要求带浏览器 UA，缺了会被挡
                 "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
        method="POST" if data is not None else "GET")
    for attempt in range(HTTP_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode()), r.headers.get("x-oneapi-request-id")
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:800]
            if e.code in RETRYABLE and attempt < HTTP_RETRIES - 1:
                time.sleep(2 ** attempt * 5)
                continue
            if soft_fail:
                print(f"  （HTTP {e.code}，本轮跳过）", flush=True)
                return None, None
            sys.exit(f"HTTP {e.code}: {body}")
        except (urllib.error.URLError, RemoteDisconnected,
                ConnectionError, TimeoutError, json.JSONDecodeError) as e:
            # 瞬时断连／SSL 抖动：2026-07-28 实测 poll 被 RemoteDisconnected 打断过整轮
            if attempt < HTTP_RETRIES - 1:
                time.sleep(2 ** attempt * 5)
                continue
            if soft_fail:
                print(f"  （{type(e).__name__}，本轮跳过）", flush=True)
                return None, None
            sys.exit(f"网络错误: {e}")


def upload(root, path, key_prefix):
    out = subprocess.run([str(root / "tools" / "oss-upload.sh"), str(path),
                          f"{key_prefix}/{Path(path).name}"],
                         capture_output=True, text=True, cwd=root)
    if out.returncode:
        sys.exit(f"oss-upload 失败: {out.stderr[-600:]}")
    url = out.stdout.strip().splitlines()[-1]
    if not url.startswith("http"):
        sys.exit(f"oss-upload 没返回 URL: {out.stdout[-400:]}")
    return url


def do_submit(a):
    root = repo_root()
    base, key = load_env(root)
    spec = json.loads(Path(a.jobs).read_text())
    dft = spec.get("defaults", {})
    prefix = dft.get("oss_prefix", "kuleshov/pixel-broll")
    sp = Path(a.state)
    sp.parent.mkdir(parents=True, exist_ok=True)
    # 断点续提：已在 state 里的条目不重复提交（重复提交 = 重复计费）
    state = json.loads(sp.read_text()) if sp.exists() else {"model": MODEL, "submitted": []}
    done = {j["name"] for j in state.get("submitted", [])}

    def persist():
        # 每提交一条就落盘：中途失败（上传瞬时错、网关 5xx）不能丢已花钱的 task id
        sp.write_text(json.dumps(state, ensure_ascii=False, indent=2))

    for job in spec["jobs"]:
        if job["name"] in done and not a.dry_run:
            print(f"skip {job['name']}（state 里已有，跳过以免重复计费）")
            continue
        name = job["name"]
        ratio = job.get("ratio", dft.get("ratio"))
        dur = int(job.get("duration", dft.get("duration", 10)))
        if ratio not in RATIOS:
            sys.exit(f"[{name}] ratio 必须显式给且合法（{RATIOS}）——省略会被上游自判")
        if not DUR_MIN <= dur <= DUR_MAX:
            sys.exit(f"[{name}] duration {dur} 越界 {DUR_MIN}–{DUR_MAX}"
                     "（越界会在排队后才拒且已计费）")
        for k in ("first", "last"):
            if not Path(job[k]).exists():
                sys.exit(f"[{name}] {k} 帧不存在: {job[k]}")

        # dry-run 不上传、不提交：纯离线校验 payload 形状与参数带宽，零成本
        def url_of(p):
            return f"<dry-run:{Path(p).name}>" if a.dry_run else upload(root, p, prefix)

        payload = {
            "model": MODEL, "prompt": job["prompt"],
            "metadata": {
                "content": [
                    {"type": "image_url", "role": "first_frame",
                     "image_url": {"url": url_of(job["first"])}},
                    {"type": "image_url", "role": "last_frame",
                     "image_url": {"url": url_of(job["last"])}},
                ],
                "resolution": job.get("resolution", dft.get("resolution", "720p")),
                "ratio": ratio,
                "generate_audio": False,   # 旁白永远走 TTS 轨
                "duration": dur,           # ⚠️ 必须在 metadata 内，顶层会被忽略
            }}

        if a.dry_run:
            print(json.dumps({name: payload}, ensure_ascii=False, indent=2))
            continue
        resp, rid = http(f"{base}/v1/videos", key, payload)
        tid = resp.get("id") or resp.get("task_id")
        if not tid:
            sys.exit(f"[{name}] 没拿到 task id: {json.dumps(resp)[:600]}")
        print(f"submitted {name} task={tid} request-id={rid}")
        state["submitted"].append({"name": name, "task_id": tid, "request_id": rid,
                                   "ratio": ratio, "duration_req_s": dur,
                                   "payload": payload})
        persist()

    if not a.dry_run:
        print(f"\n留痕 → {sp}（request_id 是成本反查凭据，进 ledger.costs）")


def do_poll(a):
    root = repo_root()
    base, key = load_env(root)
    sp = Path(a.state)
    state = json.loads(sp.read_text())
    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + a.timeout_min * 60

    while time.monotonic() < deadline:
        pending = [j for j in state["submitted"]
                   if not j.get("file") and not j.get("failed")]
        if not pending:
            break
        for job in pending:
            resp, _ = http(f"{base}/v1/videos/{job['task_id']}", key,
                           timeout=60, soft_fail=True)
            if resp is None:      # 瞬时故障：这一轮跳过这条，别让整个循环死掉
                continue
            st = resp.get("status", "")
            if st in ("completed", "succeeded"):
                url = (resp.get("metadata") or {}).get("url") or resp.get("url")
                if not url:
                    continue
                dst = outdir / f"{job['name']}_raw.mp4"
                try:
                    urllib.request.urlretrieve(url, dst)   # 签名 URL，拿到立即下
                except Exception as e:                     # 下载抖动：下一轮再试，别丢任务
                    print(f"  [{job['name']}] 下载失败（{type(e).__name__}），下一轮重试")
                    dst.unlink(missing_ok=True)
                    continue
                dur = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "csv=p=0", str(dst)], capture_output=True, text=True).stdout.strip()
                job["file"] = str(dst)
                job["duration_actual_s"] = round(float(dur), 3) if dur else None
                print(f"[done] {job['name']} → {dst} "
                      f"（请求 {job['duration_req_s']}s / 实产 {job['duration_actual_s']}s）")
            elif st in ("failed", "error"):
                job["failed"] = resp.get("error") or st
                print(f"[fail] {job['name']}: {job['failed']}")
            # 其余一律当中间态继续等（别枚举中间态）
        sp.write_text(json.dumps(state, ensure_ascii=False, indent=2))
        if any(not j.get("file") and not j.get("failed") for j in state["submitted"]):
            time.sleep(POLL_EVERY_S)

    left = [j["name"] for j in state["submitted"] if not j.get("file") and not j.get("failed")]
    sp.write_text(json.dumps(state, ensure_ascii=False, indent=2))
    if left:
        print(f"\n超时未完成: {', '.join(left)}（state 已存，可再跑一次 poll 续等）")
        return 1
    return 1 if any(j.get("failed") for j in state["submitted"]) else 0


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("submit"); s.add_argument("--jobs", required=True)
    s.add_argument("--state", required=True); s.add_argument("--dry-run", action="store_true")
    q = sub.add_parser("poll"); q.add_argument("--state", required=True)
    q.add_argument("--out", required=True); q.add_argument("--timeout-min", type=int, default=40)
    a = p.parse_args()
    return do_submit(a) or 0 if a.cmd == "submit" else do_poll(a)


if __name__ == "__main__":
    sys.exit(main())
