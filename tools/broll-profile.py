#!/usr/bin/env python3
"""生成型 b-roll 的 profile registry：列表 / 状态 / 详情 / 渲染提示词 / 串词 lint / 工序清单。

八套材质语言共用一套引擎（三闸门、画幅几何、gpt-image + seedance 绑定、clip-qa、IR 写回）。
profile 只负责会变的东西：**材质语汇、运动动词、首帧规则、缝合纪律、失败标准**，
外加少数几套的**额外工序**（`pipeline_extras`）。

引擎的一条硬纪律：**它不认识任何 profile 的 id**。
差异全部由 profile 声明（`pipeline_extras` / `variants` / `first_frame.kind` / `banned_vocab`），
引擎只知道「有些 profile 带额外步骤」。搜不到 `if pid == "..."` 这种分支就是这条纪律仍然成立。

`lint` 是这套体系的守门人：它检查一段提示词有没有混入**别的 profile 的签名词汇**。
浣熊片那段做旧报纸味的假像素，成因就是拼贴模板 find/replace 成像素后
`paper-collage` / `paper grain` 留在了里面——那时候没有这道门。

用法:
  broll-profile.py list
  broll-profile.py status
  broll-profile.py vars
  broll-profile.py show <id>
  broll-profile.py render <id> --gate 2|3 [--variant K] [--slot ID] [--var KEY=VALUE ...] [--aspect 16:9]
  broll-profile.py plan <id> [--variant K] [--param k=v ...] [--aspect 16:9]
  broll-profile.py lint <id> --text "<提示词>"   |   --file prompt.txt
  broll-profile.py route "<文稿类型关键词>"
  broll-profile.py selftest
"""
import argparse
import contextlib
import io
import json
import re
import sys
import unicodedata
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / ".claude" / "skills" / "broll-studio"
PROFILE_DIR = SKILL / "profiles"
GATE_FIELD = {2: "gate2_prompt", 3: "gate3_prompt"}
# pipeline_extras 的执行顺序。引擎按这张表照单执行——它认的是**工序种类**，不是 profile 名字。
EXTRA_STAGES = (
    ("film_level_gates", "片级前置闸门（一部片一次，定了就不改）"),
    ("gate2_extra_stills", "Gate 2 附加静帧槽位（每个都是一次出图成本）"),
    ("post_still", "Gate 2 静帧落地后的必做工序"),
    ("post_video", "Gate 3 视频落地后的必做工序"),
    ("extra_checks", "该 profile 专属的额外码判（通用项仍走 tools/clip-qa.py）"),
)


def load_variables():
    return json.loads((SKILL / "variables.json").read_text(encoding="utf-8"))


