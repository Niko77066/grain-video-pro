#!/usr/bin/env bash
# 渲染机 HTTP 渲染：HyperFrames composition 目录 → MP4（服务端渲染）。
# 用法: RENDER_URL=<渲染机端点> tools/render-remote.sh <composition目录> <输出mp4> [hyperframesVersion] [quality]
#   例:  RENDER_URL=http://<render-host>:7300/render/hyperframes \
#         tools/render-remote.sh projects/x/compose out/final.mp4 0.7.3 high
#
# **渲染机地址由环境提供**——交付到开发环境时指向那边专门的渲染机；本脚本不假设任何特定
# 出口 IP / 主机（去本机耦合 2026-07-24）。契约见 docs/render-http-api.md。
# 前提：
#   1) RENDER_URL 指向渲染机的 /render/hyperframes 端点（环境变量，必填）；
#   2) FFMPEG_RENDER_HTTP_TOKEN 鉴权 token（环境变量，由环境/宿主注入）；
#   3) 素材走 CDN URL，不打进 tar（本地相对路径资产会 404）；
#      tar 上传器默认 tools/oss-upload.sh，可用 RENDER_UPLOAD_CMD 覆写成开发环境的上传方式。
set -euo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"
# .env 存在就加载（本地开发用）；开发环境/宿主直接从进程环境注入，无需 .env。
# shellcheck disable=SC1091
[ -f "$here/.env" ] && source "$here/.env"

dir="${1:?用法: render-remote.sh <composition目录> <输出mp4> [version] [quality]}"
out="${2:?缺输出路径}"
ver="${3:-0.7.3}"
quality="${4:-high}"
: "${RENDER_URL:?缺 RENDER_URL——设为开发环境渲染机的 /render/hyperframes 端点（如 http://<host>:7300/render/hyperframes）}"
: "${FFMPEG_RENDER_HTTP_TOKEN:?缺 FFMPEG_RENDER_HTTP_TOKEN（渲染机鉴权 token，由环境注入）}"

stamp="$(date +%Y%m%d-%H%M%S)"
tarfile="$(mktemp -t render-project)-.tar.gz"
tar -czf "$tarfile" -C "$dir" .
key="kuleshov/render-jobs/${stamp}-$(basename "$dir").tar.gz"
# tar 上传器：默认 oss-upload.sh（需 S3 凭据）；开发环境可 RENDER_UPLOAD_CMD 覆写。
upload="${RENDER_UPLOAD_CMD:-$here/tools/oss-upload.sh}"
tar_url="$("$upload" "$tarfile" "$key")"
echo "· tar 已上传: $tar_url" >&2

hdr="$(mktemp -t render-headers)"
http_code=$(curl -s --max-time 600 -X POST "$RENDER_URL" \
  -H "Authorization: Bearer $FFMPEG_RENDER_HTTP_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"hyperframesVersion\":\"$ver\",\"projectTar\":{\"url\":\"$tar_url\"},\"quality\":\"$quality\"}" \
  -o "$out" -D "$hdr" -w '%{http_code}')

ctype="$(grep -i '^content-type:' "$hdr" | tr -d '\r' | awk '{print $2}')"
if [ "$http_code" = "200" ] && [[ "$ctype" == video/mp4* ]]; then
  dur_ms="$(grep -i '^x-render-duration-ms:' "$hdr" | tr -d '\r' | awk '{print $2}' || true)"
  echo "✓ 渲染成功: $out（服务端耗时 ${dur_ms:-?}ms）" >&2
  exit 0
fi
echo "✗ 渲染失败 http=$http_code（响应体如下，503=并发闸满退避重试；422=composition 业务失败看 logTail）" >&2
cat "$out" >&2; echo >&2
exit 1
