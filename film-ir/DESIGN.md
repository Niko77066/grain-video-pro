# Film IR API · 设计文档（M1 第一刀）

> 状态：实施中。四个方向决策已与作者对齐（2026-07-16）：**Python / 库+CLI 先行 / 收编+迁移 / 四动词全量**。
> 上游依据：蓝图 v3.4 §4（Film IR）、§9（G1 门）、§12（M1 范围）；`/produce` SKILL.md §2（film.json 契约）；三部成片 film.json（事实语料）。

## 0. 定位与消费者

Film IR API 是 **L3 契约层的写入口 + L4 工具层的执行入口**：`film.json` 从"手写 JSON 的约定"升级为"经 schema 校验、门禁强制的受管状态"。

消费者演进路径：

1. **现在（M1）**：Claude Code EP（`/produce` 管线）通过 CLI 调用，替代手写 JSON；
2. **将来（合并 grain）**：grain 是 TypeScript 项目，pro 视频链路的 agent 将在任务中随时调用本 API。因此**集成边界是 CLI 的结构化 JSON stdout**（语言无关），而非 Python import；届时按需再包 HTTP / MCP 皮——四动词的签名从现在起就按"可注册为 agent tool"的标准设计（参数可 JSON-schema 化、错误结构化可行动）。

Pull-based 纪律（蓝图 §12）：HTTP 服务、MCP server、DAG 执行引擎都**不在**第一刀，各自等触发条件。

## 1. 四动词 API 面（蓝图 §4.2 原样落地）

| 动词 | 签名 | 语义 |
|---|---|---|
| `ir_read` | `ir_read(project, selector) → json` | 按选择器读 IR 任意切片，只读，无副作用 |
| `ir_patch` | `ir_patch(project, ops[], revision?) → PatchResult` | 原子补丁组：全组成功或全组不写；写前全量 schema 校验；门控字段无 revision 拒改；ledger 只许 append |
| `ir_validate` | `ir_validate(project, stage?) → Report` | 跑 G1 门套件（可按 stage 选子集），输出违规清单带证据，**不改文件** |
| `ir_execute` | `ir_execute(project, targets[], dry_run?) → ExecResult` | Rule Zero 强制：target 不在 IR 里即拒绝；分发到 provider adapter；产物与留痕自动回填 |

辅助动词（工程需要，不属 IR 语义）：`ir_new`（从模板建片）、`ir_migrate`（旧片收编）。

### 1.1 选择器语法（刻意小）

```
meta.status                     # 点路径
shots[s03_top1_card].gen        # id 寻址（id-keyed 数组一律用 id，不用下标）
shots[*].status                 # 投影
shots[?status=qc_fail]          # 等值过滤
```

只支持：点路径、`[id]`、`[*]`、`[?field=value]`。不做通用 JSONPath——够 EP 和 grain agent 用，复杂查询让调用方拿全量 JSON 自己算。

### 1.2 补丁操作（不用 RFC 6902，理由：id 寻址）

```json
{ "op": "set",    "path": "shots[s03].status", "value": "redo" }
{ "op": "append", "path": "ledger.decisions",  "value": { ... } }
{ "op": "insert", "path": "shots", "value": { ... }, "after": "s02" }
{ "op": "remove", "path": "shots[s09]" }
```

JSON-Patch 用数组下标寻址，镜头一增删所有下标漂移——IR 的设计规则"一切引用靠 ID"（铁律）必须贯穿到补丁层。

### 1.3 门控字段与 revision 流程（蓝图 §4.2：改门控字段要走正式修订）

门控字段：`meta.commitment.*`、`meta.budget.cap_usd`、`meta.format`、`meta.style_pack`、`meta.aspect`、`meta.pipeline_version`；以及 **`audio.timeline`（当 `shots[]` 非空时）**——音频先行铁律的写入层化身：分镜落地后时钟不许静默改。