def load_all():
    """返回 {id: profile}。八套同级，没有「外部链」这一档了。"""
    out = {}
    for f in sorted(PROFILE_DIR.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        out[d["id"]] = d
    if not out:
        sys.exit(f"没找到 profile：{PROFILE_DIR}")
    return out


def get(profiles, pid):
    if pid not in profiles:
        sys.exit(f"未知 profile: {pid}（有 {', '.join(sorted(profiles))}）")
    return profiles[pid]


def extras(p):
    return p.get("pipeline_extras") or {}


def extras_tags(p):
    """一行摘要：这套 profile 比基础三闸门多了什么。"""
    e = extras(p)
    tags = []
    if e.get("film_level_gates"):
        tags.append(f"片级闸门×{len(e['film_level_gates'])}")
    if e.get("gate2_extra_stills"):
        tags.append(f"Gate2 多 {len(e['gate2_extra_stills'])} 张图")
    if e.get("post_still") or e.get("post_video"):
        tags.append("落地后置工序")
    if e.get("extra_checks"):
        tags.append("专属码判")
    if p.get("variants"):
        tags.append(f"{p['variants']['label']}×{len(p['variants']['options'])}")
    return "、".join(tags)


def cmd_list(profiles):
    print("生成型 b-roll · 材质语言 registry（八套同级，一套引擎）\n")
    for pid, p in sorted(profiles.items()):
        st = p.get("status", {})
        print(f"  {pid:18} {p['display_name']}")
        print(f"  {'':18} 核心优势：{p['core_strength']}")
        print(f"  {'':18} 最适合：{'、'.join(p['best_for'][:3])}")
        print(f"  {'':18} 状态：静帧 {st.get('gate2_still', '—')} ｜ 视频 {st.get('gate3_video', '—')}"
              f" ｜ 16:9 {st.get('aspect_16_9', '—')}")
        tags = extras_tags(p)
        if tags:
            print(f"  {'':18} 额外工序：{tags}（`plan {pid}` 看完整清单）")
        print()
    print("同片单一：一条片只准一种生成风格（见 routing.json 的 same_film_rule）。")
    print("状态表单独看：`broll-profile.py status`")


def pad(s, width):
    """按**显示宽度**补空格：中日韩字符与 emoji 占两列，用 len() 排不齐表。"""
    wide = sum(2 if unicodedata.east_asian_width(c) in "WF" or ord(c) > 0x2100 else 1
               for c in s)
    return s + " " * max(1, width - wide)


def cmd_status(profiles):
    print("材质语言 · 冒烟状态（**这是状态的唯一出处**，SKILL.md 不再抄一份）\n")
    w = max(len(k) for k in profiles) + 2
    print("  " + pad("profile", w) + pad("静帧", 12) + pad("视频", 12) + pad("16:9", 10) + "说明")
    for pid, p in sorted(profiles.items()):
        st = p.get("status", {})
        print("  " + pad(pid, w) + pad(st.get("gate2_still", "—"), 12)
              + pad(st.get("gate3_video", "—"), 12) + pad(st.get("aspect_16_9", "—"), 10)
              + st.get("note", ""))
    print()
    for pid, p in sorted(profiles.items()):
        st = p.get("status", {})
        if st.get("evidence"):
            print(f"  {pid}: 证据 {st['evidence']}")
        for k in st.get("known_issues", []):
            print(f"  {pid}: ⚠️ {k}")
    print("\n**排产前**：任一 profile 首次用当前模板出片，Gate 3 先跑 1 条测试 clip 目检，"
          "结论写回该 profile 的 status。跳过 = 静默降级。")


def cmd_vars(profiles):
    reg = load_variables()
    print("提示词变量 · 全仓唯一一套\n")
    for name, d in reg["variables"].items():
        users = sorted(pid for pid, p in profiles.items() if name in p.get("variables", []))
        print(f"  {name:18} {d['zh']}")
        print(f"  {'':18} {d['use']}")
        print(f"  {'':18} 用它的 profile：{'、'.join(users) or '（暂无）'}\n")
    print("旧 visual-spec.json 的字段落点（证明收敛无损）：")
    for k, v in reg["visual_spec_mapping"].items():
        if k != "note":
            print(f"  {k:38} → {v}")


def cmd_show(profiles, pid):
    print(json.dumps(get(profiles, pid), ensure_ascii=False, indent=2))


# ---------------------------------------------------------------- render

def variant_option(p, key):
    v = p.get("variants")
    if not v:
        return {}
    if key is None:
        opts = "、".join(f"{k}（{o['label']}）" for k, o in v["options"].items())
        sys.exit(f"{p['id']} 需要先选 {v['label']}（--variant）：{opts}\n"
                 f"这个选择属于 Gate 1，不该拖到出图时才定。")
    if key not in v["options"]:
        sys.exit(f"未知 {v['label']}: {key}（有 {', '.join(v['options'])}）")
    return v["options"][key]


def pick_template(p, gate, variant_key):
    """基础文本：variant 覆写优先于 profile 本体。"""
    field = GATE_FIELD[gate]
    v = p.get("variants")
    opt = {}
    if v and gate in v.get("required_for_gates", []):
        opt = variant_option(p, variant_key)
    if field in opt:
        return opt[field], opt
    if field not in p:
        sys.exit(f"{p['id']} 没有 {field}")
    return p[field], opt


def all_templates(p):
    """本 profile 的全部提示词文本（含 16:9 原文、variant 覆写、附加静帧槽位）。"""
    out = [v for k, v in p.items() if k.startswith(("gate2_prompt", "gate3_prompt"))]
    for opt in (p.get("variants") or {}).get("options", {}).values():
        out += [v for k, v in opt.items() if k.startswith(("gate2_prompt", "gate3_prompt"))]
    out += [s["prompt"] for s in extras(p).get("gate2_extra_stills", [])]
    return out


def apply_aspect(p, text, field, aspect):
    """16:9 适配。profile 若给了整段实测过的 16:9 原文就用它，否则跑替换规则。
    两条路都是声明式的——引擎不知道哪套 profile 走哪条。"""
    if aspect == "9:16":
        return text
    rules = p.get("aspect_16_9", [])
    # 施工说明（不带 → 的那些）无论走哪条路都要打出来——它们是需要人工落实的，
    # 不是文本替换的副产品。
    for rule in rules:
        if "→" not in rule:
            print(f"  ℹ️ 16:9 施工说明（需人工落实）：{rule}", file=sys.stderr)
    override = p.get(f"{field}_16_9")
    if override:
        print("  ℹ️ 用的是本 profile 的 16:9 实测原文（不走替换规则）", file=sys.stderr)
        return override
    # 一条 profile 的替换规则是全 profile 共享的，其中一部分只针对另一个闸门的模板。
    # 那种「本闸不适用」不该报警——只有**在本 profile 任何模板里都找不着**的规则才是失效规则。
    # 干草堆只能是**模板文本**：把 aspect_16_9 自己也算进去，规则永远能在自己身上命中，告警就永不开火。
    all_text = json.dumps(all_templates(p), ensure_ascii=False)
    for rule in rules:
        if "→" in rule:
            a, b = (s.strip() for s in rule.split("→", 1))
            if a in text:
                text = text.replace(a, b)
            elif a not in all_text:
                print(f"  ⚠️ 画幅替换规则失效（本 profile 任何模板里都没有 {a!r}），请人工核对",
                      file=sys.stderr)
    return text


def render(p, gate, variables, aspect, variant_key=None, slot=None):
    if slot:
        slots = {s["id"]: s for s in extras(p).get("gate2_extra_stills", [])}
        if slot not in slots:
            sys.exit(f"{p['id']} 没有 Gate 2 附加静帧槽位 {slot!r}"
                     f"（有 {', '.join(slots) or '（无）'}）")
        text, field, opt = slots[slot]["prompt"], f"slot_{slot}", {}
    else:
        text, opt = pick_template(p, gate, variant_key)
        field = GATE_FIELD[gate]

    text = apply_aspect(p, text, field, aspect)

    for name, hint in (opt.get("variable_guidance") or {}).items():
        if f"[{name}]" in text:
            print(f"  ℹ️ {name} 按本原型写：{hint}", file=sys.stderr)
    missing = [v for v in p["variables"] if f"[{v}]" in text and v not in variables]
    for k, v in variables.items():
        text = text.replace(f"[{k}]", v)
    return text, missing


def cmd_render(profiles, pid, gate, variables, aspect, variant_key, slot):
    p = get(profiles, pid)
    reg = load_variables()["variables"]
    unknown = [v for v in p.get("variables", []) if v not in reg]
    if unknown:
        sys.exit(f"{pid} 声明了变量表外的变量：{unknown}。"
                 f"要么改用 variables.json 里的名字，要么先把新变量加进 variables.json 并说明用途"
                 f"——同义变量各写一遍就是同一份知识多副本。")
    bogus = [k for k in variables if k not in reg]
    if bogus:
        print(f"  ⚠️ --var 里有变量表外的名字（会被忽略）：{bogus}", file=sys.stderr)

    if gate == 2 and not slot:
        for s in extras(p).get("gate2_extra_stills", []):
            print(f"  ❗ 本 profile 的 Gate 2 还有一张附加静帧要出："
                  f"`--slot {s['id']}`（{s['purpose']}，{s.get('cost', '成本 +1 张图')}）", file=sys.stderr)
    for g in extras(p).get("film_level_gates", []):
        print(f"  ❗ 前置：{g['name']} 必须先过（`plan {pid}` 看命令）", file=sys.stderr)

    text, missing = render(p, gate, variables, aspect, variant_key, slot)
    if missing:
        print(f"  ⚠️ 未填变量：{', '.join(missing)}（占位符原样保留）", file=sys.stderr)
    print(text)
    stray, banned = lint_text(profiles, pid, text)
    if stray or banned:
        if stray:
            print("\n  ❌ 串词：" + "；".join(f"{w}（属于 {o}）" for w, o in stray), file=sys.stderr)
        if banned:
            print("  ❌ 禁用词：" + "；".join(banned), file=sys.stderr)
        return 1
    return 0


# ---------------------------------------------------------------- plan

def fill_params(text, params):
    out = re.sub(r"\{([a-z_]+)\}", lambda m: params.get(m.group(1), m.group(0)), text)
    return out


def cmd_plan(profiles, pid, params, aspect, variant_key):
    p = get(profiles, pid)
    e = extras(p)
    params = {**(e.get("params") or {}), **params}
    opt = variant_option(p, variant_key) if p.get("variants") else {}
    ff = opt.get("first_frame") or p["first_frame"]

    print(f"# {pid} · {p['display_name']} · {aspect} 工序清单\n")
    print("三闸门是所有 profile 共有的（SKILL.md §3），下面只标出本 profile 的**额外工序**"
          "与随 profile 变的规则。\n")

    if p.get("variants"):
        print(f"[Gate 1] {p['variants']['label']}：{variant_key}（{opt['label']}）— {opt.get('when', '')}\n")

    for key, title in EXTRA_STAGES:
        items = e.get(key) or []
        if not items:
            continue
        print(f"[{title}]")
        for it in items:
            if isinstance(it, str):
                print(f"  $ {fill_params(it, params)}")
            elif key == "gate2_extra_stills":
                print(f"  · {it['id']}：{it['purpose']}（{it.get('cost', '+1 张图')}）")
                print(f"    $ python3 tools/broll-profile.py render {pid} --gate 2 --slot {it['id']} ...")
            else:
                print(f"  · {it['name']}｜成本 {it.get('cost', '—')}｜停下问：{it.get('ask', '—')}")
                if it.get("cmd"):
                    print(f"    $ {fill_params(it['cmd'], params)}")
        print()

    print("[首帧规则]")
    print(f"  kind={ff['kind']}｜{ff['spec']}")
    print(f"  {ff.get('ffmpeg', '')}\n")
    print("[缝合纪律]")
    print(f"  {p.get('stitching', '（未声明——八套都该有一句，缺了就是漏写）')}\n")
    print("[验收]")
    print(f"  通用：python3 tools/clip-qa.py <clip> --expect-size "
          f"{'1280x720' if aspect == '16:9' else '720x1280'} --json <evidence> --contact <sheet>")
    if e.get("extra_checks"):
        print("  专属：见上面「专属码判」")
    print("  批次：python3 tools/clip-batch-sheets.py --clips ... --stills ... --out-dir <evidence>")
    print("  人眼：逐条对 failure_criteria（`show " + pid + "` 看）")
    unfilled = sorted(set(re.findall(r"\{([a-z_]+)\}", json.dumps(e, ensure_ascii=False)))
                      - set(params))
    if unfilled:
        print(f"\n  ⚠️ 未填参数（命令里仍是占位符）：{', '.join(unfilled)} — 用 --param k=v 填")


# ---------------------------------------------------------------- lint

def positive_part(text):
    """只保留**肯定描述**。否定式约束不是串词——恰恰相反：
    object-theatre 的 `No paper collage`、felted-wool 的 `No clay` 是在**主动划界**，
    正是我们要的东西。把 Avoid: 段与以 No/no 开头的从句剥掉再匹配。"""
    text = re.split(r"\bAvoid\s*:", text, maxsplit=1)[0]
    clauses = re.split(r"(?<=[.\n])|,\s*(?=no\s)", text, flags=re.IGNORECASE)
    return " ".join(c for c in clauses
                    if not re.match(r"\s*no[nt]?\s", c or "", flags=re.IGNORECASE))


def hit(word, low):
    return re.search(r"(?<![a-z])" + re.escape(word.lower()) + r"(?![a-z])", low)


def lint_text(profiles, pid, text):
    """返回 (串词 [(词, 归属 profile)], 禁用词 [说明])。"""
    low = positive_part(text).lower()
    mine = {w.lower() for w in profiles[pid].get("signature_vocab", [])}
    stray = []
    for oid, other in profiles.items():
        if oid == pid:
            continue
        for w in other.get("signature_vocab", []):
            if w.lower() in mine:
                continue          # 两套共有的词不算串（例如都用 isometric）
            if hit(w, low):
                stray.append((w, oid))
    ban = profiles[pid].get("banned_vocab") or {}
    banned = [f"{w}（{ban.get('why', '本 profile 禁用')}）"
              for w in ban.get("words", []) if hit(w, low)]
    return stray, banned


def cmd_lint(profiles, pid, text):
    get(profiles, pid)
    stray, banned = lint_text(profiles, pid, text)
    if not stray and not banned:
        print(f"✅ 无串词、无禁用词（对照其余 {len(profiles) - 1} 套材质语汇）")
        return 0
    if stray:
        print(f"❌ 命中 {len(stray)} 处别的风格的签名词汇：")
        for w, o in stray:
            print(f"   {w!r} → 属于 {o}（{profiles[o]['display_name']}）")
        print("\n混风就是「拼贴模板 find/replace 成像素」那类杂交产物的成因。"
              "要么删掉这些词，要么整镜改走那个 profile。")
    if banned:
        print(f"❌ 命中 {len(banned)} 处本 profile 的禁用词：")
        for b in banned:
            print(f"   {b}")
    return 1


# ---------------------------------------------------------------- route / selftest

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


DUMMY = "X"


def cmd_selftest(profiles):
    """自洽性测试：每套 profile 的每个闸门 / 原型 / 附加槽位 / 画幅都渲一遍并自查。
    验的是三件事：变量都在表内、模板渲得出来、**每套过自己的 lint**（不串别人的词、不碰自己的禁用词）。"""
    reg = load_variables()["variables"]
    fails, n = [], 0
    for pid, p in sorted(profiles.items()):
        unknown = [v for v in p.get("variables", []) if v not in reg]
        if unknown:
            fails.append(f"{pid}: 变量表外的变量 {unknown}")
        for key in ("stitching", "first_frame", "failure_criteria", "status"):
            if not p.get(key):
                fails.append(f"{pid}: 缺 {key}")
        variables = {v: DUMMY for v in p.get("variables", [])}
        v = p.get("variants")
        keys = list(v["options"]) if v else [None]
        jobs = [(g, k, None) for g in (2, 3)
                for k in (keys if v and g in v.get("required_for_gates", []) else [None])]
        jobs += [(2, keys[0] if v else None, s["id"])
                 for s in extras(p).get("gate2_extra_stills", [])]
        for gate, vk, slot in jobs:
            for aspect in ("9:16", "16:9"):
                n += 1
                label = f"{pid} gate{gate}" + (f"/{vk}" if vk else "") \
                    + (f"/slot:{slot}" if slot else "") + f" {aspect}"
                try:
                    # 渲染期的施工说明/未命中提示是给交互用的，selftest 只要 pass/fail
                    with contextlib.redirect_stderr(io.StringIO()):
                        text, missing = render(p, gate, variables, aspect, vk, slot)
                except SystemExit as ex:
                    fails.append(f"{label}: 渲染失败 {ex}")
                    continue
                if missing:
                    fails.append(f"{label}: 未填变量 {missing}")
                stray, banned = lint_text(profiles, pid, text)
                if stray:
                    fails.append(f"{label}: 串词 "
                                 + "；".join(f"{w}→{o}" for w, o in stray))
                if banned:
                    fails.append(f"{label}: 禁用词 " + "；".join(banned))
    print(f"自洽性测试：{len(profiles)} 套 profile × {n} 次渲染")
    for f in fails:
        print(f"  ❌ {f}")
    print(f"\n{n - len(fails)}/{n} 通过" if fails else f"\n{n}/{n} 通过")
    return 1 if fails else 0


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sub.add_parser("status")
    sub.add_parser("vars")
    sub.add_parser("selftest")
    s = sub.add_parser("show"); s.add_argument("id")
    r = sub.add_parser("render"); r.add_argument("id")
    r.add_argument("--gate", type=int, choices=(2, 3), required=True)
    r.add_argument("--var", action="append", default=[], metavar="KEY=VALUE")
    r.add_argument("--aspect", default="9:16", choices=("9:16", "16:9"))
    r.add_argument("--variant", help="带运动原型等维度的 profile 必填")
    r.add_argument("--slot", help="Gate 2 附加静帧槽位 id")
    n = sub.add_parser("plan"); n.add_argument("id")
    n.add_argument("--param", action="append", default=[], metavar="key=value")
    n.add_argument("--aspect", default="9:16", choices=("9:16", "16:9"))
    n.add_argument("--variant")
    l = sub.add_parser("lint"); l.add_argument("id")
    l.add_argument("--text"); l.add_argument("--file", type=Path)
    t = sub.add_parser("route"); t.add_argument("query", nargs="?", default="")
    a = p.parse_args()

    profiles = load_all()
    if a.cmd == "list":
        return cmd_list(profiles) or 0
    if a.cmd == "status":
        return cmd_status(profiles) or 0
    if a.cmd == "vars":
        return cmd_vars(profiles) or 0
    if a.cmd == "selftest":
        return cmd_selftest(profiles)
    if a.cmd == "show":
        return cmd_show(profiles, a.id) or 0
    if a.cmd == "route":
        return cmd_route(profiles, a.query) or 0
    if a.cmd in ("render", "plan"):
        kv = {}
        for item in (a.var if a.cmd == "render" else a.param):
            if "=" not in item:
                sys.exit(f"要写成 KEY=VALUE，收到 {item!r}")
            k, v = item.split("=", 1)
            kv[k.strip()] = v
        if a.cmd == "render":
            return cmd_render(profiles, a.id, a.gate, kv, a.aspect, a.variant, a.slot)
        return cmd_plan(profiles, a.id, kv, a.aspect, a.variant) or 0
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
