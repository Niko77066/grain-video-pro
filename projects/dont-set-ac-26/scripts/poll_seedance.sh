#!/usr/bin/env bash
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
set -a; source "$ROOT/.env"; set +a
cd "$ROOT"
OUT="projects/dont-set-ac-26/shots"
id_altar="task_tSqJ2CRlyh1vvkGVHvFVLmSrhgRYPKfI"
id_smell="task_7JzlgN3NxcCyB9l8LP97sS4c3ivOkhVB"
for i in $(seq 1 90); do
  for name in altar smell; do
    [ -f "$OUT/${name}.mp4" ] && continue
    eval id=\$id_$name
    resp=$(curl -sS --max-time 60 -H "Authorization: Bearer ${ARK_VIDEO_API_KEY}" "${ARK_VIDEO_API_BASE_URL}/v1/videos/${id}")
    status=$(echo "$resp" | python3 -c "import json,sys;print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
    if [ "$status" = "completed" ] || [ "$status" = "succeeded" ]; then
      url=$(echo "$resp" | python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('metadata',{}).get('url') or d.get('url',''))" 2>/dev/null)
      if [ -n "$url" ]; then
        curl -sS --max-time 180 -o "$OUT/${name}.mp4" "$url"
        echo "[$(date +%H:%M:%S)] $name DONE -> $OUT/${name}.mp4"
        ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT/${name}.mp4" 2>&1 | head -1
      else echo "[$(date +%H:%M:%S)] $name completed no-url"; fi
    elif [ "$status" = "failed" ] || [ "$status" = "error" ]; then
      echo "[$(date +%H:%M:%S)] $name FAILED: $(echo "$resp"|head -c 200)"; echo "FAIL_$name" > "$OUT/.${name}_failed"
    else echo "[$(date +%H:%M:%S)] $name: ${status:-noresp}"; fi
  done
  c=0; for name in altar smell; do { [ -f "$OUT/${name}.mp4" ] || [ -f "$OUT/.${name}_failed" ]; } && c=$((c+1)); done
  if [ "$c" -eq 2 ]; then echo "ALL SEEDANCE RESOLVED"; exit 0; fi
  sleep 20
done
echo "POLL TIMEOUT ~30min"; exit 1
