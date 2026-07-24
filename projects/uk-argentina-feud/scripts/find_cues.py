#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 timeline.words 定位各镜切换锚点(内容词首次出现的音频戳)——音画同步基准。"""
import json

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
tl = json.load(open(f"{ROOT}/audio/timeline.json", encoding="utf-8"))
words = tl["words"]
# 拼接字符 + 每字符起戳
chars, starts = [], []
for w in words:
    for ch in w["w"]:
        chars.append(ch); starts.append(w["t"][0])
full = "".join(chars)

def cue(*kws, after=0.0):
    """找任一关键词(按顺序尝试)首次出现(after 秒后)的起戳。"""
    for kw in kws:
        i = 0
        while True:
            p = full.find(kw, i)
            if p < 0: break
            if starts[p] >= after: return round(starts[p], 2), kw
            i = p + 1
    return None, kws[0]

CUES = [
    ("sec01_横幅",      cue("横幅", "马岛")),
    ("sec01_44年",      cue("四十四", "44")),
    ("sec01_账本1806",  cue("这本账", "建国", "一八")),
    ("sec02_报题",      cue("什么仇", after=20)),
    ("sec02_大西洋",    cue("大西洋", "一万两千", "两百二十")),
    ("sec03_攻城",      cue("一八〇六", "1806", "军队", after=29)),
    ("sec03_铁路",      cue("铁路")),
    ("sec03_出口",      cue("出口", "四成")),
    ("sec03_1913富",    cue("一九一三", "1913")),
    ("sec03_1982",      cue("一九八二", "1982")),
    ("sec04_占岛",      cue("四月二日", after=81)),
    ("sec04_距离",      cue("四百八十", "480")),
    ("sec04_贝尔格拉诺",cue("贝尔", "三百二十三", "323")),
    ("sec04_飞鱼",      cue("飞鱼")),
    ("sec04_伤亡",      cue("六百四十九", "没能回家", "649")),
    ("sec04_命运",      cue("下台", "加尔铁里")),
    ("sec05_拉廷",      cue("拉廷", after=148)),
    ("sec05_红黄牌",    cue("红黄牌")),
    ("sec05_上帝之手",  cue("上帝", "用手")),
    ("sec05_世纪进球",  cue("五人", "世纪进球", "连过")),
    ("sec05_复仇",      cue("复仇")),
    ("sec05_9802",      cue("九八", "贝克汉姆")),
    ("sec06_昨天",      cue("然后就是昨天", "梅西", after=210)),
    ("sec06_拉廷去世",  cue("去世", "八十九")),
    ("sec06_金句",      cue("加时赛")),
]
print(f"全片 {tl['duration_s']}s | 逐字 {len(full)}")
for name, (t, kw) in CUES:
    print(f"  {name:<16} @ {t if t is not None else '未找到':>7}  ({kw})")
