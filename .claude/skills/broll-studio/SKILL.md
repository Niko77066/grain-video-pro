---
name: broll-studio
description: 八套生成型 b-roll 材质语言的共用引擎（GPT-Image-2 + Seedance 2.0）——像素风 / 半调纸拼贴 / 实物桌面剧场 / 技术图解 / 黏土微缩 / 毛毡动画 / 立体书分层景观 / 极简 3D 玩具世界。当用户说"像素风""pixel art""拼贴 b-roll""纸拼贴""桌面剧场""物品隐喻""技术图解""爆炸视图""黏土""毛毡""立体书""玩具世界""换个材质试试""这条用什么风格拍"，或 storyboard 有镜头路由到这八套之一时使用。强制三闸门：视觉隐喻 → 静帧 → 视频，每闸停下等确认。**同片单一**：一条片只准一种生成风格，且**不许串别的风格的材质语汇**——`tools/broll-profile.py lint` 是硬门。
---

# B-roll Studio · 八套材质语言的共用引擎

血统：**`gbro-collage-broll`（pyang5166）** 的分支——保留三闸门纪律、assemble-from-empty 首尾帧机制与 QA 结构，引擎重绑到 **GPT-Image-2 + Seedance 2.0**。

**这个 skill 不复制八套完整流程**。三闸门、画幅几何、引擎绑定、QA、IR 写回**只有一份，就在本文件与 `tools/`**；随风格变的东西全部落在 `profiles/<id>.json`：

| profile 负责 | 例子 |
|---|---|
| **材质语汇** `signature_vocab` | `tabletop / contact shadows`（物品剧场）vs `needle-felted / wool fibers`（毛毡） |
| **运动动词** `motion_verbs` | `rolling / pivoting / clicking` vs `scoot / bounce / settle` |
| **首帧规则** `first_frame.kind` | 空台面 vs **一本合上的书** vs **角色起始姿态** |
| **缝合纪律** `stitching` | 怎么和 HyperFrames 版式卡缝成一家（pixel 例外：缝合完全在 compose 层） |
| **失败标准** `failure_criteria` | 「物品悬浮」vs「毛纤维生长散开」vs「栅格没守住」 |
| **额外工序** `pipeline_extras` | 只有少数几套有：片级调色板闸门、归一层、附加静帧槽位 |
| **IR 写回** `ir_writeback` | provider / params / note 前缀（历史 provider 名不因并入本 skill 而改） |

> **引擎不认识任何 profile 的名字。** 差异一律靠 profile 声明，引擎只知道「有些 profile 带额外步骤」。
> `grep -nE 'pid *== *"' tools/broll-profile.py` 搜不到硬编码分支，是这条纪律仍然成立的证据。
> （别用裸的 `pid ==` 当证据——lint 里「跳过自己」的 `oid == pid` 是合法比较，会假阳性。）

## 1. 八套材质语言

```bash
python3 tools/broll-profile.py list            # 全表（含状态与额外工序标记）
python3 tools/broll-profile.py status          # 冒烟状态表 + known issues（**状态的唯一出处**）
python3 tools/broll-profile.py show <id>       # 单套详情（视觉参考、失败标准、缝合纪律）
python3 tools/broll-profile.py plan <id>       # 该套的完整工序清单（含额外工序，命令直接可跑）
python3 tools/broll-profile.py route "AI 机制"  # 按文稿类型选型
python3 tools/broll-profile.py vars            # 提示词变量表（全仓唯一一套）
python3 tools/broll-profile.py selftest        # 自洽性测试：每套渲一遍并过自己的 lint
```

| profile | 核心优势 | 最适合 |
|---|---|---|
| `pixel` 像素风 | 限定调色板 + 硬边栅格 | 角色重演（版权规避位）、机制图解、数据实物化、历史重演 |
| `collage` 半调纸拼贴 | 高级编辑风氛围 b-roll | 抽象隐喻的口播间奏、观点句 |
| `object-theatre` 实物桌面剧场 | 熟悉物品形成意外隐喻 | 观点、反转、效率、职场、人性 |
| `technical-diagram` 技术图解 | 把抽象机制讲清楚 | AI、Agent、工作流、系统机制 |
| `clay-miniature` 黏土微缩 | 荒诞、幽默、可变形 | 情绪、焦虑、冲突、轻观点 |
| `felted-wool` 毛毡动画 | 柔软、温暖、有人情味 | 关系、陪伴、生活、品牌价值 |
| `popup-book` 立体书／分层景观 | 擅长展示路径与世界 | 成长、旅程、生态、流程 |
| `toy-world` 极简 3D 玩具世界 | 高级、统一、产品化 | 产品功能、平台、商业与科技 |

