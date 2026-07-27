#!/usr/bin/env python3
"""G2 评委（去模型化 · 2026-07-24；评审模式 · 2026-07-27）：本工具只做确定性两端——**出题**
（组织证据 + rubric）与**阅卷**（规则派生判词 + 引用校验）。**打分由 agent 自己派发的隔离
subagent 用宿主 harness 的模型完成**，本工具不含任何模型 / 网关 / 凭据——评委的"眼睛"是宿主的
模型，不是焊死的某个 API。

## 评审模式（--mode，2026-07-27 补，见 docs/todo-from-ac-experiment.md P0）

实测：同一批 hero frame，配对评审与单臂评审给出**相反**胜负。所以模式必须显式规定，不能随手选。

- `solo`（单臂，缺省）：面前只有一件作品，回答**绝对问题**——够不够出厂、过不过 Golden 下限。
  有对手在场时分数会被对手质量污染（实测某臂对上明显更差的对手，四维各涨 3–4 分），
  所以绝对门一律单臂。产出 pass/fail。
- `paired`（配对，须 `--vs <另一个 pack>`）：两臂同席、同尺、强制选择，回答**相对问题**——
  新版比旧版好没好、A/B 哪个更好。跨会话的绝对分不可比，所以相对结论一律配对。
  **配对不产出 pass/fail**（`verdict` 恒为 null）。两臂经确定性哈希打乱成 甲/乙 并复制到中立
  擂台 `<repo>/.judge-arena/<node>-<hash>/`（不在任何一臂 pack 内，路径里没有项目名）；
  派发用擂台里的 `task.md`，对照表 `judge-armmap-<node>.json` **不得交给评委**。

两路都跑时用 `--merge` 合并；方向相反 = 结论不稳，记"无定论"，禁止声称胜负。

流程（produce SOP ③b / ⑨ 调用）：
  1) build_evidence_pack.py <project>                       # 证据包：frames/contact-sheet/golden/L0/manifest/音轨
  2) judge.py <pack> --node {hero_frames|final|audio} [--mode solo] --task
     judge.py <packA> --node ... --mode paired --vs <packB> --task
       打印隔离评审任务（rubric + 证据文件绝对路径清单 + 镜头事实 + 引用纪律 + 输出 JSON schema），
       并落 <pack>/judge-task-<node>[-paired].md
  3) agent 派发隔离 subagent：把任务 + 证据文件喂进去（subagent 看不到创作上下文），收回 JSON 打分
  4) judge.py <pack> --node ... [--mode ...] --finalize scores.json   # 规则派生判词 + 引用校验（视觉）/
       字符重合率（音频）→ <pack>/judge-report-<node>[-paired].json
  5) judge.py <packA> --node ... --merge <配对报告> <单臂A报告> <单臂B报告>   # 两路合并 → 稳/不稳

隔离纪律：subagent 只看证据（frames/video/audio + 镜头事实 manifest，零创作理由）；扣分必须引用
镜头 ID/时间码，否则整报作废重评（无锚点自评 ~46%，styles/_iteration.md）。verdict 由规则派生——
不信模型自报（存 verdict_model 作校准语料）。评委与导演不同模型家族是特性（同族自评共享盲区）——
由宿主在派发 subagent 时保证；本工具不选模型。
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

VERDICT_RULE = "overall<3.5 或命中任一反模式 或 任一 hero frame 未过 → fail（模型自报仅存 verdict_model）"
AUDIO_ACC_MIN = 0.95

# —— 合并阈值（overall 归一到 1–5 分制；换算见 README「两路合并」）——
DECISIVE_MARGIN = 0.3   # 单路 |Δoverall| < 此值 = 该路没拉开，不算证据
PAIRED_TIE_MARGIN = 0.3 # 配对两臂 |Δoverall| < 此值 = 配对判平
CONTRAST_ALARM = 0.5    # |Δ配对 − Δ单臂| ≥ 此值 = 对照效应过大，结论降级为 weak

FINAL_CRITERIA = """九维评分（各 1–5 分，可 0.5 步进）：D1 叙事结构 D2 信息密度与出处感 D3 节奏呼吸
D4 版式与视觉克制 D5 音画同步与混音 D6 质感缝合（AI 塑料感/LUT/颗粒）
D7 运动意图 D8 创意 D9 网感。
评分锚：3 = 合格可发布下限；4 = 明显高于平均；5 = 该维度挑不出可改进点。
先找缺陷再给分——note 里说不出具体缺陷或改进点的维度，禁止给到 4.5 以上。
【运动工艺专项】D3/D7 按工艺细节评：缓动有无设计（单一线性/统一 cubic = 没设计）、
元素入场有无层次（stagger）、有无次级运动与收尾定帧、动静对比是否有意图。
仅"元素在动"不构成 4 分；线性平移缩放淡入的堆砌 = D7 ≤ 3 并计入反模式。
【版式专项】克制 ≠ 稀疏：单屏元素孤立漂浮、留白无信息承载、构图重心失衡 = 扣分；
D4 给 5 的标准是每一屏都经得起单帧海报级审视。
反模式逐条核（命中即在 antipatterns 列出并扣分）：幻灯片化/冻结帧补时长、转场遮丑、
模板味（换选题还成立=没做够）、无意图运镜、AI 光泽不缝合、
动效工艺缺失（仅线性平移缩放淡入、无缓动设计/无 stagger/无次级运动）、
画面稀疏空板（元素孤立漂浮、留白无信息承载）。
【感知诚实】只评你确实看到/听到的证据。工艺判断（缓动类型/stagger/次级运动/音效/BGM）
必须能描述出具体画面或声音证据——描述不出的一律视为**不存在**，禁止按本 rubric 词表脑补；
无法确认的维度给 ≤3.5 并在 note 标注「证据不足」。夸赞不存在的元素 = 整报作废。
【引用纪律】每个维度的 note 必须引用镜头 ID 或时间码（如 s03 / 00:12–00:17），
无引用的判断无效（D9 网感可锚定标题/钩子/推荐流语境）。"""

HERO_CRITERIA = """评 hero-frame 品味门（分镜铺开前）。证据：本片 3 张 hero frame
+ 该风格包 Golden 基准 contact sheet。四维评分（各 1–5 分，可 0.5 步进）：
H1 风格贴合 H2 版式克制（克制≠稀疏：元素孤立漂浮、留白无信息承载 = 扣分）
H3 质感缝合（AI 塑料感/LUT/颗粒） H4 达到 Golden 视觉下限的把握。
评分锚：3 = 刚够铺开生产的下限；4 = 明显高于该风格包平均；5 = 挑不出可改进点。
逐条核风格包反模式，并做模板味测试（换个选题还成立 = 没做够）。逐帧引用 frame 序号。"""

FINAL_SOLO_SCHEMA = """只输出 JSON：
{"scores": {"D1": x, ..., "D9": x}, "overall": x, "antipatterns": [".."],
 "notes": {"D1": "..引用..", ...}, "verdict": "pass|fail", "one_line": ".."}"""

HERO_SOLO_SCHEMA = """未达下限 = 打回，禁止铺开全片生产。只输出 JSON：
{"scores": {"H1": x, "H2": x, "H3": x, "H4": x},
 "per_frame": [{"frame": "..", "pass": bool, "reason": "..引用.."}],
 "antipatterns": [".."], "template_test": "..", "verdict": "pass|fail",
 "notes": {"H1": "..引用..", "H2": "..", "H3": "..", "H4": "..", "overall": "..引用.."},
 "must_fix": ["..引用.."]}"""

SOLO_PREAMBLE = """【单臂绝对评审】你面前只有**一件**作品。没有对手，也不要设想对手。
本轮问的是绝对问题：它自己够不够出厂下限。
证据里若有 Golden 基准，那是**固定标尺**，不是竞争对手——用它定位下限即可，不要给 Golden 打分、
不要评"谁更好"。禁止与任何未列在证据清单中的作品比较，也禁止用"比一般的强/弱"代替对下限的判断。
"""

PAIRED_PREAMBLE = """【配对相对评审】证据里有**两件**作品，代号 甲 / 乙。它们的来历、新旧、作者
一律不告诉你；代号顺序与优劣无关，不要从顺序、文件名或镜头数量推测身份。
本轮只问相对问题：同一维度上谁做得更好。**不要**判断它们够不够出厂——那是单臂评审的事，
配对分会被对手质量污染，本报告不产出 pass/fail。
两臂用同一把尺、同一组维度打分；逐维给出更优方（可判 tie）；最后必须做**强制选择**，整体不许判平。
每条判断都要指明是哪一臂的哪个镜头 ID / 帧序号 / 时间码。
证据里若有 Golden 基准，它是两臂**共用的标尺**，不参与比较、不打分。
"""

RUBRIC = "你是独立评委，只依据给到的证据评审，禁止臆测创作过程。\n" + FINAL_CRITERIA + "\n" + FINAL_SOLO_SCHEMA
HERO_RUBRIC = "你是独立评委，" + HERO_CRITERIA + "\n" + HERO_SOLO_SCHEMA

_PAIRED_DIMS = {
    "final": ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9"],
    "hero_frames": ["H1", "H2", "H3", "H4"],
}


def _paired_schema(node: str) -> str:
    dims = _PAIRED_DIMS[node]
    kv = ", ".join(f'"{d}": x' for d in dims)
    winners = ", ".join(f'"{d}": "甲|乙|tie"' for d in dims)
    notes = ", ".join(f'"{d}": "..引用.."' for d in dims)
    return f"""只输出 JSON（两臂逐维都要给分，一维不许空缺）：
{{"arms": {{"甲": {{"scores": {{{kv}}}, "antipatterns": [".."], "notes": {{{notes}}}}},
          "乙": {{"scores": {{{kv}}}, "antipatterns": [".."], "notes": {{{notes}}}}}}},
 "per_dimension_winner": {{{winners}}},
 "forced_choice": "甲|乙",
 "why": "..引用两臂各自的镜头 ID / 帧序号 / 时间码..",
 "one_line": ".."}}"""


AUDIO_QC_PROMPT = """你在做视频的音频质检与字幕/音频校对。给你一段音频（成片音轨）和它应当念出的
脚本分节文本。请**只依据你真实听到的声音**输出 JSON，禁止照抄脚本充当转写：
{"transcript": "你逐字听到的完整中文转写（听不清的词写□，不要用脚本补全）",
 "voice": "人声性别/音色/语速/情绪的客观描述",
 "mixing": "混音观感：人声清晰度、有无爆音/齿音/忽大忽小、响度是否稳",
 "bgm_sfx": "是否存在背景音乐(BGM)与音效(SFX)；有就描述，没有就明确说无",
 "subtitle_audio_issues": ["脚本里有但没听到、或听到与脚本不一致、或多念漏念的逐条列出；无则空数组"],
 "issues": ["其它音频缺陷逐条；无则空数组"]}"""

_CITE = re.compile(r"s\d{1,3}[a-z_]*|\d{1,2}:\d{2}|\d{1,3}(?:\.\d+)?s|frame\s*\d|第\s*\d+\s*[张帧格]")
_HOLISTIC = re.compile(r"钩子|标题|开场|推荐页|推荐流|封面")

ARM_LABEL = {"arm_a": "甲", "arm_b": "乙"}
_LABEL2ARM = {"甲": "arm_a", "乙": "arm_b", "A": "arm_a", "B": "arm_b",
              "arm_a": "arm_a", "arm_b": "arm_b"}


def _mean(scores: dict | None) -> float | None:
    vals = [v for v in (scores or {}).values() if isinstance(v, (int, float))]
    return round(sum(vals) / len(vals), 3) if vals else None


def _derive_verdict(report: dict) -> None:
    """verdict 规则推导：模型对自己的判决偏宽（实测 3.2 分 + 4 条反模式仍自报 pass）。"""
    report["verdict_model"] = report.get("verdict")
    overall = report.get("overall")
    if not isinstance(overall, (int, float)):
        overall = _mean(report.get("scores"))
        report["overall"] = overall
    frame_fail = any(f.get("pass") is False for f in (report.get("per_frame") or []) if isinstance(f, dict))
    fail = ((isinstance(overall, (int, float)) and overall < 3.5)
            or bool(report.get("antipatterns")) or frame_fail)
    report["verdict"] = "fail" if fail else "pass"
    report["verdict_rule"] = VERDICT_RULE


def _cite_ok(key: str, text: str) -> bool:
    if not isinstance(text, str) or not text.strip():
        return True
    return bool(_CITE.search(text)) or (key.split(".")[-1] in ("D9", "overall", "why")
                                        and bool(_HOLISTIC.search(text)))


def _validate_citations(report: dict) -> None:
    """无镜头 ID/时间码引用的判断标 invalid（隔离评委核心纪律）。"""
    invalid = []

    def check_notes(notes, prefix):
        for k, v in (notes or {}).items():
            if not _cite_ok(k, v):
                invalid.append(f"{prefix}notes.{k}")

    check_notes(report.get("notes"), "")
    for arm, blob in (report.get("arms") or {}).items():
        check_notes((blob or {}).get("notes"), f"arms.{arm}.")
    if not _cite_ok("why", report.get("why", "")):
        invalid.append("why")
    for i, f in enumerate(report.get("per_frame") or []):
        if not _cite_ok(f"per_frame[{i}]", (f or {}).get("reason", "")):
            invalid.append(f"per_frame[{i}]")
    report["citations_valid"] = not invalid
    report["citations_invalid_items"] = invalid


def _char_overlap(ref: str, hyp: str) -> float:
    """LCS 比——粗粒度转写准确率代理（中文同音字/数字是噪声，此度量足够挡真吞字）。"""
    norm = lambda s: re.sub(r"[\s，。、！？,.!?：:；;“”‘’（）()]", "", s or "")
    ref, hyp = norm(ref), norm(hyp)
    if not ref or not hyp:
        return 0.0
    return difflib.SequenceMatcher(None, ref, hyp, autojunk=False).ratio()


def _load(p: Path) -> dict:
    return json.loads(Path(p).read_text(encoding="utf-8"))


# ——————————————————————————— 配对：盲化与落盘 ———————————————————————————

# 中立擂台：配对证据**不能**暂存在任何一臂的 pack 里。放在 packA 下面时，两臂的
# 绝对路径都带着 packA 的项目名——虽然对称（看不出哪臂是哪个），但等于告诉评委
# 「这两件里有一个是 urban-wildlife-raccoon」，帧一眼认得出就穿帮了。擂台目录只
# 用两臂路径的哈希命名，不含任何项目信息。
ARENA = Path(__file__).resolve().parents[2] / ".judge-arena"


def _pair_key(p1: Path, p2: Path) -> str:
    return "|".join(sorted([str(p1.resolve()), str(p2.resolve())]))


def _arm_order(p1: Path, p2: Path) -> list[tuple[str, Path]]:
    """确定性哈希决定谁是甲谁是乙：可复跑，且与"新/旧""A/C"的调用顺序脱钩。"""
    flip = hashlib.sha256(_pair_key(p1, p2).encode("utf-8")).digest()[0] % 2
    first, second = (p2, p1) if flip else (p1, p2)
    return [("arm_a", first), ("arm_b", second)]


def _arena_dir(p1: Path, p2: Path, node: str) -> Path:
    """本次配对的中立擂台目录。名字 = node + 两臂路径哈希，确定性、可复跑、无项目名。"""
    h = hashlib.sha256(f"{node}\n{_pair_key(p1, p2)}".encode("utf-8")).hexdigest()[:10]
    return ARENA / f"{node}-{h}"


def _arm_files(pack: Path, node: str) -> list[tuple[str, Path]]:
    """该臂要进中立目录的证据文件（Golden 不在内——它是两臂共用标尺）。"""
    out: list[tuple[str, Path]] = []
    if node == "hero_frames":
        for f in sorted((pack / "frames").glob("*.jpg")) + sorted((pack / "frames").glob("*.png")):
            out.append(("hero frame", f))
    else:
        for name, label in (("contact-sheet.jpg", "contact sheet"),
                            ("contact-sheet-offset.jpg", "contact sheet 半步错位版")):
            if (pack / name).is_file():
                out.append((label, pack / name))
        for f in sorted((pack / "frames").glob("*.jpg")):
            out.append(("逐镜帧", f))
    return out


def _stage_paired(pack: Path, other: Path, node: str) -> dict:
    """两臂证据复制进**仓库级中立擂台**（不在任何一臂 pack 内）：路径里不出现任何
    项目名，只留 arm_a/arm_b + 原始文件名（文件名带镜头 ID，引用纪律需要它）。
    同时把 armmap 对照表落回 pack——**不交给评委**，只供阅卷揭盲。"""
    root = _arena_dir(pack, other, node)
    if root.exists():
        shutil.rmtree(root)
    armmap: dict = {"node": node, "schema": "judge-armmap@1",
                    "arena": str(root.resolve()),
                    "warning": "对照表：不得随证据交给评委 subagent；仅供阅卷揭盲"}
    staged: dict[str, list[tuple[str, Path]]] = {}
    for arm, src in _arm_order(pack, other):
        dst = root / arm
        dst.mkdir(parents=True, exist_ok=True)
        files = []
        for label, f in _arm_files(src, node):
            tgt = dst / f.name
            shutil.copy2(f, tgt)
            files.append((label, tgt))
        staged[arm] = files
        m = _load(src / "manifest.json")
        armmap[arm] = {"label": ARM_LABEL[arm], "pack": str(src.resolve()),
                       "title": m.get("title"), "style_pack": m.get("style_pack"),
                       "files": len(files)}
    if not staged["arm_a"] or not staged["arm_b"]:
        raise SystemExit(f"配对失败：某一臂在 node={node} 下没有可用证据文件（先跑 build_evidence_pack.py）")
    (pack / f"judge-armmap-{node}.json").write_text(
        json.dumps(armmap, ensure_ascii=False, indent=2), encoding="utf-8")
    armmap["_staged"] = staged
    return armmap


# ——————————————————————————— 出题 ———————————————————————————

def _emit_solo(pack: Path, node: str) -> str:
    manifest = _load(pack / "manifest.json")
    ev: list[str] = []

    def add(name: str, label: str):
        f = pack / name
        if f.is_file():
            ev.append(f"- {label}: {f.resolve()}")

    extra = ""
    if node == "audio":
        prompt = AUDIO_QC_PROMPT
        add("audio.mp3", "成片音轨（真听）")
        secs = manifest.get("sections") or []
        script = "\n".join(f"[{s['id']} {s['t'][0]:.1f}-{s['t'][1]:.1f}s] {s.get('text', '')}"
                           for s in secs)
        extra = "\n## 应念脚本分节（供校对，不是让你照抄）\n" + (script or "（manifest 无 sections）")
    elif node == "hero_frames":
        prompt = HERO_RUBRIC
        for f in sorted((pack / "frames").glob("*.jpg")) + sorted((pack / "frames").glob("*.png")):
            ev.append(f"- hero frame: {f.resolve()}")
        add("golden-contact-sheet.jpg", "Golden 基准 contact sheet（固定标尺，不是对手）")
    else:  # final
        prompt = RUBRIC
        gm = manifest.get("grid_time_map", {}).get("rule", "")
        add("contact-sheet.jpg", f"本片 contact sheet（{gm}）")
        add("contact-sheet-offset.jpg", "本片 contact sheet 半步错位版")
        add("golden-contact-sheet.jpg", "Golden 基准 contact sheet（固定标尺，不是对手）")
        for f in sorted((pack / "frames").glob("*.jpg")):
            ev.append(f"- 逐镜帧: {f.resolve()}")

    facts = json.dumps(manifest.get("shots", []), ensure_ascii=False)
    amends = json.dumps(manifest.get("contract_amendments") or {}, ensure_ascii=False)
    gdef = manifest.get("golden_known_defects") or []
    if gdef:
        extra += ("\n## Golden 的已知缺陷（**不是可照抄的语法**）\n"
                  "作为标尺的 Golden 本身带下列已知违规——它们不构成标准，"
                  "本片出现同类问题照样扣分，本片**没有**这些问题不算减分项：\n"
                  + "\n".join(f"- {d}" for d in gdef) + "\n")
    preamble = "" if node == "audio" else SOLO_PREAMBLE + "\n"
    return f"""# 隔离评审任务 · node={node} · mode=solo（单臂 / 绝对判断）

