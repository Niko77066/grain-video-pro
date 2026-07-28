# 引擎知识包 · AI 纸拼贴 b-roll（halftone paper-collage）

> **本页是指针，不是内容。** 完整链路（美学标准、三闸门、色彩语义、画幅参数、引擎绑定、四条 prompt 模板、QA 判据、写回 IR）在 **`.claude/skills/collage-broll/SKILL.md`**。
>
> 为什么只留指针：同一套 prompt 模板存两份，就有两个真相源。浣熊片那段 `Retro 16-bit PIXEL-ART paper-collage animation, aged-yellow #C9A876 paper grain…` 之所以能变异成做旧报纸风，正是因为它没有唯一出处、靠抄上一条片的 film.json 传播。**模板唯一出处 = skill。**

> 何时读我：storyboard 有镜头路由到 `collage-broll`——把一句 ~5s 口播/观点句/抽象概念压成一个**视觉隐喻**的氛围 b-roll。

## 路由要点（够你决定用不用它；决定用了就去读 skill）

- **擅长**：概念、观点句、抽象隐喻的**氛围 b-roll**；高级编辑风、手作温度；垫在口播下。
- **不擅长（改用 HyperFrames）**：精确文字 / 数字 / 法条 / logo / 收尾落款；可逐层编辑的时间线；真人产品口播。要文字就用 HyperFrames **叠层在 collage 上**。
- **要像素质感**：那是另一条链，走 `.claude/skills/pixel-broll/SKILL.md`。两条链**材质语汇互斥，不许串词**。
- **状态**：9:16 ✅ 冒烟（2026-07-17，`openai-78m-logs` / s03b）；16:9 ✅ 冒烟（2026-07-28，`_smoke/broll-skills-2026-07-28`）——**未摊散，但尾段运动量只有全片 27%，横屏偏前重**，排产时把「末件在最后一秒落位」写重些。
- **成本**：每条 = 1 张 GPT-Image + 1 条 Seedance（满价约 $2.7），全进 `ledger.costs`。
- **IR 写法**：`provider: "collage_broll"`。