`pixel-broll` / `collage-broll` 两个 skill 名仍可按名调用（`/pixel-broll`、`/collage-broll`），它们现在是**指针壳**——内容在这里，profile 分别是 `pixel` 与 `collage`。

选型表在 `routing.json`（文稿类型 → 首选／备选 + tie-break）。**注意这是镜头级选型**，和 `styles/` 那层的风格包路由（`tools/route-style.py`，问「要让观众如何理解这条内容」）是两层，不冲突：风格包定全片世界，profile 定单镜材质。

## 2. 🔴 同片单一 + 不许串词（本 skill 的宪法条款）

- **同片单一**：一条片只准一种生成风格。开工时写死 `meta.style_notes.generated_style`，逐镜按该风执法。沿用 `whiteboard-generalist` 的 `STYLE_LOCK` 纪律。
- **不许串词**：提示词里不得出现别的 profile 的 `signature_vocab`，也不得出现本 profile 自己声明的 `banned_vocab`。这不是洁癖——浣熊片那段「做旧报纸味的假像素」的成因，就是拼贴模板 find/replace 成像素之后 `paper-collage` / `paper grain` 留在了里面。现在这道门是机器执行的：

```bash
python3 tools/broll-profile.py lint <id> --file prompt.txt
```

lint 只看**肯定描述**——`No paper collage` 这类否定式约束是在主动划界，正是我们要的，不算串词。

> 词表自洽性有两种修法，别混：
> - **通用词从签名表里删掉**。`modular` 曾同时挂在 technical-diagram 与 toy-world 名下，被 lint 自己抓出来——不具区分性的词不该进签名表，否则两套互相误报。同批还有 `rails` / `fingerprints` / `contact shadows`。
> - **共有词两边都挂上**。`isometric` **故意**同时挂在 `pixel` 与 `toy-world` 名下（2026-07-28 用户拍板：**两套风格都合法使用的词不算串词**），lint 对共有词不判串。这跟上一条的区别是：通用词是「谁用都不说明什么」，共有词是「这两套各自都真的以它为语汇」。
>
> 新增 profile 后跑 `selftest`。

## 3. 三闸门（强制。每闸停下等确认，部分通过就只放通过的进下一闸）

| 闸 | 产物 | 成本 | 停下问什么 |
|---|---|---|---|
| **Gate 1 · 隐喻** | 每条：核心意思 / 情绪 / 一句话视觉命题 / 各变量取值 + **选定 profile**（带 `variants` 的还要选原型） | 免费 | 隐喻对不对、这套材质是不是最合适的 |
| **Gate 2 · 静帧** | 渲染 gate2 prompt → GPT-Image-2 → 落地后置工序 → 编号 contact sheet | 便宜 | 静帧成不成立（错静帧重生一张图，远比重跑一条视频便宜） |
| **Gate 3 · 视频** | 首帧（按 profile 的 `first_frame` 规则）+ 确认静帧 → Seedance → 落地后置工序 → `clip-qa` | ~$2.7/条 | 组装是否铺满全片、有没有死尾、失败标准逐条过 |

少数 profile 在三闸门之外还有**额外工序**（见 §5）——`plan <id>` 会把它们按顺序列出来。

**批量支持部分通过**：只有确认过的条目进下一闸，未确认的留在原闸修改。重生的 contact sheet 递增 `v2`/`v3`，旧版不覆盖。逐条 QA 结论（含带瑕疵通过的判定理由）写 `<项目>/gate2-qa.md` 与 `gate3-qa.md`。

开工前跑 `bash tools/check-media-setup.sh`；全绿直接进 Gate 1，别把配置信息复述给用户。

## 4. 画幅、时长与几何

