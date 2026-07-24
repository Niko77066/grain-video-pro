#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v2 合成：B音色新时间轴(198.8s) + 11 拼贴叙事(collage,像素叙事~40%) + MG只留硬数据 + BGM垫底轨。
时间从 shot 表驱动；MG 场景内部动画用相对偏移，重排时间自动跟随。"""
import json
ROOT="projects/dont-set-ac-26"
DUR=198.81
# ===== shot 表: (id, kind, start, end, extra) =====
# kind: collage(视频轨,尾对齐或头对齐) / footage(视频轨,.real) / mg(全屏场景)
S=[
 ("altar","collage",0.0,5.66,{"clip":"altar.mp4","align":"tail"}),
 ("myth","mg",5.66,8.18,{}),
 ("s03_sweat","collage",8.18,13.94,{"clip":"v2_s03_sweat.mp4","align":"tail"}),
 ("punch","mg",13.94,23.04,{}),
 ("s06_thermo","footage",23.04,28.58,{"clip":"s06_thermo_q.mp4","ms":0.4}),
 ("s07_heat","collage",28.58,37.60,{"clip":"v2_s07_heat.mp4","align":"tail"}),
 ("humid","mg",37.60,47.02,{}),
 ("s09_sweat","collage",47.02,53.04,{"clip":"v2_s09_sweat_sci.mp4","align":"tail"}),
 ("s10_vuln","collage",53.04,62.14,{"clip":"v2_s10_vulnerable.mp4","align":"tail"}),
 ("s11_acin","collage",62.14,69.82,{"clip":"v2_s11_ac_inside.mp4","align":"tail"}),
 ("s12_acrun","footage",69.82,76.34,{"clip":"s12_ac_running.mp4","ms":0.2}),
 ("s13_comp","collage",76.34,81.70,{"clip":"v2_s13_compressor.mp4","align":"tail"}),
 ("s14_smell","collage",81.70,87.82,{"clip":"smell.mp4","align":"tail"}),
 ("why","mg",87.82,97.00,{}),
 ("tiers","mg",97.00,115.34,{}),
 ("s17a_office","footage",115.34,120.30,{"clip":"s17_public_bldg.mp4","ms":0.0}),
 ("s17b_mall","footage",120.30,124.80,{"clip":"s17b_mall.mp4","ms":0.0}),
 ("s17c_thermostat","footage",124.80,129.76,{"clip":"s17c_thermostat.mp4","ms":0.2}),
 ("s18_rkey","collage",129.76,136.30,{"clip":"v2_s18_remote_key.mp4","align":"tail"}),
 ("s19_intro","footage",136.30,139.90,{"clip":"s19_intro.mp4","ms":0.2}),
 ("tday","mg",139.90,152.64,{}),
 ("tnight","mg",152.64,157.40,{}),
 ("s21_wind","collage",157.40,166.40,{"clip":"v2_s21_wind.mp4","align":"tail"}),
 ("thum","mg",166.40,171.98,{}),
 ("tsave","mg",171.98,187.58,{}),
 ("s06_cozy","collage",187.58,197.62,{"clip":"v2_s06_cozy.mp4","align":"head"}),
]
# ===== MG 场景内容(与 v1 同,内容不变) =====
MG_HTML={
"myth":'<div class="ctr myth"><div class="halo"></div><div class="key26">26<span>℃</span></div><div class="tag t-a">不冷不热</div><div class="tag t-b">省电</div></div>',
"punch":'<div class="ctr punch"><div class="symp s1"><i>❄️</i><b>并不够凉</b></div><div class="symp s2"><i>💸</i><b>未必省电</b></div><div class="symp s3"><i>👃</i><b>还可能发臭</b></div><div class="title26"><div class="big">26<span>℃</span></div><div class="tsub">其实没那么科学</div></div></div>',
"humid":'<div class="ctr humid"><div class="hhead">同样 <b>27℃</b>，湿度决定体感</div><div class="hrow"><div class="hcol c-ok"><div class="hum">湿度 50%</div><div class="face">🙂</div><div class="feel">体感 舒适</div></div><div class="hcol c-bad"><div class="hum">湿度 80%</div><div class="face">🥵</div><div class="feel">体感≈<b>30℃</b> 闷黏</div></div></div></div>',
"why":'<div class="ctr why"><div class="qmark">?</div><div class="qtext">不够凉、又发臭<br>怎么就<b>火遍全国</b></div><div class="qtag">这其实是一场误会</div></div>',
"tiers":'<div class="ctr tiers"><div class="thead">设计规范里的夏季舒适温度</div><div class="scale"><div class="band b1"><span class="bl">I 级 · 较高标准</span><span class="br">24–26℃</span></div><div class="band b2"><span class="bl">II 级 · 一般标准</span><span class="br">26–28℃</span></div><div class="seam"><div class="pin">26℃</div></div></div><div class="pinnote">正好卡在两档的中缝 · 是个折中数</div></div>',
"tday":'<div class="ctr card"><div class="cnum">01</div><div class="ctitle">温度 · 白天</div><ul class="rows"><li><b>22℃</b> + 大风速，15 分钟速降</li><li>再调回舒适温度，一般 <b>24–26℃</b></li></ul></div>',
"tnight":'<div class="ctr card"><div class="ctitle sm">温度 · 夜间</div><ul class="rows"><li>睡觉温度<b>往上提 2℃</b></li><li>老人小孩<b>别低于 27℃</b></li></ul></div>',
"thum":'<div class="ctr card"><div class="cnum">02</div><div class="ctitle">湿度</div><ul class="rows"><li>室内湿度 <b>&gt;60%</b>，先开「除湿」</li><li>不黏不腻，比一味降温更清爽</li></ul></div>',
"tsave":'<div class="ctr card"><div class="cnum">03</div><div class="ctitle">省电三招</div><ul class="rows big"><li>短时出门<b>别关机</b>，调高温度就行</li><li>长时间开，用 <b>ECO</b> 模式</li><li>滤网<b>半个月洗一次</b></li></ul></div>',
}
# MG 动画: scene -> list of (selector, offset, dur, kind)  kind: fade/pop/slideL/slideR/rise
MG_ANIM={
"myth":[(".halo",0.1,0.5,"pop"),(".key26",0.16,0.4,"pop"),(".t-a",0.7,0.3,"rise"),(".t-b",1.1,0.3,"rise")],
"punch":[(".s1",0.3,0.35,"pop"),(".s2",1.2,0.35,"pop"),(".s3",2.1,0.35,"pop"),(".title26",5.0,0.5,"pop")],
"humid":[(".hhead",0.3,0.4,"rise"),(".c-ok",1.0,0.45,"rise"),(".c-bad",4.4,0.45,"rise")],
"why":[(".qmark",0.3,0.4,"pop"),(".qtext",1.0,0.4,"rise"),(".qtag",6.3,0.4,"pop")],
"tiers":[(".thead",0.3,0.4,"rise"),(".b1",1.4,0.5,"slideL"),(".b2",2.8,0.5,"slideR"),(".seam",10.6,0.5,"pop"),(".pinnote",11.2,0.4,"rise")],
"tday":[(".cnum",0.3,0.4,"rise"),(".ctitle",0.6,0.4,"rise"),(".rows li:nth-child(1)",1.1,0.4,"slideL"),(".rows li:nth-child(2)",2.0,0.4,"slideL")],
"tnight":[(".ctitle",0.2,0.4,"rise"),(".rows li:nth-child(1)",0.8,0.4,"slideL"),(".rows li:nth-child(2)",1.6,0.4,"slideL")],
"thum":[(".cnum",0.3,0.4,"rise"),(".ctitle",0.6,0.4,"rise"),(".rows li:nth-child(1)",1.1,0.4,"slideL"),(".rows li:nth-child(2)",2.0,0.4,"slideL")],
"tsave":[(".cnum",0.3,0.4,"rise"),(".ctitle",0.6,0.4,"rise"),(".rows li:nth-child(1)",1.1,0.4,"slideL"),(".rows li:nth-child(2)",2.0,0.4,"slideL"),(".rows li:nth-child(3)",2.9,0.4,"slideL")],
}
# 角标: (id,start,end,pos,html)  时间对齐新时间轴
BADGE=[
 ("bWho",29.5,37.4,"tl",'<div class="t1">世界卫生组织：<b>没有</b>全球统一的室温标准</div>'),
 ("bVuln",54.0,61.9,"tl",'<div class="t1">热脆弱人群：<b>老人 · 小孩 · 孕妇 · 慢病</b></div>'),
 ("bAcrun",70.5,76.1,"bl",'<div class="t1">怪味只在开机头几十秒，风稳就散了</div>'),
 ("b42",116.0,129.5,"bl",'<div class="t1">国办发〔2007〕42号：公共建筑夏季空调 <b>≥26℃</b></div>'),
 ("bWind",158.2,166.1,"tr",'<div class="t1">出风口<b>朝上 ↑</b> · 冷气自然下沉更均匀</div>'),
]
KICKER='<div id="kicker" class="clip kickov" data-start="192.60" data-duration="6.21" data-track-index="3"><div class="kq">先让屋里的人<b>舒服</b>，<br>才是真的会用空调。</div></div>'
CLIPLEN=10.04  # collage 实际时长

CSS=open(f"{ROOT}/compose/_v2css.txt").read() if False else None
# 复用 v1 CSS + 追加 kicker 叠层样式
V1=open(f"{ROOT}/compose/index.html").read()
css_start=V1.find("<style>")+7; css_end=V1.find("</style>")
CSS=V1[css_start:css_end]
CSS+="""
.kickov{position:absolute;left:0;right:0;bottom:120px;text-align:center;opacity:0;}
.kickov .kq{display:inline-block;font-family:"SerifSC";font-weight:700;font-size:58px;color:#fff;line-height:1.5;
  background:rgba(43,33,24,0.62);padding:20px 44px;border-radius:14px;text-shadow:0 3px 12px rgba(0,0,0,0.9);}