改动这些字段的 patch 必须带 `revision: {reason, supersedes?}`；API 自动在 `ledger.decisions` 追加一条修订记录。无 revision → 结构化错误 `GATED_FIELD`，附提示"走 revision 或另立项目"。

### 1.4 ledger append-only

`ledger.decisions / costs / gates` 三个数组只接受 `append`；`set`/`remove` 指向已有条目一律拒绝（错误码 `LEDGER_IMMUTABLE`）。修正历史 = 追加新条目带 `supersedes: "<旧id>"`。留痕不可事后补（铁律 2）从此由写入层保证。

### 1.5 错误模型

一切错误结构化：`{ code, message, path?, hint? }`，CLI 以 JSON 输出到 stderr。退出码：`0` 成功；`1` 校验/门禁不过（有 violations）；`2` 用法/寻址错误；`3` 引擎执行失败。code 稳定可枚举（grain 侧按 code 分支，不 parse message）。

## 2. Schema `m1-v1`

`meta.schema_version: "m1-v1"` 为新增字段（与 `pipeline_version` 分离：前者是**数据格式**版本，后者是**生产工艺**版本）。骨架与 `/produce` SKILL.md §2 完全一致：`meta / audio / anchors[] / shot_groups[] / shots[] / overlays[] / edit / ledger`。

宽容策略：**核心字段强类型，`gen`、`qc`、`source.params` 允许 extra**——生成引擎的方言字段（`task_id`、`request_id`、`payload_file`…）是宝贵留痕，schema 收编常见键但不没收长尾。

### 2.1 GenRecord（统一生成留痕块——收编三片方言的核心动作）

三部成片里 `gen` 的嵌套方式三片三样（800v 平铺、estee/samsung 嵌套且字段名不同）。m1-v1 统一为：

```
gen: {
  model: str                     # 必填
  prompt?: str | prompt_file?: str    # 完整 prompt 或其文件指针（二选一，长 prompt 落盘）
  seed?: int
  params?: {}                    # resolution/ratio/quality/size… 引擎方言，extra 允许
  refs?: [str]                   # 锚点/参考的 IR id
  request_id?: str               # 成本反查凭据（Seedance x-oneapi-request-id / TTS 等）
  task_id?: str
  date?: str                     # ISO
  cost_usd?: float
  wallclock_s?: float
  duration_actual_s?: float      # 烘焙型必填（ffprobe 实测）
  file?: str                     # 产物路径（项目目录相对）
  note?: str
  …extra 允许
}
```

### 2.2 shots[]

```
{ id, t: [start_s, end_s], voice_ref?, intent, framing?, motion?,
  source: { provider: hyperframes|seedance|image_motion|avatar|footage, template?, params? },
  anchor_refs: [], group_ref?,       # 所属镜头组（Seedance 通路）
  static_class: bool,                # 幻灯片风险口径（HTML/图片动效=true）
  candidates?: int,
  status: planned → generated → qc_pass | qc_fail → redo,
  gen: GenRecord|null, qc: {technical?, semantic?, …}|null }
```

状态机合法转移由 patch 层校验（`qc_pass` 不许直接回 `planned` 之类）；`redo` 可从任意已生成态进入（定点重做入口）。

### 2.3 其余各段（相对三片现状的收编点）

- **anchors[]**：`need`（samsung）统一为 `intent`；`picked_from`（800v）并入 `gen.note`；`candidates[]`、`cdn_url`、`used_by[]` 收编为正式字段；status：`planned → generated → picked / rejected`。
- **audio.voiceover**：强制 `gen: GenRecord` 嵌套（800v 的平铺字段迁移进去）；`audio.timeline.sections[].t` 为秒。
- **shot_groups[]**：`{ id, shots: [shot_id], duration_s, seam_out: hard_cut|tail_relay|transition|none }`（A/B/C 接缝契约的机读名）。
- **overlays[]**：`shot_range: [from_id, to_id]`，引用完整性入 G1。
- **edit**：现状字段照收；`transitions` 长度 ≤ 4 是 G1 门。
- **meta**：收编 `title_display?`、`slug?`、`audience?`；`status` 枚举 = 十阶段名 + `delivered`。

