# 风格包路由规程（三层路由 · 能力卡 · 兜底）

> 一句话原则：**按「要让观众如何理解这条内容」路由，而不是只按「这是什么内容」路由。**
>
> 机器实现：`tools/route-style.py`。受控词表：`routing-vocab.json`。回归考卷：`routing-cases.json`。
> 本文管的是路由**为什么这么判**；阈值与权重的真相源在代码与词表里，本文不复述数字。

## 0. 这次升级要修的东西

旧路由是**场景 → 包**的直连映射（「新闻播报 / 数据发布解读 → anchor-desk」写死在 `produce/SKILL.md` §1.3）。
场景这个粒度太粗：同样是「新闻」，突发快讯、政策数据解读、人物事件、机制复盘要的是四种完全不同的片。
包一多，这种映射会迅速失效——每加一个包就要重写一次分支，而且分支之间必然重叠。

新路由把决定权从「场景」挪到「理解任务」：**场景只负责缩小候选集，内容特征决定具体风格包。**

## 1. 三层输入

| 层 | 字段 | 作用 |
|---|---|---|
| ① 内容类型 | `content_type` | 缩小候选集。快讯 / 深度新闻 / 政策数据发布 / 知识科普 / 观点评论 / 案例复盘 / 人物故事 / 产品品牌 / 其它 |
| ② 表达目标 | `understanding_task`（第一路由键）、`tone` | **理解任务**是「观众此刻需要以哪种方式理解它」；`tone`（可信权威 / 强节奏 / 故事化 / 克制高级 / 轻松易懂 / 情绪张力）是打分修正项 |
| ③ 受众与素材条件 | `audience`、`material`、`aspect`、`duration_s`、`sensitivity` | 硬规则的主要来源：横竖屏、时长、有没有人物素材、依不依赖图示、敏感题材 |

**理解任务词表**（`routing-vocab.json` 是真相源）：

| 任务 | 观众心里的问题 |
|---|---|
| `verify_the_event` | 这件事到底发生了什么、证据在哪、和我有什么关系 |
| `explain_the_mechanism` | 这个现象／国家／行业，为什么会变成今天这样 |
| `read_the_official_number` | 官方刚发布的数字或政策，口径是什么、结论是什么 |
| `follow_a_person` | 这个人身上发生了什么、我为什么该在意 |
| `weigh_an_argument` | 这件事有几种说法，我该怎么想 |
| `learn_to_do` | 我该怎么动手做这件事 |
| `unknown` | 判不出来 |

`unknown` 是合法答案。**判不出来就填 `unknown`，不许猜一个填上**——填错比空着贵，见 §4 的一句话原则编码。

## 2. 能力卡（每个包一张，`styles/<pack>/capability.json`）

风格包不再靠名称或一段 prompt 描述自己，而是声明结构化能力。schema `style-capability@1` 的关键字段：

```jsonc
{
  "id": "case-file",
  "layer": "bundled",              // narrative_base | visual_skin | bundled，见 §6
  "status": "verified",            // verified | candidate | fallback
  "positioning": "事实核验型新闻解读",
  "one_liner": "让观众快速相信、看懂一件正在发生的事。",
  "signature": "带观众读证据——不是纸张，也不是红色",
  "narrative_skeleton": ["主张", "文件证据", "解释", "结论"],
  "understanding_task": { "primary": ["verify_the_event"], "secondary": ["read_the_official_number"] },
  "applicable_content": ["breaking_news", "deep_news", "..."],
  "audience": ["general", "professional"],
  "tone": ["authoritative", "urgent", "restrained_premium"],
  "pacing": "fast",
  "visual_language": ["文件精读", "同步高亮", "数字压在文件上", "..."],   // 描述性，不参与打分
  "hard_rules": {                  // ← 排除用。只放「配方本身不成立」的条件
    "requires_any": [["readable_evidence", "official_dataset"]],  // 每个子组内是「或」，组间是「且」
    "excluded_material": ["presenter_wanted"],
    "excluded_sensitivity": [],
    "why": "为什么这几条是硬的（写给人看，评审时按这条问）"
  },
  "native_format": {               // ← 画幅与时长在这里，是**适配成本**不是准入门槛
    "aspect": ["9:16"],
    "duration_s": [20, 150],
    "basis": "这一档是从哪几条实证片推出来的",
    "adaptation": {                // 偏离原生格式时，路由器把这几段原样打给 EP 当施工说明
      "aspect": "换画幅要改什么版式（安全区、分栏、字号基准、锚点重出）",
      "duration_shorter": "压短要砍哪些结构（点名砍哪个槽位，不是等比压缩）",
      "duration_longer": "拉长要加什么（加结构而不是拉长单镜），以及会带动哪条合同阈值"
    }
  },
  "material_requirements": {
    "signature": ["readable_evidence"],      // 签名素材：本包立身之本，权重最高的素材项
    "prefers": ["official_dataset", "..."],  // 加分素材
    "can_work_without": ["character_footage", "..."]
  },
  "avoid_when": ["profile_story", "tragedy"],  // 软扣分，不是禁用
  "avoid_why": "..."
}
```

