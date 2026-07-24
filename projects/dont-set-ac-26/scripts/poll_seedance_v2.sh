#!/usr/bin/env bash
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"; cd "$ROOT"; set -a; source .env; set +a
OUT="projects/dont-set-ac-26/shots"
names="s03_sweat s07_heat s09_sweat_sci s11_ac_inside s13_compressor s18_remote_key s21_wind"
for i in $(seq 1 120); do
  alldone=1
  for name in $names; do
    [ -f "$OUT/v2_${name}.mp4" ] && continue
    tid=$(grep "^${name} " /tmp/v2_seedance_rids.txt | awk '{print $2}')
    resp=$(curl -sS --max-time 60 -H "Authorization: Bearer ${ARK_VIDEO_API_KEY}" "${ARK_VIDEO_API_BASE_URL}/v1/videos/${tid}" 2>/dev/null)
    st=$(echo "$resp" | /usr/bin/python3 -c "import json,sys;print(json.load(sys.stdin).get('status',''))" 2>/dev/null)
    if [ "$st" = "completed" ] || [ "$st" = "succeeded" ]; then
      url=$(echo "$resp" | /usr/bin/python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('metadata',{}).get('url') or d.get('url',''))" 2>/dev/null)
      [ -n "$url" ] && { curl -sS --max-time 180 -o "$OUT/v2_${name}.mp4" "$url"; echo "[$(date +%H:%M:%S)] $name DONE $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT/v2_${name}.mp4" 2>/dev/null)s"; } || alldone=0
    elif [ "$st" = "failed" ] || [ "$st" = "error" ]; then echo "[$name] FAILED"; echo failed > "$OUT/.v2_${name}.failed"
    else alldone=0; fi
  done
  c=0; for name in $names; do { [ -f "$OUT/v2_${name}.mp4" ] || [ -f "$OUT/.v2_${name}.failed" ]; } && c=$((c+1)); done
  [ "$c" -eq 7 ] && { echo "ALL 7 RESOLVED"; break; }
  sleep 20
done
