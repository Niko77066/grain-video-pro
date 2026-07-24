# 引擎知识包 · 服务器渲染（渲染机 HTTP API）

> 何时读我：⑨ compose 渲染阶段选择渲染通道时；新风格包定字体方案时（第 2 节纪律）。
> 契约与排查全文：`docs/render-http-api.md`；一键脚本：`tools/render-remote.sh`。

## 1. 现状（2026-07-20 实测）

- **通路 ✅**：A（连通）/B（token）/C（真渲染）三阶段全过；65.7s 竖屏真片服务端 129s 渲完。
- **版本 ✅**：`hyperframesVersion` 按请求装（0.7.3 / 0.7.57 / 0.7.60 实测均可），与本地版本对齐不是问题。
- **切默认 ⏸ 未达帧级一致门**：openai-78m-logs 双跑对比 SSIM All 0.981 / PSNR 35.5（min 30.4）。
  差异根因＝**系统字体依赖**：composition 用 `local("PingFang SC")`/`local("Songti SC")`，Linux 渲染机
  落 font-kit 兜底，字宽微差 → **长标题换行点漂移**（法规卡《办法》标题实证）。这是内容级差异，
  不许当噪声吞掉。

## 2. 字体纪律（新片硬规则）

**compose 一律自带 woff2 字体**（uk-argentina-feud 模式：`compose/assets/fonts/*.woff2` + `@font-face`
指向相对路径），**禁止 `local("系统字体")` 承担正文/标题**——本地与渲染机才会用同一套字形。
`local()` 只允许作为 woff2 之后的最末兜底。

## 3. 切默认前的验收（下一部片执行）

1. 新片 compose 按第 2 节字体纪律构建；
2. 同一 composition 本地 + 渲染机双跑，`ffmpeg ssim/psnr` 全片对比 + 关键版式帧目检（换行/安全区）；
3. 通过 → 切服务器渲染为默认，记 `ledger.decisions`；本地渲染降为兜底通道。

## 4. 使用速记

```bash
tools/render-remote.sh <compose目录> <输出.mp4> [version默认0.7.3] [quality默认high]
# 前提：环境提供 RENDER_URL（渲染机端点，如 http://<host>:7300/render/hyperframes）+ FFMPEG_RENDER_HTTP_TOKEN；无本机 IP 假设
# 503=并发闸满（并发1），退避重试；422=composition 业务失败看 logTail
```

素材引用规则：tar 内相对路径资产实测可用（11M 级）；重媒体建议走 CDN URL 减小 tar。