### 2.4 迁移（收编三部成片）

`ir_migrate` 识别无 `schema_version` 的旧片 → 按方言规则归一 → 输出 dry-run diff，`--write` 才落盘。**本分支只对三部片做只读验证（fixtures 化）**，真实项目文件的实迁在合并回 main 时执行——避免与 M0 主线（用户仍在跑）产生合并冲突。

## 3. G1 门套件（`ir_validate`）

每条门：`{ gate, severity: error|warn, path, message, evidence }`。`error` = G1 硬门（蓝图口径：确定性、零 LLM）；`warn` = 语义自查项（M0 靠人眼/自评，暂不能代码判定的降为提示）。

| 门 | 级别 | 内容 |
|---|---|---|
| `schema` | error | 全量 pydantic 校验 |
| `refs` | error | anchor_refs / voice_ref / group_ref / overlay shot_range 全部可解析；id 全局唯一 |
| `timeline.coverage` | error | 镜头区间无缝隙、无重叠、首尾对齐 `audio.timeline.duration_s`（VO 片） |
| `timeline.commitment` | error | 音频总长在承诺 ± tolerance 内 |
| `groups.arithmetic` | error | 每个 seedance 镜头恰属一组；组时长 ≤ 15s、≤ 5 镜；各组之和 = 承诺 ± 公差（蓝图：分组算术不赌模型细心） |
| `slides.risk` | error | static_class 连续 > 2 镜；静态占比违反片型承诺 |
| `edit.transitions` | error | 转场词汇 > 4 种 |
| `status.machine` | error | 阶段/镜头状态取值与转移合法 |
| `visual.change` | warn | > 10s 无镜头边界（8–10s 视觉变化规则的可码判部分） |
| `framing.repeat` | warn | 连续同 framing > 2 镜 |
| `intent.motion` | warn | seedance 镜头缺 `motion`（运镜词）——"每镜一个主动作+运镜"的可码判部分 |

按 stage 触发：`ir_validate --stage storyboard` 只跑该阶段该过的门（分镜的八项自查里可码判的全在上表）。

## 4. `ir_execute` 与 adapter 契约

```
Adapter：
  provider 名 + 能力声明（烘焙型/声明型）
  plan(ir, target)   → { requests[], est_cost, warnings }   # dry-run 可展示
  run(plan)          → { artifacts[], gen: GenRecord }       # 真花钱
  writeback          → gen 回填 + ledger.costs 追加 + status 转移（由框架统一做，adapter 不碰文件）
```

- **Rule Zero 写入层强制**：target（`shots.s03` / `shot_groups.g01` / `audio.voiceover` / `anchors.a01`）在 IR 里查无条目、或 `source.provider` 未路由 → 拒绝执行（`RULE_ZERO`）。
- **第一刀实现**：`tts`（seed-audio-1.0 全契约：payload 构建、Base64 落盘、subtitle→逐字 timeline、留痕回填）+ `hyperframes`（lint → 不过禁 render → `--docker` render 的包装）。`seedance` / `image_motion` / `avatar` 注册占位、返回 `NOT_IMPLEMENTED`（M2 接入，接口已就位）。
- 密钥走仓库根 `.env`（`VOLC_TTS_API_KEY` 等），adapter 只读 env，任何输出不回显 key。
- **禁静默降级（铁律 5）在执行层的形状**：adapter 失败即结构化报错返回，不自动换 provider、不自动改参数重试——重试与降级是调用方（EP/agent）带着人的裁决做的事。

## 5. 并发与写入安全

- 原子写：tmp 文件 + `os.replace`；
- 文件锁：`fcntl` 排他锁包住 read-modify-write（M1 的 cron 日更与交互操作可能并发同一项目）；
- 历史即 git：不做 .bak，一片一提交的纪律不变。

## 6. 包布局

