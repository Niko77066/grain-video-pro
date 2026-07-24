# 渲染机 HTTP 渲染接口 —— 连接与测试方案

> 目标：从调用方直连渲染机的 GPU 渲染能力，把 HyperFrames composition（tar.gz）渲成 MP4。
> 渲染核 = HyperFrames（宿主侧 `packages/ffmpeg-runner/src/runner/http-render.ts` 同源，与 BullMQ 队列共用同一核）。
> **渲染机地址由环境提供**（`RENDER_URL`）——交付到开发环境时指向那边专门的渲染机；本文与 `tools/render-remote.sh` **均不假设任何特定出口 IP / 主机**（去本机耦合 2026-07-24）。

## 0. 硬前提（不满足则一定失败，先自查）

| 项 | 值 | 说明 |
|---|---|---|
| 渲染机地址 | `$RENDER_URL`（环境变量，如 `http://<render-host>:7300/render/hyperframes`） | 由开发环境/宿主提供；渲染机在其端口监听 |
| 接口路径 | `POST /render/hyperframes` | 仅此路径 + POST；其余回 404（一般已含在 `$RENDER_URL` 里） |
| 鉴权 | `Authorization: Bearer <token>` | token = 渲染机的 `FFMPEG_RENDER_HTTP_TOKEN`（由环境注入，勿硬编码） |
| 网络可达 | 调用方能连到 `$RENDER_URL` | 若渲染机有访问控制（IP 白名单/内网），由**部署环境**保证可达——不是本包的假设 |

> 早期本包曾自查"出口 IP=某固定值"（作者本机 VPN 白名单）——已移除。可达性交部署环境。

## 1. token 注入（不要硬编码进脚本）

```bash
export RENDER_URL='http://<render-host>:7300/render/hyperframes'
export FFMPEG_RENDER_HTTP_TOKEN='<渲染机 token，由环境提供>'
```

## 2. 分阶段测试（从便宜到贵，逐步排除问题）

### 阶段 A：连通性（无需 token、无需项目）
```bash
curl -s --max-time 15 -X POST "$RENDER_URL" -w '\n[http_code=%{http_code} connect=%{time_connect}s]\n'
```
- 期望：`{"error":"unauthorized"}` + `401`，connect 毫秒级 → **网络通、server ready、鉴权在工作**。
- 若超时/连不上 → `RENDER_URL` 不对，或渲染机没起，或部署环境网络/访问控制未放行。

### 阶段 B：token 是否正确（带 token、故意不给项目）
```bash
curl -s --max-time 15 -X POST "$RENDER_URL" \
  -H "Authorization: Bearer $FFMPEG_RENDER_HTTP_TOKEN" \
  -H "Content-Type: application/json" -d '{}' -w '\n[http_code=%{http_code}]\n'
```
- 期望：`400` + `{"error":"projectTar.url is required in JSON mode"}` → **token 正确**（已过鉴权、进到参数校验）。
- 若还是 `401` → token 错了，重新注入。

### 阶段 C：真渲染（需要一个可被渲染机 GET 到的项目 tar.gz）

HyperFrames 项目目录（含 `index.html` composition + 自带 custom fonts；素材用 HTML 里的 CDN URL，**不打进 tar**）：
```bash
tar -czf project.tar.gz -C <你的项目目录> .
# 把 project.tar.gz 传到渲染机能匿名 GET 的地址（公开 URL / 预签名 GET URL）
```

**方式一：成片直接回传（最简单，先用这个验通路）**
```bash
curl -s --max-time 600 -X POST "$RENDER_URL" \
  -H "Authorization: Bearer $FFMPEG_RENDER_HTTP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hyperframesVersion":"0.7.3","projectTar":{"url":"https://<project.tar.gz 地址>"}}' \
  -o out.mp4 -D headers.txt
# 成功：out.mp4 是成片，headers.txt 有 content-type: video/mp4 + x-render-duration-ms
# 失败：out.mp4 其实是 JSON 错误体，打开看 error/logTail
```