四条纪律：

1. **词表外的标签一律报错**。`routing-vocab.json` 是受控词表，路由器遇到表外标签直接退出，不做模糊匹配——防止 agent 临时造词把路由变成又一个自然语言接口。新增标签 = 改词表 + 说明它对应什么判断。
2. **硬规则和软偏好分开写**。`hard_rules` 是「不满足就不是这个包」；`avoid_when` 是「能做但不该做」。把品味写进硬规则会让包变得谁都用不了，把硬约束写成偏好会让路由静默出错。
3. **每张卡的 `hard_rules.why` 必须回链 playbook 里的具体条款**。硬规则不是拍脑袋定的门槛，是配方本身的前提（比如像素纪事的实拍占比 ≈40% 是声部表的硬配方，素材没落实就必然做成全 MG 幻灯片）。
4. 🔴 **画幅和时长不许写进 `hard_rules`**（2026-07-27 用户拍板，路由器直接报错拦着）。它们是**动态的、按用户需求调整的**，属于 `native_format` + `adaptation`——见 §3b。`adaptation` 三条（`aspect` / `duration_shorter` / `duration_longer`）缺一条，能力卡就加载失败：路由器把这几段原样打给 EP 当施工说明，缺了等于静默降级。

没有能力卡的包，路由器**看不见**它，且 `--check` 直接失败。要么补卡，要么移进 `styles/_disabled/`。

## 3. 三段路由逻辑

```
A. 硬规则排除  →  B. 能力卡打分  →  C. 置信判定与兜底
```

**A. 硬规则排除。** 只排除「配方本身不成立」的：必需素材、冲突素材、敏感题材。被排除的包连同**具体理由**一起输出——不静默丢弃，看结果的人要能判断「是这个包不合适，还是我的输入填错了」。

**B. 能力卡打分。** 权重顺序（数值在 `route-style.py` 顶部）：

```
理解任务·主位  ≫  理解任务·次位  >  内容类型  >  签名素材  >  语气 / 加分素材 / 受众 / 节奏
avoid_when 命中：大额扣分
```

理解任务的权重压过其它所有单项之和的一半以上——这是「按理解方式路由」的机器编码，不是调参偏好。

**B2（3b）. 格式适配成本，不是准入门槛。**（2026-07-27 用户拍板：「不要在视频时长和竖屏、横屏上卡死，这种东西应该是动态的，根据用户需求来调整」）

每个包声明 `native_format`——**它实证过的那一档画幅与时长**，不是它唯一能做的那一档。本片要的格式偏离原生时：

| 偏离 | 代价 | 附带产出 |
|---|---|---|
| 换画幅 | 小额扣分 | `adaptation.aspect`：换画幅要改哪些版式 |
| 时长越出带宽、但在 1.5× / 0.66× 之内 | 小额扣分（`degree: near`，收放章节） | `adaptation.duration_shorter` / `_longer` |
| 越得更远 | 双倍扣分（`degree: far`，叙事骨架要重排） | 同上 |

三条配套规则：

