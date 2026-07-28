---
name: broll-studio
description: 六套生成型 b-roll 材质语言的共用引擎（GPT-Image-2 + Seedance 2.0）——实物桌面剧场 / 技术图解 / 黏土微缩 / 毛毡动画 / 立体书分层景观 / 极简 3D 玩具世界。当用户说"桌面剧场""物品隐喻""技术图解""爆炸视图""黏土""毛毡""立体书""玩具世界""换个材质试试""这条用什么风格拍"，或 storyboard 有镜头路由到这六套之一时使用。强制三闸门：视觉隐喻 → 静帧 → 视频，每闸停下等确认。**同片单一**：一条片只准一种生成风格，且**不许串别的风格的材质语汇**——`tools/broll-profile.py lint` 是硬门。
---

# B-roll Studio · 六套材质语言的共用引擎

血统：与 `pixel-broll` / `collage-broll` 同源，都是 **`gbro-collage-broll`（pyang5166）** 的分支——保留三闸门纪律、visual-spec、assemble-from-empty 首尾帧机制与 QA 结构，引擎重绑到 **GPT-Image-2 + Seedance 2.0**。

**这个 skill 不复制六套完整流程**。三闸门、画幅几何、引擎绑定、QA、IR 写回**只有一份，就在本文件**；真正随风格变的只有四样，全部落在 `profiles/<id>.json`：

| profile 负责 | 例子 |
|---|---|
| **材质语汇** `signature_vocab` | `tabletop / contact shadows`（物品剧场）vs `needle-felted / wool fibers`（毛毡） |
| **运动动词** `motion_verbs` | `rolling / pivoting / clicking` vs `scoot / bounce / settle` |
| **首帧规则** `first_frame` | 空台面 vs **一本合上的书**（立体书不许空场起手） |
| **失败标准** `failure_criteria` | 「物品悬浮」vs「毛纤维生长散开」vs「连接线先于模块出现」 |

## 1. 八套材质语言（六套在本 skill，两套有独立 skill）

```bash
python3 tools/broll-profile.py list          # 全表
python3 tools/broll-profile.py show <id>     # 单套详情（含视觉参考与失败标准）
python3 tools/broll-profile.py route "AI 机制"  # 按文稿类型选型
```

| profile | 核心优势 | 最适合 |
|---|---|---|
| `object-theatre` 实物桌面剧场 | 熟悉物品形成意外隐喻 | 观点、反转、效率、职场、人性 |
| `technical-diagram` 技术图解 | 把抽象机制讲清楚 | AI、Agent、工作流、系统机制 |
| `clay-miniature` 黏土微缩 | 荒诞、幽默、可变形 | 情绪、焦虑、冲突、轻观点 |
| `felted-wool` 毛毡动画 | 柔软、温暖、有人情味 | 关系、陪伴、生活、品牌价值 |
| `popup-book` 立体书／分层景观 | 擅长展示路径与世界 | 成长、旅程、生态、流程 |
| `toy-world` 极简 3D 玩具世界 | 高级、统一、产品化 | 产品功能、平台、商业与科技 |
| `pixel` 像素风 → `.claude/skills/pixel-broll/` | 限定调色板 + 硬边栅格 | 角色重演、数据实物化、历史重演 |
| `collage` 半调纸拼贴 → `.claude/skills/collage-broll/` | 高级编辑风氛围 b-roll | 抽象隐喻的口播间奏 |

选型表在 `routing.json`（文稿类型 → 首选／备选 + tie-break）。**注意这是镜头级选型**，和 `styles/` 那层的风格包路由（`tools/route-style.py`，问「要让观众如何理解这条内容」）是两层，不冲突：风格包定全片世界，profile 定单镜材质。

## 2. 🔴 同片单一 + 不许串词（本 skill 的宪法条款）

- **同片单一**：一条片只准一种生成风格。开工时写死 `meta.style_notes.generated_style`，逐镜按该风执法。沿用 `whiteboard-generalist` 的 `STYLE_LOCK` 纪律。
- **不许串词**：提示词里不得出现别的 profile 的 `signature_vocab`。这不是洁癖——浣熊片那段「做旧报纸味的假像素」的成因，就是拼贴模板 find/replace 成像素之后 `paper-collage` / `paper grain` 留在了里面。现在这道门是机器执行的：

```bash
python3 tools/broll-profile.py lint <id> --file prompt.txt
```

lint 只看**肯定描述**——`No paper collage` 这类否定式约束是在主动划界，正是我们要的，不算串词。

