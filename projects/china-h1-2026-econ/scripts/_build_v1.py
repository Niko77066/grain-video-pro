#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""IR → HyperFrames composition 生成器（compose 阶段）。

纪律（SKILL §⑧ / references/hyperframes.md）：
- **compose 里禁止手写脱离 audio.timeline 的秒数**：所有镜头区间从 film.json.shots[].t 读，
  所有元素入场时刻从 audio/timeline_fa.json 的逐字戳用 `cue("关键词")` 派生。换音轨后重跑本
  脚本即全链路跟随。
- timeline `{paused:true}` + 注册到 window.__timelines[compositionId]；
- <video> 一律 muted、且是根的直接子节点；声音走独立 <audio>；
- 禁 Math.random / Date.now / rAF / repeat:-1；只 tween transform/opacity/color/borderRadius。

用法: build_compose.py <project_dir>
"""
import json, re, sys
from pathlib import Path

P = Path(sys.argv[1] if len(sys.argv) > 1 else "projects/china-h1-2026-econ")
ir = json.loads((P / "film.json").read_text(encoding="utf-8"))
fa = json.loads((P / "audio/timeline_fa.json").read_text(encoding="utf-8"))
DUR = ir["audio"]["timeline"]["duration_s"]
SHOT = {s["id"]: s for s in ir["shots"]}
CID = "econ26"

# ---------------------------------------------------------------- 词点 cue
_chars = "".join(w["w"] for w in fa["words"])


def cue(phrase, nth=0, at="start"):
    """返回剧本中某个词组的真实音频戳（首字起点 / 末字终点）。查不到即报错，不许估算。"""
    pos = -1
    for _ in range(nth + 1):
        pos = _chars.find(phrase, pos + 1)
        if pos < 0:
            raise SystemExit(f"cue 未命中: {phrase!r} (nth={nth})")
    i = pos if at == "start" else pos + len(phrase) - 1
    return round(fa["words"][i]["t"][0 if at == "start" else 1], 3)


def t0(sid):
    return round(SHOT[sid]["t"][0], 3)


def t1(sid):
    return round(SHOT[sid]["t"][1], 3)


def dur(sid):
    return round(SHOT[sid]["t"][1] - SHOT[sid]["t"][0], 3)


# ---------------------------------------------------------------- 媒体表
VIDEOS = [  # (dom_id, shot_id, file, extra_class)
    ("v_s01", "s01_hook_anchor",     "assets/clips/av_s01.mp4",      "anchor"),
    ("v_s03", "s03_city_aerial",     "assets/clips/c_s03_sky.mp4",   "real"),
    ("v_s05", "s05_site_aerial",     "assets/clips/c_s05_site.mp4",  "real"),
    ("v_s07", "s07_street_crowd",    "assets/clips/c_s07_street.mp4","real"),
    ("v_s08", "s08_question_anchor", "assets/clips/av_s08.mp4",      "anchor"),
    ("v_s09", "s09_port_aerial",     "assets/clips/c_s09_port.mp4",  "real"),
    ("v_s11", "s11_robot_line",      "assets/clips/c_s11_robot.mp4", "real"),
    ("v_s15", "s15_supermarket",     "assets/clips/c_s15_market.mp4","real"),
    ("v_s17", "s17_close_anchor",    "assets/clips/av_s17.mp4",      "anchor"),
]
PHOTOS = [  # (dom_id, shot_id, file, kenburns_to)
    ("ph_s06", "s06_housing_photo",    "assets/img/i_s06_housing.jpg",    1.045),
    ("ph_s10", "s10_containers_photo", "assets/img/i_s10_containers.jpg", 1.050),
    ("ph_s12", "s12_equipment_photo",  "assets/img/i_s12_equipment.jpg",  1.040),
]
# 带来源脚注的镜头（数据在场时才挂脚注，不占满全片）
FOOT_SHOTS = ["s02_gdp_screen", "s03_city_aerial", "s05_site_aerial", "s06_housing_photo",
              "s07_street_crowd", "s09_port_aerial", "s10_containers_photo",
              "s11_robot_line", "s12_equipment_photo", "s13_output_bars",
              "s15_supermarket", "s16_cpi_card", "s18_end_card"]

# ---------------------------------------------------------------- 版式片段
def metric(lab, val, note, cls, aid):
    u = ""
    m = re.match(r"^(.*?)(%)$", val)
    if m:
        val, u = m.group(1), '<span class="u">%</span>'
    return (f'<div class="metric" data-a="{aid}"><div class="lab">{lab}</div>'
            f'<div class="val {cls}">{val}{u}</div>'
            f'<div class="note">{note}</div></div>')


def barrow(lab, val, pct, color, aid):
    return (f'<div class="brow" data-a="{aid}"><div class="bk"><span>{lab}</span>'
            f'<b style="color:{color}">{val}</b></div>'
            f'<div class="btrack"><i data-bar="{aid}" style="width:{pct}%;background:{color}"></i></div></div>')


BUG = ('<div id="bug"><span class="mark"></span><span class="txt">经济半年报</span>'
       '<span class="date">2026 上半年</span></div>')
FOOT = '<div id="foot">数据来源：国家统计局 2026 年 7 月 15 日发布</div>'

GOLD, RED, BLUE, DIM = "var(--gold)", "#E8555C", "#5FB0E8", "var(--ink-dim)"

SCENES = []   # (dom_id, shot_id, css_class, inner_html)

SCENES.append(("ov_s01", "s01_hook_anchor", "ov", f"""
<div class="scrim-r"></div>
<div class="scrim-b"></div>
<div class="datacol">
  {metric('国内生产总值 · 同比', '+4.7%', '落在全年 4.5—5% 目标区间内', 'up', 'm1')}
  {metric('固定资产投资 · 同比', '−5.7%', '其中房地产开发投资 −18.0%', 'down', 'm2')}