.kickov .kq b{color:var(--accent);}
/* v3 fixes: tiers 叠加不再重叠 + 去掉左上小标题 */
.tiers .scale{position:relative;width:900px;}
.tiers .band{margin:26px 0;}
.tiers .seam{position:absolute;left:50%;top:50%;bottom:auto;transform:translate(-50%,-50%);flex-direction:column;opacity:0;}
.tiers .pin{font-size:50px;padding:4px 18px;box-shadow:0 4px 14px rgba(0,0,0,0.45);}
.tiers .pinnote{margin-top:34px;font-family:"SansSC";font-weight:700;font-size:32px;color:var(--mark);opacity:0;}
#logo{display:none!important;}
"""

H=['<!doctype html>','<html lang="zh" data-resolution="landscape" data-fps="30">',
'<head><meta charset="UTF-8"><title>空调别开26度 v2 — Kuleshov</title>',
'<script src="assets/gsap.min.js"></script><script src="assets/captions_data.js"></script>',
'<style>'+CSS+'</style></head><body>',
f'<div id="main-composition" data-composition-id="main-video" data-width="1280" data-height="720" data-start="0" data-duration="{DUR:.2f}" data-fps="30">',
f'  <audio id="vo" class="clip" src="assets/voiceover.mp3" data-start="0" data-duration="{DUR:.2f}" data-track-index="0" data-volume="1" data-has-audio="true"></audio>',
f'  <audio id="bgm" class="clip" src="assets/bgm_bed.mp3" data-start="0" data-duration="198.98" data-track-index="4" data-volume="1" data-has-audio="true"></audio>']
# video track (collage+footage)
for sid,kind,s,e,x in S:
    if kind not in("collage","footage"): continue
    dur=e-s
    if kind=="collage":
        ms = round(CLIPLEN-dur,2) if x.get("align")=="tail" else 0.0
        cls="clip fullframe"
    else:
        ms=x.get("ms",0.2); cls="clip fullframe real"
    H.append(f'  <video id="v_{sid}" class="{cls}" src="assets/clips/{x["clip"]}" muted data-start="{s:.2f}" data-duration="{dur:.2f}" data-media-start="{ms:.2f}" data-track-index="1"></video>')
# MG scenes
for sid,kind,s,e,x in S:
    if kind!="mg": continue
    H.append(f'  <div id="mg_{sid}" class="clip mg" data-start="{s:.2f}" data-duration="{e-s:.2f}" data-track-index="2">{MG_HTML[sid]}</div>')
# badges + kicker + logo + layers
for bid,s,e,pos,html in BADGE:
    H.append(f'  <div id="{bid}" class="clip badge {pos}" data-start="{s:.2f}" data-duration="{e-s:.2f}" data-track-index="3">{html}</div>')
H.append('  '+KICKER)
H.append(f'  <div id="capbox" class="clip" data-start="0" data-duration="{DUR:.2f}" data-track-index="5"></div>')
# v3: 去掉左上角小标题水印(用户要求)
for lid,ti in [("lut",100),("grain",102),("vig",103),("fade",104)]:
    H.append(f'  <div id="{lid}" class="clip" data-start="0" data-duration="{DUR:.2f}" data-track-index="{ti}"></div>')
# GSAP
J=['<script>','const tl=gsap.timeline({paused:true});']
def anim(sel,t,dur,kind):
    fr={"pop":"{opacity:0,scale:1.15}","rise":"{opacity:0,y:16}","slideL":"{opacity:0,x:-24}","slideR":"{opacity:0,x:24}","fade":"{opacity:0}"}[kind]
    to={"pop":"{opacity:1,scale:1,duration:%.2f,ease:'power3.out'}","rise":"{opacity:1,y:0,duration:%.2f,ease:'power2.out'}","slideL":"{opacity:1,x:0,duration:%.2f,ease:'power2.out'}","slideR":"{opacity:1,x:0,duration:%.2f,ease:'power2.out'}","fade":"{opacity:1,duration:%.2f}"}[kind]%dur
    return f"tl.fromTo('{sel}',{fr},{to},{t:.2f});"
for sid,kind,s,e,x in S:
    if kind!="mg": continue
    for sel,off,dur,k in MG_ANIM.get(sid,[]):
        J.append(anim(f"#mg_{sid} {sel}",s+off,dur,k))
    if sid=="punch":  # symptoms fade out before title
        J.append(f"tl.to('#mg_punch .symp',{{opacity:0,duration:0.3}},{s+4.6:.2f});")
# badges + kicker fade in/out
for bid,s,e,pos,html in BADGE+[("kicker",192.60,198.81,"","")]:
    J.append(f"tl.to('#{bid}',{{opacity:1,duration:0.4,ease:'power2.out'}},{s:.2f});tl.to('#{bid}',{{opacity:0,duration:0.3}},{e-0.35:.2f});tl.set('#{bid}',{{opacity:0}},{e:.2f});")
# captions
J.append('const box=document.querySelector("#capbox");')
J.append('(window.__captions||[]).forEach((c)=>{tl.to(box,{opacity:1,duration:0.08,onStart:()=>{box.textContent=c.text;}},c.start);tl.to(box,{opacity:0,duration:0.08},c.end);});')
J.append(f'tl.set(box,{{opacity:0}},{DUR-0.1:.2f});')
J.append(f'tl.to("#fade",{{opacity:1,duration:1.2,ease:"none"}},{DUR-1.2:.2f});')
J.append('window.__timelines=window.__timelines||{};window.__timelines["main-video"]=tl;')
J.append('</script>')
H.append('\n'.join(J)); H.append('</div></body></html>')
open(f"{ROOT}/compose/index.html","w").write('\n'.join(H))
from collections import Counter
c=Counter(k for _,k,_,_,_ in S)
print("v2 index.html written. shots:",len(S),dict(c))
