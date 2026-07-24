#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 pixel-chronicle 合成 index.html（数据实物化 MG + collage + Pexels空镜 + 字幕/角标 + 缝合层）。
时间全部来自 film.json/timeline（compose 零手写秒数原则：镜头区间/字幕由 IR 派生）。BGM 轨预留(引擎暂不可用,DEBT)。"""
import json
ROOT="projects/dont-set-ac-26"
d=json.load(open(f"{ROOT}/film.json",encoding="utf-8"))
DUR=d['audio']['timeline']['duration_s']  # 185.64
shots={s['id']:s for s in d['shots']}
def slot(sid): return shots[sid]['t'][0], shots[sid]['t'][1]

# ---- 视频轨(track1): (elid, src, start, end, media_start, is_real) ----
VID=[
 ("altar","clips/altar.mp4",0.0,5.14,4.89,False),
 ("sweat","clips/s03_sweat_room.mp4",7.28,12.72,0.2,True),
 ("thermo","clips/s06_thermo_q.mp4",21.86,27.00,0.4,True),
 ("climates","clips/s07_climates.mp4",27.00,35.20,0.5,True),
 ("sweatm","clips/s09_sweat_sci.mp4",44.90,51.04,1.0,True),
 ("vuln","clips/s10_vulnerable.mp4",51.04,59.94,0.0,True),
 ("acrun","clips/s12_ac_running.mp4",67.06,74.50,0.2,True),
 ("smell","clips/smell.mp4",79.60,85.62,4.01,False),
 ("office","clips/s17_public_bldg.mp4",109.92,114.90,0.0,True),
 ("mall","clips/s17b_mall.mp4",114.90,119.00,0.0,True),
 ("thermostat","clips/s17c_thermostat.mp4",119.00,123.00,0.2,True),
 ("reach","clips/s19_intro.mp4",128.72,132.56,0.2,True),
 ("wind","clips/s21_tip_wind.mp4",148.94,156.88,0.5,True),
 ("cozy","clips/s24_cozy_home.mp4",175.90,180.30,0.2,True),
]

# ---- MG 场景(track2): (elid, start, end, inner_html) ----
def sc(elid,s,e,inner): return (elid,s,e,inner)
MG=[]
# s02 传说光环
MG.append(sc("myth",5.14,7.28,
 '<div class="ctr myth"><div class="halo"></div><div class="key26">26<span>℃</span></div>'
 '<div class="tag t-a">不冷不热</div><div class="tag t-b">省电</div></div>'))
# s04 三症状→报题
MG.append(sc("punch",12.72,21.86,
 '<div class="ctr punch">'
 '<div class="symp s1"><i>❄️</i><b>并不够凉</b></div><div class="symp s2"><i>💸</i><b>未必省电</b></div><div class="symp s3"><i>👃</i><b>还可能发臭</b></div>'
 '<div class="title26"><div class="big">26<span>℃</span></div><div class="tsub">其实没那么科学</div></div></div>'))
# s08 湿度体感对照 signature
MG.append(sc("humid",35.20,44.90,
 '<div class="ctr humid"><div class="hhead">同样 <b>27℃</b>，湿度决定体感</div>'
 '<div class="hrow"><div class="hcol c-ok"><div class="hum">湿度 50%</div><div class="face">🙂</div><div class="feel">体感 舒适</div></div>'
 '<div class="hcol c-bad"><div class="hum">湿度 80%</div><div class="face">🥵</div><div class="feel">体感≈<b>30℃</b> 闷黏</div></div></div></div>'))
# s11 空调内部剖面
MG.append(sc("acin",59.94,67.06,
 '<div class="ctr acin"><div class="chip">再说那股怪味</div>'
 '<div class="unit"><div class="coil"></div><div class="drip"></div>'
 '<div class="lab l1">灰尘</div><div class="lab l2">冷凝水</div><div class="lab l3">霉菌</div></div></div>'))
# s13 压缩机短循环
MG.append(sc("comp",74.50,79.60,
 '<div class="ctr comp"><div class="chead">26℃ 让压缩机</div>'
 '<div class="cyc"><span class="dot on">开</span><span class="dot">停</span><span class="dot on">开</span><span class="dot">停</span><span class="dot on">开</span></div>'
 '<div class="csub">反复启停 · 风忽大忽小</div></div>'))
# s15 设问
MG.append(sc("why",85.62,93.76,
 '<div class="ctr why"><div class="qmark">?</div><div class="qtext">不够凉、又发臭<br>怎么就<b>火遍全国</b></div>'
 '<div class="qtag">这其实是一场误会</div></div>'))
# s16 两档温度带 signature
MG.append(sc("tiers",93.76,109.92,
 '<div class="ctr tiers"><div class="thead">设计规范里的夏季舒适温度</div>'
 '<div class="scale"><div class="band b1"><span class="bl">I 级 · 较高标准</span><span class="br">24–26℃</span></div>'
 '<div class="band b2"><span class="bl">II 级 · 一般标准</span><span class="br">26–28℃</span></div>'
 '<div class="seam"><div class="pin">26℃</div><div class="pinlab">正好卡在中缝 · 折中数</div></div></div></div>'))
# s18 遥控器加键
MG.append(sc("rkey",123.00,128.72,
 '<div class="ctr rkey"><div class="remote"><div class="rscreen">26℃</div><div class="rkeys"><span></span><span></span><span class="hot">26</span><span></span></div></div>'
 '<div class="rlab">厂商顺手加了个专属键</div></div>'))
# s20_day 温度tip白天
MG.append(sc("tday",132.56,144.52,
 '<div class="ctr card"><div class="cnum">01</div><div class="ctitle">温度 · 白天</div>'
 '<ul class="rows"><li><b>22℃</b> + 大风速，15 分钟速降</li><li>再调回舒适温度，一般 <b>24–26℃</b></li></ul></div>'))
# s20_night 夜间
MG.append(sc("tnight",144.52,148.94,
 '<div class="ctr card"><div class="ctitle sm">温度 · 夜间</div>'
 '<ul class="rows"><li>睡觉温度<b>往上提 2℃</b></li><li>老人小孩<b>别低于 27℃</b></li></ul></div>'))
# s22 湿度tip
MG.append(sc("thum",156.88,161.56,
 '<div class="ctr card"><div class="cnum">02</div><div class="ctitle">湿度</div>'
 '<ul class="rows"><li>室内湿度 <b>&gt;60%</b>，先开「除湿」</li><li>不黏不腻，比一味降温更清爽</li></ul></div>'))
# s23 省电三招
MG.append(sc("tsave",161.56,175.90,
 '<div class="ctr card"><div class="cnum">03</div><div class="ctitle">省电三招</div>'
 '<ul class="rows big"><li>短时出门<b>别关机</b>，调高温度就行</li><li>长时间开，用 <b>ECO</b> 模式</li><li>滤网<b>半个月洗一次</b></li></ul></div>'))
# s25 金句
MG.append(sc("kick",180.30,185.64,
 '<div class="ctr kick"><div class="kq">先让屋里的人<b>舒服</b>，<br>才是真的会用空调。</div></div>'))

# ---- 章节卡(track2, 黑场闸门叠字): 打脸/溯源/正解 ----
CHAP=[  # 借用 MG 首镜前的极短闸门; 这里用叠在 punch 尾后 sec 边界的黑场由 fade-ish 处理,简化:不单独做章节卡,交给硬切+报题
]

# ---- 角标(track3): (elid, start, end, pos, html) ----
BADGE=[
 ("bWho",28.0,35.0,"tl",'<div class="t1">世界卫生组织：<b>没有</b>全球统一的室温标准</div>'),
 ("bSweat",45.6,51.0,"bl",'<div class="t1">湿度高 → 汗蒸发慢 → 热<span class="r">憋在身上</span></div>'),
 ("bVuln",52.0,59.8,"tl",'<div class="t1">热脆弱人群：<b>老人 · 小孩 · 孕妇 · 慢病</b></div>'),
 ("bAcrun",67.8,74.3,"bl",'<div class="t1">怪味只在开机头几十秒，风稳就散了</div>'),
 ("b42",110.5,122.8,"bl",'<div class="t1">国办发〔2007〕42号：公共建筑夏季空调 <b>≥26℃</b></div>'),
 ("bWind",149.6,156.6,"tr",'<div class="t1">出风口<b>朝上 ↑</b> · 冷气自然下沉更均匀</div>'),
]

# ---- logo 水印 ----
LOGO='<div id="logo" class="clip" data-start="0" data-duration="%.2f" data-track-index="6">生活祛魅 · 每天多懂一点</div>'%DUR

# ===================== CSS =====================
CSS = r'''
@font-face{font-family:"SerifSC";font-weight:700;src:url("assets/fonts/serif-sc-700-latin.woff2") format("woff2");unicode-range:U+0000-00FF,U+2000-206F,U+2190-21FF;}
@font-face{font-family:"SerifSC";font-weight:700;src:url("assets/fonts/serif-sc-700-cn.woff2") format("woff2");}
@font-face{font-family:"SansSC";font-weight:700;src:url("assets/fonts/sans-sc-700-latin.woff2") format("woff2");unicode-range:U+0000-00FF,U+2000-206F;}
@font-face{font-family:"SansSC";font-weight:700;src:url("assets/fonts/sans-sc-700-cn.woff2") format("woff2");}
@font-face{font-family:"SansSC";font-weight:400;src:url("assets/fonts/sans-sc-400-cn.woff2") format("woff2");}
:root{--paper:#C9A876;--ink:#2B2118;--cream:#F5EAD0;--accent:#FFD21E;--gilt:#6E4A0C;--mark:#8A2419;--ok:#2E6B40;}
*{margin:0;padding:0;box-sizing:border-box;}
body,html{width:1280px;height:720px;overflow:hidden;background:var(--ink);font-family:"SansSC",sans-serif;}
#main-composition{position:relative;width:1280px;height:720px;overflow:hidden;background:var(--ink);}
.fullframe{position:absolute;inset:0;width:1280px;height:720px;object-fit:cover;}
.real{filter:sepia(0.28) saturate(0.82) contrast(1.05) brightness(0.96);}
.mg{position:absolute;inset:0;width:1280px;height:720px;overflow:hidden;
  background:var(--paper);background-image:radial-gradient(circle at 30% 20%,rgba(245,234,208,0.35),transparent 60%);}
.ctr{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;color:var(--ink);}
/* s02 myth */
.myth .halo{position:absolute;width:520px;height:520px;border-radius:50%;opacity:0;
  background:radial-gradient(circle,rgba(255,210,30,0.55),transparent 62%);}
.myth .key26{font-family:"SerifSC";font-weight:700;font-size:170px;color:var(--ink);opacity:0;letter-spacing:2px;}
.myth .key26 span{font-size:80px;color:var(--gilt);}
.myth .tag{position:absolute;font-family:"SansSC";font-weight:700;font-size:34px;color:var(--ink);background:var(--cream);
  border:2px solid var(--gilt);border-radius:40px;padding:8px 26px;opacity:0;box-shadow:0 4px 14px rgba(43,33,24,0.25);}
.myth .t-a{left:270px;top:230px;} .myth .t-b{right:270px;top:400px;}
/* s04 punch */
.punch .symp{position:absolute;opacity:0;display:flex;align-items:center;gap:16px;background:var(--cream);border:2px solid var(--ink);
  border-radius:14px;padding:14px 30px;font-family:"SansSC";font-weight:700;font-size:40px;color:var(--ink);box-shadow:0 6px 0 rgba(43,33,24,0.85);}
.punch .symp i{font-style:normal;font-size:46px;} .punch .symp b{color:var(--mark);}
.punch .s1{left:150px;top:150px;} .punch .s2{right:150px;top:300px;} .punch .s3{left:220px;top:470px;}
.punch .title26{opacity:0;} .punch .title26 .big{font-family:"SerifSC";font-weight:700;font-size:210px;color:var(--ink);line-height:0.9;}
.punch .title26 .big span{font-size:96px;color:var(--gilt);} .punch .title26 .tsub{font-family:"SansSC";font-weight:700;font-size:52px;color:var(--mark);margin-top:10px;letter-spacing:4px;}
/* s08 humidity */
.humid .hhead{font-family:"SansSC";font-weight:700;font-size:46px;color:var(--ink);margin-bottom:36px;opacity:0;}
.humid .hhead b{color:var(--gilt);font-family:"SerifSC";font-size:56px;}
.humid .hrow{display:flex;gap:70px;}
.humid .hcol{opacity:0;width:390px;border-radius:20px;padding:30px 20px;border:3px solid var(--ink);background:var(--cream);}
.humid .c-ok{box-shadow:0 8px 0 rgba(62,124,79,0.6);} .humid .c-bad{box-shadow:0 8px 0 rgba(192,57,43,0.6);}
.humid .hum{font-family:"SansSC";font-weight:700;font-size:38px;color:var(--ink);} .humid .face{font-size:110px;margin:8px 0;}
.humid .feel{font-family:"SansSC";font-weight:700;font-size:34px;} .humid .c-ok .feel{color:var(--ok);} .humid .c-bad .feel{color:var(--mark);}
.humid .c-bad .feel b{font-family:"SerifSC";font-size:44px;}
/* s11 acin */
.acin .chip{position:absolute;top:70px;font-family:"SerifSC";font-weight:700;font-size:58px;color:var(--ink);letter-spacing:6px;opacity:0;}
.acin .chip::before{content:"『";color:var(--gilt);}.acin .chip::after{content:"』";color:var(--gilt);}
.acin .unit{position:relative;width:640px;height:230px;background:var(--cream);border:4px solid var(--ink);border-radius:20px;margin-top:60px;opacity:0;overflow:hidden;}
.acin .coil{position:absolute;left:0;right:0;top:60px;height:60px;background:repeating-linear-gradient(90deg,var(--ink) 0 6px,transparent 6px 22px);opacity:0.5;}
.acin .drip{position:absolute;left:0;right:0;bottom:0;height:34px;background:linear-gradient(180deg,transparent,rgba(43,33,24,0.35));}
.acin .lab{position:absolute;font-family:"SansSC";font-weight:700;font-size:30px;color:var(--mark);opacity:0;}
.acin .l1{left:120px;top:130px;} .acin .l2{right:120px;top:120px;} .acin .l3{left:50%;transform:translateX(-50%);bottom:90px;}
/* s13 comp */
.comp .chead{font-family:"SansSC";font-weight:700;font-size:52px;color:var(--ink);margin-bottom:30px;opacity:0;}
.comp .cyc{display:flex;gap:22px;}
.comp .dot{width:96px;height:96px;border-radius:16px;border:3px solid var(--ink);display:flex;align-items:center;justify-content:center;
  font-family:"SansSC";font-weight:700;font-size:38px;color:var(--ink);background:var(--cream);opacity:0;}
.comp .dot.on{background:var(--accent);} .comp .csub{margin-top:28px;font-family:"SansSC";font-weight:700;font-size:36px;color:var(--mark);opacity:0;}
/* s15 why */
.why .qmark{font-family:"SerifSC";font-weight:700;font-size:220px;color:var(--gilt);line-height:0.8;opacity:0;}
.why .qtext{font-family:"SansSC";font-weight:700;font-size:52px;color:var(--ink);margin-top:10px;opacity:0;line-height:1.3;}
.why .qtext b{color:var(--mark);} .why .qtag{margin-top:26px;font-family:"SerifSC";font-weight:700;font-size:42px;color:var(--ink);background:var(--accent);padding:8px 30px;border-radius:10px;opacity:0;}
/* s16 tiers */
.tiers .thead{font-family:"SansSC";font-weight:700;font-size:44px;color:var(--ink);margin-bottom:40px;opacity:0;}
.tiers .scale{position:relative;width:860px;}
.tiers .band{position:relative;height:96px;border-radius:14px;border:3px solid var(--ink);display:flex;align-items:center;justify-content:space-between;
  padding:0 34px;margin:16px 0;font-family:"SansSC";font-weight:700;opacity:0;}
.tiers .b1{background:#DDECDD;} .tiers .b2{background:#F3E2C2;}
.tiers .bl{font-size:34px;color:var(--ink);} .tiers .br{font-size:46px;color:var(--gilt);font-family:"SerifSC";}
.tiers .seam{position:absolute;left:50%;top:-10px;bottom:-10px;transform:translateX(-50%);display:flex;flex-direction:column;align-items:center;justify-content:center;opacity:0;}
.tiers .pin{font-family:"SerifSC";font-weight:700;font-size:64px;color:#fff;background:var(--mark);border-radius:12px;padding:6px 20px;box-shadow:0 4px 12px rgba(0,0,0,0.4);}
.tiers .pinlab{margin-top:10px;font-family:"SansSC";font-weight:700;font-size:30px;color:var(--mark);background:var(--cream);padding:4px 16px;border-radius:8px;}
/* s18 rkey */
.rkey .remote{width:230px;height:360px;background:var(--cream);border:4px solid var(--ink);border-radius:34px;padding:26px 0;display:flex;flex-direction:column;align-items:center;opacity:0;box-shadow:0 10px 0 rgba(43,33,24,0.4);}
.rkey .rscreen{width:170px;height:80px;background:#8FB6A6;border-radius:8px;display:flex;align-items:center;justify-content:center;font-family:"SerifSC";font-weight:700;font-size:44px;color:var(--ink);}
.rkey .rkeys{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:26px;}
.rkey .rkeys span{width:60px;height:60px;border-radius:50%;background:#E4D6B4;border:2px solid var(--ink);}
.rkey .rkeys .hot{background:var(--accent);font-family:"SansSC";font-weight:700;font-size:28px;color:var(--ink);display:flex;align-items:center;justify-content:center;opacity:0;}
.rkey .rlab{margin-top:34px;font-family:"SansSC";font-weight:700;font-size:38px;color:var(--ink);opacity:0;}
/* list cards s20/s22/s23 */
.card{padding:0 90px;} .card .cnum{font-family:"SerifSC";font-weight:700;font-size:120px;color:var(--gilt);opacity:0;line-height:0.8;}
.card .ctitle{font-family:"SerifSC";font-weight:700;font-size:70px;color:var(--ink);letter-spacing:4px;opacity:0;margin:6px 0 30px;}
.card .ctitle.sm{font-size:56px;}
.card .rows{list-style:none;text-align:left;max-width:900px;} .card .rows li{font-family:"SansSC";font-weight:700;font-size:44px;color:var(--ink);
  margin:18px 0;padding-left:44px;position:relative;opacity:0;}
.card .rows.big li{font-size:42px;} .card .rows li::before{content:"";position:absolute;left:0;top:14px;width:22px;height:22px;background:var(--accent);border:2px solid var(--ink);border-radius:5px;}
.card .rows li b{color:var(--mark);}
/* s25 kicker */
.kick .kq{font-family:"SerifSC";font-weight:700;font-size:66px;color:var(--ink);line-height:1.5;opacity:0;max-width:1000px;}
.kick .kq b{color:var(--mark);}
/* badges */
.badge{position:absolute;opacity:0;background:rgba(43,33,24,0.74);border:1px solid rgba(201,147,43,0.55);border-radius:10px;padding:12px 22px;max-width:760px;}
.badge .t1{font-family:"SansSC";font-weight:700;color:var(--cream);font-size:30px;line-height:1.35;}
.badge .t1 b{color:var(--accent);} .badge .t1 .r{color:#F0A090;}
.badge.tl{left:52px;top:56px;} .badge.tr{right:52px;top:56px;text-align:right;} .badge.bl{left:52px;bottom:150px;}
#capbox{position:absolute;left:50%;transform:translateX(-50%);bottom:40px;max-width:1040px;display:inline-block;
  background:rgba(43,33,24,0.74);padding:8px 26px;border-radius:8px;font-family:"SerifSC";font-weight:700;color:#fff;font-size:33px;line-height:1.3;text-align:center;text-shadow:0 2px 8px rgba(0,0,0,0.9);opacity:0;}
#logo{position:absolute;left:36px;top:26px;font-family:"SansSC";font-weight:700;font-size:23px;color:var(--cream);
  background:rgba(43,33,24,0.72);padding:5px 14px;border-radius:7px;letter-spacing:2px;}
#lut{position:absolute;inset:0;pointer-events:none;background:linear-gradient(180deg,rgba(201,168,118,0.10),transparent 42%,rgba(43,33,24,0.16));mix-blend-mode:multiply;}
#grain{position:absolute;inset:0;pointer-events:none;opacity:0.08;mix-blend-mode:overlay;background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>");}
#vig{position:absolute;inset:0;pointer-events:none;box-shadow:inset 0 0 150px 8px rgba(43,33,24,0.4);}
#fade{position:absolute;inset:0;background:#000;opacity:0;}
'''

# ===================== 组装 HTML =====================
H=[]
H.append('<!doctype html>')
H.append('<html lang="zh" data-resolution="landscape" data-fps="30">')
H.append('<head><meta charset="UTF-8"><title>空调别开26度 — Kuleshov</title>')
H.append('<script src="assets/gsap.min.js"></script><script src="assets/captions_data.js"></script>')
H.append('<style>'+CSS+'</style></head><body>')
H.append(f'<div id="main-composition" data-composition-id="main-video" data-width="1280" data-height="720" data-start="0" data-duration="{DUR:.2f}" data-fps="30">')
# audio
H.append(f'  <audio id="vo" class="clip" src="assets/voiceover.mp3" data-start="0" data-duration="{DUR:.2f}" data-track-index="0" data-volume="1" data-has-audio="true"></audio>')
H.append('  <!-- BGM 轨 DEBT: MiniMax music 引擎当前网关不可用(404),VO-first出片,BGM待引擎恢复后muxin -->')
# video track1
for elid,src,s,e,ms,real in VID:
    cls="clip fullframe real" if real else "clip fullframe"
    H.append(f'  <video id="v_{elid}" class="{cls}" src="assets/{src}" muted data-start="{s:.2f}" data-duration="{e-s:.2f}" data-media-start="{ms:.2f}" data-track-index="1"></video>')
# MG track2
for elid,s,e,inner in MG:
    H.append(f'  <div id="mg_{elid}" class="clip mg" data-start="{s:.2f}" data-duration="{e-s:.2f}" data-track-index="2">{inner}</div>')
# badges track3
for elid,s,e,pos,html in BADGE:
    H.append(f'  <div id="{elid}" class="clip badge {pos}" data-start="{s:.2f}" data-duration="{e-s:.2f}" data-track-index="3">{html}</div>')
# capbox, logo, layers
H.append(f'  <div id="capbox" class="clip" data-start="0" data-duration="{DUR:.2f}" data-track-index="5"></div>')
H.append('  '+LOGO)
for lid,ti in [("lut",100),("grain",102),("vig",103),("fade",104)]:
    H.append(f'  <div id="{lid}" class="clip" data-start="0" data-duration="{DUR:.2f}" data-track-index="{ti}"></div>')

# ===================== GSAP =====================
J=[]
J.append('<script>')
J.append('const tl=gsap.timeline({paused:true});')
# helper appear/disappear for MG scene inner elements handled per-scene below
# s02 myth
J.append('tl.fromTo("#mg_myth .halo",{opacity:0,scale:0.6},{opacity:1,scale:1,duration:0.5,ease:"power2.out"},5.24);')
J.append('tl.fromTo("#mg_myth .key26",{opacity:0,scale:1.2},{opacity:1,scale:1,duration:0.4,ease:"power3.out"},5.3);')
J.append('tl.fromTo("#mg_myth .t-a",{opacity:0,y:16},{opacity:1,y:0,duration:0.3},5.9);')
J.append('tl.fromTo("#mg_myth .t-b",{opacity:0,y:16},{opacity:1,y:0,duration:0.3},6.3);')
# s04 punch: three symptoms staggered then title
J.append('[["#mg_punch .s1",13.0],["#mg_punch .s2",13.9],["#mg_punch .s3",14.8]].forEach(([id,t])=>{tl.fromTo(id,{opacity:0,scale:1.3,y:-10},{opacity:1,scale:1,y:0,duration:0.35,ease:"power4.out"},t);});')
J.append('tl.to("#mg_punch .symp",{opacity:0,duration:0.3},17.4);')
J.append('tl.fromTo("#mg_punch .title26",{opacity:0,scale:1.15},{opacity:1,scale:1,duration:0.5,ease:"power3.out"},17.7);')
# s08 humidity
J.append('tl.fromTo("#mg_humid .hhead",{opacity:0,y:14},{opacity:1,y:0,duration:0.4},35.5);')
J.append('tl.fromTo("#mg_humid .c-ok",{opacity:0,y:26},{opacity:1,y:0,duration:0.45,ease:"power2.out"},36.2);')
J.append('tl.fromTo("#mg_humid .c-bad",{opacity:0,y:26},{opacity:1,y:0,duration:0.45,ease:"power2.out"},39.6);')
# s11 acin
J.append('tl.fromTo("#mg_acin .chip",{opacity:0},{opacity:1,duration:0.4},60.1);')
J.append('tl.fromTo("#mg_acin .unit",{opacity:0,y:20},{opacity:1,y:0,duration:0.5},60.8);')
J.append('[["#mg_acin .l1",62.2],["#mg_acin .l2",63.2],["#mg_acin .l3",64.2]].forEach(([id,t])=>tl.fromTo(id,{opacity:0,scale:1.2},{opacity:1,scale:1,duration:0.3},t));')
# s13 comp
J.append('tl.fromTo("#mg_comp .chead",{opacity:0},{opacity:1,duration:0.35},74.7);')
J.append('gsap.utils.toArray("#mg_comp .dot").forEach((el,i)=>tl.fromTo(el,{opacity:0,scale:0.7},{opacity:1,scale:1,duration:0.22,ease:"power3.out"},75.2+i*0.32));')
J.append('tl.fromTo("#mg_comp .csub",{opacity:0},{opacity:1,duration:0.35},77.2);')
# s15 why
J.append('tl.fromTo("#mg_why .qmark",{opacity:0,scale:0.7},{opacity:1,scale:1,duration:0.4,ease:"power3.out"},85.9);')
J.append('tl.fromTo("#mg_why .qtext",{opacity:0,y:16},{opacity:1,y:0,duration:0.4},86.6);')
J.append('tl.fromTo("#mg_why .qtag",{opacity:0,scale:0.9},{opacity:1,scale:1,duration:0.4,ease:"back.out(1.6)"},91.9);')
# s16 tiers
J.append('tl.fromTo("#mg_tiers .thead",{opacity:0,y:14},{opacity:1,y:0,duration:0.4},94.1);')
J.append('tl.fromTo("#mg_tiers .b1",{opacity:0,x:-40},{opacity:1,x:0,duration:0.5,ease:"power2.out"},95.2);')
J.append('tl.fromTo("#mg_tiers .b2",{opacity:0,x:40},{opacity:1,x:0,duration:0.5,ease:"power2.out"},96.6);')
J.append('tl.fromTo("#mg_tiers .seam",{opacity:0,scale:0.7},{opacity:1,scale:1,duration:0.5,ease:"back.out(1.8)"},104.4);')
# s18 rkey
J.append('tl.fromTo("#mg_rkey .remote",{opacity:0,y:26},{opacity:1,y:0,duration:0.5},123.3);')
J.append('tl.fromTo("#mg_rkey .rkeys .hot",{opacity:0,scale:1.6},{opacity:1,scale:1,duration:0.4,ease:"back.out(2)"},124.6);')
J.append('tl.fromTo("#mg_rkey .rlab",{opacity:0},{opacity:1,duration:0.4},125.4);')
# list cards
def listcard(prefix,base):
    return (f'tl.fromTo("#mg_{prefix} .cnum",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.4}},{base});'
            f'tl.fromTo("#mg_{prefix} .ctitle",{{opacity:0,y:14}},{{opacity:1,y:0,duration:0.4}},{base+0.3});'
            f'gsap.utils.toArray("#mg_{prefix} .rows li").forEach((el,i)=>tl.fromTo(el,{{opacity:0,x:-24}},{{opacity:1,x:0,duration:0.4,ease:"power2.out"}},{base+0.8}+i*0.9));')
J.append(listcard("tday",132.9))
J.append(listcard("tnight",144.8))
J.append(listcard("thum",157.2))
J.append(listcard("tsave",161.9))
# s25 kicker
J.append('tl.fromTo("#mg_kick .kq",{opacity:0,y:20},{opacity:1,y:0,duration:0.8,ease:"power2.out"},180.7);')
# badges
J.append('[["#bWho",28.0,35.0],["#bSweat",45.6,51.0],["#bVuln",52.0,59.8],["#bAcrun",67.8,74.3],["#b42",110.5,122.8],["#bWind",149.6,156.6]].forEach(([id,s,e])=>{tl.to(id,{opacity:1,duration:0.4,ease:"power2.out"},s);tl.to(id,{opacity:0,duration:0.3},e-0.35);tl.set(id,{opacity:0},e);});')
# captions
J.append('const box=document.querySelector("#capbox");')
J.append('(window.__captions||[]).forEach((c)=>{tl.to(box,{opacity:1,duration:0.08,onStart:()=>{box.textContent=c.text;}},c.start);tl.to(box,{opacity:0,duration:0.08},c.end);});')
J.append(f'tl.set(box,{{opacity:0}},{DUR-0.1:.2f});')
# fade out tail
J.append(f'tl.to("#fade",{{opacity:1,duration:1.2,ease:"none"}},{DUR-1.2:.2f});')
J.append('window.__timelines=window.__timelines||{};window.__timelines["main-video"]=tl;')
J.append('</script>')
H.append('\n'.join(J))
H.append('</div></body></html>')
open(f"{ROOT}/compose/index.html","w",encoding="utf-8").write('\n'.join(H))
print("index.html written:",len('\n'.join(H)),"bytes")
print("clips:",len(VID)," MG scenes:",len(MG)," badges:",len(BADGE))
