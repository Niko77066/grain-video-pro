#!/usr/bin/env python3
"""从 gate1.json 生成 Gate 2 出图单与 Gate 3 提交单——提示词一律走 tools/broll-profile.py 渲染。

不手抄模板：手抄就是「模板没有唯一出处、靠抄传播」那个 bug 的复发路径。
渲染顺带跑串词 lint，任一条命中别的 profile 的签名词汇就整批停下。
"""
import io
import json
import subprocess
import sys
from pathlib import Path

P = Path("projects/_smoke/broll-studio-2026-07-28")
TOOL = ["python3", "tools/broll-profile.py"]
SIZE = {"9:16": "720x1280"}


def render(profile, gate, variables, extra_key=None):
    if extra_key:                       # popup-book 的首帧提示词不在 gate2/3 里
        prof = json.loads(io.open(f".claude/skills/broll-studio/profiles/{profile}.json",
                                  encoding="utf-8").read())
        text = prof[extra_key]
        for k, v in variables.items():
            text = text.replace(f"[{k}]", v)
        return text
    cmd = TOOL + ["render", profile, "--gate", str(gate)]
    for k, v in variables.items():
        cmd += ["--var", f"{k}={v}"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"[{profile} gate{gate}] 渲染/lint 失败:\n{r.stderr}")
    if r.stderr.strip():
        print(f"  ⚠️ {profile} gate{gate}: {r.stderr.strip()}", file=sys.stderr)
    return r.stdout.rstrip("\n")


def main():
    spec = json.loads((P / "gate1.json").read_text(encoding="utf-8"))
    aspect = spec["aspect"]
    imgjobs, sdjobs, prompts = [], [], {}

    for s in spec["shots"]:
        prof, v = s["profile"], s["vars"]
        g2 = render(prof, 2, v)
        g3 = render(prof, 3, v)
        prompts[prof] = {"gate2": g2, "gate3": g3}
        imgjobs.append({"name": f"{prof}_last", "size": SIZE[aspect], "prompt": g2})

        if prof == "popup-book":        # 首帧规则例外：合上的书，要多出一张图
            g2f = render(prof, 2, v, extra_key="gate2_first_frame_prompt")
            prompts[prof]["gate2_first_frame"] = g2f
            imgjobs.append({"name": f"{prof}_first", "size": SIZE[aspect], "prompt": g2f})

        sdjobs.append({"name": prof, "ratio": aspect, "duration": spec["duration_s"],
                       "prompt": g3,
                       "first": f"{P}/anchors/{prof}_first.png",
                       "last": f"{P}/anchors/{prof}_last.png"})

    (P / "anchors").mkdir(parents=True, exist_ok=True)
    (P / "shots").mkdir(parents=True, exist_ok=True)
    (P / "anchors" / "imgjobs.json").write_text(json.dumps(
        {"defaults": {"quality": "medium", "output_format": "png"}, "jobs": imgjobs},
        ensure_ascii=False, indent=2), encoding="utf-8")
    (P / "shots" / "jobs.json").write_text(json.dumps(
        {"defaults": {"resolution": "720p",
                      "oss_prefix": "kuleshov/_smoke/broll-studio-2026-07-28"},
         "jobs": sdjobs}, ensure_ascii=False, indent=2), encoding="utf-8")
    (P / "prompts.json").write_text(json.dumps(prompts, ensure_ascii=False, indent=2),
                                    encoding="utf-8")
    print(f"✅ {len(imgjobs)} 张静帧 / {len(sdjobs)} 条 clip 的提示词已渲染并过 lint")


if __name__ == "__main__":
    main()
