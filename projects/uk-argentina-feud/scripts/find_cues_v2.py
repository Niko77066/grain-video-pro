#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v4 cue：从 forced-align timeline（剧本1:1真实戳）定位画面/角标锚点 → cues_v4.json"""
import json

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
tl = json.load(open(f"{ROOT}/audio/timeline.json", encoding="utf-8")) if False else \
     json.load(open(f"{ROOT}/audio/timeline_fa.json", encoding="utf-8"))
words = tl["words"]
full = "".join(w["w"] for w in words)
starts = [w["t"][0] for w in words]
ends = [w["t"][1] for w in words]

def cue(kw, after=0.0, end=False):
    i = 0
    while True:
        p = full.find(kw, i)
        if p < 0:
            raise SystemExit(f"cue 未找到: {kw}")
        if starts[p] >= after:
            return round(ends[p + len(kw) - 1], 2) if end else round(starts[p], 2)
        i = p + 1

C = {
  # sec01
  "score_start":      0.0,
  "banner":           cue("是庆祝时"),
  "banner_end":       cue("球场上", end=True),
  "b44":              cue("四十四年前"),
  "account":          cue("这么说吧"),
  "account_end":      cue("还要老", end=True),
  # sec02
  "slogan":           cue("什么仇什么怨", after=18),
  "map02":            cue("隔着"),
  "map02_end":        cue("手腕", end=True),
  # sec03
  "chap1":            cue("故事得从"),
  "invade":           cue("英国军队来了"),
  "invade_end":       cue("无条件投降", end=True),
  "identity":         cue("就这两仗"),
  "trade":            cue("不过往后一百年"),
  "rail":             cue("三分之二"),
  "trade_end":        cue("非正式帝国", end=True),
  "wealth":           cue("靠这套买卖"),
  "y1913":            cue("一九一三年的阿根廷"),
  "y1982":            cue("一九八二年到了"),
  # sec04
  "occupy":           cue("那年四月二日"),
  "ruler":            cue("它离阿根廷"),
  "ruler_end":        cue("跑半个地球", end=True),
  "fleet":            cue("撒切尔真把舰队"),
  "belgrano":         cue("五月二日"),
  "belgrano_end":     cue("这一艘船上", end=True),
  "sheffield":        cue("两天后"),
  "sheffield_end":    cue("军舰被击沉", end=True),
  "toll":             cue("七十四天后"),
  "toll_nums":        cue("六百四十九个"),
  "fate":             cue("战败第三天"),
  "fate_end":         cue("轻松连任", end=True),
  "acct_open":        cue("仗打完了"),
  # sec05
  "rattin":           cue("一九六六年世界杯"),
  "rattin_sit":       cue("一屁股"),
  "rattin_sit_end":   cue("红毯", end=True),
  "rattin_end":       cue("世纪劫案", end=True),
  "redcard":          cue("顺便说一句"),
  "redcard_end":      cue("才发明的", end=True),
  "mexico":           cue("二十年后"),
  "hand":             cue("马拉多纳"),
  "hand_end":         cue("上帝之手", end=True),
  "goal":             cue("第二个从中场"),
  "goal_end":         cue("世纪进球", end=True),
  "memoir":           cue("很多年后"),
  "revenge":          cue("他说"),
  "revenge_end":      cue("这就是复仇", end=True),
  "y9802":            cue("之后还有两笔账"),
  "y9802_end":        cue("扳回一城", end=True),
  # sec06
  "yesterday":        cue("然后就是前两天"),
  "messi":            cue("三十九岁的梅西"),
  "photo":            cue("有个人"),
  "photo_end":        cue("八十九岁", end=True),
  "banner2":          cue("横幅在亚特兰大"),
  "final":            cue("对英格兰"),
  "gold":             cue("而阿根廷人"),
  "end":              round(tl["duration_s"], 2),
}
json.dump(C, open(f"{ROOT}/audio/cues_v4.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for k, v in C.items():
    print(f"  {k:<14} {v:>8}")
