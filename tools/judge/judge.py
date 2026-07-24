#!/usr/bin/env python3
"""G2 评委（去模型化 · 2026-07-24）：本工具只做确定性两端——**出题**（组织证据 + rubric）
与**阅卷**（规则派生判词 + 引用校验）。**打分由 agent 自己派发的隔离 subagent 用宿主 harness
的模型完成**，本工具不含任何模型 / 网关 / 凭据——评委的"眼睛"是宿主的模型，不是焊死的某个 API。

流程（produce SOP ③b / ⑨ 调用）：
  1) build_evidence_pack.py <project>                       # 证据包：frames/contact-sheet/golden/L0/manifest/音轨
  2) judge.py <pack> --node {hero_frames|final|audio} --task
       打印隔离评审任务（rubric + 证据文件绝对路径清单 + 镜头事实 + 引用纪律 + 输出 JSON schema），
       并落 <pack>/judge-task-<node>.md
  3) agent 派发隔离 subagent：把任务 + 证据文件喂进去（subagent 看不到创作上下文），收回 JSON 打分
  4) judge.py <pack> --node ... --finalize scores.json      # 规则派生判词 + 引用校验（视觉）/
       字符重合率（音频）→ <pack>/judge-report-<node>.json

隔离纪律：subagent 只看证据（frames/video/audio + 镜头事实 manifest，零创作理由）；扣分必须引用
镜头 ID/时间码，否则整报作废重评（无锚点自评 ~46%，styles/_iteration.md）。verdict 由规则派生——
不信模型自报（存 verdict_model 作校准语料）。评委与导演不同模型家族是特性（同族自评共享盲区）——
由宿主在派发 subagent 时保证；本工具不选模型。
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

VERDICT_RULE = "overall<3.5 或命中任一反模式 → fail（模型自报仅存 verdict_model）"
AUDIO_ACC_MIN = 0.95

RUBRIC = """你是独立评委，只依据给到的证据评审，禁止臆测创作过程。
九维评分（各 1–5 分，可 0.5 步进）：D1 叙事结构 D2 信息密度与出处感 D3 节奏呼吸
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
无引用的判断无效（D9 网感可锚定标题/钩子/推荐流语境）。只输出 JSON：
{"scores": {"D1": x, ..., "D9": x}, "overall": x, "antipatterns": [".."],
 "notes": {"D1": "..引用..", ...}, "verdict": "pass|fail", "one_line": ".."}"""

HERO_RUBRIC = """你是独立评委，评 hero-frame 品味门（分镜铺开前）。证据：本片 3 张 hero frame
+ 该风格包 Golden 基准 contact sheet。判断每张 hero frame 是否达到 Golden 的视觉下限
（风格贴合 / 版式克制——克制≠稀疏，元素孤立漂浮、留白无信息承载 = 扣分 / 质感缝合），
并逐条核风格包反模式。未达下限 = 打回，禁止铺开全片生产。逐帧引用 frame 序号。只输出 JSON：
{"per_frame": [{"frame": "..", "pass": bool, "reason": "..引用.."}],
 "antipatterns": [".."], "template_test": "..", "verdict": "pass|fail",
 "notes": {"overall": "..引用.."}, "must_fix": ["..引用.."]}"""

AUDIO_QC_PROMPT = """你在做视频的音频质检与字幕/音频校对。给你一段音频（成片音轨）和它应当念出的
脚本分节文本。请**只依据你真实听到的声音**输出 JSON，禁止照抄脚本充当转写：
{"transcript": "你逐字听到的完整中文转写（听不清的词写□，不要用脚本补全）",
 "voice": "人声性别/音色/语速/情绪的客观描述",
 "mixing": "混音观感：人声清晰度、有无爆音/齿音/忽大忽小、响度是否稳",
 "bgm_sfx": "是否存在背景音乐(BGM)与音效(SFX)；有就描述，没有就明确说无",
 "subtitle_audio_issues": ["脚本里有但没听到、或听到与脚本不一致、或多念漏念的逐条列出；无则空数组"],
 "issues": ["其它音频缺陷逐条；无则空数组"]}"""

_CITE = re.compile(r"s\d{1,3}[a-z_]*|\d{1,2}:\d{2}|\d{1,3}(?:\.\d+)?s")
_HOLISTIC = re.compile(r"钩子|标题|开场|推荐页|推荐流|封面")


def _derive_verdict(report: dict) -> None:
    """verdict 规则推导：模型对自己的判决偏宽（实测 3.2 分 + 4 条反模式仍自报 pass）。"""
    report["verdict_model"] = report.get("verdict")
    overall = report.get("overall")
    if not isinstance(overall, (int, float)):
        vals = [v for v in (report.get("scores") or {}).values() if isinstance(v, (int, float))]
        overall = (sum(vals) / len(vals)) if vals else None
        report["overall"] = round(overall, 3) if isinstance(overall, (int, float)) else None
    fail = (isinstance(overall, (int, float)) and overall < 3.5) or bool(report.get("antipatterns"))
    report["verdict"] = "fail" if fail else "pass"
    report["verdict_rule"] = VERDICT_RULE


def _validate_citations(report: dict) -> None:
    """无镜头 ID/时间码引用的判断标 invalid（隔离评委核心纪律）。"""
    invalid = []
    for k, v in (report.get("notes") or {}).items():
        if not isinstance(v, str) or not v.strip():
            continue
        if _CITE.search(v) or (k in ("D9", "overall") and _HOLISTIC.search(v)):
            continue
        invalid.append(f"notes.{k}")
    for i, f in enumerate(report.get("per_frame") or []):
        r = (f or {}).get("reason", "")
        if isinstance(r, str) and r.strip() and not _CITE.search(r):
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
    return json.loads(p.read_text(encoding="utf-8"))


def emit_task(pack: Path, node: str) -> str:
    """出题：组织证据文件清单 + rubric + 镜头事实 → 隔离 subagent 的评审任务。"""
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
        add("golden-contact-sheet.jpg", "Golden 基准 contact sheet")
    else:  # final
        prompt = RUBRIC
        gm = manifest.get("grid_time_map", {}).get("rule", "")
        add("contact-sheet.jpg", f"本片 contact sheet（{gm}）")
        add("contact-sheet-offset.jpg", "本片 contact sheet 半步错位版")
        add("golden-contact-sheet.jpg", "Golden 基准 contact sheet（并排对照）")
        for f in sorted((pack / "frames").glob("*.jpg")):
            ev.append(f"- 逐镜帧: {f.resolve()}")

    facts = json.dumps(manifest.get("shots", []), ensure_ascii=False)
    amends = json.dumps(manifest.get("contract_amendments") or {}, ensure_ascii=False)
    task = f"""# 隔离评审任务 · node={node}