> 词表自洽性：`modular` 曾同时挂在 technical-diagram 与 toy-world 名下，被 lint 自己抓出来（不具区分性的通用词不该进签名表），已修。新增 profile 时跑一遍「六套模板过各自 lint」的自洽性测试。

## 3. 三闸门（强制。每闸停下等确认，部分通过就只放通过的进下一闸）

| 闸 | 产物 | 成本 | 停下问什么 |
|---|---|---|---|
| **Gate 1 · 隐喻** | 每条：核心意思 / 情绪 / 一句话视觉命题 / `KEY_OBJECTS` / `PALETTE` / `ASSEMBLY_ORDER` + **选定 profile** | 免费 | 隐喻对不对、这套材质是不是最合适的 |
| **Gate 2 · 静帧** | 渲染 gate2 prompt → GPT-Image-2 → 编号 contact sheet | 便宜 | 静帧成不成立（错静帧重生一张图，远比重跑一条视频便宜） |
| **Gate 3 · 视频** | 首帧（按 profile 的 `first_frame` 规则）+ 确认静帧 → Seedance → `clip-qa` | ~$2.7/条 | 组装是否铺满全片、有没有死尾、失败标准逐条过 |

**批量支持部分通过**：只有确认过的条目进下一闸，未确认的留在原闸修改。重生的 contact sheet 递增 `v2`/`v3`，旧版不覆盖。逐条 QA 结论（含带瑕疵通过的判定理由）写 `<项目>/gate2-qa.md` 与 `gate3-qa.md`。

开工前跑 `bash tools/check-media-setup.sh`；全绿直接进 Gate 1，别把配置信息复述给用户。

## 4. 画幅、时长与几何

| | 9:16 竖屏（原生） | 16:9 横屏 |
|---|---|---|
| GPT-Image-2 `size` | `720x1280` | `1280x720`（16 的倍数，见 `image-motion.md`） |
| 首帧空场 `-s` | `1080x1920` | `1920x1080` |
| 尾帧归一 | `scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920` | `scale=1920:1080:...,crop=1920:1080` |
| Seedance `metadata.ratio` | `"9:16"` | `"16:9"` |

`render --aspect 16:9` 会按 profile 的 `aspect_16_9` 自动改画幅句，并把需要人工落实的施工说明打到 stderr。**横屏必带聚簇约束**（中央 60% + 外三分之一留空）——这是拼贴链 2026-07-28 横屏实测证明有效的抗摊散手段。

### ⚠️ 时长：profile 默认 10s，不是 5s

原始风格设计稿写的是 5s。**本仓按 10s 落地**，理由是实测而非偏好：`seedance.md` 记着「5s 组装被用户打回『过得太快』是必然，定格拼装需要呼吸」，10s 原生慢组装一次过。六套 profile 的 `native.duration_s` 因此统一是 10。

真要 5s 的镜位（快切蒙太奇里的一格），显式覆写并记进 `ledger.decisions`——但别指望组装动作在 5s 里读得清。

### 首帧规则随 profile 变

五套是**空场起手**（`first_frame.kind = empty_surface`，`ffmpeg -f lavfi -i color=...`）。

**`popup-book` 例外**：必须以「一本合上的书 / 一张平整页面」起手，不许空场——否则整个空间凭空出现，产生不可控变形。它的 Gate 2 因此要出**两张图**（`gate2_first_frame_prompt` + `gate2_prompt`），比别的风格多一次出图成本。

## 5. 跑起来（9:16、object-theatre 为例）

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

`tools/seedance.py` 把三条最容易写错的契约固化成会报错的形状：`duration` 必须在 `metadata` 内（顶层会被忽略，恒出 5.04s）、`ratio` 不许省略（省略由上游自判画幅）、越界 duration 提交前本地拦截（越界会在**排队后**才拒且**已计费**）。首尾帧自动过 `tools/oss-upload.sh`；worktree 无 `.env` 时先 `ln -sf <主仓库>/.env .env`。

## 6. 验收

机器码判走 `tools/clip-qa.py`：

| 项 | 判据 |
|---|---|
| 死尾 | 尾 2s 运动量 ≥ 全片中位的 **25%**（相对判据）。绝对阈值跨不了内容类型，2026-07-28 实测证伪，见该脚本常量处 |
| 规格 | 9:16 → 720×1280、16:9 → 1280×720；**零音轨** |

人眼再过两层：

1. **通用**：首帧符合该 profile 的 `first_frame` 规则；中段能看到元素**逐件进入**而非整体淡入；无切镜/zoom/漂移；无假字/logo/水印；尾帧≈确认静帧（轻微细节漂移不影响语义即通过，不为此重跑）。
2. **profile 专属**：逐条对 `failure_criteria`（`broll-profile.py show <id>` 看）。这六套的失败方式各不相同——黏土会变脸多手、毛毡会长毛散开、图解会先连线后装模块、玩具世界会滑向 3C 广告 CG。

