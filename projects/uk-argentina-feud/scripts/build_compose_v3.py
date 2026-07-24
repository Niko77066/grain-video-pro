#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 compose v3 index.html：空镜≤3s快切 + 像素事件贴cue + 角标叠画面 + 精确字幕。"""
import os
ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
DUR = 222.76
SEG = 3.0  # 空镜单素材最长3s

# 像素事件(贴cue)：id,start,dur,src
PIX = [("banner",8.3,5.0,"s01_banner"),("account",15.0,5.0,"s01_1806"),("invade",29.0,5.0,"s03_invade"),
       ("belgrano",102.8,5.0,"s04_belgrano"),("sheffield",114.0,5.0,"s04_sheffield"),
       ("rattin",148.1,5.0,"s05_rattin"),("hand",172.7,5.0,"s05_hand"),("goal",177.7,5.0,"s05_goal")]
PHOTO = (206.0,8.0)  # 拉廷档案照
# 各节非事件段的相关 broll 池(≤3s 快切轮换)
POOLS = [
 (0.0,20.06,["broll2/crowd1_g","broll2/flag1_g","broll/stadium_g","broll2/city2_g"]),
 (20.6,28.48,["broll2/ocean1_g","broll2/ocean2_g","broll2/island1_g"]),
 (28.48,74.88,["broll2/building1_g","broll2/building2_g","broll2/city2_g","broll2/city1_g","broll2/train1_g","broll2/cargo1_g","broll2/cattle1_g","broll2/grain1_g","broll2/london2_g"]),
 (75.5,139.0,["broll2/island1_g","broll2/greysea1_g","broll2/warship1_g","broll2/ocean2_g","broll2/memorial1_g","broll2/london1_g","broll2/london2_g"]),
 (139.0,197.52,["broll/stadium_g","broll2/building2_g","broll2/city1_g","broll2/london1_g"]),
 (197.52,222.76,["broll2/crowd1_g","broll2/flag1_g","broll/stadium_g","broll2/airport1_g","broll2/ocean1_g"]),
]
# 角标：start,dur,id,inner_html,pos
BADGE = [
 (0.3,7.7,"bScore",'<div class="sc">阿根廷 <b>2</b> - 1 英格兰</div><div class="m">补时 90\'+2 绝杀</div>',"score"),
 (11.3,3.2,"b44",'<div class="big">44<span style="font-size:30px">年前的战争</span></div>',"tr"),
 (20.8,7.2,"bRep",'<div class="big"><span class="g">什么仇</span>什么怨</div><div class="sub">英国 · 阿根廷 — 掰了两百二十年手腕</div>',"report"),
 (62.0,8.0,"bRail",'<div class="t1"><b>2/3</b> 铁路是英国资本 · <b>四成</b>出口卖到英国</div>',"bl"),
 (70.5,4.0,"bWealth",'<div class="t1">1913 人均收入 · 阿根廷 <b>&gt;</b> 法国 <b>&gt;</b> 德国</div>',"bl"),
 (86.4,7.0,"bDist",'<div class="t1">马岛 · 离阿根廷 <b>480km</b> · 离英国 <span class="r">12,700km</span></div>',"bl"),
 (123.5,5.5,"bToll",'<div class="t1">七十四天，没能回家</div><div class="t1"><span class="r">649</span> 阿 · <span class="r">255</span> 英 · <span class="r">3</span> 岛民</div>',"tl"),
 (130.0,6.5,"bFate",'<div class="t1">加尔铁里 <span class="r">下台</span> · 撒切尔 <b>连任</b></div>',"tr"),
 (161.0,6.0,"bCard",'<div class="t1">红黄牌 · 这场混乱之后才发明</div>',"tr"),
 (187.5,3.5,"bRev",'<div class="q">他说，<span class="hl">这就是复仇。</span></div>',"revenge"),
 (191.5,5.5,"b9802",'<div class="t1">1998 阿点球淘汰 · 2002 贝克汉姆复仇</div>',"bl"),
 (199.0,6.0,"bMessi",'<div class="t1">三十九岁的梅西 · <b>两次助攻</b></div>',"tl"),
 (219.0,3.7,"bGold",'<div class="g">阿根廷人踢的，一直是<b>那七十四天的加时赛</b>。</div>',"gold"),
]
CHAP = [(28.48,1.5,"钱")]  # 血章用 1982 大字过渡（避免与 1982 track2 重叠）
# 1982 大字过渡
BIG1982 = (76.1,3.0)

def clips_for_pool(t0,t1,pool,busy):
    """在[t0,t1]用 pool ≤3s 快切填，跳过 busy(事件)区间。"""
    out=[]; t=t0; i=0
    while t < t1-0.05:
        # 跳过 busy
        skip=False
        for bs,be in busy:
            if bs-0.01 <= t < be:
                t=be; skip=True; break
        if skip: continue
        nxt=t1
        for bs,be in busy:
            if t < bs < nxt: nxt=bs
        d=min(SEG, nxt-t)
        if d < 0.6: t=nxt; continue
        out.append((round(t,2),round(d,2),pool[i%len(pool)])); i+=1; t+=d
    return out

busy=[(s,s+d) for _,s,d,_ in PIX]+[(PHOTO[0],PHOTO[0]+PHOTO[1])]+[(c[0],c[0]+c[1]) for c in CHAP]+[(BIG1982[0],BIG1982[0]+BIG1982[1])]
broll_clips=[]
for t0,t1,pool in POOLS:
    broll_clips += clips_for_pool(t0,t1,pool,busy)

