# 引擎知识包 · 生成型 b-roll（八套材质语言）

> **本页是指针，不是内容。** 完整链路（三闸门、画幅几何、引擎绑定、提示词模板、QA 判据、批次总览、写回 IR）在 **`.claude/skills/broll-studio/SKILL.md`**；逐套的材质语汇、首帧规则、缝合纪律、失败标准、状态与额外工序在 `profiles/<id>.json`。
>
> 为什么只留指针：同一套流程存两份，就有两个真相源。浣熊片那段 `Retro 16-bit PIXEL-ART paper-collage animation, aged-yellow #C9A876 paper grain…` 之所以能变异成做旧报纸风，正是因为它没有唯一出处、靠抄上一条片的 film.json 传播。**模板唯一出处 = profile；流程唯一出处 = broll-studio。**
>
> 2026-07-28 起，原来的三处知识（`pixel-broll` / `collage-broll` 两个独立 skill + `broll-studio` 六个 profile）统一成 **一套引擎 + 八个 profile**。那两个 skill 名仍可按名调用，但已经是指针壳。

> 何时读我：storyboard 有镜头路由到任一生成型材质语言——把一句 ~5s 口播 / 观点句 / 抽象概念压成一个**视觉隐喻**的镜头。

## 路由要点（够你决定用不用它；决定用了就去读 skill）

```bash
python3 tools/broll-profile.py route "<文稿类型>"   # 镜头级选型（首选 + 备选 + tie-break）
python3 tools/broll-profile.py status              # 逐套冒烟状态，**状态的唯一出处**
```

- **擅长**：概念、观点句、抽象隐喻的氛围 b-roll；角色重演（版权规避位）；机制/因果图解；数据实物化；情绪落点。**八套各有所长，选型问「要用什么材质说这句话」。**
- **不擅长（改用 HyperFrames）**：精确文字 / 数字 / 法条 / logo / 收尾落款；可逐层编辑的时间线；真人产品口播。要文字就用 HyperFrames **叠层在生成画面上**。
- **同片单一**：一条片只准一种生成风格，且不许串别的 profile 的材质语汇（`broll-profile.py lint` 是机器门）。
- **成本**：每条 = 1 张 GPT-Image + 1 条 Seedance（满价约 $2.7），带附加静帧槽位的多算一张图；全进 `ledger.costs`。
- **IR 写法**：由 profile 的 `ir_writeback` 声明（`collage` 仍是 `provider: "collage_broll"`，`pixel` 与六套是 `provider: "seedance"`——历史契约，不许为整齐去改）。
