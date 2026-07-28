#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""same-source 外挂字幕：剧本文本 + 强制对齐时戳 → WebVTT（`out/final.vtt`）。

为什么是这套口径（2026-07-28 起，grain 发布硬门）：
- **外挂不烧**：交付物是 MP4 + VTT 两件，compose 里不许有字幕层
  （`carrier-contracts/video.md` 三件套：MP4 + content.md + 外挂 VTT + 渲染证明）；
- **same-source**：文本取自剧本 `audio/narration.txt`，时间取自强制对齐
  `audio/timeline_fa.json` 的真实字戳。**禁止拿 ASR 转写文本当字幕**——中文数字与同音字会漂，
  ASR 只允许提供时间锚（`references/forced-alignment.md`）；
- **不带标点**：句末标点删除，句中停顿换全角空格。**切分仍然用标点**（断句依据），只在输出层剥离。

用法:
  tools/make-vtt.py <project_dir>                    # 写 out/final.vtt
  tools/make-vtt.py <project_dir> --limit 16 --stdout
退出码 1 = 生成失败或自检不过。
"""
import argparse, json, re, sys
from pathlib import Path

SENT_END = "。？！"
PAUSE = "，、；："
ALNUM = re.compile(r"[一-鿿A-Za-z0-9]")
PUNCT = re.compile(r"[，。、；：？！,.;:?!]")
NUM_SEP = re.compile(r"(?<=\d)[.,:](?=\d)")   # 5.3% / 1,200 / 00:12 里的分隔符不是标点


def strip_punct(t: str) -> str:
    t = re.sub(f"[{SENT_END}]", "", t)
    t = re.sub(f"[{PAUSE}]", "　", t)
    return t.strip("　 ").strip()


def build_cues(words, lines, limit):
    """按标点切片 → 合并到 limit 字以内（不跨句末）→ 绑真实字戳。"""
    idx, frags, buf, disp = 0, [], [], ""
    for line in lines:
        for ch in line:
            if ALNUM.match(ch):
                buf.append(idx); idx += 1
            disp += ch
            if ch in (SENT_END + PAUSE) and buf:
                frags.append([disp.strip(), buf[0], buf[-1]]); buf, disp = [], ""
        if buf:
            frags.append([disp.strip(), buf[0], buf[-1]]); buf = []
        disp = ""
    if idx != len(words):
        raise SystemExit(f"✗ 剧本可计字数 {idx} ≠ 对齐轴字数 {len(words)}——"
                         f"剧本与 timeline_fa.json 不同源，先重跑强制对齐（forced-alignment.md）")

    n = lambda t: len(PUNCT.sub("", t))
    merged = []
    for f in frags:
        prev = merged[-1] if merged else None
        if prev and prev[0][-1] not in SENT_END and n(prev[0]) + n(f[0]) <= limit:
            prev[0] += f[0]; prev[2] = f[2]
        else:
            merged.append(f)

    # 单个标点片段本身就超长时（"正好落在全年四点五到五的目标区间里" = 17 字，中间无标点可切），
    # 按字戳均分成 ≤limit 的几块——每个字都有真实时戳，切点时间准确，不引入估算。
    split = []
    for text, a, b in merged:
        cnt = n(text)
        if cnt <= limit:
            split.append([text, a, b]); continue
        parts = -(-cnt // limit)                      # 向上取整块数，尽量等长
        size = -(-cnt // parts)
        chars = [c for c in text if ALNUM.match(c)]   # 与字戳一一对应
        head_i = a
        pos = 0
        for k in range(parts):
            chunk = chars[pos: pos + size]
            if not chunk:
                break
            split.append(["".join(chunk), head_i, head_i + len(chunk) - 1])
            head_i += len(chunk); pos += len(chunk)
    merged = split

    cues = [{"text": strip_punct(t),
             "start": round(words[a]["t"][0], 3),
             "end": round(words[b]["t"][1] + 0.12, 3)} for t, a, b in merged]
    for a, b in zip(cues, cues[1:]):          # 相邻 <0.24s 直接对接，防闪缝
        if b["start"] - a["end"] < 0.24:
            a["end"] = b["start"]
    return cues


def resolve_inputs(P: Path):
    """逐字轴 + 剧本文本的解析顺序（历史项目文件名不统一，按优先级找）。"""
    words = None
    for rel in ("audio/timeline_fa.json", "audio/timeline.json"):
        f = P / rel
        if f.exists():
            d = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(d, dict) and d.get("words"):
                words = d["words"]; break
    if not words:
        raise SystemExit("✗ 找不到逐字对齐轴（audio/timeline_fa.json 或带 words 的 timeline.json）——"
                         "VTT 时间必须来自强制对齐，禁按字数估算（forced-alignment.md）")

    lines = None
    txt = P / "audio/narration.txt"
    if txt.exists():
        lines = [l.strip() for l in txt.read_text(encoding="utf-8").splitlines() if l.strip()]
    else:
        sp = P / "audio/spoken_text.json"
        sec = P / "audio/sections.json"
        if sp.exists():
            d = json.loads(sp.read_text(encoding="utf-8"))
            order = d.get("order") or sorted(d.get("sections", {}))
            lines = [d["sections"][k].strip() for k in order if d.get("sections", {}).get(k)]
        elif sec.exists():
            d = json.loads(sec.read_text(encoding="utf-8"))
            ft = d.get("fulltext")
            if ft:
                lines = [l.strip() for l in ft.splitlines() if l.strip()]
    if not lines:
        raise SystemExit("✗ 找不到剧本文本（audio/narration.txt / spoken_text.json / sections.json.fulltext）——"
                         "字幕文本必须来自剧本，禁用 ASR 转写文本（同音字与数字会漂）")
    return words, lines


def ts(sec: float) -> str:
    h, rem = divmod(max(0.0, sec), 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"


def to_vtt(cues) -> str:
    out = ["WEBVTT", ""]
    for i, c in enumerate(cues, 1):
        out += [str(i), f"{ts(c['start'])} --> {ts(c['end'])}", c["text"], ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project")
    ap.add_argument("--limit", type=int, default=16, help="每条最多几个字（不含标点计）")
    ap.add_argument("--stdout", action="store_true", help="VTT 打到 stdout，不写文件")
    a = ap.parse_args()

    P = Path(a.project.rstrip("/"))
    words, lines = resolve_inputs(P)
    cues = build_cues(words, lines, a.limit)

    bad = [c["text"] for c in cues if PUNCT.search(NUM_SEP.sub("", c["text"]))]
    if bad:
        raise SystemExit(f"✗ 自检不过：{len(bad)} 条仍含标点，例 {bad[0]!r}")
    long = [c["text"] for c in cues if len(c["text"].replace("　", "")) > a.limit]
    if long:
        raise SystemExit(f"✗ 自检不过：{len(long)} 条超 {a.limit} 字（切分逻辑有 bug），例 {long[0]!r}")

    vtt = to_vtt(cues)
    if a.stdout:
        print(vtt); return

    (P / "out").mkdir(exist_ok=True)
    (P / "out/final.vtt").write_text(vtt, encoding="utf-8")
    longest = max(len(c["text"].replace("　", "")) for c in cues)
    print(f"✓ out/final.vtt：{len(cues)} 条，最长 {longest} 字（全角空格不计），"
          f"覆盖 {cues[0]['start']:.2f}–{cues[-1]['end']:.2f}s，标点残留 0")


if __name__ == "__main__":
    main()
