#!/usr/bin/env python3
"""Kuleshov compose 出厂硬查——把散文铁律固化成会开火的门。
用法: python3 tools/kuleshov-lint.py projects/<片名>
检查：① woff2 字体纪律(禁 local 承担正文/标题) ② 时效词(相对时间词，出厂前须复核) ③ docsrc/脚注压容器边框(启发式)。
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

    print(f"=== kuleshov-lint: {proj} ===")
    for w in warns: print(f"  ⚠️  WARN  {w}")
    for e in errors: print(f"  ❌  ERROR {e}")
    if not errors and not warns: print("  ✅ 全过")
    elif not errors: print(f"  ✅ 无 error（{len(warns)} 条 warning 待人工确认）")
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
