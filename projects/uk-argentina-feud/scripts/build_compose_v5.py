#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compose v5：Gentle_Senior 音轨 + 修正版强制对齐 + broll 全片一素材一次（硬性 no-reuse）。
- 所有时间点从 cues_v4.json 派生（音轨换了自动跟随）
- broll：单素材全片最多用一次；切段 2.2~5s；池耗尽按 fallback 链借未用素材；仍不够则大声报错
- banner2 像素复用取消 → 真实横幅新闻 ≤3.2s（RESERVE 专用）
- 素材窗尾部留 0.6s 余量防暗尾/黑闪"""
import json, os, subprocess

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
C = json.load(open(f"{ROOT}/audio/cues_v4.json", encoding="utf-8"))
tl = json.load(open(f"{ROOT}/audio/timeline_fa.json", encoding="utf-8"))
VO_DUR = round(tl["duration_s"], 2)
DUR = round(VO_DUR + 1.4, 2)
PIXLEN = 10.03

# ---- 像素事件（全 cue 派生）----
TRADE_S = round(C["rail"] - 4.3, 2); TRADE_E = round(TRADE_S + PIXLEN, 2)
BELG_S  = round(C["belgrano"] + 0.5, 2); BELG_E = round(BELG_S + 7.0, 2)
RATTIN_E = round(C["rattin_sit_end"] + 0.3, 2); RATTIN_S = round(RATTIN_E - PIXLEN, 2)
INVADE_S = round(C["invade_end"] - 9.73, 2)
GOAL_E  = round(C["memoir"] + 1.5, 2)
PIX = [
 ("banner",   C["banner"],        round(C["banner_end"]+0.25,2), "s01_banner_s"),
 ("account",  C["account"],       C["slogan"],                   "s01_1806_s"),
 ("map02",    C["map02"],         C["chap1"],                    "s02_map_s"),
 ("invade",   INVADE_S,           round(C["invade_end"]+0.3,2),  "s03_invade_s"),
 ("trade",    TRADE_S,            TRADE_E,                       "s03_trade_s"),
 ("ruler",    round(C["ruler_end"]-PIXLEN,2), C["ruler_end"],    "s04_ruler_s"),
 ("belgrano", BELG_S,             BELG_E,                        "s04_belgrano_s"),
 ("sheffield",C["sheffield"],     round(C["sheffield_end"]+0.3,2),"s04_sheffield_s"),
 ("rattin",   RATTIN_S,           RATTIN_E,                      "s05_rattin_s"),
 ("hand",     C["hand"],          round(C["hand_end"]+0.4,2),    "s05_hand_s"),
 ("goal",     C["goal"],          GOAL_E,                        "s05_goal_s"),
 ("n9802",    round(C["y9802"]+0.8,2), round(C["y9802_end"]+0.3,2), "s05_9802_s"),
]
MS_OVERRIDE = {"belgrano": 0.0}
PHOTO = (C["photo"], C["banner2"])
CHAP = [(C["chap1"], 1.5, "钱")]
BIG1982 = (C["y1982"], 3.0)
BANNER_NEWS_E = round(C["banner2"] + 3.2, 2)

POOL_SEGS = [
 (0.0,                        C["banner"],       "match2026"),
 (round(C["banner_end"]+0.25,2), C["account"],   "match2026"),
 (C["slogan"],                C["map02"],        "ocean"),
 (round(C["chap1"]+1.5,2),    INVADE_S,          "colonial"),
 (round(C["invade_end"]+0.3,2), TRADE_S,         "colonial"),
 (TRADE_E,                    C["y1982"],        "london"),
 (round(C["y1982"]+3.0,2),    round(C["ruler_end"]-PIXLEN,2), "falklands"),
 (C["ruler_end"],             BELG_S,            "fleet"),
 (BELG_E,                     C["sheffield"],    "greysea"),
 (round(C["sheffield_end"]+0.3,2), C["fate"],    "surrender"),
 (C["fate"],                  C["rattin"],       "fate"),
 (C["rattin"],                RATTIN_S,          "wembley"),
 (RATTIN_E,                   C["mexico"],       "wembley"),
 (C["mexico"],                C["hand"],         "azteca"),
 (GOAL_E,                     round(C["y9802"]+0.8,2), "azteca"),
 (round(C["y9802_end"]+0.3,2), C["photo"],       "match_replay"),
 (C["banner2"],               BANNER_NEWS_E,     "banner_news"),
 (BANNER_NEWS_E,              round(DUR-1.2,2),  "night_end"),
]
TAG2SEC = {"match2026":["sec01","sec06"], "ocean":["sec02"], "colonial":["sec03"],
           "london":["sec03"], "falklands":["sec04"], "fleet":["sec04"],
           "greysea":["sec04","sec02"], "surrender":["sec04"], "fate":["sec04"],
           "wembley":["sec05","sec06"], "azteca":["sec05","sec06"],
           "match_replay":["sec01","sec06"], "banner_news":["sec01"], "night_end":["sec06","sec01"]}
TAG_FILTER = {
 "colonial":  ["版画", "牛车", "赶牛", "收割"],
 "london":    ["伦敦", "收割", "麦", "蒸汽", "谷物", "麦穗", "街景"],
 "falklands": ["阿军", "岛民", "荒", "礁", "风蚀"],
 "fleet":     ["出港", "鹞式", "编队"],
 "greysea":   ["灰", "剪影", "破灰浪", "军舰"],
 "surrender": ["斯坦利", "火炮", "纪念碑"],
 "fate":      ["伦敦", "编队", "纪念碑"],
 "wembley":   ["1966", "温布利"],
 "azteca":    ["阿兹特克", "草皮", "黄昏", "方尖碑"],
 "match_replay": ["进球", "看台", "横幅特写"],
 "night_end": ["夜", "黄昏"],
}
TAG_EXCLUDE = {"colonial": ["伦敦", "街景", "银行"],
 "match_replay": ["舰", "军", "炮", "纪念", "伦敦", "1966", "1982"],
 "night_end": ["舰", "军", "炮", "1966", "1982"]}
TAG_PREF = {"match2026":["进球","2026","横幅","球迷","夜"], "ocean":["大西洋","巨浪","海"],
            "colonial":["版画"], "london":["伦敦","银行"], "falklands":["阿军","岛民"],
            "fleet":["出港"], "greysea":["破灰浪"], "surrender":["斯坦利"],
            "fate":["伦敦雨夜","伦敦"], "wembley":["人海","看台"], "azteca":["阿兹特克"],
            "match_replay":["进球"], "banner_news":[], "night_end":["夜"]}
RESERVE = {"banner_news": ["broll3/wc_banner_players_g"],
           "match_replay": ["broll3/wc_fans_banner2_g", "broll3/wc_goal_action_g"],
           "azteca":      ["broll3/azteca_aerial_g"],
           "night_end":   ["broll3/ba_congress_night_g", "broll3/puerto_madero_dusk_g"]}

mani = json.load(open(f"{ROOT}/compose/assets/broll3/manifest.json", encoding="utf-8"))
entries = mani["items"]
keep2 = mani.get("keep_from_broll2", [])
DURS, DESC, SECOF = {}, {}, {}
for e in entries:
    p = f"broll3/{e['file'].removesuffix('.mp4')}"
    DURS[p] = e["dur_s"]; DESC[p] = e["desc"]; SECOF[p] = e["section"]
for k in keep2:
    p = f"broll2/{k['file'].removesuffix('.mp4')}"
    f = f"{ROOT}/compose/assets/{p}.mp4"
    if os.path.exists(f):
        DURS[p] = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                                        "-of","csv=p=0",f],capture_output=True,text=True).stdout.strip())
        DESC[p] = k.get("reason",""); SECOF[p] = k["section"]

reserved = {f for v in RESERVE.values() for f in v}
taken = set()

def rank(files, prefs):
    return sorted(files, key=lambda p: -sum(1 for w in prefs if w in DESC[p]))

def candidates(tag):
    """三级：tag过滤 → 同section未过滤(剔除exclude) → 任意section未用。全程剔 reserved/taken。"""
    secs, prefs = TAG2SEC[tag], TAG_PREF[tag]
    if tag in RESERVE:
        own = [f for f in RESERVE[tag] if f not in taken]
        if own or tag == "banner_news":
            if own or tag == "banner_news":
                pass
        if own:
            return own
        if tag == "banner_news":
            return []
    excl = TAG_EXCLUDE.get(tag, [])
    base = [p for p in DURS if SECOF[p] in secs and p not in reserved and p not in taken
            and not any(x in DESC[p] for x in excl)]
    kws = TAG_FILTER.get(tag)
    lv1 = [p for p in base if kws and any(k in DESC[p] for k in kws)] if kws else base
    if lv1: return rank(lv1, prefs)
    if base: return rank(base, prefs)
    anyf = [p for p in DURS if p not in reserved and p not in taken
            and not any(x in DESC[p] for x in excl)]
    return rank(anyf, prefs)

warns = []
def clips_for_pool(t0, t1, tag):
    out, t = [], t0
    while t < t1 - 0.05:
        rem = round(t1 - t, 2)
        cs = candidates(tag)
        if not cs:
            warns.append(f"素材耗尽 tag={tag} @{t:.1f}s 剩{rem:.1f}s")
            break
        src = cs[0]; taken.add(src)
        cap = round(min(5.0, DURS[src] - 0.8), 2)
        d = min(rem, cap)
        if rem - d < 2.0 and rem <= cap:
            d = rem
        elif rem - d < 2.0:
            d = round(rem - 2.0, 2)
        if d < 1.2:
            taken.discard(src)
            if out:
                ps, pd, pf, pm = out[-1]
                out[-1] = (ps, round(pd + rem, 2), pf, pm)
            break
        out.append((round(t, 2), round(d, 2), src, 0.2)); t = round(t + d, 2)
    return out

broll = []
for t0, t1, tag in POOL_SEGS:
    broll += clips_for_pool(t0, t1, tag)
for w in warns:
    print("!!", w)

# track1 统一收集 → 缝隙<1.3s 并入前段（防黑闪；卡片/照片盖住的大缝不动）
track1 = []
for st, d, src, ms in broll:
    track1.append({"kind": "broll", "start": st, "dur": d, "src": src, "ms": ms})
for pid, st, en, src in PIX:
    d = round(min(en - st, PIXLEN), 2)
    ms = MS_OVERRIDE.get(pid, round(max(0.0, PIXLEN - (en - st)), 2))
    track1.append({"kind": "pix", "id": pid, "start": round(st, 2), "dur": d, "src": src, "ms": ms})
track1.sort(key=lambda c: c["start"])
for a, b in zip(track1, track1[1:]):
    gap = round(b["start"] - (a["start"] + a["dur"]), 2)
    if 0.01 < gap < 1.3:
        if b["ms"] >= gap:   # 后一条向前扩，媒体窗前移，payoff 不动
            b["ms"] = round(b["ms"] - gap, 2); b["start"] = round(b["start"] - gap, 2); b["dur"] = round(b["dur"] + gap, 2)
            print(f"  缝隙并入(后条前扩): {b.get('id', b['src'])} +{gap}s")
        else:                # 前一条延长；媒体窗整体前移防越过素材末尾
            a["dur"] = round(a["dur"] + gap, 2)
            a["ms"] = round(max(0.0, min(a["ms"], PIXLEN - a["dur"])), 2)
            print(f"  缝隙并入(前条延长): {a.get('id', a['src'])} +{gap}s ms→{a['ms']}")

vt = []
n = 0
for c in track1:
    if c["kind"] == "broll":
        n += 1
        vt.append(f'      <video id="b{n}" class="clip fullframe real" src="assets/{c["src"]}.mp4" muted data-start="{c["start"]}" data-duration="{c["dur"]}" data-media-start="{c["ms"]}" data-track-index="1"></video>')
    else:
        vt.append(f'      <video id="{c["id"]}" class="clip fullframe" src="assets/{c["src"]}.mp4" muted data-start="{c["start"]}" data-duration="{c["dur"]}" data-media-start="{c["ms"]}" data-track-index="1"></video>')
vt.append(f'      <img id="photo" class="clip fullframe" src="assets/s06_photo.png" data-start="{round(PHOTO[0],2)}" data-duration="{round(PHOTO[1]-PHOTO[0],2)}" data-track-index="1" />')

mg = []
for ci, (st, d, zh) in enumerate(CHAP):
    mg.append(f'      <div id="chap{ci}" class="clip mg chap" data-start="{round(st,2)}" data-duration="{d}" data-track-index="2"><div class="ctr"><div class="zh">{zh}</div><div class="rule"></div></div></div>')
mg.append(f'      <div id="s1982" class="clip mg" data-start="{round(BIG1982[0],2)}" data-duration="{BIG1982[1]}" data-track-index="2"><div class="ctr"><div class="big1982">1982</div></div></div>')

BADGE = [
 (0.3,            round(C["banner"]-0.3,2),  "bScore", '<div class="sc">阿根廷 <b>2</b> - 1 英格兰</div><div class="m">补时 90\'+2 绝杀</div>', "score"),
 (C["b44"],       round(C["banner_end"]+0.25,2), "b44", '<div class="big">44<span style="font-size:30px">年前的战争</span></div>', "tr"),
 (C["slogan"],    round(C["chap1"]-0.3,2),   "bRep",   '<div class="big"><span class="g">什么仇</span>什么怨</div><div class="sub">英国 · 阿根廷 — 掰了两百二十年手腕</div>', "report"),
 (C["rail"],      TRADE_E,                   "bRail",  '<div class="t1"><b>2/3</b> 铁路是英国资本 · <b>四成</b>出口卖到英国</div>', "bl"),
 (C["y1913"],     round(C["y1982"]-0.2,2),   "bWealth",'<div class="t1">1913 人均收入 · 阿根廷 <b>&gt;</b> 法国 <b>&gt;</b> 德国</div>', "bl"),
 (round(C["ruler"]+1.6,2), C["ruler_end"],   "bDist",  '<div class="t1">马岛 · 离阿根廷 <b>480km</b> · 离英国 <span class="r">12,700km</span></div>', "bl"),
 (C["toll_nums"], C["fate"],                 "bToll",  '<div class="t1">七十四天，没能回家</div><div class="t1"><span class="r">649</span> 阿 · <span class="r">255</span> 英 · <span class="r">3</span> 岛民</div>', "tl"),
 (round(C["fate"]+0.5,2), C["fate_end"],     "bFate",  '<div class="t1">加尔铁里 <span class="r">下台</span> · 撒切尔 <b>连任</b></div>', "tr"),
 (C["redcard"],   round(C["redcard_end"]+0.3,2), "bCard", '<div class="t1">红黄牌 · 这场混乱之后才发明</div>', "tr"),
 (C["revenge"],   round(C["y9802"]+1.3,2),   "bRev",   '<div class="q">他说，<span class="hl">这就是复仇。</span></div>', "revenge"),
 (round(C["y9802"]+2.0,2), round(C["y9802_end"]+0.3,2), "b9802", '<div class="t1">1998 阿点球淘汰 · 2002 贝克汉姆复仇</div>', "bl"),
 (C["messi"],     round(C["photo"]+1.0,2),   "bMessi", '<div class="t1">三十九岁的梅西 · <b>两次助攻</b></div>', "tl"),
 (C["gold"],      round(DUR-1.2,2),          "bGold",  '<div class="g">阿根廷人踢的，一直是<b>那七十四天的加时赛</b>。</div>', "gold"),
]
bd = []
for st, en, bid, inner, pos in BADGE:
    bd.append(f'      <div id="{bid}" class="clip badge {pos}" data-start="{round(st,2)}" data-duration="{round(en-st,2)}" data-track-index="3">{inner}</div>')
bd_js = ",".join(f'["#{bid}",{round(st,2)},{round(en,2)}]' for st, en, bid, _, _ in BADGE)

BGM_FILE = "bgm_v5.mp3" if os.path.exists(f"{ROOT}/compose/assets/bgm_v5.mp3") else "bgm.mp3"
BGM_DUR = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",
                                f"{ROOT}/compose/assets/{BGM_FILE}"],capture_output=True,text=True).stdout.strip())
BGM_DUR = round(min(BGM_DUR, DUR), 2)

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
  <audio id="bgm" class="clip" src="assets/{BGM_FILE}" data-start="0" data-duration="{BGM_DUR}" data-track-index="4" data-volume="0.23" data-has-audio="true"></audio>
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
    tl.set(box,{{opacity:0}},{round(DUR-0.1,2)});
    tl.to("#fade",{{opacity:1,duration:1.4,ease:"none"}},{round(DUR-1.5,2)});
    window.__timelines=window.__timelines||{{}}; window.__timelines["main-video"]=tl;
  </script>
</div></body></html>'''
open(f"{ROOT}/compose/index.html", "w", encoding="utf-8").write(html)
n_reuse = 0  # taken 是集合，硬性一次
print(f"index.html v5: DUR={DUR} VO={VO_DUR} | broll {len(broll)}(素材{len(taken)}种，一素材一次) + 像素 {len(PIX)} + 照片1 + 角标 {len(BADGE)} | BGM {BGM_FILE} {BGM_DUR}s")
print(f"像素覆盖 {round(sum(min(en-st,PIXLEN) for _,st,en,_ in PIX)+PHOTO[1]-PHOTO[0],1)}s")
unused = [p for p in DURS if p not in taken and p not in reserved]
print(f"未用素材 {len(unused)}: {sorted(unused)[:10]}")