</div>
<div class="rule lowerrule" data-a="rule"></div>
<div class="lower">
  <div class="kicker" data-a="kick">同一张表</div>
  <div class="headline" data-a="head">两组数字，方向正好相反</div>
</div>"""))

SCENES.append(("mg_s02", "s02_gdp_screen", "mg", f"""
<div class="grid-bg" data-a="gridbg" data-layout-allow-overflow></div>
<div class="pane">
  <div class="ptitle" data-a="pt">上半年国内生产总值</div>
  <div class="gdprow">
    <div class="gdpleft">
      <div class="bignum" data-a="big"><span data-count="69.57" data-dec="2">0.00</span><span class="unit">万亿元</span></div>
      <div class="yoy" data-a="yoy">同比 <b>+4.7%</b></div>
      <div class="band" data-a="band"><span>全年目标区间 4.5—5%</span></div>
    </div>
    <div class="gdpright">
      <div class="qbars">
        <div class="qb"><div class="qtrack"><i data-a="q1"></i></div><div class="qlab">一季度 <b>+5.0%</b></div></div>
        <div class="qb"><div class="qtrack"><i data-a="q2"></i></div><div class="qlab">二季度 <b>+4.3%</b></div></div>
      </div>
    </div>
  </div>
</div>"""))

SCENES.append(("ov_s03", "s03_city_aerial", "ov", """
<div class="stripwrap" data-a="strip"><div class="strip">
  <span class="sk">全年目标区间</span><span class="sv">4.5—5%</span>
  <span class="sdiv"></span><span class="sk">上半年实际</span><span class="sv gold">+4.7%</span>
</div></div>"""))

SCENES.append(("mg_s04", "s04_turn_card", "mg", """
<div class="grid-bg" data-a="gridbg" data-layout-allow-overflow></div>
<div class="turn">
  <div class="kicker" data-a="kick">但翻到投资和消费</div>
  <div class="turnbig" data-a="big">情况<span class="rev">反过来</span>了</div>
</div>
<div class="flipcol">
  <div class="fliprow up" data-a="a1"><span class="ar">▲</span>
    <div class="ftxt"><div class="fl">国内生产总值</div><div class="fv">+4.7%</div></div></div>
  <div class="fliprow down" data-a="a2"><span class="ar">▼</span>
    <div class="ftxt"><div class="fl">投资 · 消费</div><div class="fv small">同时往下走</div></div></div>
</div>"""))

SCENES.append(("ov_s05", "s05_site_aerial", "ov", """
<div class="tag-ll" data-a="tag">
  <div class="tk">固定资产投资 · 上半年同比</div>
  <div class="tv down"><span data-count="-5.7" data-dec="1">0.0</span>%</div>
  <div class="tbar"><i data-a="tb"></i></div>