## 7. 写回 IR

```json
{ "source": { "provider": "seedance",
    "params": { "ai_stylized": true, "craft": "broll-studio",
                "profile": "object-theatre", "aspect": "9:16", "duration_s": 10 },
    "note": "<profile 中文名>·<一句话隐喻>" } }
```

留痕：`gen` 记 model / 完整 prompt / seed / 首尾帧 / `x-oneapi-request-id` / 实测时长；`qc` 挂 `evidence/broll-qa-<镜>.json`；成本进 `ledger.costs`（1 张 GPT-Image + 1 条 Seedance ≈ $2.7；`popup-book` 多一张图）。选 profile、选底色、部分通过、带瑕疵放行都进 `ledger.decisions`。

## 8. 什么时候不要用

精确文字／数字／法条／logo → HyperFrames 叠层；可逐层编辑的时间线 → HyperFrames；真人产品口播 → 不走本流程；要像素或纸拼贴 → 那两条有独立 skill。

## 9. 状态

⚠️ **先读这条**：六套的 Gate 2 提示词在 2026-07-28 冒烟之后经历了一轮**按参考实图的重写**（见下）。
因此那轮的**视频结果只对 `clay-miniature` 仍然有效**——其余五套的 gate2/gate3 模板都换过，旧成片不再为当前模板背书。

| profile | Gate 2 静帧 | Gate 3 视频 | 说明 |
|---|---|---|---|
| `clay-miniature` | ✅ | ✅ 32% | **唯一端到端冒烟有效**的一套（模板未改动） |
| `object-theatre` | ✅ 人眼过 | ⚠️ 未验 | 按 PES 重写：手进画面、物品替身、转换发生在动作里 |
| `technical-diagram` | ✅ 人眼过 | ⚠️ 未验 | 按 Vectary + IBM 重建，**牛皮纸专利图皮肤已删** |
| `felted-wool` | ✅ 人眼过 | ⚠️ 未验 | 按 Fuzzy Feelings 重写：角色具体化、灰调电影感、全员从画外进场 |
| `popup-book` | ✅ 人眼过 | ⚠️ 未验 | 配色改走 collage 的色彩纪律；内部打光；撤回了错误的 hold 改动 |
| `toy-world` | ✅ 人眼过 | ⚠️ 未验 | 按 Cash App 重建（第三版才对） |

**排产前**：任一 profile 首次用当前模板出片，Gate 3 先跑 1 条测试 clip 目检，结论写回本表。

### 那一轮冒烟真正留下的东西

模板都换了，但**过程里挖出来的知识仍然有效**，已各归其位：

1. **`popup-book` 的死尾判红通常不是缺陷，是剪辑问题**——书展开完的定格是这门语言的收尾语法。正解是 compose 层尾裁，不是改提示词重生（我曾据机器判红去删那句 hold，改坏了语法且判得更红 16%→9%，已撤回）。见该 profile 的 notes。
2. **死尾判据的第二个失效模式：中段爆发型**。`popup-book` v2 尾段绝对 YDIF 0.657 是七条测试片里第二高，却因中段爆发抬高分母只得 9%。换过两种更抗爆发的分母都救不回来。**判据未放松**，只加 advisory 提示人眼复核——数据与三次失败尝试记在 `tools/clip-qa.py` 常量处。
3. **Gate 2 值回票价**：`toy-world` v1 尾帧模块没对接，而隐喻是「模块自己拼起来」；Image 2 不是完成态，Gate 3 就会朝着「没拼上」组装。一张图的钱挡住一条片的钱。
4. **首帧规则确实分两种**：五套空场起手，`popup-book` 必须以合上的书起手（Gate 2 出两张图）。引擎按 `first_frame.kind` 分支，不是注释。
5. **实产时长六条全是 10.042s**，与 pixel / collage 两链一致。
6. **串词 lint 抓出四处词表设计错**（`modular` / `rails` / `fingerprints` / `contact shadows`）——通用词不该进签名表，否则两套互相误报。新增 profile 时跑一遍自洽性测试。

### 仍未验

- 同一条片里多镜共用一套 profile 的一致性（每套只出过一条）。
- 16:9：六套的 `aspect_16_9` 施工说明未出片验证。
- **PES 那套要 Seedance 画真人的手做精细动作**——手是 AI 视频最容易崩的部位，这条风险只有真跑才知道。
- **闸门与串词纪律**：`evals.json` 7 条考卷。
