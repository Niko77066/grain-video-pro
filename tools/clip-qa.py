#!/usr/bin/env python3
"""生成型 clip 的通用码判：规格 / 死尾 / contact sheet。

八套生成型材质语言共用（`broll-studio` 的 profile 层）。各套的美术判据不同
（像素查栅格锁色、拼贴查摊散聚簇），但「交付物是不是一条合格的 clip」是同一套问题，
只该有一份实现。批次级的总览三张图在 `tools/clip-batch-sheets.py`。

死尾判据是宪法红线（禁冻结帧补时长）的码判投影：Seedance 默认会把组装塞在前段、
尾部长时间 hold。判据用 signalstats 的 YDIF，但比的是**尾段与全片自身的运动量之比**，
不是绝对阈值——绝对阈值跨不了内容类型（见常量处的实测说明）。

用法:
  clip-qa.py clip.mp4 [--json qa.json] [--contact sheet.jpg]
                      [--expect-size 1280x720] [--tail-ratio-min 0.25]
退出码 0=pass / 1=fail。
"""
import argparse
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path

TAIL_WINDOW_S = 2.0        # 死尾检查的尾段长度
SAMPLE_FPS = 8             # YDIF 采样率
# 死尾判据用**相对量**：尾段运动量 / 全片运动量。
# 2026-07-28 冒烟实测推翻了原来的绝对阈值（YDIF<1 视为近静止）——
# 它是拿半调拼贴/摄影内容标的，搬到平色像素画上必然误报：像素画在暗底上
# 相邻帧的平均亮度差本来就只有 0.3–0.4，动得好好的也全线判红（四条测试片误报三条）。
# 相对判据与内容亮度无关，且在负对照上仍然开火（真冻尾 0.00、全程动 1.57）。
TAIL_RATIO_MIN = 0.25      # 尾段运动量不得低于全片中位的 25%
TAIL_ABS_FLOOR = 0.10      # 兜底：尾段中位 YDIF 低于此值 = 真冻帧，无论比值多少都判红
# ⚠️ 已知失效模式（2026-07-28 broll-studio 冒烟发现，**未修，故意的**）：
# 「中段爆发型」会被误判红。popup-book v2 的尾段绝对 YDIF 0.657 是七条测试片里第二高的
# （toy-world 只有 0.194 却以 29% 通过），但它中段书本翻开的爆发把全片中位抬到 7.03，
# 比值只剩 9%。试过换分母（前段 p60、截尾中位 p75）都救不回来——比值家族分离不了这个案例。
# 唯一能分离的是加一条「尾段绝对量」的或门，但可用样本只有 2 条（0.291 判红 / 0.657 判绿），
# 按这个校准阈值等于拟合噪声，而且绝对量会被颗粒/闪烁抬高，等于把门放松。
# 因此：判红照旧，但绝对量偏高时附 advisory，提示人眼复核。等样本够了再走棘轮。
TAIL_ABS_ADVISORY = 0.50   # 尾段绝对 YDIF 高于此值而比值判红 → 疑似中段爆发型误报


def probe(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "stream=codec_type,width,height,r_frame_rate",
         "-show_entries", "format=duration", "-of", "json", str(path)],
        capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[-1000:])
    d = json.loads(r.stdout)
    v = next(s for s in d["streams"] if s["codec_type"] == "video")
    num, den = (int(x) for x in v["r_frame_rate"].split("/"))
    return {"width": v["width"], "height": v["height"],
            "fps": round(num / den, 3) if den else None,
            "duration_s": round(float(d["format"]["duration"]), 3),
            "has_audio": any(s["codec_type"] == "audio" for s in d["streams"])}