> 你是 Kuleshov 独立评委（G2），与创作者物理隔离：只看下列证据，不接受、不索取任何创作过程解释。

{preamble}## 评分/评审标准
{prompt}

## 证据文件（附给你评审，逐个看）
{chr(10).join(ev) if ev else "（无证据文件——先跑 build_evidence_pack.py）"}

## 镜头事实清单（id/区间/意图/景别/来源，零创作理由）
{facts}

## 合同带宽内调整（评审时须知悉）
{amends}
{extra}

## 交回
只输出上面 schema 规定的一个 JSON 对象。扣分/判断必须引用镜头 ID 或时间码，无引用的判断无效。
"""


def _emit_paired(pack: Path, other: Path, node: str) -> str:
    armmap = _stage_paired(pack, other, node)
    staged = armmap.pop("_staged")
    criteria = HERO_CRITERIA if node == "hero_frames" else FINAL_CRITERIA

    blocks, facts = [], {}
    for arm in ("arm_a", "arm_b"):
        lab = ARM_LABEL[arm]
        lines = [f"- {label}: {f.resolve()}" for label, f in staged[arm]]
        blocks.append(f"### {lab} 臂证据\n" + "\n".join(lines))
        m = _load(Path(armmap[arm]["pack"]) / "manifest.json")
        facts[lab] = {"shots": m.get("shots", []),
                      "contract_amendments": m.get("contract_amendments") or {},
                      "grid_time_map": m.get("grid_time_map", {}).get("rule", "")}
    # 标尺也要进擂台：它原本在 packA 里，直接给路径等于把 packA 的项目名递给评委
    src_golden = pack / "golden-contact-sheet.jpg"
    gold_line = ""
    if src_golden.is_file():
        golden = Path(armmap["arena"]) / "golden-contact-sheet.jpg"
        shutil.copy2(src_golden, golden)
        gold_line = ("\n### 两臂共用标尺（不打分、不参与比较）\n"
                     f"- Golden 基准 contact sheet: {golden.resolve()}")

    return f"""# 隔离评审任务 · node={node} · mode=paired（配对 / 相对判断）

