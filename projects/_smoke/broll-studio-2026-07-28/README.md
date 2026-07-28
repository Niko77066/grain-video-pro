# 冒烟：broll-studio 六套材质语言（2026-07-28）

不是一条片，是六套 profile 的首次端到端验证。**每套的选题都按它自己的 `best_for` 定**，不是同一句话套六遍——冒烟要验的是「这套材质在它擅长的内容上成不成立」。

全部 9:16 / 10s / 720p。提示词一律经 `tools/broll-profile.py render` 渲染（不手抄模板），渲染时自动过串词 lint。

| profile | 选题 |
|---|---|
| `object-theatre` | AI 不是替你工作的员工，是放大问题的镜子 |
| `technical-diagram` | Agent 不是模型外面套个提示词，是模型／记忆／工具／反馈的循环 |
| `clay-miniature` | 工具越堆越多，人成了被自己工具堵住的那根管子 |
| `felted-wool` | 所有工具都在帮你更快，没有一个问你累不累 |
| `popup-book` | 一条选题从灵感走到分发，每一层都会掉人 |
| `toy-world` | 好产品不是给更多按钮，是让复杂模块自己拼起来 |

- 提示词：`prompts.json`（gate2 / gate3 逐条，popup-book 多一条 gate2_first_frame）
- 留痕：`runs/`（img-state 7 张 + img-state-v2 重生 1 张 + sd-state 6 条，含 x-oneapi-request-id）
- 证据：`evidence/`（gate2 contact sheet、逐条 QA JSON 与 contact sheet、summary.json）
- 成本：8 张 GPT-Image-2 + 6 条 Seedance 10s ≈ **$19**

## Gate 2 拦下的一条

**`toy-world` v1 的尾帧模块没有对接**，而它的隐喻是「模块自己拼起来」。Image 2 必须是**完成态**——否则 Gate 3 会朝着「没拼上」组装，成片的最后一拍会和文案相反。v1 保留在 `anchors/toy-world_last_raw.png` 供对照，v2（模块贴合、连接器落位）才是用于生成的尾帧。

这就是 Gate 2 存在的理由：一张图的钱挡住一条片的钱。

## 首帧规则确实分两种

五套走 `empty_surface`（lavfi 纯色场）；`popup-book` 走 `closed_book`——它的 Gate 2 出了**两张**图（合上的书 + 展开的世界）。profile 里 `first_frame.kind` 这个字段不是注释，是引擎按它分支的。

## Gate 3 结果

| profile | 判定 | 尾段/全片运动量 | 备注 |
|---|---|---|---|
| `object-theatre` | ✅ pass | 43% | 方块堆叠→顶针→放大镜落下→**末秒裂缝在镜下裂开并延伸到桌面**，payoff 落在末拍 |
| `technical-diagram` | ✅ pass | 36% | 底板→导轨→核心→记忆鼓→工具臂→**反馈管在模块装完之后才延伸**→信号脉冲。因果顺序正确 |
| `clay-miniature` | ✅ pass | 32% | 管子滚入→角色跳入挥手→压进管口→漏斗落下→工具块逐个落入→末帧挤压。无变脸、无多肢 |
| `felted-wool` | ✅ pass | 27% | 桌子→人物伏案→两个小工具角色左右冲刺（带毛纤维速度线）→杯子静静落位→她侧头。刚过线 |
| `popup-book` v1 | ❌ fail | 16% | **前 1/3 就全部展开，后 2/3 只剩灯泡微亮**。根因见下 |
| `popup-book` v2 | ❌ 9%（带 advisory）→ 人眼放行 | 9% | 修模板后展开延续到第 7 帧；判红是判据的中段爆发型误报，判定理由见 `gate3-qa.md` |
| `toy-world` | ✅ pass | 29% | 主机落台→珊瑚色楔块旋转对接→石板色楔块对接→连接器落入顶部→末帧＝确认静帧 |

### popup-book 判红的根因：模板自己在要一个 hold

原 gate3 模板末句是 `Preserve the final layered composition from Image 2 and **end with a stable theatrical hold**.`——**它把死尾直接写进了提示词**。纸艺机械本来就展开得快，再加一句"以稳定的舞台定格收尾"，必然前重后空。

