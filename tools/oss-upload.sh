#!/usr/bin/env bash
# 上传本地资产到 grain S3 并输出公网 CDN URL(给 Seedance @ref / 数字人参考用)。
# 用法: tools/oss-upload.sh <本地文件> [远端key]
#   远端 key 默认 kuleshov/assets/<文件名>;kuleshov 资产一律放 kuleshov/ 命名空间,
#   不要写进 grain 业务前缀(dev/、grains/ 等)。
# 依赖: curl >= 7.75(--aws-sigv4);凭据从仓库根 .env 读取。
set -euo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$here/.env"

file="${1:?用法: oss-upload.sh <本地文件> [远端key]}"
[ -f "$file" ] || { echo "文件不存在: $file" >&2; exit 1; }
key="${2:-kuleshov/assets/$(basename "$file")}"

case "$file" in
  *.png) ctype="image/png" ;;
  *.jpg|*.jpeg) ctype="image/jpeg" ;;
  *.webp) ctype="image/webp" ;;
  *.mp3) ctype="audio/mpeg" ;;
  *.wav) ctype="audio/wav" ;;
  *.mp4) ctype="video/mp4" ;;
  *) ctype="application/octet-stream" ;;
esac

curl -sS --fail -X PUT "https://${AWS_S3_BUCKET}.s3.${AWS_REGION}.amazonaws.com/${key}" \
  --aws-sigv4 "aws:amz:${AWS_REGION}:s3" \
  --user "${AWS_ACCESS_KEY_ID}:${AWS_SECRET_ACCESS_KEY}" \
  -H "Content-Type: ${ctype}" \
  --data-binary "@${file}" > /dev/null

url="https://storage.neodrop.ai/${key}"
# 上传即验证公网可达,失败立刻暴露而不是等到 Seedance 排队后才发现
code=$(curl -sS -o /dev/null -w '%{http_code}' -I "$url")
[ "$code" = "200" ] || { echo "上传成功但 CDN 不可达(HTTP $code): $url" >&2; exit 1; }
echo "$url"