> 你是 Kuleshov 独立评委（G2），与创作者物理隔离：只看下列证据，不接受、不索取任何创作过程解释。

{PAIRED_PREAMBLE}
## 评分/评审标准
{criteria}

## 证据文件（两臂各自逐个看完，再回来比）
{blocks[0]}

{blocks[1]}{gold_line}

## 镜头事实清单（按臂给出；id/区间/意图/景别/来源，零创作理由）
{json.dumps(facts, ensure_ascii=False)}

## 交回
{_paired_schema(node)}

强制选择不许弃权；每条判断必须写明是哪一臂的哪个镜头 ID / 帧序号 / 时间码，无引用的判断无效。
本轮**不产出 pass/fail**——不要写"够/不够出厂"。
"""


def emit_task(pack: Path, node: str, mode: str = "solo", other: Path | None = None) -> str:
    """出题：组织证据文件清单 + rubric + 镜头事实 → 隔离 subagent 的评审任务。"""
    if mode == "paired":
        task = _emit_paired(pack, other, node)
        name = f"judge-task-{node}-paired.md"
        # 题面也落一份进中立擂台：派发 subagent 时给这个路径，别给 pack 里那份——
        # 文件路径本身会把其中一臂的项目名带进评委上下文。
        arena_task = _arena_dir(pack, other, node) / "task.md"
        arena_task.write_text(task, encoding="utf-8")
        print(f"中立题面（派发用这个）: {arena_task}", file=sys.stderr)
    else:
        task = _emit_solo(pack, node)
        name = f"judge-task-{node}.md"
    (pack / name).write_text(task, encoding="utf-8")   # pack 内留档
    return task


# ——————————————————————————— 阅卷 ———————————————————————————

def _finalize_paired(pack: Path, node: str, raw: dict) -> dict:
    armmap_f = pack / f"judge-armmap-{node}.json"
    if not armmap_f.is_file():
        raise SystemExit(f"缺少臂对照表 {armmap_f}——先用 --mode paired --vs <pack> --task 出题")
    armmap = _load(armmap_f)

    arms: dict = {}
    for key, blob in (raw.get("arms") or {}).items():
        arm = _LABEL2ARM.get(str(key).strip())
        if not arm:
            raise SystemExit(f"打分 JSON 的臂代号无法识别: {key!r}（应为 甲/乙）")
        arms[arm] = dict(blob or {})
    missing = {"arm_a", "arm_b"} - set(arms)
    if missing:
        raise SystemExit(f"打分 JSON 缺臂: {sorted(missing)}——配对报告必须两臂都在")

    for arm, blob in arms.items():
        blob["label"] = ARM_LABEL[arm]
        blob["pack"] = armmap[arm]["pack"]          # 揭盲
        blob["overall"] = _mean(blob.get("scores"))

    oa, ob = arms["arm_a"]["overall"], arms["arm_b"]["overall"]
    if oa is None or ob is None:
        raise SystemExit("配对报告某一臂没有可用分数——无法派生胜负")
    delta = round(ob - oa, 3)
    winner = "tie" if abs(delta) < PAIRED_TIE_MARGIN else ("arm_b" if delta > 0 else "arm_a")

    fc = _LABEL2ARM.get(str(raw.get("forced_choice", "")).strip())
    report = {
        "node": node, "mode": "paired", "pack": str(pack.resolve()),
        "arms": arms,
        "delta_b_minus_a": delta, "tie_margin": PAIRED_TIE_MARGIN,
        "winner": winner,
        "winner_pack": None if winner == "tie" else arms[winner]["pack"],
        "winner_model": fc,
        "winner_rule": f"|Δoverall| < {PAIRED_TIE_MARGIN} → tie；否则 overall 高者胜（模型强制选择仅存 winner_model）",
        "per_dimension_winner": raw.get("per_dimension_winner") or {},
        "why": raw.get("why", ""), "one_line": raw.get("one_line", ""),
        "verdict": None,
        "absolute_verdict": "n/a — 配对分被对手质量污染，绝对判断（出厂/Golden 下限）必须另跑 --mode solo",
    }
    _validate_citations(report)
    return report


def finalize(pack: Path, node: str, scores_file: Path, mode: str = "solo") -> dict:
    """阅卷：读 subagent 打分 JSON → 规则派生判词 + 引用校验（视觉）/ 字符重合率（音频）。"""
    manifest = _load(pack / "manifest.json")
    raw = _load(scores_file)
    if mode == "paired":
        report = _finalize_paired(pack, node, raw)
    elif node == "audio":
        secs = manifest.get("sections") or []
        script_full = "".join(s.get("text", "") for s in secs)
        acc = _char_overlap(script_full, raw.get("transcript", ""))
        sub_issues = raw.get("subtitle_audio_issues") or []
        ok = acc >= AUDIO_ACC_MIN and not sub_issues
        report = {
            "node": "audio", "mode": "solo", "pack": str(pack.resolve()),
            "ok": ok, "verdict": "pass" if ok else "fail",
            "accuracy": round(acc, 4), "acc_min": AUDIO_ACC_MIN,
            "transcript": raw.get("transcript", ""),
            "audio": {k: raw.get(k) for k in ("voice", "mixing", "bgm_sfx")},
            "subtitle_audio_issues": sub_issues, "issues": raw.get("issues") or [],
        }
    else:
        report = dict(raw)
        report["node"] = node
        report["mode"] = "solo"
        report["pack"] = str(pack.resolve())
        _derive_verdict(report)
        _validate_citations(report)
        report["golden"] = manifest.get("golden")
    suffix = "-paired" if mode == "paired" else ""
    out = pack / f"judge-report-{node}{suffix}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


# ——————————————————————————— 两路合并 ———————————————————————————

def merge(pack: Path, node: str, paired_f: Path, solo_a_f: Path, solo_b_f: Path) -> dict:
    """配对 + 单臂两路合并。方向相反 = 结论不稳，记"无定论"，禁止声称胜负。

    实测（2026-07-27 A/C 形态实验）：同一批 hero frame，T1 配对判 C 大胜、单臂判 A 微胜——
    对照效应本身强度不稳（T2 几乎没拉开），所以"都用同一种模式"抵消不掉，只能显式判不稳。
    """
    pr, sa, sb = _load(paired_f), _load(solo_a_f), _load(solo_b_f)
    if pr.get("mode") != "paired":
        raise SystemExit(f"{paired_f} 不是配对报告（mode={pr.get('mode')!r}）")
    for f, r in ((solo_a_f, sa), (solo_b_f, sb)):
        if r.get("mode") != "solo":
            raise SystemExit(f"{f} 不是单臂报告（mode={r.get('mode')!r}）")

    pa, pb = pr["arms"]["arm_a"]["pack"], pr["arms"]["arm_b"]["pack"]
    if (sa.get("pack"), sb.get("pack")) != (pa, pb):
        raise SystemExit("单臂报告与配对臂对不上——第 2/3 个参数须依次是 arm_a / arm_b 的单臂报告：\n"
                         f"  arm_a = {pa}\n  arm_b = {pb}\n"
                         f"  给到的 = {sa.get('pack')} / {sb.get('pack')}")

    invalid = [n for n, r in (("paired", pr), ("solo_a", sa), ("solo_b", sb))
               if r.get("citations_valid") is False]
    d_paired = pr["delta_b_minus_a"]
    d_solo = (None if sa.get("overall") is None or sb.get("overall") is None
              else round(sb["overall"] - sa["overall"], 3))

    def strong(d):
        """该路有没有拉开（|Δ| ≥ 判定下限）——决定它算不算证据。"""
        return d is not None and abs(d) >= DECISIVE_MARGIN

    def raw_sign(d):
        """原始朝向（不过下限门）——只用来查两路是否指向相反，翻转必须先于强弱判定。"""
        return 0 if d is None or d == 0 else (1 if d > 0 else -1)

    contrast = None if d_solo is None else round(d_paired - d_solo, 3)
    flipped = (d_solo is not None and raw_sign(d_paired) and raw_sign(d_solo)
               and raw_sign(d_paired) != raw_sign(d_solo))
    reasons = []

    if invalid:
        conclusion, winner = "invalid", None
        reasons.append(f"引用校验未过的报告：{invalid}——整报作废重评")
    elif d_solo is None:
        conclusion, winner = "inconclusive", None
        reasons.append("单臂路缺分数，无法与配对路互证")
    elif flipped and (strong(d_paired) or strong(d_solo)):
        # 翻转优先于强弱：2026-07-27 T1 就是配对 Δ 大、单臂 Δ 小却反向，只能记无定论。
        conclusion, winner = "inconclusive", None
        reasons.append(f"两路方向相反（配对 Δ={d_paired:+}，单臂 Δ={d_solo:+}）——记无定论，不得声称胜负")
        if abs(contrast) >= CONTRAST_ALARM:
            reasons.append(f"对照效应 |Δ配对−Δ单臂|={abs(contrast)}，远超告警线 {CONTRAST_ALARM}")
    elif not strong(d_paired) and not strong(d_solo):
        conclusion, winner = "tie", None
        reasons.append(f"两路都没拉开（|Δ| < {DECISIVE_MARGIN}）——判平，不得声称胜负")
    else:
        lead = d_paired if strong(d_paired) else d_solo
        winner = "arm_b" if lead > 0 else "arm_a"
        if not (strong(d_paired) and strong(d_solo)):
            conclusion = "weak"
            reasons.append(f"只有一路拉开（配对 Δ={d_paired:+}，单臂 Δ={d_solo:+}）——只能写「倾向」，不得声称胜负")
        elif abs(contrast) >= CONTRAST_ALARM:
            conclusion = "weak"
            reasons.append(f"对照效应过大（|Δ配对−Δ单臂|={abs(contrast)} ≥ {CONTRAST_ALARM}）——方向虽同，强度不可信")
        else:
            conclusion = "decisive"
            reasons.append(f"两路同向且都拉开（配对 Δ={d_paired:+}，单臂 Δ={d_solo:+}）")

    margin = (None if winner is None or d_solo is None
              else round(min(abs(d_paired), abs(d_solo)), 3))
    report = {
        "node": node, "mode": "merged", "schema": "judge-merge@1",
        "arms": {a: {"label": ARM_LABEL[a], "pack": pr["arms"][a]["pack"],
                     "overall_paired": pr["arms"][a]["overall"],
                     "overall_solo": (sa if a == "arm_a" else sb).get("overall")}
                 for a in ("arm_a", "arm_b")},
        "delta_paired": d_paired, "delta_solo": d_solo, "contrast_effect": contrast,
        "thresholds": {"decisive_margin": DECISIVE_MARGIN, "contrast_alarm": CONTRAST_ALARM},
        "conclusion": conclusion,
        "winner": winner,
        "winner_pack": None if winner is None else pr["arms"][winner]["pack"],
        "conservative_margin": margin,
        "claim_allowed": conclusion == "decisive",
        "ratchet_action": "keep" if conclusion == "decisive" else "revert",
        "ratchet_rule": "只有 decisive 且胜方是新版才 keep；tie/weak/inconclusive 一律 revert（「没证明更好」≠「更好」）",
        "reasons": reasons,
        "sources": {"paired": str(Path(paired_f).resolve()),
                    "solo_arm_a": str(Path(solo_a_f).resolve()),
                    "solo_arm_b": str(Path(solo_b_f).resolve())},
    }
    out = pack / f"judge-merge-{node}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(
        description="G2 评委（去模型化）：出题/阅卷/合并三端，打分交 agent 派发的 subagent",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pack", help="证据包目录（build_evidence_pack.py 产出）")
    ap.add_argument("--node", required=True, choices=["hero_frames", "final", "audio"])
    ap.add_argument("--mode", default="solo", choices=["solo", "paired"],
                    help="solo=单臂绝对判断（缺省，三个门都是绝对判断）；paired=配对相对判断，须配 --vs")
    ap.add_argument("--vs", metavar="PACK_B", help="配对模式的另一臂证据包")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--task", action="store_true", help="出题：打印隔离评审任务（交 subagent）")
    g.add_argument("--finalize", metavar="SCORES_JSON",
                   help="阅卷：subagent 打分 JSON → 判词 + 校验")
    g.add_argument("--merge", nargs=3, metavar=("PAIRED_REPORT", "SOLO_ARM_A", "SOLO_ARM_B"),
                   help="合并两路：配对报告 + 依次对应 arm_a / arm_b 的单臂报告")
    args = ap.parse_args()
    pack = Path(args.pack)

    # 模式与参数的一致性（防"随手选了哪种"重演）
    if args.mode == "paired" and not args.vs and args.task:
        ap.error("--mode paired 必须给 --vs <另一个证据包>")
    if args.vs and args.mode != "paired":
        ap.error("--vs 只在 --mode paired 下有意义（相对判断走配对，绝对判断走单臂）")
    if args.mode == "paired" and args.node == "audio":
        ap.error("audio 门是绝对判断（转写准确率 / 混音下限），不支持配对")

    if args.task:
        sys.stdout.write(emit_task(pack, args.node, args.mode,
                                   Path(args.vs) if args.vs else None))
        return 0
    if args.merge:
        r = merge(pack, args.node, *(Path(p) for p in args.merge))
        print(json.dumps({"ok": True, "node": args.node,
                          "report": str(pack / f"judge-merge-{args.node}.json"),
                          "conclusion": r["conclusion"], "winner_pack": r["winner_pack"],
                          "claim_allowed": r["claim_allowed"],
                          "ratchet_action": r["ratchet_action"],
                          "reasons": r["reasons"]}, ensure_ascii=False, indent=2))
        return 0
    report = finalize(pack, args.node, Path(args.finalize), args.mode)
    suffix = "-paired" if args.mode == "paired" else ""
    print(json.dumps({"ok": True, "node": args.node, "mode": args.mode,
                      "report": str(pack / f"judge-report-{args.node}{suffix}.json"),
                      "verdict": report.get("verdict"), "overall": report.get("overall"),
                      "winner_pack": report.get("winner_pack"),
                      "delta_b_minus_a": report.get("delta_b_minus_a"),
                      "accuracy": report.get("accuracy"),
                      "citations_valid": report.get("citations_valid")},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