| | 9:16 竖屏（原生） | 16:9 横屏 |
|---|---|---|
| GPT-Image-2 `size` | `720x1280` | `1280x720`（16 的倍数，见 `image-motion.md`） |
| 首帧空场 `-s` | `1080x1920` | `1920x1080` |
| 尾帧归一 | `scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920` | `scale=1920:1080:...,crop=1920:1080` |
| Seedance `metadata.ratio` | `"9:16"` | `"16:9"` |
| contact sheet `scale` | `180:320` | `320:180` |

`size` 必须是 16 的倍数，故出图走 `1280x720` 而非 `1920x1080`；`1920x1080` 只出现在 ffmpeg 首尾帧（lavfi/crop 不受 16 倍数约束）。

`render --aspect 16:9` 有两条路，**都是声明式的**：

- profile 给了 `gate2_prompt_16_9` / `gate3_prompt_16_9`（整段实测过的横屏原文）→ 直接用那段，不做替换。`collage` 走这条。
- 否则按 profile 的 `aspect_16_9` 逐条替换；不带 `→` 的条目是**施工说明**，打到 stderr 等人工落实（两条路都会打）。

**横屏必带聚簇约束**（中央 60% + 外三分之一留空）——这是拼贴链 2026-07-28 横屏实测证明有效的抗摊散手段，删了就摊。

### ⚠️ 时长：profile 默认 10s，不是 5s

原始风格设计稿写的是 5s。**本仓按 10s 落地**，理由是实测而非偏好：`seedance.md` 记着「5s 组装被用户打回『过得太快』是必然，定格拼装需要呼吸」，10s 原生慢组装一次过。八套 profile 的 `native.duration_s` 因此统一是 10；实产 ≈10.04s 是常态（三条链共 12 条实测一致）。

真要 5s 的镜位（快切蒙太奇里的一格），显式覆写并记进 `ledger.decisions`——但别指望组装动作在 5s 里读得清。

### 首帧规则随 profile（和运动原型）变

`first_frame.kind` 是数据，不是注释；引擎按 kind 分支：

- `empty_surface` —— 默认路径：六套无变体的走这条，`pixel` 的**组装型原型 A** 也走这条（`ffmpeg -f lavfi -i color=...`；`plan pixel --variant A` 可验证，A 不欠附加静帧）。
- `closed_book` —— `popup-book`：必须以「一本合上的书 / 一张平整页面」起手，不许空场，否则整个空间凭空出现、产生不可控变形。
- `character_start_pose` —— `pixel` 的角色动作型原型：首帧是角色**起始**姿态的静帧。

**首尾帧里有哪一张要出图，Gate 2 就要多出一张**——`popup-book` 多的是首帧（合上的书），`pixel` 原型 B 多的是尾帧（完成姿态，走 ref）。这条工序差异声明在 `pipeline_extras.gate2_extra_stills`，不是散在注释里；`render --gate 2` 会主动提醒还有几个槽位没出。细节见 §5。

## 5. 额外工序（`pipeline_extras`）

八套里有几套天生比三闸门多几步。这些步骤**写在 profile 的数据里**，引擎照单执行，认的是工序**种类**而不是 profile 名字：

| 键 | 是什么 | 谁在用 |
|---|---|---|
| `film_level_gates` | 片级前置闸门（一部片一次，定了就不改） | `pixel` 的 Gate 0 主调色板 |
| `gate2_extra_stills` | Gate 2 的附加静帧槽位，每个 +1 张图成本。槽位可用 **`when_variant`** 把自己限定在某些变体下（不写 = 所有变体都要） | `popup-book` 的「合上的书」首帧（无条件）；`pixel` 的 `last_frame_ref` 尾帧（`when_variant: ["B"]`） |
| `post_still` / `post_video` | 静帧 / 视频落地后的必做工序 | `pixel` 的归一层 |
| `extra_checks` | 该套专属的额外码判（通用项仍走 `clip-qa.py`） | `pixel` 的栅格 + 锁色 |
| `params` | 上面那些命令里 `{palette}` `{grid}` 这类占位符的默认值 | 同上 |

表外的键（如 `why` / `check_criteria` / `encode_note`）引擎不执行、也不丢弃——`plan` 以「profile 附注」原文照录（操作性纪律不许隐形，`--crf 0` 就吃过静默丢弃的亏）。