1. **不排除任何包。** 竖屏的播报题、横屏的案卷题、60 秒的机制解释题，照样能路由到对应的专用包，只是分数低一档。
2. **命中适配 → 置信封顶 `medium`。** 适配是要动手改的，不是免费的，所以不给 `high`；`recommendation.adaptations` 里带 `field / native / requested / cost / todo`，EP **必须原样记进 `ledger.decisions`**。合同阈值是按原生格式标定的（比如案卷的静态持有上限按 65s 片标、主播台的四声部份额按 16:9 单片标定），换格式后要么走带宽内 amendments，要么按 `[单片标定]` 重新观测——**不许假装带宽还成立**。
3. **`adaptation` 文本是施工说明，不是免责声明。** 写「三章压两章、删 S7/S8 槽位、保住钩子与收尾」这种可执行的话；写「适当调整」等于没写。

**C. 置信与兜底。** 输出 **Top 3 而不是硬选一个**，默认推荐第一名并给一句理由。

| 置信 | 条件 | 行为 |
|---|---|---|
| `high` | 契合度过高线、明显领先第二名、且**不需要格式适配** | 直接用第一名 |
| `medium` | 契合度过中线但没到高线 **／** 与第二名咬得很近（标 `tie`）**／** 需要格式适配 | 仍用第一名，但理由里必须写出第二名和差在哪、要做哪些适配，全部记 `ledger.decisions` |
| `low` | 见下 | **落兜底包** `whiteboard-generalist` |

落 `low` 的三种情形（注意：**画幅或时长不合都不在其中**）：

1. 所有专用包的配方前提都不成立（缺必需素材 / 素材冲突 / 敏感题材）；
2. 契合度低于中线；
3. **最高分的包没有承担这条片的理解任务**——哪怕它内容类型、素材、语气全中。

第 3 条是一句话原则的机器编码，也是本次升级最重要的一条：`unknown` 的理解任务必然落兜底。宁可用兜底包保下限，也不让模型凭「这是条新闻」自作主张选一个花哨的专用包。

## 4. 三个包的分工（用户 2026-07-27 拍板）

按**观众此刻需要的理解方式**区分，不按题材区分：

| 包 | 定位 | 解决的核心任务 | 叙事骨架 | 签名 |
|---|---|---|---|---|
| `case-file` 案卷档案 | 事实核验型新闻解读 | 让观众快速相信、看懂一件正在发生的事 | 主张 → 文件证据 → 解释 → 结论 | **带观众读证据**（文件高亮、数字压在原始材料上、居中极简）——不是纸张，也不是红色 |
| `pixel-chronicle` 像素纪事 | 结构化深度知识叙事 | 把复杂对象讲出结构、历史和情绪落点 | 反差钩子 → 三层结构解释 → 人／现实落点 → 情绪收束 | **把抽象知识做成可感知的世界**（实物化数据、像素重演与真实影像交替、统一做旧质感）——不是像素 |
| `anchor-desk` 主播台 | 官方口径播报型解读 | 让观众拿到官方刚发布的数字、它的口径和一句结论 | 主播报题 → 数据屏拆口径 → 实拍物证 → 转折设问 → 结论卡 | **学电视新闻的形式而不学它的腔调** |
| `whiteboard-generalist` 公用白板 | **生产兜底模板，不是第三个风格 SKU** | 保下限 | 由 brief 决定 | 没有签名动作，这是设计意图 |

`case-file` 与 `anchor-desk` 的理解任务互为主次（前者主 `verify_the_event`、次 `read_the_official_number`，后者反过来）。**分界线是主播，不是画幅**：`case-file` 是 faceless 三声部包（排斥 `presenter_wanted`），`anchor-desk` 的四声部里主播一个镜都不能删（排斥 `presenter_declined`）——这两条是硬规则。画幅只是各自的原生格式：竖屏案卷、横屏主播台都能换过去，代价是版式适配（考卷 rc08 / rc12 就是这两种换法）。

`whiteboard-generalist` 的 `status` 是 `fallback`：它**不参与竞争打分**。它不会因为「什么都沾一点」挤掉专用包，也不会因为分低被漏掉——路由器永远把它作为最后一行兜底候选输出。

## 5. 用法