**方式二：成片旁路上传到你的存储（生产推荐，不占响应体）**
```bash
curl -s --max-time 600 -X POST "$RENDER_URL" \
  -H "Authorization: Bearer $FFMPEG_RENDER_HTTP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hyperframesVersion":"0.7.3","projectTar":{"url":"https://<project.tar.gz 地址>"},
       "output":{"url":"https://<你的预签名 PUT 上传地址>"}}'
# 成功：回 200 + {"output":{"url":...},"probed":{durationSec,width,height,hasAudio}}
```

`tools/render-remote.sh` 把上面 tar 打包 + 上传（默认 `oss-upload.sh`，可 `RENDER_UPLOAD_CMD` 覆写）+ POST 一步做完。

## 3. 请求参数全集（JSON body 字段）

| 字段 | 必填 | 默认 | 说明 |
|---|---|---|---|
| `hyperframesVersion` | ✅ | 无 | 填 `0.7.3`（当前生产版本）；调用方最清楚自己 composition 针对哪版 |
| `projectTar.url` | ✅(JSON模式) | 无 | 项目 tar.gz 的 GET URL，渲染机流式拉取 |
| `output.url` | ❌ | 无 | 给了→渲染机 PUT 上传成片；不给→MP4 从响应体流式回传 |
| `quality` | ❌ | `high` | `draft` / `standard` / `high` |
| `composition` | ❌ | 全片 | 只渲某个子 composition（相对项目根） |
| `variablesJson` | ❌ | 无 | composition 变量的 JSON 字符串（配 `--strict-variables`） |
| `timeoutMs` | ❌ | 服务端上限 | 渲染超时；传了也不能超过服务端 `httpRenderMaxTimeoutMs` |
| `protocolTimeoutMs` | ❌ | 无 | CDP 协议超时 |
| `disableStreamingEncode` | ❌ | `true` | Grain 生产默认禁 streaming encode |
| `lowMemoryMode` | ❌ | 无 | 低内存模式 |
| `browserGpuMode` | ❌ | 有 NVIDIA→`hardware`，否则`software` | `hardware`/`software`/`auto`（浏览器 WebGL 光栅化） |
| `gpu` | ❌ | `false` | NVENC 编码；数据中心卡 probe 可能失败，确认可用再开 |

> **raw 直传模式**（不想托管 tar 时）：`Content-Type` 用非 JSON（如 `application/gzip`），body 直接是 tar.gz 字节，上面参数改走 **query string**，输出地址走 `?outputUrl=` 或请求头 `X-Output-Url`。

## 4. 响应码对照

| HTTP | 含义 | 处理 |
|---|---|---|
| `200` | 成功 | 有 output.url→JSON 元数据；否则响应体是 MP4 |
| `400` | 参数非法 | 看 `error`：缺 `hyperframesVersion` / 缺 `projectTar.url` / 布尔或枚举 typo（如 `gpu=flase` 会被拒，不静默兜底） |
| `401` | 鉴权失败 | token 缺失或错误 |
| `404` | 路径/方法错 | 确认 `$RENDER_URL` 指向 `POST /render/hyperframes` |
| `422` | composition 渲染失败 | 业务失败，看 `exitCode`/`timedOut`/`logTail`——composition 本身问题，改后重试 |
| `503` | 渲染机忙 | 并发闸满载（默认并发 1），退避后重试 |
| `500` | 内部错误 | 看 `error`（下载 tar / 转码 / 上传等基建失败） |

## 5. 排查速查

| 现象 | 最可能原因 |
|---|---|
| curl 超时、连不上 | `RENDER_URL` 不对 / 渲染机没起 / 部署环境网络或访问控制未放行 |
| 秒回 401 | token 没带 / 带错 |
| 400 缺字段 | body 不是合法 JSON 对象，或漏了 `hyperframesVersion` / `projectTar.url` |
| 422 + logTail | composition 渲染失败（业务问题），不是通路问题 |
| 拉不到 tar / 500 | `projectTar.url` 渲染机 GET 不到（非公开 / 需要鉴权头 / 网络不通） |
