#!/usr/bin/env python3
"""Kuleshov compose 出厂硬查——把散文铁律固化成会开火的门。
用法: python3 tools/kuleshov-lint.py projects/<片名>
检查：① woff2 字体纪律(禁 local 承担正文/标题) ② 时效词(相对时间词，出厂前须复核) ③ docsrc/脚注压容器边框(启发式)
      ④ 组件底板(压在画面上的数据组件禁深色底框——PPT 味，2026-07-27 用户拍板) ⑤ 字幕标点(专业视频不加)。
退出码 1 = 有 error（禁出厂）；warning 不阻断但必须人工确认。
背景见 docs/postmortem-hf-breach.md。"""
import sys, os, re, json

def main():
    proj = sys.argv[1].rstrip("/") if len(sys.argv) > 1 else "."
    html_path = os.path.join(proj, "compose", "index.html")
    errors, warns = [], []

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
        except Exception:
            caps = []
            warns.append("captions_data.js 解析失败，字幕标点门未执行——请人工确认。")
        bad = [c.get("text", "") for c in caps
               if re.search(r"[，。、；：？！,.;:?!]", c.get("text", ""))]
        if bad:
            errors.append(f"字幕含标点符号（{len(bad)}/{len(caps)} 条），专业视频不在字幕里加标点。"
                          f"示例：{bad[0][:24]!r}。切分可以用标点，渲染不许带——见 scripts/gen_captions.py。")

    print(f"=== kuleshov-lint: {proj} ===")
    for w in warns: print(f"  ⚠️  WARN  {w}")
    for e in errors: print(f"  ❌  ERROR {e}")
    if not errors and not warns: print("  ✅ 全过")
    elif not errors: print(f"  ✅ 无 error（{len(warns)} 条 warning 待人工确认）")
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