> 你是 Kuleshov 独立评委（G2），与创作者物理隔离：只看下列证据，不接受、不索取任何创作过程解释。

## 评分/评审标准
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
    (pack / f"judge-task-{node}.md").write_text(task, encoding="utf-8")
    return task


def finalize(pack: Path, node: str, scores_file: Path) -> dict:
    """阅卷：读 subagent 打分 JSON → 规则派生判词 + 引用校验（视觉）/ 字符重合率（音频）。"""
    manifest = _load(pack / "manifest.json")
    raw = _load(scores_file)
    if node == "audio":
        secs = manifest.get("sections") or []
        script_full = "".join(s.get("text", "") for s in secs)
        acc = _char_overlap(script_full, raw.get("transcript", ""))
        sub_issues = raw.get("subtitle_audio_issues") or []
        ok = acc >= AUDIO_ACC_MIN and not sub_issues
        report = {
            "node": "audio", "ok": ok, "verdict": "pass" if ok else "fail",
            "accuracy": round(acc, 4), "acc_min": AUDIO_ACC_MIN,
            "transcript": raw.get("transcript", ""),
            "audio": {k: raw.get(k) for k in ("voice", "mixing", "bgm_sfx")},
            "subtitle_audio_issues": sub_issues, "issues": raw.get("issues") or [],
        }
    else:
        report = dict(raw)
        report["node"] = node
        _derive_verdict(report)
        _validate_citations(report)
        report["golden"] = manifest.get("golden")
    out = pack / f"judge-report-{node}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(
        description="G2 评委（去模型化）：出题/阅卷两端，打分交 agent 派发的 subagent",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pack", help="证据包目录（build_evidence_pack.py 产出）")
    ap.add_argument("--node", required=True, choices=["hero_frames", "final", "audio"])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--task", action="store_true", help="出题：打印隔离评审任务（交 subagent）")
    g.add_argument("--finalize", metavar="SCORES_JSON",
                   help="阅卷：subagent 打分 JSON → 判词 + 校验")
    args = ap.parse_args()
    pack = Path(args.pack)
    if args.task:
        sys.stdout.write(emit_task(pack, args.node))
        return 0
    report = finalize(pack, args.node, Path(args.finalize))
    print(json.dumps({"ok": True, "node": args.node,
                      "report": str(pack / f"judge-report-{args.node}.json"),
                      "verdict": report.get("verdict"), "overall": report.get("overall"),
                      "accuracy": report.get("accuracy"),
                      "citations_valid": report.get("citations_valid")},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