</div>"""))

SCENES.append(("ph_s06", "s06_housing_photo", "ph", """
<img src="assets/img/i_s06_housing.jpg" data-a="kb">
<div class="veil-b"></div>
<div class="hugewrap" data-a="huge">
  <div class="hk">房地产开发投资</div>
  <div class="hv down"><span data-count="-18.0" data-dec="1">0.0</span>%</div>
</div>"""))

SCENES.append(("ov_s07", "s07_street_crowd", "ov", """
<div class="tag-lr" data-a="tag">
  <div class="tk">社会消费品零售总额 · 上半年</div>
  <div class="tv flat">+<span data-count="1.3" data-dec="1">0.0</span>%</div>
  <div class="tsub">248722 亿元</div>
</div>"""))

SCENES.append(("ov_s08", "s08_question_anchor", "ov", """
<div class="scrim-r"></div>
<div class="qmark" data-a="q">?</div>
<div class="qghost" data-a="g">4.7<span class="u">%</span></div>"""))

SCENES.append(("ov_s09", "s09_port_aerial", "ov", f"""
<div class="scrim-b"></div>
<div class="card" data-a="card">
  <div class="ct">货物进出口 · 累计同比</div>
  <div class="cs"><span data-count="25.47" data-dec="2">0.00</span> 万亿元</div>
  <div class="bars">
    {barrow('进出口合计', '+16.9%', 68, GOLD, 'b1')}
  </div>
  <div class="cfoot" data-a="cf">其中机电产品出口 <b>+20.1%</b>，占出口总额 <b>63.5%</b></div>
</div>
<div class="rule lowerrule" data-a="rule"></div>
<div class="lower">
  <div class="kicker" data-a="kick">谁扛起了 4.7%</div>
  <div class="headline" data-a="head">外贸</div>
</div>"""))

SCENES.append(("ph_s10", "s10_containers_photo", "ph", f"""
<img src="assets/img/i_s10_containers.jpg" data-a="kb">
<div class="veil-b"></div>
<div class="card slim" data-a="card">
  <div class="ct">拆开来看</div>
  <div class="bars">
    {barrow('出口 14.73 万亿元', '+13.4%', 54, '#8FA8C4', 'b1')}
    {barrow('进口 10.74 万亿元', '+22.1%', 88, BLUE, 'b2')}
  </div>
  <div class="scale"><span>0%</span><span>5%</span><span>10%</span><span>15%</span><span>20%</span><span>25%</span></div>
</div>"""))

SCENES.append(("ov_s11", "s11_robot_line", "ov", """
<div class="tag-ll" data-a="tag">
  <div class="tk">高技术制造业增加值 · 上半年同比</div>
  <div class="tv up">+<span data-count="13.3" data-dec="1">0.0</span>%</div>
  <div class="tbar"><i data-a="tb" class="up"></i></div>
</div>"""))

SCENES.append(("ph_s12", "s12_equipment_photo", "ph", """
<img src="assets/img/i_s12_equipment.jpg" data-a="kb">
<div class="veil-b"></div>
<div class="hugewrap" data-a="huge">
  <div class="hk">装备制造业增加值</div>
  <div class="hv up">+<span data-count="9.3" data-dec="1">0.0</span>%</div>
</div>"""))

SCENES.append(("mg_s13", "s13_output_bars", "mg", f"""
<div class="grid-bg" data-a="gridbg" data-layout-allow-overflow></div>
<div class="pane wide">
  <div class="ptitle" data-a="pt">上半年产量 · 同比</div>
  <div class="bars big">
    {barrow('工业机器人', '+28.0%', 58, GOLD, 'b1')}
    {barrow('锂离子电池', '+39.3%', 81, GOLD, 'b2')}
    {barrow('3D 打印设备', '+48.5%', 100, BLUE, 'b3')}
  </div>
  <div class="scale"><span>0%</span><span>10%</span><span>20%</span><span>30%</span><span>40%</span><span>50%</span></div>
</div>"""))

SCENES.append(("mg_s14", "s14_overlooked_card", "mg", """
<div class="grid-bg" data-a="gridbg" data-layout-allow-overflow></div>
<div class="turn">
  <div class="kicker" data-a="kick">这份表里还有一行</div>
  <div class="turnbig" data-a="big">容易<span class="rev">被跳过</span></div>