```bash
python3 tools/broll-profile.py plan pixel --variant B --param palette=projects/<片>/palette/master.png
python3 tools/broll-profile.py render popup-book --gate 2 --slot first_frame --var PALETTE=deep-green
python3 tools/broll-profile.py render pixel --gate 2 --slot last_frame_ref --variant B \
  --var FRAMING=side-view --var END_POSE="<动完是什么样，含被动作带动的元素>"
```

新 profile 要加工序时，**先看能不能用现成的键表达**。表达不了就停下来问——那说明它不只是一套材质语言，可能真该独立成 skill。

### 两个附加槽位的额外工序（这两套比别人多一张图）

| profile | 槽位 | 出的是哪一张 | 机制 | 什么时候要 |
|---|---|---|---|---|
| `popup-book` | `first_frame` | **首帧**：一本合上的书 | 普通出图（空场起手会让空间凭空出现） | 每条都要 |
| `pixel` | `last_frame_ref` | **尾帧**：动作完成姿态 | `/v1/images/edits` 挂 **ref**（归一后的首帧当参考图） | **只有运动原型 B** |

`pixel` 的 ref 槽位是**角色一致性**的解法：把一致性放在便宜的图像阶段解决，而不是在 Seedance 提示词里复述长相（复述与锚点冲突时模型自己选，那就是变脸的成因）。工序顺序是硬的——首帧出图 → 归一 → 拿归一图当 ref 出尾帧 → 尾帧再归一。

**「哪些变体要这张」是机器门，不是文本约束**：槽位自己声明 `when_variant`，引擎按当前 `--variant` 过滤——`pixel` 原型 A 下 `render` / `plan` 根本不会提起 `last_frame_ref`，硬点 `--slot last_frame_ref --variant A` 直接报错说「这一张不用出」；带槽位却不给 `--variant` 会被逼着先选变体（那本来就是 Gate 1 的决定）。`when_variant` 是通用声明式字段，`popup-book` 的槽位不写它，行为一如从前。

> 第一版曾把这个条件写在槽位 `purpose` 的第一句，于是引擎在原型 A 下先命令你出图、再在括号里说不适用——一句自相矛盾的祈使句。**条件能声明就别写成叮嘱**：这跟本次重构的主线是同一条理由。

## 6. 提示词变量（全仓唯一一套）

`variables.json` 是变量的唯一注册表，profile 的 `variables` 只能从里面取名，`render` 会校验。取表外的名字直接报错——这道校验防的是「每套 profile 长出自己一套同义变量」。

```bash
python3 tools/broll-profile.py vars     # 变量含义 + 谁在用 + 旧 visual-spec 字段的落点
```

### 🔴 填色写自然语言，hex 只作补充锁值

**模型不认 hex**（2026-07-28 用户拍板）。`PALETTE` 一律填颜色名（`deep-green` / `warm sand`）；`PALETTE_HEX` 的用途是**机器精确性**——首帧空场的 ffmpeg lavfi 靠它保证首帧与静帧同色——写进提示词时只能跟在颜色名后面作补充（`perfectly flat deep-green paper field (#1E4438)`），**不许单独承担一个色彩描述槽位**。

两处看着像反例的都不是：`pixel` 的 `PALETTE_LIST` 是**锁色清单**（模型读不准没关系，归一层在生成之后物理量化到这张表），它 gate2 的底色 hex 与紧邻上一句的锁色表连读。这两段都是冒烟原文，**别按本条去改写它们**。

> **历史**：collage 链原来在 Gate 2 前写一份结构化 `visual-spec.json`，六套 profile 走变量填空。两者是同一件事的两种写法，2026-07-28 收敛到变量——理由很物理：`render` 真的读变量，而 visual-spec **没有任何程序读它**。旧字段逐个的落点在 `variables.json` 的 `visual_spec_mapping` 里，没有信息丢失。**不要再写那份中间文件。**

## 7. 跑起来（9:16、object-theatre 为例）

