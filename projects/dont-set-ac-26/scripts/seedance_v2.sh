#!/usr/bin/env bash
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"; cd "$ROOT"; set -a; source .env; set +a
CDN="https://storage.neodrop.ai/kuleshov/dont-set-ac-26/v2"
A="projects/dont-set-ac-26/anchors"
# name:hex:elements
JOBS=(
"s03_sweat:B4562A:a red starburst backing, then the halftone overheated person fanning, then sweat beads and rising heat lines"
"s07_heat:C88A2A:the cracked-ground strip, then the big halftone sun disc, then the sun rays popping out one by one and heat-shimmer strips"
"s09_sweat_sci:2E6E6A:the halftone skin/arm strip, then the clinging sweat droplets, then the swarm of blue water-vapor dots crowding in and red blocking arrows"
"s11_ac_inside:3B4A32:the AC outer shell, then the interior coils, then dust motes and condensation drips, then greenish mold patches"
"s13_compressor:B8912E:the compressor unit body, then the on/off toggle, then the pulsing airflow arcs growing outward on both sides"
"s18_remote_key:4A3B5C:the paper remote control body, then its rows of keys, then the halftone hand entering and pressing one highlighted cream key"
"s21_wind:2C5A8A:the cut-paper room outline and furniture, then pale-blue cool-air wave arcs flowing down from the ceiling and spreading along the floor"
)
> /tmp/v2_seedance_rids.txt
for j in "${JOBS[@]}"; do
  name="${j%%:*}"; rest="${j#*:}"; hex="${rest%%:*}"; elem="${rest#*:}"
  ffmpeg -y -i "$A/v2_${name}.png" -vf "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720" "$A/v2_${name}_last.png" 2>/dev/null
  ffmpeg -y -f lavfi -i "color=c=0x${hex}:s=1280x720" -frames:v 1 "$A/v2_${name}_first.png" 2>/dev/null
  fu=$(tools/oss-upload.sh "$A/v2_${name}_first.png" "kuleshov/dont-set-ac-26/v2/v2_${name}_first.png" 2>/dev/null)
  lu=$(tools/oss-upload.sh "$A/v2_${name}_last.png" "kuleshov/dont-set-ac-26/v2/v2_${name}_last.png" 2>/dev/null)
  prompt="Paper-collage stop-motion assembly. Use Image 1 as the exact empty first frame (a flat paper field) and Image 2 as the exact completed last frame. One continuous locked-off horizontal 16:9 shot, no camera movement. Open on the empty paper field, then assemble the scene piece by piece with crisp physical stop-motion timing, PACED EVENLY ACROSS THE ENTIRE CLIP: pieces keep sliding in and snapping into place continuously through the whole shot, do NOT finish early, do NOT hold a long static frame; first ${elem}, with the final fragments snapping into place in the last second to complete Image 2. Preserve the 16:9 framing, the paper color field, uncoated paper grain, halftone dots, cream keylines, crisp cut edges and soft shadows. Restrained tactile 2D paper craft only. No scene cuts, no camera movement, no zoom, no morphing, no new objects, no text, no letters, no numbers, no logos, no watermark, no sound."
  /usr/bin/python3 -c "
import json,sys
p={'model':'doubao-seedance-2-0-260128','prompt':sys.argv[1],'metadata':{'content':[
 {'type':'image_url','image_url':{'url':sys.argv[2]},'role':'first_frame'},
 {'type':'image_url','image_url':{'url':sys.argv[3]},'role':'last_frame'}],
 'resolution':'720p','ratio':'16:9','generate_audio':False,'duration':10}}
json.dump(p,open('/tmp/sd_'+sys.argv[4]+'.json','w'))
" "$prompt" "$fu" "$lu" "$name"
  resp=$(curl -sS -X POST "${ARK_VIDEO_API_BASE_URL}/v1/videos" -H "Authorization: Bearer ${ARK_VIDEO_API_KEY}" -H "Content-Type: application/json" --max-time 90 --data-binary @/tmp/sd_$name.json)
  tid=$(echo "$resp" | /usr/bin/python3 -c "import json,sys;d=json.load(sys.stdin);print(d.get('id') or d.get('task_id') or '')" 2>/dev/null)
  echo "$name $tid" | tee -a /tmp/v2_seedance_rids.txt
done
echo "SUBMIT_DONE"
