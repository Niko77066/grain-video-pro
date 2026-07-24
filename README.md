# Kuleshov — 多源视频生产能力包（外挂）

一套 **harness 无关**的自动视频生产能力：知识（风格包 + 十阶段 SOP）+ 契约（Film IR + 风格合同 + 门禁）+ 工具（CLI / 实测层 / 评委）。设计成被**宿主 agent harness**（如团队自研 harness / Codex / Claude Code）驱动——本仓不含常驻编排层，编排（主循环、subagent 派发、任务调度）由宿主提供。

- 生产 SOP：`.claude/skills/produce/SKILL.md`（十阶段，**默认端到端自主**，质量靠 G1 硬门 + G2 隔离评委卡门回炉）。
- 唯一真相源：每片 `projects/<片名>/film.json`（Film IR）；一切读写走 `kuleshov-ir` CLI。
- 铁律与品味宪法：根目录 `CLAUDE.md`。

## 宿主 harness 怎么驱动它

1. 读 `produce/SKILL.md` 作为分阶段 SOP（brief→research→…→deliver）。
2. IR 读写 / 门禁：调 `kuleshov-ir <read|patch|validate|execute>`（**结构化 JSON 出 stdout + 退出码**，语言无关的集成缝）。
3. 花钱的生成动作（出图 / Seedance / TTS / 音乐 / 检索 / 渲染）：**由宿主的 provider 工具执行**——film-ir adapters（`film_ir/execute/`）负责把 IR 镜头翻译成 provider 请求方言，真调用交宿主（不在容器内持有 key）。
4. 评委（品味/质量门）：`tools/judge/` **去模型化**——`build_evidence_pack` 出证据 → `judge.py --task` 出题 → **宿主派发隔离 subagent 打分**（用宿主模型）→ `judge.py --finalize` 阅卷。

## 目录清单：什么可移植、什么本地/组织/宿主特定

| 类别 | 内容 | 交付说明 |
|---|---|---|
| **可移植知识** | `styles/`（playbook + `contract.json`，含 whiteboard 兜底）、`.claude/skills/produce/`（SOP + `references/`）、`.claude/skills/rednote-mentor/`、`CLAUDE.md`、`docs/` | 核心资产，纯文本，任何 harness 直接消费 |
| **可移植工具** | `film-ir/`（`kuleshov-ir` CLI + 门套件）、`tools/kuleshov-lint.py`、`tools/measure-render.py`、`tools/judge/`（去模型、无 key）、`tools/preflight.sh` | Python/CLI；依赖见下「前置」 |
| **本地-dev / 自带-key** | `.env` 里的 provider key（见 `.env.example`）：TTS/音乐/Seedance/检索 | 本地跑通用；**交付给宿主时这些由宿主 provider 工具注入，容器内不持有** |
| **⚠ 组织基建（不可移植）** | `tools/render-remote.sh`（焊死组织 VPN 出口 IP + 私有渲染机 + `FFMPEG_RENDER_HTTP_TOKEN`）、`tools/oss-upload.sh`（组织 S3） | 宿主用自己的渲染器/存储替代；渲染核本身是 HyperFrames（宿主侧同源） |
| **宿主特定（Claude Code）** | `.claude/settings.json` 的 film.json 直写拦截 hook（只在 Claude Code 生效）、`.git/hooks/post-checkout` 的 `.env` 软链 | 可移植的等价保证 = 「`kuleshov-ir patch` 是 film.json 唯一合法写入口」这条契约 + CI 校验，不靠 hook |
| **一次性示例（可弃）** | `projects/*`（已交付样片作参考；mp4/wav gitignored）。`projects/uk-argentina-feud/scripts/` = 死脚本（硬编码到已删 worktree，**非管线/非包的一部分**，见其 README） | 参考用；不是可复用能力 |

## 前置（可移植工具的运行环境）

- Python 3.12；`pip install -e film-ir`（装 `kuleshov-ir`，依赖 pydantic/click）；`pip install -r tools/requirements.txt`（numpy，供 measure-render）。
- PATH 上：`ffmpeg` / `ffprobe`（可用环境变量 `FFMPEG`/`FFPROBE` 覆盖）、`node`/`npx`（HyperFrames 合成）、`git`；可选 `docker`（本地渲染兜底）。
- 凭据：见 `.env.example`（本地-dev）；宿主环境由 harness 注入。

## 现状与边界

- **风格包形态**（风格包 vs 拆 style-skill+contract）本版**保留现有风格包形态**——未出片验证前不赌哪种更好。
- `meme-ledger` 风格包**暂禁用**（未完成，在 `styles/_disabled/`）。
- 与 grain harness 的具体集成（打包成 grain step-skill、provider 走 grain 原生工具、发布三件套/封印）见 `docs/grain-delivery-plan.md`——那是宿主侧的集成工作，不在本包内实现。