```bash
# 常规路由（produce §1.3 开拍时跑）
python3 tools/route-style.py --features projects/<slug>/routing.json

# 命令行等价形式
python3 tools/route-style.py \
  --topic "OpenAI 被要求交出 7800 万条日志" \
  --content-type deep_news --understanding-task verify_the_event \
  --tone authoritative,urgent --audience general,professional \
  --material readable_evidence,presenter_declined --aspect 9:16 --duration 75

# 写进 ledger.decisions 用 JSON
python3 tools/route-style.py --features f.json --json

# 能力卡清单 + 理解任务覆盖矩阵（看空位）
python3 tools/route-style.py --list

# 路由回归：改能力卡 / 改权重 / 加新包之后必跑
python3 tools/route-style.py --check
```

`--check` 跑 `routing-cases.json` 的 15 条考题：三条用户示例、两条真片回放（`openai-78m-logs` / `china-h1-2026-econ`）、四条格式适配（竖屏播报 / 横屏案卷 / 240s 超长案卷 / 60s 竖屏机制解释双适配）、六条边界（无证据、伤亡题材软扣分、理解任务未判定、并列、两条空位）。**改路由不跑回归 = 修好一个弄坏三个。**

## 6. 两类风格包：基础叙事 vs 视觉修饰

目标形态是把风格包拆成两类，路由输出一个组合：

- **基础叙事包**：快讯 / 解释型 / 人物叙事 / 复盘 / 评论——决定结构、节奏与镜头语法；
- **视觉修饰包**：科技感 / 财经质感 / 手绘 / 纪录片 / 极简信息图——决定美术和包装。

```
基础叙事：解释型知识讲解
视觉修饰：极简信息图
```

**当前状态（诚实版）：四个包全部是 `layer: bundled`——叙事骨架和美术长在一起，拆不开。** 路由器的输出结构已经是 `{narrative_base, visual_skin}`，但 `visual_skin` 现在恒为 `null`。这是**空位不是已有能力**，不要在别处把它写成已经上线。

### 拆分决议（2026-07-27 用户拍板 · 待办登记）

> 「基础叙事包 vs 视觉修饰包没有拆是对的，可以先记下来，等我们风格包再扩展一批再来拆。」

- **触发条件**：`styles/` 下专用包再扩展一批（现 3 个专用包 + 1 兜底 → 达到 6 个专用包量级，或更早出现「同一叙事骨架要换两套美术」的真实需求），届时启动拆分。
- **不提前拆的理由**：3 个包时多一层组合，只会让每个包都要维护两个半成品；组合的价值要等到「叙事骨架数 × 美术数」明显大于「包数」才出现。
- **迁移路径**（到时候照这个走）：把 `bundled` 卡的 `visual_language` + playbook 视觉系统章节抽成 `visual_skin` 卡；`narrative_skeleton` + `pacing` + 声部表 + `understanding_task` 留在 `narrative_base` 卡；`contract.json` 按同一条线切开（版式/色彩阈值跟 skin 走，声部份额与节奏阈值跟 base 走）；`native_format` 跟 **base** 走（它约束的是叙事骨架能撑多长、什么画幅），`adaptation.aspect` 里属于美术的部分随 skin 走。路由器输出的 `visual_skin` 字段那时才开始有值——不改输出结构，只填空。
- **不拆期间的纪律**：新包照旧写成 `bundled`；但 playbook 的「叙事骨架」和「视觉系统」两节必须分得清（未来切割线就在这里），签名动作要写成**行为**而不是材质（「带观众读证据」而不是「纸张和红色」）——写不清的包，将来也拆不开。

## 7. 理解任务空位表

`python3 tools/route-style.py --list` 直接打这张表。当前：

| 理解任务 | 认领的包 | 状态 |
|---|---|---|
| `verify_the_event` | case-file（主）/ anchor-desk（次） | ✓ |
| `explain_the_mechanism` | pixel-chronicle（主） | ✓ |
| `read_the_official_number` | anchor-desk（主）/ case-file（次） | ✓ |
| `follow_a_person` | — | **空位**：人物故事型解释。有采访/人物素材的 2 分钟片现在只能落兜底 |
| `weigh_an_argument` | — | **空位**：观点辩论型评论 |
| `learn_to_do` | — | **空位**：操作教学型 |

