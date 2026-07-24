# 反主观翻译总表

一个感受词 → 五种引擎方言，全部可执行。**对标拆解（`/benchmark-breakdown`）的产出落进这张表**；风格包引用总表条目子集。

行状态：`[继承]` 来自蓝图/已验证实践；`[假设]` 未经出片验证的推理初值——用过之后要么转正要么改数。

| 感受词 | 剪辑 | GSAP | Seedance 提示词 | 图片动效 | 数字人 | 状态 |
|---|---|---|---|---|---|---|
| 干脆 / snappy | 平均镜头 ≤ 2.5s，硬切为主 | `power4.out`，0.2–0.4s | quick whip pan, snap zoom, fast cut rhythm | Ken Burns ≤ 3s，位移 ≥ 8% | 语速 165wpm+，手势频度高 | [继承] |
| 沉稳 / 权威 | 平均镜头 4–6s，切点只落句读 | `power2.inOut`，0.5–0.8s，位移小 | slow dolly in, locked-off tripod, steady composition | 时长 4–6s，位移 3–5% | 语速 ≤ 140wpm，停顿明显 | [假设] |
| 温暖 / 生活流 | 让动作做完再切，容忍 6s+ 长镜 | 淡入为主，0.8–1.2s | handheld subtle sway, natural window light, medium shot | crossfade 0.5s，暖色 LUT | 语气软，语尾下沉 | [假设] |
| 紧迫 / breaking | 剪辑密度 30+ cuts/min，J-cut 抢拍 | 入场 0.15–0.25s，stagger 0.05s | fast tracking shot, crash zoom, rapid subject motion | 禁用（太慢，改版式卡） | 语速顶格，重音密集 | [假设] |
| 静谧奢华 / nocturne | 平均镜头 4–6s，J-cut 默认，切点落句读 | `power2.out` 0.6–0.9s，透明度+小位移，禁弹跳 | slow dolly in, macro close-up, shallow depth of field, single soft top light, dark ambience, amber glass reflections | 4–6s，位移 3–5%，暗角+暖琥珀 LUT | 本行风格不用数字人 | [假设] |

## 使用规则

1. script / storyboard 里出现感受词，必须能在本表找到行；找不到 → 先加行（标 `[假设]`）再用；
2. 拉片验证或成片被用户打高分的行 → 状态转 `[已验证]` 并记来源片名；
3. 风格包 playbook 只**引用**行名 + 覆写差异参数，不整行复制（防止走样）。
