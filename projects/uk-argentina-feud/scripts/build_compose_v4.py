#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compose v4：mmC音轨(244.6s) + forced-align字幕/cue + 像素镜头降速尾对齐 + broll3重构池 + BGM。
像素挂载：media_start = clip_len - mount_len（尾对齐，组装完成拍点落在文案上；belgrano例外头对齐）。
broll：tag按desc关键词过滤 + 全tag全局轮换 + 同素材复用时错开media-start（防同画面重复）。"""
import json, os, subprocess

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
C = json.load(open(f"{ROOT}/audio/cues_v4.json", encoding="utf-8"))
DUR = 246.0
VO_DUR = 244.62
SEG = 3.0
PIXLEN = 10.03

# ---- 像素事件（id, start, end, src）----
PIX = [
 ("banner",   C["banner"],          C["banner_end"]+0.25,  "s01_banner_s"),
 ("account",  C["account"],         C["slogan"],           "s01_1806_s"),
 ("map02",    C["map02"],           C["chap1"],            "s02_map_s"),
 ("invade",   C["invade_end"]-9.73, C["invade_end"]+0.3,   "s03_invade_s"),
 ("trade",    62.0,                 72.03,                 "s03_trade_s"),
 ("ruler",    C["ruler_end"]-10.03, C["ruler_end"],        "s04_ruler_s"),
 ("belgrano", 109.4,                116.4,                 "s04_belgrano_s"),
 ("sheffield",C["sheffield"],       C["sheffield_end"]+0.3,"s04_sheffield_s"),
 ("rattin",   158.0,                168.03,                "s05_rattin_s"),
 ("hand",     C["hand"],            C["hand_end"]+0.4,     "s05_hand_s"),
 ("goal",     C["goal"],            197.5,                 "s05_goal_s"),
 ("n9802",    C["y9802"]+0.8,       C["y9802_end"]+0.3,    "s05_9802_s"),
 ("banner2",  C["banner2"],         C["gold"],             "s01_banner_s"),
]
MS_OVERRIDE = {"belgrano": 0.0}   # 组装完成点在5s(降速后)，头对齐避免空纸场撞沉船文案
PHOTO = (C["photo"], C["banner2"])
CHAP = [(C["chap1"], 1.5, "钱")]
BIG1982 = (C["y1982"], 3.0)

# ---- 空镜池 ----
POOL_SEGS = [
 (0.0,                  C["banner"],          "match2026"),
 (C["banner_end"]+0.25, C["account"],         "match2026"),
 (C["slogan"],          C["map02"],           "ocean"),
 (C["chap1"]+1.5,       C["invade_end"]-9.73, "colonial"),
 (C["invade_end"]+0.3,  62.0,                 "colonial"),
 (72.03,                C["y1982"],           "london"),
 (C["y1982"]+3.0,       C["ruler_end"]-10.03, "falklands"),
 (C["ruler_end"],       109.4,                "fleet"),
 (116.4,                C["sheffield"],       "greysea"),
 (C["sheffield_end"]+0.3, C["fate"],          "surrender"),
 (C["fate"],            152.95,               "fate"),
 (152.95,               158.0,                "wembley"),
 (168.03,               C["mexico"],          "wembley"),
 (C["mexico"],          C["hand"],            "azteca"),
 (197.5,                C["y9802"]+0.8,       "azteca"),
 (C["y9802_end"]+0.3,   C["photo"],           "match_replay"),
 (C["gold"],            DUR-1.2,              "night_end"),
]
TAG2SEC = {"match2026":["sec01","sec06"], "ocean":["sec02"], "colonial":["sec03"],
           "london":["sec03"], "falklands":["sec04"], "fleet":["sec04"],
           "greysea":["sec04","sec02"], "surrender":["sec04"], "fate":["sec04"],
           "wembley":["sec05"], "azteca":["sec05"], "match_replay":["sec01"], "night_end":["sec06"]}
# desc 必含其一（过滤同 section 内不贴题素材）；命中<1条时回退全 section
TAG_FILTER = {
 "colonial":  ["版画", "牛车"],
 "london":    ["伦敦", "收割", "麦", "蒸汽", "谷物", "麦穗"],
 "falklands": ["阿军", "岛民", "荒", "礁", "风蚀"],
 "fleet":     ["出港", "鹞式", "编队"],
 "greysea":   ["灰", "剪影", "破灰浪"],
 "surrender": ["斯坦利", "火炮", "纪念碑"],
 "fate":      ["伦敦", "编队", "纪念碑"],
 "wembley":   ["1966", "温布利"],
 "azteca":    ["阿兹特克", "草皮"],
 "match_replay": ["进球", "横幅", "看台"],
 "night_end": ["夜", "黄昏"],
}
TAG_PREF = {"match2026":["进球","2026","横幅","球迷","夜"], "ocean":["大西洋","巨浪","海"],
            "colonial":["版画"], "london":["伦敦","银行"], "falklands":["阿军","岛民"],
            "fleet":["出港"], "greysea":["破灰浪"], "surrender":["斯坦利"],
            "fate":["伦敦雨夜","伦敦"], "wembley":["人海","看台"], "azteca":["阿兹特克"], "match_replay":["进球"], "night_end":["夜"]}

mani = json.load(open(f"{ROOT}/compose/assets/broll3/manifest.json", encoding="utf-8"))
entries = mani["items"]
keep2 = mani.get("keep_from_broll2", [])

# 素材时长表（broll3 从 manifest；broll2 ffprobe）
DURS = {}
for e in entries:
    DURS[f"broll3/{e['file'].removesuffix('.mp4')}"] = e["dur_s"]
for k in keep2:
    p = f"broll2/{k['file'].removesuffix('.mp4')}"
    f = f"{ROOT}/compose/assets/{p}.mp4"
    if os.path.exists(f):
        DURS[p] = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                                        "-of","csv=p=0",f],capture_output=True,text=True).stdout.strip())

def pool_for(tag):
    secs, prefs = TAG2SEC[tag], TAG_PREF[tag]
    cand = [("broll3", e["file"], e["desc"]) for e in entries if e["section"] in secs]
    cand += [("broll2", k["file"], k.get("reason","")) for k in keep2 if k["section"] in secs]
    kws = TAG_FILTER.get(tag)
    if kws:
        hit = [c for c in cand if any(k in c[2] for k in kws)]
        if hit: cand = hit
    cand.sort(key=lambda c: -sum(1 for p in prefs if p in c[2]))
    return [f"{d}/{f.removesuffix('.mp4')}" for d, f, _ in cand]

rot = {}      # tag → 全局轮换游标
use = {}      # file → 已用次数（错开 media-start）
def next_clip(tag, pool):
    i = rot.get(tag, 0); rot[tag] = i + 1
    return pool[i % len(pool)]

def media_start_for(src, d):
    n = use.get(src, 0); use[src] = n + 1
    total = DURS.get(src, 6.0)
    ms = 0.2 + 2.8 * n
    if ms + d > total - 0.1:            # 放不下就回绕
        ms = 0.2 if d + 0.3 <= total else 0.0
        use[src] = 1
    return round(ms, 2)

def clips_for_pool(t0, t1, tag, pool):
    out, t = [], t0
    while t < t1 - 0.05:
        d = min(SEG, t1 - t)
        if d < 0.6:
            if out:
                ps, pd, pf, pm = out[-1]
                out[-1] = (ps, round(pd + d, 2), pf, pm)
            break
        if t1 - t < SEG + 0.6:
            d = t1 - t
        src = next_clip(tag, pool)
        out.append((round(t, 2), round(d, 2), src, None)); t += d
    # media-start 放到时序确定后再算
    return [(s, d, f, media_start_for(f, d)) for s, d, f, _ in out]

broll, missing = [], []
for t0, t1, tag in POOL_SEGS:
    p = pool_for(tag)
    if not p:
        missing.append((tag, t0, t1)); continue
    broll += clips_for_pool(t0, t1, tag, p)
if missing:
    print("!! 空池(需处理，禁静默):", missing)

vt = []
for n, (st, d, src, ms) in enumerate(broll, 1):
    vt.append(f'      <video id="b{n}" class="clip fullframe real" src="assets/{src}.mp4" muted data-start="{st}" data-duration="{d}" data-media-start="{ms}" data-track-index="1"></video>')
for pid, st, en, src in PIX:
    d = round(min(en - st, PIXLEN), 2)
    ms = MS_OVERRIDE.get(pid, round(max(0.0, PIXLEN - (en - st)), 2))
    vt.append(f'      <video id="{pid}" class="clip fullframe" src="assets/{src}.mp4" muted data-start="{round(st,2)}" data-duration="{d}" data-media-start="{ms}" data-track-index="1"></video>')
vt.append(f'      <img id="photo" class="clip fullframe" src="assets/s06_photo.png" data-start="{round(PHOTO[0],2)}" data-duration="{round(PHOTO[1]-PHOTO[0],2)}" data-track-index="1" />')

mg = []
for ci, (st, d, zh) in enumerate(CHAP):
    mg.append(f'      <div id="chap{ci}" class="clip mg chap" data-start="{round(st,2)}" data-duration="{d}" data-track-index="2"><div class="ctr"><div class="zh">{zh}</div><div class="rule"></div></div></div>')
mg.append(f'      <div id="s1982" class="clip mg" data-start="{round(BIG1982[0],2)}" data-duration="{BIG1982[1]}" data-track-index="2"><div class="ctr"><div class="big1982">1982</div></div></div>')

BADGE = [
 (0.3,            C["banner"]-0.3,      "bScore", '<div class="sc">阿根廷 <b>2</b> - 1 英格兰</div><div class="m">补时 90\'+2 绝杀</div>', "score"),
 (C["b44"],       C["banner_end"]+0.25, "b44",    '<div class="big">44<span style="font-size:30px">年前的战争</span></div>', "tr"),
 (C["slogan"],    C["chap1"]-0.3,       "bRep",   '<div class="big"><span class="g">什么仇</span>什么怨</div><div class="sub">英国 · 阿根廷 — 掰了两百二十年手腕</div>', "report"),
 (C["rail"],      72.03,                "bRail",  '<div class="t1"><b>2/3</b> 铁路是英国资本 · <b>四成</b>出口卖到英国</div>', "bl"),
 (C["y1913"],     C["y1982"]-0.2,       "bWealth",'<div class="t1">1913 人均收入 · 阿根廷 <b>&gt;</b> 法国 <b>&gt;</b> 德国</div>', "bl"),
 (C["ruler"]+1.6, C["ruler_end"],       "bDist",  '<div class="t1">马岛 · 离阿根廷 <b>480km</b> · 离英国 <span class="r">12,700km</span></div>', "bl"),
 (C["toll_nums"], C["fate"],            "bToll",  '<div class="t1">七十四天，没能回家</div><div class="t1"><span class="r">649</span> 阿 · <span class="r">255</span> 英 · <span class="r">3</span> 岛民</div>', "tl"),
 (C["fate"]+0.5,  C["fate_end"],        "bFate",  '<div class="t1">加尔铁里 <span class="r">下台</span> · 撒切尔 <b>连任</b></div>', "tr"),
 (C["redcard"],   C["redcard_end"]+0.3, "bCard",  '<div class="t1">红黄牌 · 这场混乱之后才发明</div>', "tr"),
 (C["revenge"],   C["y9802"]+1.3,       "bRev",   '<div class="q">他说，<span class="hl">这就是复仇。</span></div>', "revenge"),
 (C["y9802"]+2.0, C["y9802_end"]+0.3,   "b9802",  '<div class="t1">1998 阿点球淘汰 · 2002 贝克汉姆复仇</div>', "bl"),
 (C["messi"],     C["photo"]+1.0,       "bMessi", '<div class="t1">三十九岁的梅西 · <b>两次助攻</b></div>', "tl"),
 (C["gold"],      DUR-1.2,              "bGold",  '<div class="g">阿根廷人踢的，一直是<b>那七十四天的加时赛</b>。</div>', "gold"),
]
bd = []
for st, en, bid, inner, pos in BADGE:
    bd.append(f'      <div id="{bid}" class="clip badge {pos}" data-start="{round(st,2)}" data-duration="{round(en-st,2)}" data-track-index="3">{inner}</div>')
bd_js = ",".join(f'["#{bid}",{round(st,2)},{round(en,2)}]' for st, en, bid, _, _ in BADGE)

CSS = open(f"{ROOT}/compose/_css_v3.txt").read()

html = f'''<!doctype html>
<html lang="zh" data-resolution="landscape" data-fps="30">
<head><meta charset="UTF-8"><title>英国和阿根廷：什么仇什么怨 — Kuleshov</title>
<script src="assets/gsap.min.js"></script><script src="assets/captions_data.js"></script>
<style>{CSS}
#fade{{background:#000;opacity:0;}}</style></head>
<body>
<div id="main-composition" data-composition-id="main-video" data-width="1280" data-height="720" data-start="0" data-duration="{DUR}" data-fps="30">
  <audio id="vo" class="clip" src="assets/voiceover.mp3" data-start="0" data-duration="{VO_DUR}" data-track-index="0" data-volume="1" data-has-audio="true"></audio>
  <audio id="bgm" class="clip" src="assets/bgm.mp3" data-start="0" data-duration="243.0" data-track-index="4" data-volume="0.23" data-has-audio="true"></audio>
{chr(10).join(vt)}
{chr(10).join(mg)}
{chr(10).join(bd)}
  <div id="capbox" class="clip" data-start="0" data-duration="{DUR}" data-track-index="5"></div>
  <div id="lut" class="clip" data-start="0" data-duration="{DUR}" data-track-index="100"></div>
  <div id="scan" class="clip" data-start="0" data-duration="{DUR}" data-track-index="101"></div>
  <div id="grain" class="clip" data-start="0" data-duration="{DUR}" data-track-index="102"></div>
  <div id="vig" class="clip" data-start="0" data-duration="{DUR}" data-track-index="103"></div>
  <div id="fade" class="clip" data-start="0" data-duration="{DUR}" data-track-index="104"></div>
  <script>
    const tl=gsap.timeline({{paused:true}}); const q=(s)=>document.querySelector(s);
    gsap.set("#photo",{{transformOrigin:"50% 42%"}}); tl.fromTo("#photo",{{scale:1.03}},{{scale:1.12,duration:{round(PHOTO[1]-PHOTO[0],2)},ease:"none"}},{round(PHOTO[0],2)});
    tl.fromTo("#s1982 .big1982",{{opacity:0,scale:1.15}},{{opacity:1,scale:1,duration:0.5,ease:"power2.out"}},{round(BIG1982[0],2)}); tl.to("#s1982 .big1982",{{opacity:0,duration:0.3}},{round(BIG1982[0]+BIG1982[1]-0.3,2)}); tl.set("#s1982 .big1982",{{opacity:0}},{round(BIG1982[0]+BIG1982[1],2)});
    gsap.utils.toArray(".chap").forEach(el=>{{const s=parseFloat(el.dataset.start);tl.fromTo(el.querySelector(".zh"),{{opacity:0}},{{opacity:1,duration:0.4}},s+0.1);tl.fromTo(el.querySelector(".rule"),{{width:0}},{{width:200,duration:0.5}},s+0.2);}});
    [{bd_js}].forEach(([id,s,e])=>{{tl.to(id,{{opacity:1,duration:0.4,ease:"power2.out"}},s);tl.to(id,{{opacity:0,duration:0.3,ease:"power2.in"}},e-0.35);tl.set(id,{{opacity:0}},e);}});
    const box=q("#capbox");
    (window.__captions||[]).forEach((c)=>{{tl.to(box,{{opacity:1,duration:0.1,onStart:()=>{{box.textContent=c.text;}}}},c.start);tl.to(box,{{opacity:0,duration:0.1}},c.end);}});
    tl.set(box,{{opacity:0}},{DUR-0.1});
    tl.to("#fade",{{opacity:1,duration:1.4,ease:"none"}},{DUR-1.5});
    window.__timelines=window.__timelines||{{}}; window.__timelines["main-video"]=tl;
  </script>
</div></body></html>'''
open(f"{ROOT}/compose/index.html", "w", encoding="utf-8").write(html)
print(f"index.html v4.1: broll {len(broll)} + 像素 {len(PIX)} + 照片1 + 角标 {len(BADGE)}")
print(f"像素覆盖 {round(sum(min(en-st,PIXLEN) for _,st,en,_ in PIX)+PHOTO[1]-PHOTO[0],1)}s / {DUR}s")
print(f"素材使用 {len(use)} 种 / 复用分布 {sorted(use.values(),reverse=True)[:8]}")