```
film-ir/
  pyproject.toml            # 包名 kuleshov-film-ir，import 名 film_ir
  DESIGN.md                 # 本文
  src/film_ir/
    models.py               # pydantic m1-v1
    store.py                # 载入/原子写/锁
    selectors.py            # §1.1 语法
    patch.py                # §1.2–1.4
    gates/                  # §3，每门一函数，注册表聚合
    execute/                # §4，base + registry + tts + hyperframes + 占位
    migrate.py              # §2.4
    errors.py               # §1.5
    cli.py                  # kuleshov-ir 入口
  tests/                    # pytest；fixtures = 三部成片 film.json 快照
```

## 7. 刻意不做（本刀）

HTTP/MCP 皮；L1–L2 感知仪器与 L4 评委（M1 后半的"渲染后自审"另立）；DAG 调度；成本 estimate→reserve 预留（M1 只 reconcile 记账）；G2 评委门。每项都有蓝图里的触发条件，pull-based。

## 8. 真实片库校准记录（2026-07-16，三片只读迁移）

- **800v**：收编 15 处，G1 全绿（0 error / 0 warn）——生产最严谨的一部，门阈值与其现状吻合。
- **samsung**：收编 30 处；`timeline.coverage` 报 s06_dataflow 与 s06_avatar_analysis 重叠 6.4s——**不是数据错误，是数字人抠像叠 MG 的合成层**。当前 schema 假设 shots 严格时序，"镜头并行轨 / 合成关系"是真实存在的表达需求（蓝图 §12.4 IR 表达力张力的第一个实证）。**待作者裁决**：加 `track`/`composite_with` 字段，还是这类前景层归 overlays。samsung 另有转场 6 种 > 4 上限（当时用户裁决接受，属历史豁免）。
- **estee**：收编 58 处；抓到真实漂移——`shot_groups` 引用了两个已改名镜头（`s03a_1982_day` 等）、4 个 seedance 镜头 qc_pass 但缺 `gen.file`。**手写 JSON 必然漂移，这正是写入层校验的存在理由**。
- 三部片的实迁（--write）留到合并回 main 时执行，避免与 M0 主线冲突。

## 8.1 两条核心链路收编（2026-07-20，实迁已落盘）

M0 精简后仓库只剩两条核心链路，方言收编 + `--write` 实迁均已完成（回归 fixtures 各留只读副本）：

- **openai-78m-logs**（case-file 链路）：收编 35 处，门套件 **0 error** / 2 warn（两个 overlay 无定位）。新增 `collage_broll` provider（GPT-Image 静帧 → Seedance 首尾帧的混合通路，映射成 seedance 会被 groups.arithmetic 误伤）。发现真相源坏 JSON 一处（v3 交付时 next_action 改写残留，已修，commit b85af4c）——**手编 JSON 连语法正确都保证不了，直写拦截的又一实证**。
- **uk-argentina-feud**（pixel-chronicle 链路）：收编 46 处，门套件 35 error / 18 warn——全部是真实校准发现、非迁移缺陷，性质同 samsung 并行轨案例，**待作者裁决**三个 IR 表达力开放点：
  1. `voice_ref` 指向 `voiceover.sections`，但真实时间戳活在外部 `audio/timeline_fa.json`（forced-alignment 产物），`timeline.sections` 为空 → 25 处 refs error。裁决点：迁移时把外部对齐结果回填进 IR，还是 schema 承认"外部对齐文件"为一等引用。
  2. 章节闸门间 0.35s 缝隙 ×5 属有意设计（章节呼吸），`timeline.coverage` 按无缝假设报 error。裁决点：加 `gap_intent` 留痕，还是门放宽容差。
  3. 4 个独立 seedance 镜头不进组（当时无组语义需求）→ `groups.arithmetic` error。裁决点：单镜头是否要求自成单元素组。
  另：末镜止于 240.04s vs 音频 256.68s（差 16.64s，片尾 credits 段无镜头条目）——待核实是留痕缺失还是真实结构。