def tail_motion(path):
    """返回 (尾段/全片 运动量比值, 尾段中位 YDIF, 全片中位 YDIF, 采样帧数)。"""
    r = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vf",
         f"fps={SAMPLE_FPS},signalstats,metadata=print:file=-", "-f", "null", "-"],
        capture_output=True, text=True)
    ydifs = [float(m) for m in re.findall(r"lavfi\.signalstats\.YDIF=([0-9.]+)", r.stdout)]
    if len(ydifs) < 4:
        return 1.0, 0.0, 0.0, len(ydifs)
    tail = ydifs[-int(TAIL_WINDOW_S * SAMPLE_FPS):]
    m_all = statistics.median(ydifs)
    m_tail = statistics.median(tail)
    ratio = m_tail / m_all if m_all else 0.0
    return round(ratio, 3), round(m_tail, 3), round(m_all, 3), len(ydifs)


def contact_sheet(path, spec, dst):
    tile = min(8, max(2, int(spec["duration_s"])))
    w, h = spec["width"], spec["height"]
    sw = 320 if w >= h else 180
    sh = round(sw * h / w / 2) * 2
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(path), "-vf",
                    f"fps={tile}/{spec['duration_s']:.3f},scale={sw}:{sh}:flags=neighbor,"
                    f"tile={tile}x1", "-frames:v", "1", str(dst)], check=True)


def run(target, expect_size=None, tail_ratio_min=TAIL_RATIO_MIN, contact=None):
    """返回 (result_dict, passed)。给 verify.py 之类的上层直接 import 复用。"""
    spec = probe(target)
    res = {"target": str(target), "spec": spec, "checks": {}, "verdict": "pass"}

    def mark(key, passed, detail, **extra):
        res["checks"][key] = {"pass": passed, "detail": detail, **extra}
        if not passed:
            res["verdict"] = "fail"

    mark("audio", not spec["has_audio"],
         "有音轨——必须零音轨交付（旁白走 TTS 轨）" if spec["has_audio"] else "无音轨")

    if expect_size:
        want = tuple(int(x) for x in expect_size.lower().split("x"))
        got = (spec["width"], spec["height"])
        mark("size", got == want, f"{got[0]}x{got[1]}"
             + ("" if got == want else f"，期望 {want[0]}x{want[1]}"))
    else:
        mark("size", True, f"{spec['width']}x{spec['height']}")

    ratio, m_tail, m_all, n = tail_motion(target)
    frozen = m_tail < TAIL_ABS_FLOOR
    passed = ratio >= tail_ratio_min and not frozen
    # 判红但尾段绝对量不低 → 大概率是「中段爆发型」误报（见常量处的已知失效模式）。
    # 仍判红（不放松门），但把线索给出来，让人眼有据可依。
    advisory = (not passed) and (not frozen) and m_tail >= TAIL_ABS_ADVISORY
    mark("dead_tail", passed,
         f"尾 {TAIL_WINDOW_S}s 运动量为全片的 {ratio:.0%}"
         f"（下限 {tail_ratio_min:.0%}；尾段中位 YDIF {m_tail} / 全片 {m_all}，采样 {n} 帧）"
         + ("　⚠️ 尾段近乎完全冻结" if frozen else "")
         + (f"　ℹ️ 但尾段绝对量 {m_tail} ≥ {TAIL_ABS_ADVISORY}，疑似中段爆发型误报——人眼复核 "
            f"contact sheet 后可带理由放行，理由写进 gate3-qa.md" if advisory else ""),
         tail_ratio=ratio, ydif_tail=m_tail, ydif_all=m_all,
         burst_advisory=advisory)

    if contact:
        Path(contact).parent.mkdir(parents=True, exist_ok=True)
        contact_sheet(target, spec, contact)
        res["contact_sheet"] = str(contact)

    return res, res["verdict"] == "pass"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("target", type=Path)
    p.add_argument("--json", type=Path)
    p.add_argument("--contact", type=Path)
    p.add_argument("--expect-size", help="如 1280x720")
    p.add_argument("--tail-ratio-min", type=float, default=TAIL_RATIO_MIN)
    a = p.parse_args()

    res, passed = run(a.target, a.expect_size, a.tail_ratio_min, a.contact)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