</div>
<div class="rowsmotif">
  <div class="mrow" data-a="r1"><span class="mk">生产</span><span class="mv"></span></div>
  <div class="mrow" data-a="r2"><span class="mk">外贸</span><span class="mv"></span></div>
  <div class="mrow hl" data-a="r3"><span class="mk">居民收入 · 物价</span><span class="mv"></span></div>
  <div class="mrow" data-a="r4"><span class="mk">投资</span><span class="mv"></span></div>
</div>"""))

SCENES.append(("ov_s15", "s15_supermarket", "ov", """
<div class="card compare" data-a="card">
  <div class="ct">谁跑得更慢</div>
  <div class="crow" data-a="c1">
    <div class="ck">居民人均可支配收入 · 实际</div>
    <div class="cv">+<span data-count="4.2" data-dec="1">0.0</span>%</div>
    <div class="ctrack"><i data-a="cb1"></i></div>
  </div>
  <div class="crow" data-a="c2">
    <div class="ck">同期经济增速</div>
    <div class="cv gold">+<span data-count="4.7" data-dec="1">0.0</span>%</div>
    <div class="ctrack"><i data-a="cb2" class="gold"></i></div>
  </div>
  <div class="cfoot" data-a="cf">收入跑输了增长</div>
</div>"""))

SCENES.append(("mg_s16", "s16_cpi_card", "mg", """
<div class="grid-bg" data-a="gridbg" data-layout-allow-overflow></div>
<div class="pane">
  <div class="ptitle" data-a="pt">居民消费价格 · 上半年同比</div>
  <div class="cpi">
    <div class="cpitrack">
      <div class="cpibar"><i data-a="cb"></i></div>
      <div class="target" data-a="tgt"><span>全年目标 2% 左右</span></div>
      <div class="cpiscale"><span>0</span><span>0.5%</span><span>1.0%</span><span>1.5%</span><span>2.0%</span><span>2.5%</span></div>
    </div>
    <div class="cpival" data-a="cv">+<span data-count="1.0" data-dec="1">0.0</span>%</div>
  </div>
  <div class="cpinote" data-a="cn">核心 CPI +1.2%　｜　工业生产者出厂价格 +1.5%</div>
</div>"""))

SCENES.append(("mg_s18", "s18_end_card", "mg", """
<div class="grid-bg" data-a="gridbg" data-layout-allow-overflow></div>
<div class="endtop">
  <div class="kicker" data-a="kick">上半年这一棒，谁在跑</div>
  <div class="endsub" data-a="sub">外需与高技术制造在加速，投资与消费在减速。</div>
</div>
<div class="rule lowerrule wide" data-a="rule"></div>
<div class="endline">
  <div class="q" data-a="q1">下半年要看的，</div>
  <div class="q" data-a="q2">是<em>内需</em>能不能接得住。</div>
</div>
<div class="split">
  <div class="row" data-a="r1"><div class="k">货物进出口</div><div class="v gold">+16.9%</div>
    <div class="bar"><i data-a="rb1" style="background:var(--gold)"></i></div></div>
  <div class="row" data-a="r2"><div class="k">高技术制造业增加值</div><div class="v gold">+13.3%</div>
    <div class="bar"><i data-a="rb2" style="background:var(--gold)"></i></div></div>
  <div class="row" data-a="r3"><div class="k">社会消费品零售总额</div><div class="v red">+1.3%</div>
    <div class="bar"><i data-a="rb3" style="background:#E8555C"></i></div></div>