还有一个**条件空位**（任务有包认领，但常见条件组合下配方前提不成立，回归考卷 rc03 就是证据）：

- **概念拆解型**：抽象概念 + 新手 + 只有图示需求、**没有反差事实/因果链、也没有实拍或档案素材**。`pixel-chronicle` 的三层结构解释在这种输入上没有内容可填，落兜底。注意这是**素材前提**空位，不是时长问题——60s 的机制解释题只要有反差事实和实拍来源，照样落 `pixel-chronicle` 并出压短施工说明（考卷 rc14）。

> **「竖屏播报型」曾被记为空位，2026-07-27 已消解**：画幅不再是硬门之后，竖屏 + 要主播的题直接落 `anchor-desk` 并出换画幅施工说明（考卷 rc08）。空位表只记**理解任务与素材前提**的缺口，不记格式缺口——格式是适配问题。

**新增风格包的第一个问题不是「它长什么样」，而是「它认领哪个理解任务的空位」。** 认领不了空位、只是换套美术的包，说明它应该是未来的视觉修饰包（见 §6 拆分决议），不是一个新的基础叙事包。

## 7b. Golden 样片

登记册 `styles/golden-set.json`（成片是重媒体、不入库，本地归档在 `~/kuleshov-archive/golden/`）。三个专用包各一条，2026-07-27 用户交付：

| 包 | Golden | 规格（实测） | 一句话 |
|---|---|---|---|
| `case-file` | `openai-78m-logs` | 1080×1920 · 65.8s · −14.02 LUFS | 文件实证卡语法与「数字压在材料上」的范本；**无烧字幕**，字幕两条铁律在它身上无从对照 |
| `pixel-chronicle` | `uk-argentina-feud` | 1280×720 · 255.7s · −13.93 LUFS | 做旧缝合层与 MG↔实拍交替节奏的范本；**字幕带标点 + 带底框，早于 2026-07-27 两条拍板，照抄即违规** |
| `anchor-desk` | `china-h1-2026-econ` | 1920×1080 · 82.0s · −14.11 LUFS | **当前唯一同时满足「字幕不带标点」+「组件无底框」的 Golden**；但文件实证缺位、音频门未验 |

🔴 **`known_defects` 必须随 Golden 一起进评委上下文**——`build_evidence_pack.py --golden <pack>` 会把它写进 `manifest.golden_known_defects`，`judge.py` 再拼进评委任务，并明确告诉评委「Golden 里的违规不构成标准」。Golden 是工艺下限参照，不是逐帧临摹目标。

兜底包不该有 Golden（不走考片制上架）；评它出的片时 Golden 位留空或放一条同仓同画幅成片作工艺下限参照，并在 `golden_note` 写明「不是本片的风格目标」。

## 8. 新增／修改风格包的流程

1. 从被验证的优秀作品拉片蒸馏（`/benchmark-breakdown`），写 `playbook.md`——先说清它认领哪个**理解任务空位**；
2. 写 `capability.json`：理解任务主/次、硬规则（每条回链 playbook 条款）、`native_format` + 三条 `adaptation`、签名素材、`avoid_when`；
3. 在 `routing-cases.json` 加考题：至少一条**该命中**、一条**该被排除**（素材前提不成立时必须落兜底）、一条**该出格式适配**；
4. `python3 tools/route-style.py --check` 全绿——**新包不许把老片的路由结果改掉**，改掉了就是能力卡边界没划清；
5. 写 `contract.json` 机器硬门 + `test-shots.json` 考题镜头（`_iteration.md`）；
6. 出样片 → 盲评赢基线 → `status` 从 `candidate` 转 `verified`；
7. 转正的样片归档进 `~/kuleshov-archive/golden/<pack>__<project>.mp4` 并登记 `golden-set.json`（含实测规格与 `known_defects`）。

路由层的准入与出片层的考片制是两件事：**能力卡决定它会不会被选中，考片制决定它能不能上架。** 未考片的包照样参与路由（标 `candidate`），因为不让它被选中就永远拿不到样片。
