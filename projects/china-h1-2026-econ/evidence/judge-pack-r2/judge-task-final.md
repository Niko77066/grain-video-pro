# 隔离评审任务 · node=final

> 你是 Kuleshov 独立评委（G2），与创作者物理隔离：只看下列证据，不接受、不索取任何创作过程解释。

## 评分/评审标准
你是独立评委，只依据给到的证据评审，禁止臆测创作过程。
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
 "notes": {"D1": "..引用..", ...}, "verdict": "pass|fail", "one_line": ".."}

## 证据文件（附给你评审，逐个看）
- 本片 contact sheet（行优先；第 n 格(从1数)时间 = 偏移 + (n-1)*interval_s）: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack/contact-sheet.jpg
- 本片 contact sheet 半步错位版: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack/contact-sheet-offset.jpg
- Golden 基准 contact sheet（并排对照）: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack/golden-contact-sheet.jpg
- 逐镜帧: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack/frames/s01_hook_anchor_0003.46s.jpg
- 逐镜帧: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack/frames/s02_gdp_screen_0010.28s.jpg
- 逐镜帧: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack/frames/s03_city_aerial_0015.35s.jpg
- 逐镜帧: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack/frames/s04_turn_card_0018.95s.jpg
- 逐镜帧: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack/frames/s05_site_aerial_0022.65s.jpg
- 逐镜帧: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack/frames/s06_housing_photo_0025.95s.jpg
- 逐镜帧: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack/frames/s07_street_crowd_0029.56s.jpg
- 逐镜帧: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack/frames/s08_question_anchor_0034.46s.jpg
- 逐镜帧: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack/frames/s09_port_aerial_0040.50s.jpg
- 逐镜帧: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack/frames/s10_containers_photo_0046.14s.jpg
- 逐镜帧: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack/frames/s11_robot_line_0050.94s.jpg
- 逐镜帧: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack/frames/s12_equipment_photo_0054.64s.jpg
- 逐镜帧: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack/frames/s13_output_bars_0058.28s.jpg
- 逐镜帧: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack/frames/s14_overlooked_card_0062.30s.jpg
- 逐镜帧: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack/frames/s15_supermarket_0066.88s.jpg
- 逐镜帧: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack/frames/s16_cpi_card_0072.31s.jpg
- 逐镜帧: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack/frames/s17_close_anchor_0076.62s.jpg
- 逐镜帧: /Users/admin/deeplang/grain-video-pro/.claude/worktrees/finance-video-production-bd1929/projects/china-h1-2026-econ/evidence/judge-pack/frames/s18_end_card_0080.18s.jpg

## 镜头事实清单（id/区间/意图/景别/来源，零创作理由）
[{"id": "s01_hook_anchor", "t": [0.0, 6.91], "intent": "钩子：立住『同一张表上有两组方向相反的数字』——+4.7% 与 −5.7% 同屏对置。", "framing": "主播中景 · 右侧双数字组 · 左下标题条", "provider": "avatar"}, {"id": "s02_gdp_screen", "t": [6.91, 13.65], "intent": "稳的一面：GDP 近 70 万亿、+4.7%，一/二季度 5.0 与 4.3 的落差同屏可见。", "framing": "全屏数据屏 · 季度柱状 + 目标带", "provider": "hyperframes"}, {"id": "s03_city_aerial", "t": [13.65, 17.05], "intent": "把『落在目标区间内』落到具体城市实景上，给数据一次呼吸。", "framing": "城市夜景航拍全景", "provider": "footage"}, {"id": "s04_turn_card", "t": [17.05, 20.84], "intent": "叙事转折点：『但翻到投资和消费，情况反过来了』——用版式做 But 的重音。", "framing": "全屏转折字卡 · 大字", "provider": "hyperframes"}, {"id": "s05_site_aerial", "t": [20.84, 24.46], "intent": "固定资产投资 −5.7%：实拍在建工地给『投资在缩』一个物证面。", "framing": "工地航拍全景 · 左下数据角标", "provider": "footage"}, {"id": "s06_housing_photo", "t": [24.46, 27.44], "intent": "房地产开发投资 −18.0%：从工地全景推到楼体，数字从 −5.7 递进到 −18.0。", "framing": "楼体照片缓推特写 · 大数字", "provider": "image_motion"}, {"id": "s07_street_crowd", "t": [27.44, 31.68], "intent": "社会消费品零售总额只涨 1.3%：人流很密，但增速很薄——画面与数字的反差本身是论点。", "framing": "步行街人流平视 · 右下数据角标", "provider": "footage"}, {"id": "s08_question_anchor", "t": [31.68, 37.24], "intent": "设问：『那百分之四点七，是谁扛起来的？』——全片唯一一次推近，给设问物理重量。", "framing": "主播近景（全片唯一一次推近）", "provider": "avatar"}, {"id": "s09_port_aerial", "t": [37.24, 43.75], "intent": "答案一是外贸：25.47 万亿元、+16.9%，港口作业画面与数据卡同框。", "framing": "港口航拍全景 · 右侧数据卡", "provider": "footage"}, {"id": "s10_containers_photo", "t": [43.75, 48.52], "intent": "拆开外贸：出口 +13.4%、进口 +22.1%——进口跑得更快是本节的暗线。", "framing": "集装箱堆场照片缓推 · 出口/进口双条", "provider": "image_motion"}, {"id": "s11_robot_line", "t": [48.52, 53.36], "intent": "答案二是制造：高技术制造业增加值 +13.3%，产线在动是这条论断的物证。", "framing": "机械臂产线中景 · 左下数据角标", "provider": "footage"}, {"id": "s12_equipment_photo", "t": [53.36, 55.93], "intent": "装备制造业 +9.3%：从产线整体推到单台设备，把『装备』这个词落到具体机器上。", "framing": "激光切割设备特写缓推 · 大数字", "provider": "image_motion"}, {"id": "s13_output_bars", "t": [55.93, 60.63], "intent": "新动能产量：机器人 +28.0%、锂电 +39.3%、3D 打印 +48.5%（第三条只上屏不口播）。", "framing": "全屏产量增速条 · 三条", "provider": "hyperframes"}, {"id": "s14_overlooked_card", "t": [60.63, 63.97], "intent": "第二次转折：『这份表里还有一行，容易被跳过』——全片唯一带主观色彩的一句。", "framing": "全屏转折字卡 · 大字", "provider": "hyperframes"}, {"id": "s15_supermarket", "t": [63.97, 69.78], "intent": "居民人均可支配收入实际 +4.2% vs 经济增速 +4.7%：收入那条短一截，跑输写在画面上。", "framing": "超市生鲜区中景 · 右侧对比条", "provider": "footage"}, {"id": "s16_cpi_card", "t": [69.78, 74.84], "intent": "居民消费价格 +1.0%，离全年 2% 目标还差不少——需求端偏冷的第二个证据。", "framing": "全屏物价对照卡 · 实际 vs 目标", "provider": "hyperframes"}, {"id": "s17_close_anchor", "t": [74.84, 78.4], "intent": "收束前半句：『外需和制造这一棒已经跑起来了。』", "framing": "主播中景收尾", "provider": "avatar"}, {"id": "s18_end_card", "t": [78.4, 81.96], "intent": "落在未决问题上：『下半年要看的，是内需能不能接得住。』并给出判据三指标。", "framing": "全屏结论字卡 · 右侧三指标", "provider": "hyperframes"}]

## 合同带宽内调整（评审时须知悉）
{}


## 交回
只输出上面 schema 规定的一个 JSON 对象。扣分/判断必须引用镜头 ID 或时间码，无引用的判断无效。