```bash
S=tools; P=projects/<片>
# Gate 1 定完隐喻后，渲染 Gate 2 提示词（自动跑串词 lint）
python3 $S/broll-profile.py render object-theatre --gate 2 \
  --var VISUAL_METAPHOR="AI 是一面会放大问题的镜子" \
  --var KEY_OBJECTS="a magnifying glass, a cracked lens, stacked problem blocks, a widening crack" \
  --var PALETTE="warm sand" > $P/anchors/s03.prompt.txt

# Gate 2：出图 → contact sheet → 停下等确认
python3 $S/gpt-image.py --jobs $P/anchors/imgjobs.json --out $P/anchors --state $P/runs/img-state.json

# Gate 3：首帧（按 profile 规则）+ 尾帧归一 → 提交 → 轮询 → QA
ffmpeg -y -f lavfi -i color=c=0x<PALETTE主色>:s=1080x1920 -frames:v 1 $P/anchors/s03_first.png
ffmpeg -y -i $P/anchors/s03_raw.png \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" $P/anchors/s03_last.png
python3 $S/broll-profile.py render object-theatre --gate 3 \
  --var ASSEMBLY_ORDER="the magnifying glass rolls in and settles, then the problem blocks stack under it, then the lens cracks" \
  > $P/shots/s03.prompt.txt
python3 $S/seedance.py submit --jobs $P/shots/jobs.json --state $P/runs/sd-state.json --dry-run
python3 $S/seedance.py submit --jobs $P/shots/jobs.json --state $P/runs/sd-state.json
python3 $S/seedance.py poll   --state $P/runs/sd-state.json --out $P/shots/
python3 $S/clip-qa.py $P/shots/s03_raw.mp4 --expect-size 720x1280 \
        --json $P/evidence/broll-qa-s03.json --contact $P/evidence/s03-contact.jpg
```

`jobs.json`：

```json
{ "defaults": {"ratio":"9:16","resolution":"720p","duration":10,"oss_prefix":"kuleshov/<片>/<profile>"},
  "jobs": [ {"name":"s03","prompt":"<Seedance prompt>",
             "first":"projects/<片>/anchors/s03_first.png",
             "last":"projects/<片>/anchors/s03_last.png"} ] }
```

`tools/seedance.py` 把三条最容易写错的契约固化成会报错的形状：`duration` 必须在 `metadata` 内（顶层会被忽略，恒出 5.04s）、`ratio` 不许省略（省略由上游自判画幅）、越界 duration 提交前本地拦截（越界会在**排队后**才拒且**已计费**）。首尾帧自动过 `tools/oss-upload.sh`；worktree 无 `.env` 时先 `ln -sf <主仓库>/.env .env`。

**带额外工序的 profile 别照抄上面这段**——先跑 `plan <id>` 拿它自己的清单。

## 8. 验收

机器码判走 `tools/clip-qa.py`（**通用项全仓只有这一份实现**）：

| 项 | 判据 |
|---|---|
| 死尾 | 尾 2s 运动量 ≥ 全片中位的 **25%**（相对判据）。绝对阈值跨不了内容类型，2026-07-28 实测证伪，见该脚本常量处 |
| 规格 | 9:16 → 720×1280、16:9 → 1280×720；**零音轨** |

带 `extra_checks` 的 profile 再跑它自己那份专属码判（`pixel` 的栅格 + 锁色由 `tools/verify.py` 出，且它会自动调 `clip-qa.py` 补通用项——**不是第二份死尾判据**）。

**多条一起做时必出批次总览三张图**（单看逐条会漏掉批次级问题）：

```bash
python3 tools/clip-batch-sheets.py --out-dir $P/evidence \
  --clips $P/shots/s03.mp4 $P/shots/s05.mp4 --stills $P/anchors/s03.png $P/anchors/s05.png
```

出 `omni-contact-sheet-all.jpg`（逐条组装进程）、`video-first-frame-all.jpg`（验真的按首帧规则起手）、`end-frame-comparison-all.jpg`（确认静帧 ‖ 视频末帧）。

人眼再过两层：

1. **通用**：首帧符合该 profile 的 `first_frame` 规则；中段能看到元素**逐件进入**而非整体淡入；无切镜/zoom/漂移；无假字/logo/水印；尾帧≈确认静帧（轻微细节漂移不影响语义即通过，不为此重跑）。
2. **profile 专属**：逐条对 `failure_criteria`（`show <id>` 看）。八套的失败方式各不相同——黏土会变脸多手、毛毡会长毛散开、图解会先连线后装模块、玩具世界会滑向 3C 广告 CG、拼贴横屏会摊散、像素会守不住栅格。

