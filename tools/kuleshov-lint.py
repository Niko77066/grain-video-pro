#!/usr/bin/env python3
"""Kuleshov compose 出厂硬查——把散文铁律固化成会开火的门。
用法: python3 tools/kuleshov-lint.py projects/<片名>
检查：① woff2 字体纪律(禁 local 承担正文/标题) ② 时效词(相对时间词，出厂前须复核) ③ docsrc/脚注压容器边框(启发式)
      ④ 组件底板(压在画面上的数据组件禁深色底框——PPT 味，2026-07-27 用户拍板) ⑤ 字幕标点(专业视频不加)
      ⑥ GSAP 供给(用了 gsap 就必须自带在盘真 gsap.min.js 或全表 shim；顺带禁 CDN 外链)
      ⑦ 字幕外挂(交付=MP4+VTT 两件，禁烧进画面；存量 review/delivered 只 warn)。
退出码 1 = 有 error（禁出厂）；warning 不阻断但必须人工确认。
背景见 docs/postmortem-hf-breach.md。"""
import sys, os, re, json

def main():
    proj = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "."
    html_path = os.path.join(proj, "compose", "index.html")
    errors, warns = [], []
    # 数字内部的 . , : 是数值的一部分（5.3% / 1,200 / 00:12），不是标点——⑤⑦ 共用
    _num_sep = re.compile(r"(?<=\d)[.,:](?=\d)")

    html = open(html_path, encoding="utf-8").read() if os.path.exists(html_path) else ""

    # ① woff2 纪律：任何 @font-face 的 src 只有 local(...) 而无 url(...) = 违规
    if html:
        for m in re.finditer(r"@font-face\s*\{([^}]*)\}", html):
            body = m.group(1)
            if "src:" in body and "local(" in body and "url(" not in body:
                fam = re.search(r'font-family:\s*["\']?([^;"\']+)', body)
                errors.append(f"woff2 纪律违规：@font-face 用 local() 系统字体承担 [{fam.group(1) if fam else '?'}]（渲染机会 font-kit 兜底→换行漂移）。改自带 woff2。")
        # 兜底：font-family 栈里出现常见 macOS 系统字体名（PingFang/Songti/SF Mono/Heiti）且未声明为 woff2 @font-face
        declared = set(re.findall(r'@font-face\s*\{[^}]*font-family:\s*["\']?([^;"\'{]+)["\']?[^}]*url\(', html))
        declared = {d.strip() for d in declared}
        for fam in re.findall(r'font-family:\s*([^;{}]+)[;}]', html):
            for sysf in ("PingFang", "Songti", "Heiti", "STHeiti", "Yuanti"):
                if sysf in fam and not any(sysf in d for d in declared):
                    warns.append(f"font-family 栈含系统字体 '{sysf}'（{fam.strip()[:60]}）——确认它只作 woff2 之后的末位兜底，不是主字体。")

    # ② 时效词：旁白/脚本里的相对时间词，出厂前须复核仍准确
    text = ""
    for p in (os.path.join(proj, "audio", "sections.json"),):
        if os.path.exists(p):
            try: text += json.load(open(p)).get("fulltext", "")
            except Exception: pass
    sm = os.path.join(proj, "script.md")
    if os.path.exists(sm):
        text += open(sm, encoding="utf-8").read()
    TIMEWORDS = ["昨天","今天","明天","前天","后天","昨日","今日","刚刚","刚才","眼下","这两天","这几天","本周","上周","下周","这个月","上个月","最近","日前","近日","目前","如今","现如今","today","yesterday","this week","last week"]
    hit = sorted({w for w in TIMEWORDS if w in text})
    if hit:
        warns.append(f"时效词命中 {hit}——48h 窗口内发布仍准确？出厂前逐个复核，或换绝对日期。")

    # ③ docsrc / 脚注压容器边框（启发式，针对案卷卡这类结构）
    if html:
        db = re.search(r"\.docbody\s*\{([^}]*)\}", html)
        ds = re.search(r"\.docsrc\s*\{([^}]*)\}", html)
        if db and ds and "border" in db.group(1):
            def px(block, key):
                m = re.search(rf"{key}:\s*(\d+)px", block)
                if m: return int(m.group(1))
                mi = re.search(r"inset:\s*(\d+)px", block)
                return int(mi.group(1)) if (mi and key in ("top","bottom","left","right")) else None
            frame_bottom = px(db.group(1), "bottom")
            ds_bottom = px(ds.group(1), "bottom")
            fs = re.search(r"font-size:\s*(\d+)px", ds.group(1))
            ds_fs = int(fs.group(1)) if fs else 28
            if frame_bottom is not None and ds_bottom is not None:
                # 脚注顶 ≈ ds_bottom + 行高(≈fs*1.5)；须低于内框底边(frame_bottom)才不压线
                if ds_bottom + ds_fs * 1.5 > frame_bottom:
                    errors.append(f".docsrc 脚注(bottom {ds_bottom}px + 行高≈{int(ds_fs*1.5)}px)顶过了 .docbody 内框底边({frame_bottom}px)——压边框线。加大 .docbody bottom 或降低 .docsrc。")

    # ④ 组件底板（PPT 味）——2026-07-27 用户拍板，宪法级：
    #   「压在画面上的数据组件带深色底框 = AI 味 / PPT 风格，能无底框就无底框；
    #     左上角标那种信息层级的加个底框无所谓。」
    #   判定：一条 CSS 规则同时有「实色填充」和「边框或内边距」＝ 一个浮动面板。
    #   放行：整屏背景 / 渐变到透明的压暗层 / 图表轨道（有填充但无边框无内边距）/ 白名单。
    #   例外走显式声明：在规则前一行写 /* lint-allow-panel: <理由> */。
    if html:
        ALLOW = ("#bug", "#dip", "#wipe", "#root", "html", "body", ".scene", ".studio",
                 ".mrow", "::-webkit", "@")
        ALLOW_SUBSTR = ("scrim", "veil", "grid-bg", "track", "tbar", "cpibar", "-bg")
        # 硬 error 名单：这些是明确的「压在画面上的数据组件」，无歧义
        DENY_NAMED = {".card", ".tag-ll", ".tag-lr", ".strip", "#foot", ".cap", ".hugewrap",
                      ".band", ".chartcard", ".metric", ".datacol"}
        css_blocks = re.findall(r"(/\*[^*]*\*/\s*)?([^{}@/][^{}]*)\{([^{}]*)\}", html)
        for comment, sel, body in css_blocks:
            sel = re.sub(r"/\*.*?\*/", "", sel, flags=re.S)   # 选择器前粘的注释不进报错文案
            sel = " ".join(sel.split())
            if not sel or "%" in sel:               # keyframes 百分比块
                continue
            if comment and "lint-allow-panel" in comment:
                continue
            low = sel.lower()
            if any(low.startswith(a) or low == a for a in ALLOW) or any(x in low for x in ALLOW_SUBSTR):
                continue
            bg = re.search(r"background(?:-color)?\s*:\s*([^;]+)", body)
            if not bg:
                continue
            v = bg.group(1).strip().lower()
            if v.startswith(("none", "transparent", "inherit", "initial")):
                continue
            # 渐变到透明的压暗层不算底板（无可见边界）
            if "gradient(" in v and re.search(r"rgba\([^)]*,\s*0\s*\)", v):
                continue
            m = re.search(r"rgba\([^)]*,\s*([\d.]+)\s*\)", v)
            if m and float(m.group(1)) < 0.12:      # 近乎透明，不构成底板
                continue
            has_border = bool(re.search(r"\bborder(?:-(?:top|right|bottom|left))?\s*:\s*(?!none)[^;]*\d+px", body))
            has_pad = bool(re.search(r"\bpadding(?:-(?:top|right|bottom|left))?\s*:\s*[^;]*[1-9]", body))
            # deny 名单只匹配「最后一个简单选择器」，不做全串包含——
            # 否则 `.card .rows li::before`（列表小圆点）会被当成数据卡。
            def _hits_deny(selector: str) -> bool:
                for part in selector.split(","):
                    last = part.strip().split()[-1] if part.strip() else ""
                    last = re.sub(r"::?[a-z-]+(\([^)]*\))?$", "", last)   # 去伪类/伪元素
                    toks = set(re.findall(r"[.#][A-Za-z0-9_-]+", last))
                    if toks & set(DENY_NAMED):
                        return True
                return False
            named = _hits_deny(low)
            if named and (has_border or has_pad or "box-shadow" in body):
                errors.append(f"组件底板违规：`{sel[:58]}` 是压在画面上的数据组件却带了填充/边框/投影"
                              f"（{v[:40]}）——PPT 味来源。去掉 background/border/box-shadow，"
                              f"可读性改用『渐变到透明的压暗层 + 多层 text-shadow 等效描边』。")
            elif has_border and has_pad:
                # 泛化网只降 warn：印章/徽标/标签这类器件在别的风格包里是刻意设计，
                # 机器分不清它和 PPT 面板——交人判断，不误伤到 error。
                warns.append(f"疑似浮动面板：`{sel[:58]}` 同时有实色填充({v[:32]})、边框与内边距。"
                             f"若它是压在画面上的数据组件 → 按宪法去底框；若是印章/徽标这类刻意器件 → "
                             f"在规则前加 /* lint-allow-panel: 理由 */ 消掉本条。")

    # ⑤ 字幕标点——2026-07-27 用户拍板：专业视频的字幕从不加标点符号。
    capf = os.path.join(proj, "compose", "assets", "captions_data.js")
    if os.path.exists(capf):
        raw = open(capf, encoding="utf-8").read()
        try:
            caps = json.loads(raw.split("=", 1)[1].strip().rstrip(";\n").strip())
            if not isinstance(caps, list) or not all(isinstance(c, dict) for c in caps):
                raise ValueError("captions_data 不是 [{text,...}] 数组")
        except Exception as e:
            caps = []
            warns.append(f"captions_data.js 解析失败（{e}），字幕标点门未执行——请人工确认。")
        # 数字内部的 . , : 不是标点，是数值的一部分（5.3% / 1,200 / 00:12 / 9:16）——
        # 先掏空它们再查。gen_captions.py 的 strip_punct 也只剥标点、不动数字，
        # 两边口径必须一致，否则这道 error 门会挡住合规产出的字幕。
        bad = [c.get("text", "") for c in caps
               if re.search(r"[，。、；：？！,.;:?!]", _num_sep.sub("", c.get("text", "") or ""))]
        if bad:
            errors.append(f"字幕含标点符号（{len(bad)}/{len(caps)} 条），专业视频不在字幕里加标点。"
                          f"示例：{bad[0][:24]!r}。切分可以用标点，渲染不许带——见 scripts/gen_captions.py。")

    # ⑥ GSAP 供给纪律（2026-07-28 补门；此前只是散文，`tools/lint.py` 那道门在本仓从未存在）：
    #   compose 用了 gsap / 注册了 __timelines，就必须**要么**自带在盘的真 assets/gsap.min.js，
    #   **要么**内联 shim 且实现渲染机 seek 驱动会调的生命周期全表。两者皆无、或 shim 漏方法
    #   → 渲染到 capture 阶段才炸 [Browser:PAGEERROR] …is not a function（浪费一整次渲染）。
    #   判定是项目级而非单文件：任一 html 供给了，全 compose 就算有（同一页面共享 window）。
    LIFECYCLE = ["seek", "totalTime", "time", "timeScale", "pause", "paused", "play",
                 "resume", "restart", "kill", "invalidate", "eventCallback", "progress", "duration"]
    compose_dir = os.path.join(proj, "compose")
    pages = []
    for root, _dirs, files in os.walk(compose_dir):
        for fn in files:
            if fn.endswith(".html"):
                p = os.path.join(root, fn)
                try: pages.append((p, open(p, encoding="utf-8").read()))
                except Exception as e: warns.append(f"{p} 读取失败（{e}），GSAP 供给门未覆盖该文件。")
    uses_gsap = any(re.search(r"\bgsap\s*\.", t) or "__timelines" in t for _p, t in pages)
    if uses_gsap:
        real_gsap, shim_texts, cdn, named_cause = None, [], [], False
        for path, t in pages:
            for src in re.findall(r"<script[^>]+src\s*=\s*[\"']([^\"']+)[\"']", t):
                if re.match(r"(https?:)?//", src):
                    cdn.append((os.path.relpath(path, proj), src))
                    continue
                if "gsap" not in src.lower():
                    continue
                cand = os.path.normpath(os.path.join(os.path.dirname(path), src.split("?")[0]))
                if not os.path.exists(cand):
                    errors.append(f"GSAP 供给违规：`{os.path.relpath(path, proj)}` 引了 `{src}`，"
                                  f"但该文件不在盘上（渲染机 tar 只带 compose 目录，缺文件=页面直接崩）。")
                    named_cause = True
                    continue
                blob = open(cand, "rb").read()
                # 真 gsap.min.js ≈72KB 且含生命周期方法名；小文件/假货挡在这里
                if len(blob) < 40_000 or not all(k.encode() in blob for k in ("timeScale", "invalidate", "eventCallback")):
                    errors.append(f"GSAP 供给违规：`{os.path.relpath(cand, proj)}` 只有 {len(blob)//1024}KB "
                                  f"或缺生命周期方法，不是真 gsap.min.js（仓内规范来源 assets/gsap.min.js，3.14.2，72KB）。")
                    named_cause = True
                else:
                    real_gsap = os.path.relpath(cand, proj)
        for _path, t in pages:
            for m in re.finditer(r"window\.gsap\s*=", t):
                shim_texts.append(t[max(0, m.start() - 4000): m.start() + 20000])
        if cdn:
            errors.append(f"禁 CDN（硬规则 5）：{cdn[0][0]} 引了外链 `{cdn[0][1]}`"
                          + (f" 等 {len(cdn)} 处" if len(cdn) > 1 else "")
                          + "——渲染机 tar 只带 compose 目录且渲染期禁网络请求。拷进 assets/ 用相对路径。")
            if any("gsap" in s.lower() for _f, s in cdn):
                named_cause = True                      # CDN 引的就是 gsap，原因已具名，不再叠泛化那条
        if not real_gsap and not shim_texts and not named_cause:
            errors.append("GSAP 供给违规：compose 用了 gsap/__timelines，却既没自带在盘的真 "
                          "`assets/gsap.min.js`，也没有内联 shim——渲染机 seek 驱动会在 capture 阶段炸 "
                          "PAGEERROR。首选 `cp assets/gsap.min.js <proj>/compose/assets/`，"
                          "万不得已才整块抄 references/gsap-fallback-shim.md。")
        elif not real_gsap and shim_texts:
            missing = [k for k in LIFECYCLE
                       if not any(re.search(rf"\b{k}\s*[:=]", s) for s in shim_texts)]
            if missing:
                errors.append(f"GSAP shim 漏方法 {missing}——渲染机 seek 驱动会调生命周期全表"
                              f"（{'/'.join(LIFECYCLE[:4])}…），漏哪个就在某个引擎版本上崩。"
                              f"整块抄 references/gsap-fallback-shim.md §2，别删方法。")
            else:
                warns.append("compose 走的是内联 GSAP shim 而非真 gsap.min.js——生命周期全表在，"
                             "但只覆盖数值/transform 属性；颜色、路径类补间要真 GSAP。能自带就自带。")

    # ⑦ 字幕外挂门（2026-07-28 起，按 grain 发布硬门收口 `carrier-contracts/video.md`）：
    #   交付物 = MP4 + 外挂 VTT 两件，**compose 里不许有字幕层**（禁烧进画面、禁手写）。
    #   存量不追溯：status 已到 review/delivered 的片子是旧政策下做完的，只报 warn。
    #   没有烧录豁免——2026-07-28 用户拍板"默认不烧字幕"，社媒平台是否消费外挂字幕不影响本门。
    meta = {}
    fj = os.path.join(proj, "film.json")
    if os.path.exists(fj):
        try: meta = (json.load(open(fj, encoding="utf-8")).get("meta") or {})
        except Exception as e: warns.append(f"film.json 解析失败（{e}），字幕外挂门按新片口径执行。")
    status = (meta.get("status") or "").lower()
    legacy = status in ("review", "delivered")          # 旧政策下已完工，不追溯

    burned = []
    if os.path.exists(capf):
        burned.append(os.path.relpath(capf, proj))
    for path, page in pages:                            # pages 由 ⑥ 扫出（compose/**/*.html）
        if re.search(r"captions_data|window\.__captions", page):
            rel = os.path.relpath(path, proj)
            if rel not in burned: burned.append(rel)

    out_dir = os.path.join(proj, "out")
    vtts = [f for f in os.listdir(out_dir) if f.endswith(".vtt")] if os.path.isdir(out_dir) else []
    mp4s = [f for f in os.listdir(out_dir) if f.endswith(".mp4")] if os.path.isdir(out_dir) else []

    if burned:
        msg = (f"字幕烧进了画面（{', '.join(burned[:2])}）——交付物必须是 MP4 + 外挂 VTT 两件，"
               f"compose 里不留字幕层（grain 发布三件套：禁烧进画面、禁手写）。"
               f"改法：`python3 tools/make-vtt.py {proj}` 出 out/final.vtt，compose 去掉字幕层。")
        if legacy:
            warns.append(f"存量烧录字幕（status={status}，2026-07-28 政策不追溯）：{', '.join(burned[:2])}。"
                         f"重做或复用这条片的 compose 时必须改成外挂 VTT。")
        else:
            errors.append(msg)
    if mp4s and not vtts:
        m = (f"out/ 有成片（{mp4s[0]}）却没有外挂字幕 .vtt——发布门要求 "
             f"metadata.subtitles=[{{format:'vtt'}}]。跑 `python3 tools/make-vtt.py {proj}`。")
        (warns if legacy else errors).append(m)
    for v in vtts:
        cues = re.split(r"\n\s*\n", open(os.path.join(out_dir, v), encoding="utf-8").read())
        texts = [ln for blk in cues for ln in blk.splitlines()[2:]
                 if not ln.startswith("WEBVTT") and "-->" not in ln and ln.strip()]
        bad_v = [x for x in texts if re.search(r"[，。、；：？！,.;:?!]", _num_sep.sub("", x))]
        if bad_v:
            errors.append(f"out/{v} 有 {len(bad_v)}/{len(texts)} 条带标点——外挂字幕同样不许带标点"
                          f"（渲染层剥离，切分仍用标点）。示例：{bad_v[0][:24]!r}")

    print(f"=== kuleshov-lint: {proj} ===")
    for w in warns: print(f"  ⚠️  WARN  {w}")
    for e in errors: print(f"  ❌  ERROR {e}")
    if not errors and not warns: print("  ✅ 全过")
    elif not errors: print(f"  ✅ 无 error（{len(warns)} 条 warning 待人工确认）")
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
