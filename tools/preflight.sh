#!/usr/bin/env bash
# 能力预检（P1-5，2026-07-21 升级计划）：开工即产出各通路就绪状态，
# storyboard 不得把镜头路由到 missing 的 provider——把"最后一刻发现缺凭据然后静默绕路"
# （Codex 空调片：缺渲染机 token 于是本机渲染还自称未降级）消灭在花钱之前。
# 输出 <project>/capabilities.json（不含任何秘密值，只有 ready/missing）。
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="${1:-.}"
ENV_FILE="$REPO/.env"
# worktree 无 .env 时回退主仓（.env gitignored，只活在主仓）
if [[ ! -f "$ENV_FILE" ]]; then
  MAIN="$(git -C "$REPO" rev-parse --path-format=absolute --git-common-dir 2>/dev/null | xargs dirname 2>/dev/null || true)"
  [[ -n "${MAIN:-}" && -f "$MAIN/.env" ]] && ENV_FILE="$MAIN/.env"
fi

has_key() {  # .env 里该键存在且非空
  [[ -f "$ENV_FILE" ]] && grep -qE "^${1}=..*" "$ENV_FILE"
}
status_key() { has_key "$1" && echo ready || echo missing_credentials; }
status_cmd() { command -v "$1" >/dev/null 2>&1 && echo ready || echo missing; }

docker_status=missing
command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1 && docker_status=ready

film_ir=missing
{ command -v kuleshov-ir >/dev/null 2>&1 || [[ -x "$REPO/film-ir/.venv/bin/kuleshov-ir" ]]; } && film_ir=ready

cat > "$PROJECT/capabilities.json" <<JSON
{
  "schema": "capabilities@1",
  "checked_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "minimax_tts": "$(status_key MINIMAX_MUSIC_API_KEY)",
  "apihub_news": "$(status_key API_HUB_TOKEN)",
  "pexels": "$(status_key PEXELS_API_KEY)",
  "pixabay": "$(status_key PIXABAY_API_KEY)",
  "kimi_judge": "$(status_key KIMI_API_KEY)",
  "remote_render_http": "$(status_key FFMPEG_RENDER_HTTP_TOKEN)",
  "docker_render": "$docker_status",
  "ffmpeg": "$(status_cmd ffmpeg)",
  "film_ir_cli": "$film_ir"
}
JSON
cat "$PROJECT/capabilities.json"