# 组装 video track
vt=[]
n=0
for st,d,src in broll_clips:
    n+=1; vt.append(f'      <video id="b{n}" class="clip fullframe real" src="assets/{src}.mp4" muted data-start="{st}" data-duration="{d}" data-media-start="0.3" data-track-index="1"></video>')
for pid,st,d,src in PIX:
    vt.append(f'      <video id="{pid}" class="clip fullframe" src="assets/{src}.mp4" muted data-start="{st}" data-duration="{d}" data-media-start="0" data-track-index="1"></video>')
vt.append(f'      <img id="photo" class="clip fullframe" src="assets/s06_photo.png" data-start="{PHOTO[0]}" data-duration="{PHOTO[1]}" data-track-index="1" />')

# MG：章节卡 + 1982
mg=[]
for ci,(st,d,zh) in enumerate(CHAP):
    mg.append(f'      <div id="chap{ci}" class="clip mg chap" data-start="{st}" data-duration="{d}" data-track-index="2"><div class="ctr"><div class="zh">{zh}</div><div class="rule"></div></div></div>')
mg.append(f'      <div id="s1982" class="clip mg" data-start="{BIG1982[0]}" data-duration="{BIG1982[1]}" data-track-index="2"><div class="ctr"><div class="big1982">1982</div></div></div>')

# 角标
bd=[]
for st,d,bid,inner,pos in BADGE:
    bd.append(f'      <div id="{bid}" class="clip badge {pos}" data-start="{st}" data-duration="{d}" data-track-index="3">{inner}</div>')
bd_js=",".join(f'["#{bid}",{st},{round(st+d,2)}]' for st,d,bid,_,_ in BADGE)

CSS = open(f"{ROOT}/compose/_css_v3.txt").read() if os.path.exists(f"{ROOT}/compose/_css_v3.txt") else ""

html = f'''<!doctype html>
<html lang="zh" data-resolution="landscape" data-fps="30">
<head><meta charset="UTF-8"><title>英国和阿根廷：什么仇什么怨 — Kuleshov</title>
<script src="assets/gsap.min.js"></script><script src="assets/captions_data.js"></script>
<style>{CSS}</style></head>
<body>
<div id="main-composition" data-composition-id="main-video" data-width="1280" data-height="720" data-start="0" data-duration="{DUR}" data-fps="30">
  <audio id="vo" class="clip" src="assets/voiceover.mp3" data-start="0" data-duration="{DUR}" data-track-index="0" data-volume="1" data-has-audio="true"></audio>
{chr(10).join(vt)}
{chr(10).join(mg)}
{chr(10).join(bd)}
  <div id="capbox" class="clip" data-start="0" data-duration="{DUR}" data-track-index="5"></div>
  <div id="lut" class="clip" data-start="0" data-duration="{DUR}" data-track-index="100"></div>
  <div id="scan" class="clip" data-start="0" data-duration="{DUR}" data-track-index="101"></div>
  <div id="grain" class="clip" data-start="0" data-duration="{DUR}" data-track-index="102"></div>
  <div id="vig" class="clip" data-start="0" data-duration="{DUR}" data-track-index="103"></div>
  <script>
    const tl=gsap.timeline({{paused:true}}); const q=(s)=>document.querySelector(s);
    gsap.set("#photo",{{transformOrigin:"50% 42%"}}); tl.fromTo("#photo",{{scale:1.03}},{{scale:1.12,duration:{PHOTO[1]},ease:"none"}},{PHOTO[0]});
    tl.fromTo("#s1982 .big1982",{{opacity:0,scale:1.15}},{{opacity:1,scale:1,duration:0.5,ease:"power2.out"}},{BIG1982[0]}); tl.to("#s1982 .big1982",{{opacity:0,duration:0.3}},{round(BIG1982[0]+BIG1982[1]-0.3,2)}); tl.set("#s1982 .big1982",{{opacity:0}},{round(BIG1982[0]+BIG1982[1],2)});
    gsap.utils.toArray(".chap").forEach(el=>{{const s=parseFloat(el.dataset.start);tl.fromTo(el.querySelector(".zh"),{{opacity:0}},{{opacity:1,duration:0.4}},s+0.1);tl.fromTo(el.querySelector(".rule"),{{width:0}},{{width:200,duration:0.5}},s+0.2);}});
    [{bd_js}].forEach(([id,s,e])=>{{tl.to(id,{{opacity:1,duration:0.4,ease:"power2.out"}},s);tl.to(id,{{opacity:0,duration:0.3,ease:"power2.in"}},e-0.35);tl.set(id,{{opacity:0}},e);}});
    const box=q("#capbox");
    (window.__captions||[]).forEach((c)=>{{tl.to(box,{{opacity:1,duration:0.1,onStart:()=>{{box.textContent=c.text;}}}},c.start);tl.to(box,{{opacity:0,duration:0.1}},c.end);}});
    tl.set(box,{{opacity:0}},{round(DUR-0.1,2)});
    window.__timelines=window.__timelines||{{}}; window.__timelines["main-video"]=tl;
  </script>
</div></body></html>'''
open(f"{ROOT}/compose/index.html","w",encoding="utf-8").write(html)
print(f"index.html v3: broll快切 {len(broll_clips)} + 像素 {len(PIX)} + 档案照1 + 角标 {len(BADGE)} + 章节 {len(CHAP)}")
print(f"总clip: {len(broll_clips)+len(PIX)+1} 视觉 | 覆盖 0-{DUR}s")
