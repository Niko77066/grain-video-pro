"""Film IR schema m1-v1（pydantic）。

收编原则（DESIGN.md §2）：核心字段强类型；gen / qc / source.params 允许 extra——
引擎方言字段是宝贵留痕，schema 收编常见键但不没收长尾。
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SCHEMA_VERSION = "m1-v1"

# 十阶段 + 终态（/produce SOP §3）
STAGES = ("brief", "research", "blueprint", "script", "audio", "storyboard",
          "anchors", "motion", "compose", "review", "deliver")
MetaStatus = Literal["brief", "research", "blueprint", "script", "audio", "storyboard",
                     "anchors", "motion", "compose", "review", "deliver", "delivered"]

Provider = Literal["hyperframes", "seedance", "image_motion", "avatar", "footage", "tts",
                   "collage_broll"]  # 拼贴 b-roll：静帧(GPT-Image)→Seedance 首尾帧 assemble 混合通路（uk-argentina / openai-78m 方言实证）

ShotStatus = Literal["planned", "sourced", "generated", "qc_pass", "qc_fail", "redo"]
AnchorStatus = Literal["planned", "generated", "acquired", "selected", "locked", "rejected"]
SeamType = Literal["tail_relay", "hard_cut", "transition", "none"]  # A / B / C 接缝契约


class IRModel(BaseModel):
    model_config = ConfigDict(extra="allow", validate_assignment=True)


def _check_interval(t: tuple[float, float]) -> tuple[float, float]:
    if t[1] <= t[0]:
        raise ValueError(f"区间终点必须大于起点: {t}")
    return t


# ---------------------------------------------------------------- meta

class Commitment(IRModel):
    type: str = ""            # 承诺词汇仍在 M0 演化中，暂不闭集
    duration_s: float = 60
    tolerance_pct: float = 5


class Budget(IRModel):
    cap_usd: Optional[float] = None   # null = 未设上限（只记账不熔断）
    spent_usd: float = 0


class Meta(IRModel):
    title: str
    title_display: Optional[str] = None
    slug: Optional[str] = None
    format: str = ""          # 片型
    style_pack: str = ""
    commitment: Commitment = Field(default_factory=Commitment)
    aspect: str = "16:9"
    audience: Optional[str] = None
    budget: Budget = Field(default_factory=Budget)
    pipeline_version: str = "m0-v1"      # 生产工艺版本
    schema_version: str = SCHEMA_VERSION  # 数据格式版本（与工艺版本分离）
    status: MetaStatus = "brief"
    # 风格合同带宽内调整：{"<合同dotted路径>": 数值}，经 ir patch 写入（自动留痕）。
    # 越出 styles/<pack>/contract.json 的 amend 带宽 = 违约（style.contract.amend 门）。
    contract_amendments: dict = Field(default_factory=dict)
    # 用户把哪些门委托给 EP 代决（端到端授权的显式留痕，防"EP 代决"被写成"用户已批准"）
    approval_policy: Optional[dict] = None


# ---------------------------------------------------------------- 生成留痕

class GenRecord(IRModel):
    """统一生成留痕块——铁律 2 的数据形状。extra 允许（引擎方言）。"""
    model: str = ""
    prompt: Optional[str] = None
    prompt_file: Optional[str] = None
    seed: Optional[int] = None
    params: dict = Field(default_factory=dict)
    refs: list[str] = Field(default_factory=list)
    request_id: Optional[str] = None
    task_id: Optional[str] = None
    date: Optional[str] = None
    cost_usd: Optional[float] = None
    wallclock_s: Optional[float] = None
    duration_actual_s: Optional[float] = None
    file: Optional[str] = None
    note: Optional[str] = None


# ---------------------------------------------------------------- audio

class TimelineSection(IRModel):
    id: str
    t: tuple[float, float]
    text: Optional[str] = None

    _iv = field_validator("t")(_check_interval)


class AudioTimeline(IRModel):
    file: Optional[str] = None
    source: Optional[str] = None       # 如 "seed-audio subtitle" / "whisperx"
    duration_s: float
    sections: list[TimelineSection] = Field(default_factory=list)
    words: Optional[list] = None
    words_file: Optional[str] = None
    words_count: Optional[int] = None


class Voiceover(IRModel):
    file: Optional[str] = None
    status: Optional[str] = None
    text_prompt_file: Optional[str] = None  # TTS adapter 的输入指针
    voice_profile: Optional[str] = None
    gen: Optional[GenRecord] = None


class Music(IRModel):
    file: Optional[str] = None
    role: Optional[str] = None
    type: Optional[str] = None
    mix: Optional[str] = None
    gen: Optional[GenRecord] = None


class Audio(IRModel):
    voiceover: Optional[Voiceover] = None
    music: Optional[Music] = None
    timeline: Optional[AudioTimeline] = None


# ---------------------------------------------------------------- anchors

class AnchorCandidate(IRModel):
    file: str


class Anchor(IRModel):
    id: str
    type: str                 # 开放词表：character_sheet/product/style_frame/keyframe/avatar_portrait/logo/prop/screen_capture…
    intent: Optional[str] = None
    status: AnchorStatus = "planned"
    file: Optional[str] = None
    cdn_url: Optional[str] = None
    aspect: Optional[str] = None
    used_by: list[str] = Field(default_factory=list)
    candidates: list[AnchorCandidate] = Field(default_factory=list)
    gen: Optional[GenRecord] = None
    note: Optional[str] = None


# ---------------------------------------------------------------- shots

class ShotSource(IRModel):
    provider: Provider
    template: Optional[str] = None
    params: dict = Field(default_factory=dict)


class ShotQC(IRModel):
    technical: Optional[str] = None
    semantic: Optional[str] = None


class Shot(IRModel):
    id: str
    t: tuple[float, float]
    voice_ref: Optional[str] = None
    intent: str
    framing: Optional[str] = None
    motion: Optional[str] = None
    source: ShotSource
    anchor_refs: list[str] = Field(default_factory=list)
    group_ref: Optional[str] = None
    static_class: bool = False           # 幻灯片风险口径
    candidates: Optional[int] = None
    status: ShotStatus = "planned"
    gen: Optional[GenRecord] = None
    qc: Optional[ShotQC] = None

    _iv = field_validator("t")(_check_interval)


class ShotGroup(IRModel):
    """Seedance 生成调度单元（≤15s、≤5 镜）+ 接缝契约。"""
    id: str
    shots: list[str]
    provider: str = "seedance"
    duration_s: Optional[float] = None
    duration_planned_s: Optional[float] = None
    seam_internal: Optional[str] = None
    seam_out: Optional[SeamType] = None
    seam_note: Optional[str] = None      # 人读的接缝意图（迁移时保留原文）
    note: Optional[str] = None


# ---------------------------------------------------------------- overlays / edit

class Overlay(IRModel):
    id: str
    type: str
    intent: Optional[str] = None
    text: Optional[str] = None
    shot_range: Optional[tuple[str, str]] = None   # [from_id, to_id] 连续区间
    shot_refs: Optional[list[str]] = None          # 非连续多镜头引用（与 shot_range 二选一）
    scope: Optional[str] = None                    # "global" = 全片层
    source: Optional[str] = None                   # provider 名
    status: Optional[str] = None
    note: Optional[str] = None


class Edit(IRModel):
    transitions: list[str] = Field(default_factory=list)
    lut: Optional[str] = None
    grain: Optional[str] = None
    loudness_lufs: float = -14
    ducking: Optional[dict] = None


# ---------------------------------------------------------------- ledger

# ledger 条目是历史人写留痕：只强制 id + date，其余可选——过度必填会逼出假数据。
# 新增条目的完整性由写入方（API 自动追加、SOP 纪律）保证，不由 schema 追认历史。

class Decision(IRModel):
    id: str
    date: str
    decision: str
    stage: Optional[str] = None
    why: Optional[str] = None
    supersedes: Optional[str] = None


class Cost(IRModel):
    id: str
    date: str
    stage: Optional[str] = None
    item: Optional[str] = None
    model: Optional[str] = None
    request_id: Optional[str] = None
    cost_usd: Optional[float] = None
    note: Optional[str] = None


class GateRecord(IRModel):
    id: str
    date: str
    stage: Optional[str] = None
    check: Optional[str] = None
    result: Optional[str] = None   # 自由文本：pass / pass_with_flag / 证据摘要
    evidence: Optional[str] = None


class Ledger(IRModel):
    decisions: list[Decision] = Field(default_factory=list)
    costs: list[Cost] = Field(default_factory=list)
    gates: list[GateRecord] = Field(default_factory=list)


# ---------------------------------------------------------------- 根

class FilmIR(IRModel):
    meta: Meta
    audio: Audio = Field(default_factory=Audio)
    anchors: list[Anchor] = Field(default_factory=list)
    shot_groups: list[ShotGroup] = Field(default_factory=list)
    shots: list[Shot] = Field(default_factory=list)
    overlays: list[Overlay] = Field(default_factory=list)
    edit: Edit = Field(default_factory=Edit)
    ledger: Ledger = Field(default_factory=Ledger)

    @model_validator(mode="after")
    def _unique_ids(self) -> "FilmIR":
        for name in ("anchors", "shot_groups", "shots", "overlays"):
            items = getattr(self, name)
            seen: set[str] = set()
            for it in items:
                if it.id in seen:
                    raise ValueError(f"{name} 内 id 重复: {it.id}")
                seen.add(it.id)
        for name in ("decisions", "costs", "gates"):
            items = getattr(self.ledger, name)
            seen = set()
            for it in items:
                if it.id in seen:
                    raise ValueError(f"ledger.{name} 内 id 重复: {it.id}")
                seen.add(it.id)
        return self

    def dump(self) -> dict:
        return self.model_dump(mode="json", exclude_none=True)
