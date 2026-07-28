#!/usr/bin/env python3
"""生成型 b-roll 的 profile registry：列表 / 详情 / 渲染提示词 / 串词 lint。

八套材质语言共用一套引擎（三闸门、几何、gpt-image + seedance 绑定、clip-qa）。
profile 只负责会变的四样：**材质语汇、运动动词、首帧规则、失败标准**。

`lint` 是这套体系的守门人：它检查一段提示词有没有混入**别的 profile 的签名词汇**。
浣熊片那段做旧报纸味的假像素，成因就是拼贴模板 find/replace 成像素后
`paper-collage` / `paper grain` 留在了里面——那时候没有这道门。

用法:
  broll-profile.py list
  broll-profile.py show <id>
  broll-profile.py render <id> --gate 2|3 [--var KEY=VALUE ...] [--aspect 16:9]
  broll-profile.py lint <id> --text "<提示词>"   |   --file prompt.txt
  broll-profile.py route "<文稿类型关键词>"
"""
import argparse
import json
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / ".claude" / "skills" / "broll-studio"
PROFILE_DIR = SKILL / "profiles"


def load_all():
    """返回 {id: profile}，含 _external.json 里的外部链（它们只参与 lint 与选型）。"""
    out = {}
    for f in sorted(PROFILE_DIR.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if f.name == "_external.json":
            for ext in d["profiles"]:
                ext["_external"] = True
                out[ext["id"]] = ext
        else:
            d["_external"] = False
            out[d["id"]] = d
    if not out:
        sys.exit(f"没找到 profile：{PROFILE_DIR}")
    return out


def get(profiles, pid):
    if pid not in profiles:
        sys.exit(f"未知 profile: {pid}（有 {', '.join(sorted(profiles))}）")
    return profiles[pid]


def cmd_list(profiles):
    print("生成型 b-roll · 材质语言 registry\n")
    for pid, p in sorted(profiles.items(), key=lambda kv: (kv[1]["_external"], kv[0])):
        tag = "  [独立 skill]" if p["_external"] else ""
        print(f"  {pid:18} {p['display_name']}{tag}")
        print(f"  {'':18} 核心优势：{p['core_strength']}")
        print(f"  {'':18} 最适合：{'、'.join(p['best_for'][:3])}")
        if p["_external"]:
            print(f"  {'':18} → {p['skill']}")
        print()
    print("同片单一：一条片只准一种生成风格（见 routing.json 的 same_film_rule）。")


def cmd_show(profiles, pid):
    p = get(profiles, pid)
    print(json.dumps(p, ensure_ascii=False, indent=2))


def render(p, gate, variables, aspect):
    if p["_external"]:
        sys.exit(f"{p['id']} 是独立 skill（{p['skill']}），提示词模板在那边，不由本工具渲染")
    key = {2: "gate2_prompt", 3: "gate3_prompt"}[gate]
    text = p[key]

    if aspect == "16:9":
        for rule in p.get("aspect_16_9", []):
            if "→" in rule:
                a, b = (s.strip() for s in rule.split("→", 1))
                if a in text:
                    text = text.replace(a, b)
                else:
                    print(f"  ⚠️ 画幅替换未命中（模板里没有 {a!r}），请人工核对", file=sys.stderr)
            else:
                print(f"  ℹ️ 16:9 施工说明（需人工落实）：{rule}", file=sys.stderr)

    missing = [v for v in p["variables"] if f"[{v}]" in text and v not in variables]
    for k, v in variables.items():
        text = text.replace(f"[{k}]", v)
    return text, missing


def cmd_render(profiles, pid, gate, variables, aspect):
    p = get(profiles, pid)
    text, missing = render(p, gate, variables, aspect)
    if missing:
        print(f"  ⚠️ 未填变量：{', '.join(missing)}（占位符原样保留）", file=sys.stderr)
    print(text)
    stray = lint_text(profiles, pid, text)
    if stray:
        print("\n  ❌ 串词：" + "；".join(f"{w}（属于 {o}）" for w, o in stray), file=sys.stderr)
        return 1
    return 0


def positive_part(text):
    """只保留**肯定描述**。否定式约束不是串词——恰恰相反：
    object-theatre 的 `No paper collage`、felted-wool 的 `No clay` 是在**主动划界**，
    正是我们要的东西。把 Avoid: 段与以 No/no 开头的从句剥掉再匹配。"""
    text = re.split(r"\bAvoid\s*:", text, maxsplit=1)[0]
    clauses = re.split(r"(?<=[.\n])|,\s*(?=no\s)", text, flags=re.IGNORECASE)
    return " ".join(c for c in clauses
                    if not re.match(r"\s*no[nt]?\s", c or "", flags=re.IGNORECASE))


def lint_text(profiles, pid, text):
    """返回 [(命中词, 归属 profile)]——命中别的 profile 的签名词汇即串风格。"""
    low = positive_part(text).lower()
    mine = {w.lower() for w in profiles[pid].get("signature_vocab", [])}
    hits = []
    for oid, other in profiles.items():
        if oid == pid:
            continue
        for w in other.get("signature_vocab", []):
            wl = w.lower()
            if wl in mine:
                continue          # 两套共有的词不算串（例如都用 miniature）
            # 词边界匹配，避免 "pixel" 命中 "pixelated" 之外的误伤由词表本身控制
            if re.search(r"(?<![a-z])" + re.escape(wl) + r"(?![a-z])", low):
                hits.append((w, oid))
    return hits


def cmd_lint(profiles, pid, text):
    get(profiles, pid)
    stray = lint_text(profiles, pid, text)
    if not stray:
        print(f"✅ 无串词（对照其余 {len(profiles) - 1} 套材质语汇）")
        return 0
    print(f"❌ 命中 {len(stray)} 处别的风格的签名词汇：")
    for w, o in stray:
        print(f"   {w!r} → 属于 {o}（{profiles[o]['display_name']}）")
    print("\n混风就是「拼贴模板 find/replace 成像素」那类杂交产物的成因。"
          "要么删掉这些词，要么整镜改走那个 profile。")
    return 1


def cmd_route(profiles, query):
    rules = json.loads((SKILL / "routing.json").read_text(encoding="utf-8"))
    q = query.strip()
    hits = [r for r in rules["rules"] if any(t and t in r["script_type"] for t in (q, *q.split()))]
    if not hits:
        print(f"没匹配到「{q}」。全表：\n")
        hits = rules["rules"]
    for r in hits:
        pr, al = profiles.get(r["primary"]), profiles.get(r["alt"])
        print(f"  {r['script_type']}")
        print(f"    首选 {r['primary']:18} {pr['display_name'] if pr else ''}")
        print(f"    备选 {r['alt']:18} {al['display_name'] if al else ''}")
    print(f"\n判不出来时：{rules['tie_break']}")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    s = sub.add_parser("show"); s.add_argument("id")
    r = sub.add_parser("render"); r.add_argument("id")
    r.add_argument("--gate", type=int, choices=(2, 3), required=True)
    r.add_argument("--var", action="append", default=[], metavar="KEY=VALUE")
    r.add_argument("--aspect", default="9:16", choices=("9:16", "16:9"))
    l = sub.add_parser("lint"); l.add_argument("id")
    l.add_argument("--text"); l.add_argument("--file", type=Path)
    t = sub.add_parser("route"); t.add_argument("query", nargs="?", default="")
    a = p.parse_args()

    profiles = load_all()
    if a.cmd == "list":
        return cmd_list(profiles) or 0
    if a.cmd == "show":
        return cmd_show(profiles, a.id) or 0
    if a.cmd == "route":
        return cmd_route(profiles, a.query) or 0
    if a.cmd == "render":
        variables = {}
        for kv in a.var:
            if "=" not in kv:
                sys.exit(f"--var 要写成 KEY=VALUE，收到 {kv!r}")
            k, v = kv.split("=", 1)
            variables[k.strip()] = v
        return cmd_render(profiles, a.id, a.gate, variables, a.aspect)
    if a.cmd == "lint":
        if a.file:
            text = a.file.read_text(encoding="utf-8")
        elif a.text:
            text = a.text
        else:
            text = sys.stdin.read()
        return cmd_lint(profiles, a.id, text)


if __name__ == "__main__":
    sys.exit(main())