</div>"""))

BARW = {"ov_s09": {"b1": 68}, "ph_s10": {"b1": 54, "b2": 88},
        "mg_s13": {"b1": 58, "b2": 81, "b3": 100},
        "mg_s18": {"rb1": 100, "rb2": 79, "rb3": 8}}

# ---------------------------------------------------------------- 时间线
J = []


def add(line):
    J.append(line)


def scene_toggle(dom, sid):
    add(f'tl.set("#{dom}",{{opacity:1}},{t0(sid)}); tl.set("#{dom}",{{opacity:0}},{t1(sid)});')


def fromto(sel, frm, to, at):
    add(f'tl.fromTo("{sel}",{frm},{to},{at});')


def countup(dom, at, d=1.1):
    add(f'countUp("#{dom} [data-count]",{at},{d});')


for dom, sid, cls, _ in SCENES:
    scene_toggle(dom, sid)
    # 每个场景整段的持续微动：网格底缓移 / 静帧 Ken Burns —— 防"入场后长时间冻结"
    if cls == "mg":
        fromto(f"#{dom} .grid-bg", "{x:0,y:0}", f'{{x:-46,y:-18,duration:{dur(sid)},ease:"none"}}', t0(sid))
    if cls == "ph":
        kb = next(k for d, s, f, k in PHOTOS if d == dom)
        fromto(f"#{dom} [data-a=kb]", "{scale:1.0}", f'{{scale:{kb},duration:{dur(sid)},ease:"none"}}', t0(sid))

# —— 逐镜元素时刻，全部由词点派生 ——
POP = '{opacity:0,y:22}', '{opacity:1,y:0,duration:0.52,ease:"power3.out"}'
POPX = '{opacity:0,x:34}', '{opacity:1,x:0,duration:0.52,ease:"power3.out"}'
FADE = '{opacity:0}', '{opacity:1,duration:0.5,ease:"power2.out"}'
BARIN = "{scaleX:0}", '{scaleX:1,duration:%s,ease:"power2.out",transformOrigin:"0%% 50%%"}'


def bar(sel, at, d=1.0):
    fromto(sel, BARIN[0], BARIN[1] % d, at)


# s01
fromto("#ov_s01 .scrim-r", *FADE, t0("s01_hook_anchor"))
fromto("#ov_s01 .scrim-b", *FADE, t0("s01_hook_anchor"))
fromto("#ov_s01 [data-a=kick]", *POP, cue("七月十五号") + 0.35)
fromto("#ov_s01 [data-a=head]", *POP, cue("同一张表上"))
fromto("#ov_s01 .lowerrule", BARIN[0], BARIN[1] % 0.7, cue("同一张表上") + 0.15)
fromto("#ov_s01 [data-a=m1]", *POPX, cue("有两组数字"))
fromto("#ov_s01 [data-a=m2]", *POPX, cue("方向正好相反"))
# s02 —— 数字随元素入场即刻 count 到位（防"屏上数字与旁白口径不一致"）
_a = cue("先看稳的")
fromto("#mg_s02 [data-a=pt]", *POP, _a)
fromto("#mg_s02 [data-a=big]", '{opacity:0,scale:1.10}', '{opacity:1,scale:1,duration:0.45,ease:"power3.out"}', _a + 0.30)
countup("mg_s02", _a + 0.36, 0.85)
fromto("#mg_s02 [data-a=yoy]", *POP, _a + 1.05)
fromto("#mg_s02 [data-a=q1]", "{scaleY:0}", '{scaleY:1,duration:0.85,ease:"power2.out",transformOrigin:"50% 100%"}', _a + 0.80)
fromto("#mg_s02 [data-a=q2]", "{scaleY:0}", '{scaleY:1,duration:0.85,ease:"power2.out",transformOrigin:"50% 100%"}', _a + 1.15)
fromto("#mg_s02 [data-a=band]", "{scaleX:0,opacity:0}", '{scaleX:1,opacity:1,duration:0.7,ease:"power2.out",transformOrigin:"0% 50%"}', cue("同比增长百分之四点七"))
# s03
fromto("#ov_s03 [data-a=strip]", '{opacity:0,y:26}', '{opacity:1,y:0,duration:0.55,ease:"power3.out"}', t0("s03_city_aerial") + 0.20)
# s04
_a = t0("s04_turn_card") + 0.12
fromto("#mg_s04 [data-a=kick]", *POP, _a)
fromto("#mg_s04 [data-a=big]", '{opacity:0,scale:1.12}', '{opacity:1,scale:1,duration:0.55,ease:"power3.out"}', _a + 0.42)
fromto("#mg_s04 [data-a=a1]", '{opacity:0,y:-34}', '{opacity:0.55,y:0,duration:0.5,ease:"power3.out"}', _a + 0.90)
fromto("#mg_s04 [data-a=a2]", '{opacity:0,y:34}', '{opacity:1,y:0,duration:0.5,ease:"power3.out"}', _a + 1.20)
# s05
_a = t0("s05_site_aerial") + 0.15
fromto("#ov_s05 [data-a=tag]", '{opacity:0,x:-30}', '{opacity:1,x:0,duration:0.55,ease:"power3.out"}', _a)
countup("ov_s05", _a + 0.22, 0.8)
bar("#ov_s05 [data-a=tb]", _a + 0.22, 0.85)
# s06
_a = t0("s06_housing_photo") + 0.14
fromto("#ph_s06 [data-a=huge]", *POPX, _a)
countup("ph_s06", _a + 0.20, 0.75)
# s07
_a = t0("s07_street_crowd") + 0.16
fromto("#ov_s07 [data-a=tag]", '{opacity:0,x:30}', '{opacity:1,x:0,duration:0.55,ease:"power3.out"}', _a)
countup("ov_s07", _a + 0.20, 0.7)
# s08
fromto("#ov_s08 .scrim-r", *FADE, t0("s08_question_anchor"))
fromto("#ov_s08 [data-a=g]", '{opacity:0,scale:1.1}', '{opacity:0.26,scale:1,duration:0.6,ease:"power2.out"}', cue("那百分之四点七"))
fromto("#ov_s08 [data-a=q]", '{opacity:0,scale:0.5,rotation:-12}', '{opacity:1,scale:1,rotation:0,duration:0.6,ease:"back.out(2)"}', cue("是谁扛起来的"))
add(f'tl.fromTo("#v_s08",{{scale:1.0}},{{scale:1.065,duration:{dur("s08_question_anchor")},ease:"power1.inOut"}},{t0("s08_question_anchor")});')
# s09 —— 卡片内容紧凑铺满，杜绝"大黑框空板"
_a = t0("s09_port_aerial") + 0.15
fromto("#ov_s09 .scrim-b", *FADE, t0("s09_port_aerial"))
fromto("#ov_s09 [data-a=kick]", *POP, _a)
fromto("#ov_s09 [data-a=head]", *POP, _a + 0.16)
fromto("#ov_s09 .lowerrule", BARIN[0], BARIN[1] % 0.7, _a + 0.30)
fromto("#ov_s09 [data-a=card]", '{opacity:0,x:44}', '{opacity:1,x:0,duration:0.55,ease:"power3.out"}', _a + 0.55)
countup("ov_s09", _a + 0.75, 0.85)
fromto("#ov_s09 [data-a=b1]", *POP, _a + 1.05)
bar("#ov_s09 [data-bar=b1]", _a + 1.10, 0.95)
fromto("#ov_s09 [data-a=cf]", *FADE, _a + 1.55)
# s10
_a = t0("s10_containers_photo") + 0.12
fromto("#ph_s10 [data-a=card]", '{opacity:0,x:44}', '{opacity:1,x:0,duration:0.55,ease:"power3.out"}', _a)
fromto("#ph_s10 .scale", *FADE, _a + 0.35)
fromto("#ph_s10 [data-a=b1]", *POP, _a + 0.40)
bar("#ph_s10 [data-bar=b1]", _a + 0.45, 0.95)
countup("ph_s10", _a + 0.45, 0.8)
fromto("#ph_s10 [data-a=b2]", *POP, cue("进口涨百分之二十二点一") - 0.35)
bar("#ph_s10 [data-bar=b2]", cue("进口涨百分之二十二点一") - 0.30, 1.0)
# s11
_a = cue("还有制造")
fromto("#ov_s11 [data-a=tag]", '{opacity:0,x:-30}', '{opacity:1,x:0,duration:0.55,ease:"power3.out"}', _a)
countup("ov_s11", _a + 0.25, 0.8)
bar("#ov_s11 [data-a=tb]", _a + 0.25, 0.90)
# s12
_a = t0("s12_equipment_photo") + 0.14
fromto("#ph_s12 [data-a=huge]", *POPX, _a)
countup("ph_s12", _a + 0.18, 0.7)
# s13 —— 三条错峰但都在前 2.2s 内铺满，剩余时间靠网格与阅读承担
_a = t0("s13_output_bars") + 0.12
fromto("#mg_s13 [data-a=pt]", *POP, _a)
fromto("#mg_s13 .scale", *FADE, _a + 0.35)
for i, k in enumerate(("b1", "b2", "b3")):
    at = round(_a + 0.42 + i * 0.62, 3)
    fromto(f"#mg_s13 [data-a={k}]", *POP, at)
    bar(f"#mg_s13 [data-bar={k}]", at + 0.05, 1.0)
# s14
_a = t0("s14_overlooked_card") + 0.12
fromto("#mg_s14 [data-a=kick]", *POP, _a)
fromto("#mg_s14 [data-a=big]", '{opacity:0,scale:1.12}', '{opacity:1,scale:1,duration:0.55,ease:"power3.out"}', _a + 0.45)
for _i, _k in enumerate(("r1", "r2", "r3", "r4")):
    fromto(f"#mg_s14 [data-a={_k}]", '{opacity:0,x:26}',
           '{opacity:%s,x:0,duration:0.45,ease:"power2.out"}' % (1 if _k == "r3" else 0.34),
           round(_a + 0.55 + _i * 0.20, 3))
# s15
_a = t0("s15_supermarket") + 0.15
fromto("#ov_s15 [data-a=card]", '{opacity:0,x:44}', '{opacity:1,x:0,duration:0.6,ease:"power3.out"}', _a)
fromto("#ov_s15 [data-a=c1]", *POP, _a + 0.35)
bar("#ov_s15 [data-a=cb1]", _a + 0.40, 1.2)
countup("ov_s15", _a + 0.40, 0.85)
fromto("#ov_s15 [data-a=c2]", *POP, cue("跑输了经济增速") - 0.55)
bar("#ov_s15 [data-a=cb2]", cue("跑输了经济增速") - 0.50, 1.0)
fromto("#ov_s15 [data-a=cf]", *FADE, cue("跑输了经济增速") + 0.55)
# s16
_a = t0("s16_cpi_card") + 0.12
fromto("#mg_s16 [data-a=pt]", *POP, _a)
fromto("#mg_s16 .cpiscale", *FADE, _a + 0.30)
bar("#mg_s16 [data-a=cb]", _a + 0.40, 1.0)
fromto("#mg_s16 [data-a=cv]", '{opacity:0,scale:1.12}', '{opacity:1,scale:1,duration:0.45,ease:"back.out(1.5)"}', _a + 0.40)
countup("mg_s16", _a + 0.45, 0.75)
fromto("#mg_s16 [data-a=tgt]", '{opacity:0,x:-40}', '{opacity:1,x:0,duration:0.65,ease:"power3.out"}', cue("离百分之二的目标") - 0.45)
fromto("#mg_s16 [data-a=cn]", *FADE, cue("离百分之二的目标") + 0.5)
# s18
_a = t0("s18_end_card")
fromto("#mg_s18 [data-a=kick]", *POP, _a + 0.10)
fromto("#mg_s18 [data-a=sub]", *FADE, _a + 0.32)
fromto("#mg_s18 .lowerrule", BARIN[0], BARIN[1] % 0.9, cue("下半年要看的") - 0.20)
fromto("#mg_s18 [data-a=q1]", *POP, cue("下半年要看的"))
fromto("#mg_s18 [data-a=q2]", *POP, cue("是内需能不能接得住"))
for i, k in enumerate(("r1", "r2", "r3")):
    at = round(_a + 0.52 + i * 0.28, 3)
    fromto(f"#mg_s18 [data-a={k}]", *POPX, at)
    bar(f"#mg_s18 [data-a=rb{i+1}]", at + 0.10, 0.85)

# 转场：两张转折字卡走 dip_to_navy，结论卡走 gold_wipe（全片转场词汇 3 种 ≤4）
for sid in ("s04_turn_card", "s14_overlooked_card"):
    a = t0(sid)
    add(f'tl.fromTo("#dip",{{opacity:0}},{{opacity:1,duration:0.13,ease:"power2.in"}},{round(a-0.13,3)});')
    add(f'tl.to("#dip",{{opacity:0,duration:0.24,ease:"power2.out"}},{a});')
_w0 = round(t0("s18_end_card") - 0.24, 3)
add(f'tl.fromTo("#wipe",{{opacity:1,scaleX:0,transformOrigin:"0% 50%"}},'
    f'{{opacity:1,scaleX:1,duration:0.30,ease:"power3.inOut"}},{_w0});')
add(f'tl.fromTo("#wipe",{{opacity:1,scaleX:1,transformOrigin:"100% 50%"}},'
    f'{{opacity:1,scaleX:0,duration:0.30,ease:"power3.inOut"}},{round(_w0 + 0.30, 3)});')
add(f'tl.set("#wipe",{{opacity:0}},{round(_w0 + 0.62, 3)});')

# 脚注：只在带数据的镜头在场（合并相邻镜头成连续可见窗；每窗收尾带 tl.set 硬杀，
# 否则非线性 seek 落在淡出之后会留下陈旧可见状态 —— hyperframes lint gsap_exit_missing_hard_kill）
_wins = []
for sid in FOOT_SHOTS:
    a, b = t0(sid), t1(sid)
    if _wins and abs(_wins[-1][1] - a) < 1e-6:
        _wins[-1][1] = b
    else:
        _wins.append([a, b])
add('tl.set("#foot",{opacity:0},0);')
for a, b in _wins:
    add(f'tl.to("#foot",{{opacity:1,duration:0.28}},{a});')
    add(f'tl.to("#foot",{{opacity:0,duration:0.24}},{round(b - 0.24, 3)});')
    add(f'tl.set("#foot",{{opacity:0}},{b});')

# ---------------------------------------------------------------- HTML
CSS = (P / "compose-v1/style.css").read_text(encoding="utf-8")
_cap_js = (P / "compose-v1/assets/captions_data.js").read_text(encoding="utf-8")
_caps = json.loads(_cap_js.split("=", 1)[1].strip().rstrip(";\n").strip())
caps_html = "".join(f'<div class="cap" id="cap{i}">{c["text"]}</div>'
                    for i, c in enumerate(_caps))
media = []
for dom, sid, f, cls in VIDEOS:
    media.append(f'<video id="{dom}" class="clip fullframe {cls}" src="{f}" muted playsinline '
                 f'data-start="{t0(sid)}" data-duration="{dur(sid)}" data-media-start="0" '
                 f'data-track-index="1"></video>')
scenes_html = []
for dom, sid, cls, inner in SCENES:
    scenes_html.append(f'<div id="{dom}" class="scene {cls}">{inner}</div>')

html = f"""<!doctype html>
<html lang="zh" data-resolution="landscape" data-fps="30">
<head><meta charset="UTF-8"><title>经济半年报 · 4.7% 背后的两组数字 — Kuleshov</title>
<script src="assets/gsap.min.js"></script>
<script src="assets/captions_data.js"></script>
<style>
{CSS}
</style></head>
<body>
<div id="root" data-composition-id="{CID}" data-width="1920" data-height="1080"
     data-start="0" data-duration="{DUR}" data-fps="30">
