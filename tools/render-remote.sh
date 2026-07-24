#!/usr/bin/env bash
# 渲染机 HTTP 渲染：HyperFrames composition 目录 → MP4（服务端 GPU 渲染）。
# 用法: tools/render-remote.sh <composition目录> <输出mp4> [hyperframesVersion] [quality]
#   例:  tools/render-remote.sh projects/x/compose out/final_remote.mp4 0.7.3 high
# 前提（缺一必失败，契约见 docs/render-http-api.md）：
#   1) 出口 IP 必须是 13.158.136.168（VPN 东京节点）——脚本自查；
#   2) .env 里有 FFMPEG_RENDER_HTTP_TOKEN（飞书环境变量表 ffmpeg-runner 段，生产值）；
#   3) 素材走 CDN URL，不打进 tar（本地相对路径资产会 404）。
set -euo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$here/.env"

dir="${1:?用法: render-remote.sh <composition目录> <输出mp4> [version] [quality]}"
out="${2:?缺输出路径}"
ver="${3:-0.7.3}"
quality="${4:-high}"
: "${FFMPEG_RENDER_HTTP_TOKEN:?缺 FFMPEG_RENDER_HTTP_TOKEN（见飞书环境变量表 ffmpeg-runner 段）}"

RENDER_URL="http://34.212.107.38:7300/render/hyperframes"

egress="$(curl -s -4 --max-time 8 https://api.ipify.org || true)"
if [ "$egress" != "13.158.136.168" ]; then
  echo "✗ 出口 IP=$egress ≠ 13.158.136.168 —— VPN 切东京节点后重试（安全组只放行该源 IP）" >&2
  exit 1
fi

stamp="$(date +%Y%m%d-%H%M%S)"
tarfile="$(mktemp -t render-project)-.tar.gz"
tar -czf "$tarfile" -C "$dir" .
key="kuleshov/render-jobs/${stamp}-$(basename "$dir").tar.gz"
tar_url="$("$here/tools/oss-upload.sh" "$tarfile" "$key")"
echo "· tar 已上传: $tar_url" >&2

hdr="$(mktemp -t render-headers)"
http_code=$(curl -s -4 --max-time 600 -X POST "$RENDER_URL" \
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