已修订为「铺满整条 clip、每层依次缓慢升起、中心主体在最后一秒升起」，并把这条写进该 profile 的 `failure_criteria`。复验用**同一对首尾帧、只换 prompt**（单变量）。结果：**视觉上修好了**（展开延续到第 7 帧，漏斗后段才出现），但**机器判更红（9%）**——因为中段书本翻开的爆发把全片中位从 1.76 抬到 7.03，分母变大。

v2 尾段绝对 YDIF **0.657，是七条测试片里第二高的**（通过的 toy-world 只有 0.194）。试过两种更抗爆发的分母（前段 p60、截尾中位 p75）都救不回来——**比值家族分离不了这个案例**。

**没有为此放松阈值**：唯一能分离的是加「尾段绝对量」或门，但可用样本只有 2 条，按这个校准等于拟合噪声，且绝对量会被颗粒/闪烁抬高。判据不动，只加 advisory 提示人眼复核（`tools/clip-qa.py` 常量处记了完整数据与失败的尝试）。人眼判定与理由写在 `gate3-qa.md`。

### 三条通用观察

1. **实产时长六条全是 10.042s**（请求 10s），与 pixel/collage 两链一致。
2. **静帧 → 视频存在风格漂移**：`technical-diagram` 的静帧是手绘感编辑风技术插画，视频更像等距 3D 渲染资产。Seedance 会把插画质感往三维推——需要精确保持平面插画质感的场合要留意。
3. **`felted-wool` 长成了一整间屋子**（墙、窗、盆栽），比 profile 说的「one felted character and 2–4 felted objects」丰富得多。不算失败，但说明该 profile 的 Composition 段对场景规模约束不足。

### 链路健壮性

本轮实测撞到 **3 次 URLError + 1 次 oss-upload SSL**：前者被上一轮修的 soft-fail 全部接住（以前一次断连整轮暴毙），后者暴露上传函数还没有重试——**已补**（同一类缺口的第三处）。另外 `gpt-image.py` 出图时撞 shell 超时，逐条落盘让 6/7 张的 request-id 全部保住，续跑只补了缺的那一张。


---

## 后续：按参考实图重写（同日）

用户看片后指出静帧质量不及预期，并要求**以参考链接为准、不要照抄给定提示词**。逐个打开参考的**画面**（不只是文案）之后，五套推倒重写：

| profile | 偏差 | 依据 |
|---|---|---|
| `object-theatre` | 原提示词那句 `no human hands` **与 PES 直接冲突**——手是这门语言的动词；且原隐喻根本没有物品替身，只是把东西摆在一起 | PES 实读：棒球切开变成骰子，转换发生在那一刀上，真人手全程在画面里 |
| `toy-world` | 两版都错：v1 淡雅极简产品渲染、v3 被我做成了 Brawlidays 的木头玩具火车 | Cash App 实图：素白舞台 + 唯一电光绿、石膏台座与玻璃展柜、亚克力果冻／充气软胶／哑光石膏／铬跳材质、色溢到白面 |
| `felted-wool` | 通用可爱娃娃 + 甜柔粉 + 全景深 | Fuzzy Feelings 实图：具体老人、细金属丝眼镜、斜纹呢与针织、绣线五官、灰调降饱和、浅景深 + 颗粒 |
| `technical-diagram` | 牛皮纸专利图路线被用户否掉 | Vectary 实读（真实产品的动画爆炸视图）+ IBM 实看（单一强色满底 + 网格 + 发丝白线 + productive motion） |
| `popup-book` | 三色调和配色被判「不好看」 | 改走 collage 的色彩纪律：一块按语意选的强平色场 + 暖白纸 + 唯一点色（**只借色彩纪律，不借材质语汇**） |

`clay-miniature` 未改动——用户认可。

**因此本轮的视频结果只对 `clay-miniature` 仍然有效**，其余五套的成片对应旧模板，已在 skill 状态节标注为「静帧已验 / 视频待验」。

重写轮成本：12 张 high-quality 静帧（$1 量级），未再跑视频。