<audio id="vo" class="clip" src="assets/vo.mp3" data-start="0" data-duration="{DUR}"
       data-track-index="0" data-volume="1" data-has-audio="true"></audio>
{chr(10).join(media)}
{chr(10).join(scenes_html)}
{BUG}
{FOOT}
<div id="dip"></div><div id="wipe"></div>
<div id="capbox">{caps_html}</div>
<div id="vig"></div>
</div>
<script>
const tl = gsap.timeline({{paused:true}});
function countUp(sel, at, d){{
  document.querySelectorAll(sel).forEach((el)=>{{
    const target = parseFloat(el.getAttribute("data-count"));
    const dec = parseInt(el.getAttribute("data-dec")||"1",10);
    const o = {{v:0}};
    tl.to(o,{{v:target,duration:d,ease:"power1.out",
      onUpdate:()=>{{ el.textContent = o.v.toFixed(dec); }}}},at);
  }});
}}
{chr(10).join(J)}
(window.__captions||[]).forEach((c,i)=>{{
  const el = "#cap"+i;
  tl.set(el,{{opacity:0}},0);
  tl.to(el,{{opacity:1,duration:0.10}},c.start);
  tl.to(el,{{opacity:0,duration:0.10}},c.end);
  tl.set(el,{{opacity:0}},c.end+0.10);
}});
window.__timelines = window.__timelines || {{}};
window.__timelines["{CID}"] = tl;
</script>
</body></html>
"""
(P / "compose-v1/index.html").write_text(html, encoding="utf-8")
print(f"写出 compose/index.html：{len(SCENES)} 场景 / {len(VIDEOS)} 视频 / {len(J)} 条 tween / 总长 {DUR}s")
