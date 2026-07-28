#!/usr/bin/env bash
# 生成型镜头链路（broll-studio 的八套材质语言）的开工前自检。
# 进 Gate 0 之前跑一次。全绿直接开工，不要把配置信息复述给用户。
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
root="$here"; while [ "$root" != "/" ] && [ ! -f "$root/.env" ]; do root="$(dirname "$root")"; done

fail=0
ok(){ printf '  ✅ %s\n' "$1"; }
no(){ printf '  ❌ %s\n' "$1"; fail=1; }

echo "生成型镜头链路 · 环境自检"

command -v ffmpeg >/dev/null && ok "ffmpeg $(ffmpeg -version | head -1 | awk '{print $3}')" \
  || no "ffmpeg 缺失 — macOS: brew install ffmpeg"
command -v ffprobe >/dev/null && ok "ffprobe" || no "ffprobe 缺失（随 ffmpeg 一起装）"

# 脚本按 3.9 写（macOS 系统 python3 就是 3.9.6，脚本已在其上验过）
python3 - <<'PY' >/dev/null 2>&1 && ok "python3 $(python3 -V 2>&1 | awk '{print $2}') + Pillow" \
  || no "python3 >= 3.9 + Pillow 缺失 — python3 -m pip install --user Pillow"
import sys, PIL
assert sys.version_info >= (3, 9)
PY

if [ -f "$root/.env" ]; then
  ok ".env 在 $root"
  for k in ARK_VIDEO_API_BASE_URL ARK_VIDEO_API_KEY; do
    grep -q "^${k}=" "$root/.env" && ok "$k 已配置" || no "$k 未在 .env 里"
  done
else
  no ".env 找不到 — worktree 里先 ln -sf <主仓库>/.env .env"
fi

[ -x "$root/tools/oss-upload.sh" ] && ok "tools/oss-upload.sh 可执行" \
  || no "tools/oss-upload.sh 缺失或不可执行（Seedance 参考帧必须是公网 URL）"

echo
[ "$fail" = 0 ] && echo "全部通过。" || echo "有未通过项——先补齐再进 Gate 0。"
exit "$fail"