**时长调和**：compose **尾裁**掉末端残余 hold 到 shot 槽位——前提是组装已铺满、只剩很短 hold；**组装过早完成就得重生或缩短槽位，尾裁救不了**。挂载尾对齐规则见 `seedance.md`。

## 9. 写回 IR

写法由 profile 的 `ir_writeback` 声明（`show <id>` 看）——**不同 profile 的 provider 名不同是历史契约，不许为了整齐去改**：`pixel` 与六套走 `provider: "seedance"`（合同 `traits.pixel_narrative` 的 fallback 按 provider 认），`collage` 走 `provider: "collage_broll"`（存量 film.json 按它认）。

```json
{ "source": { "provider": "<ir_writeback.provider>",
    "params": { "...": "见 ir_writeback.params，profile 字段填 <id>" },
    "note": "<note_prefix>·<一句话隐喻>" } }
```

留痕：`gen` 记 model / 完整 prompt / seed / 首尾帧 / `x-oneapi-request-id` / 实测时长；`qc` 挂 `evidence/<链>-qa-<镜>.json`；成本进 `ledger.costs`（1 张 GPT-Image + 1 条 Seedance ≈ $2.7；带附加静帧槽位的多算一张图——`popup-book` 每条都多一张，`pixel` **只有运动原型 B** 每条多一张，原型 A 仍是 1 张）。选 profile、选运动原型、选底色、部分通过、带瑕疵放行都进 `ledger.decisions`。

## 10. 什么时候不要用

精确文字／数字／法条／logo → HyperFrames 叠层（可以叠在生成画面上，兼得质感与信息）；可逐层编辑的时间线 → HyperFrames；真人产品口播 → 不走本流程。

## 11. 状态

**状态的唯一出处是 profile 的 `status` 字段**，看表跑：

```bash
python3 tools/broll-profile.py status
```

本文件不再抄一份——抄一份就多一个会漂的副本，而这次重构的全部动机就是消除副本。

### 挖出来的知识（跨 profile 有效，所以留在这里）

1. **`popup-book` 的死尾判红通常不是缺陷，是剪辑问题**——书展开完的定格是这门语言的收尾语法。正解是 compose 层尾裁，不是改提示词重生（据机器判红去删那句 hold，改坏了语法且判得更红 16%→9%，已撤回）。见该 profile 的 `notes`。
2. **死尾判据的第二个失效模式：中段爆发型**。`popup-book` v2 尾段绝对 YDIF 0.657 是七条测试片里第二高，却因中段爆发抬高分母只得 9%。换过两种更抗爆发的分母都救不回来。**判据未放松**，只加 advisory 提示人眼复核——数据与三次失败尝试记在 `tools/clip-qa.py` 常量处。
3. **死尾的绝对阈值被证伪**（2026-07-28 pixel 链冒烟）：`YDIF<1 视为近静止` 是拿半调拼贴/摄影内容标的，平色像素画在暗底上相邻帧亮度差本就 0.3–0.4，四条测试片误报三条。改相对判据后与内容亮度脱钩，负对照仍开火。
4. **Gate 2 值回票价**：`toy-world` v1 尾帧模块没对接，而隐喻是「模块自己拼起来」；Image 2 不是完成态，Gate 3 就会朝着「没拼上」组装。一张图的钱挡住一条片的钱。
5. **归一层是必需的，不是可选后处理**（`pixel`）：Seedance 原始输出非纯色方块 30.5%（横）/ 49.0%（竖）、越界色 10 万+；归一后 0% / 0 种。
6. **角色一致性靠 `/v1/images/edits` 挂参考图**解决在便宜的图像阶段，不靠在 Seedance prompt 里复述长相——复述与锚点冲突时模型会自己选，那就是变脸的成因。
7. **串词 lint 抓出四处词表设计错**（`modular` / `rails` / `fingerprints` / `contact shadows`）——通用词不该进签名表，否则两套互相误报。

### 仍未验（跨 profile）

- 同一条片里多镜共用一套 profile 的一致性（多数 profile 只出过一条）。
- 16:9 只有 `collage` 与 `pixel` 出过片；其余六套的 `aspect_16_9` 施工说明未出片验证。
- **闸门、串词与偷跑纪律**：`evals.json` 19 条考卷（八套共用一份），改 profile 或引擎后跑一遍。
