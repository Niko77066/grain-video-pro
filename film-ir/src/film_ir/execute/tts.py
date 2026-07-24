"""TTS adapter（去模型化 · 2026-07-24）：旁白走 **MiniMax speech-2.8-hd 固定音色**——
不再走火山 seed-audio（seed-audio 分节音色漂移，长片单 pass MiniMax 根治，见 tts-longform-minimax）。

与其它 provider 一致：plan() 把旁白输入译成 MiniMax 请求方言（无 key），run() 委托宿主——
宿主的 MiniMax TTS 工具执行后 ir_patch 回填 audio.voiceover.file + gen.file（key 跟项目走、不自持）。
**逐字 timeline 由 forced-alignment 另建**（剧本 1:1 强制对齐，references/forced-alignment.md），
不拿 TTS 自报字幕充当（whisper/subtitle 比例映射会漂）。
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from ..errors import IRError, RULE_ZERO
from ..models import FilmIR
from .base import Adapter, Plan, RunResult, Target

MODEL = "speech-2.8-hd"       # MiniMax 固定音色、长片单 pass
MAX_PROMPT_CHARS = 10000      # 单次上限预警阈（远宽于 seed-audio 的 3000/120s）


def _next_dec_id(ir: FilmIR) -> str:
    mx = 0
    for d in ir.ledger.decisions:
        m = re.fullmatch(r"d(\d+)", str(d.id))
        if m:
            mx = max(mx, int(m.group(1)))
    return f"d{mx + 1:02d}"


class TTSAdapter(Adapter):
    name = "tts"
    mode = "audio"

    def _read_text_prompt(self, ir: FilmIR, project_dir: Path) -> str:
        vo = ir.audio.voiceover
        if vo is None or not vo.text_prompt_file:
            raise IRError(
                RULE_ZERO,
                "audio.voiceover.text_prompt_file 缺失——IR 里没有旁白输入就不许调 TTS",
                path="audio.voiceover.text_prompt_file",
                hint="先把〈声音档描述〉+「朗读：」+全文写入文件并回填该字段")
        f = project_dir / vo.text_prompt_file
        if not f.is_file():
            raise IRError(RULE_ZERO, f"text_prompt_file 不存在: {f}",
                          path="audio.voiceover.text_prompt_file")
        return f.read_text(encoding="utf-8").strip()

    def plan(self, ir: FilmIR, target: Target, project_dir: Path) -> Plan:
        text = self._read_text_prompt(ir, project_dir)
        vo = ir.audio.voiceover
        warnings = []
        if len(text) > MAX_PROMPT_CHARS:
            warnings.append(f"text_prompt {len(text)} 字符，超 MiniMax 单次上限 {MAX_PROMPT_CHARS}——需分节")
        req = {"model": MODEL, "text": text,
               "voice_profile": vo.voice_profile,   # 项目固定音色（宿主解析成 MiniMax voice_id）
               "audio_config": {"format": "mp3", "sample_rate": 48000},
               "note": "长片单 pass 固定音色；timeline 由 forced-alignment 另建，不用 TTS 自报字幕"}
        return Plan(target=target.raw, provider=self.name,
                    description=f"旁白 TTS（MiniMax {MODEL}，{len(text)} 字符）→ 交宿主生成",
                    requests=[req], warnings=warnings)

    def run(self, ir: FilmIR, target: Target, plan: Plan, project_dir: Path) -> RunResult:
        (project_dir / "audio").mkdir(exist_ok=True)
        req_rel = "audio/voiceover.request.json"
        (project_dir / req_rel).write_text(
            json.dumps(plan.requests, ensure_ascii=False, indent=2), encoding="utf-8")
        today = time.strftime("%Y-%m-%d")
        gen = {"model": f"{MODEL} (delegated)", "params": plan.requests[0],
               "request_file": req_rel, "date": today,
               "note": "去模型化委托：宿主 MiniMax TTS 执行后 ir_patch 回填 audio.voiceover.file + "
                       "gen.file/duration_actual_s；随后 forced-alignment 建 audio.timeline（剧本 1:1）"}
        ops = [
            {"op": "set", "path": "audio.voiceover.status", "value": "awaiting_generation"},
            {"op": "set", "path": "audio.voiceover.gen", "value": gen},
            {"op": "append", "path": "ledger.decisions", "value": {
                "id": _next_dec_id(ir), "date": today, "stage": str(ir.meta.status),
                "decision": "旁白 TTS 请求已译好（MiniMax speech-2.8-hd）、交宿主执行",
                "why": "去模型化：key 跟项目走（宿主 MiniMax 工具注入），外挂不持 provider key"}},
        ]
        return RunResult(ops=ops, artifacts=[str(project_dir / req_rel)],
                         summary=f"MiniMax TTS 请求已备好交宿主执行：{req_rel}")
