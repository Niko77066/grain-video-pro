#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gate 3：Seedance 首尾帧组装 payload（pixel 版 assemble-from-empty）。
用法: gen_seedance.py <sid> <first_url> <last_url> [duration]"""
import json, sys

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
sid, first, last = sys.argv[1], sys.argv[2], sys.argv[3]
dur = int(sys.argv[4]) if len(sys.argv) > 4 else 5

HEAD = ("Retro 16-bit PIXEL-ART paper-collage stop-motion assembly. Use Image 1 as the exact empty first frame "
        "(a flat aged-yellow #C9A876 paper field) and Image 2 as the exact completed last frame. One continuous "
        "locked-off horizontal 16:9 shot, no camera movement. Open on the empty paper field, then assemble the scene "
        "piece by piece with crisp pixel stop-motion timing, PACED EVENLY ACROSS THE ENTIRE CLIP: chunky pixel-art "
        "groups keep sliding and popping into place continuously through the whole shot — do NOT finish early, do NOT "
        "hold a long static frame; ")
TAIL = (" Preserve the 16:9 framing, #C9A876 paper grain, pixel dithering, cream keylines, chunky pixels and soft "
        "shadows. Restrained tactile 2D pixel paper-craft only. No scene cuts, no camera movement, no zoom, no "
        "morphing, no new objects, no text, no letters, no numbers, no logos, no watermark, no sound.")

ORDER = {
 "s05_hand": "first the pixel grass field and stadium crowd tiles slide in, then the goal frame and the red goalkeeper, "
             "then the navy-blue player leaps up from below, and finally the ball snaps to his raised fist in the last "
             "second to complete Image 2.",
 "s01_banner": "first the stadium stand and rows of crowd silhouettes slide in from below, then the big blank "
               "sky-blue-and-white cloth banner unfurls open across the middle in the last second to complete Image 2.",
 "s01_1806": "first the flat field settles, then the old ledger book slides in and opens with pages fanning, then the "
             "quill pen and ink pot snap into place in the last second to complete Image 2.",
 "s03_invade": "first the colonial buildings and cobbled street slide in, then the column of red-coated soldiers marches "
               "up the street, then townsfolk appear on the rooftops and the fire pours down in the last second to complete Image 2.",
 "s03_trade": "first the dock and sea slide in, then the steamship, then the steam train with cargo, then the cattle and "
              "stacked wheat sacks snap into place in the last second to complete Image 2.",
 "s04_belgrano": "first the cold night sea and clouds slide in, then the lone warship silhouette settles on the horizon, "
                 "then the faint periscope and its wake line appear in the last second to complete Image 2.",
 "s04_sheffield": "first the sea and sky slide in, then the distant warship silhouette settles, then the sea-skimming "
                  "missile streaks in with its trail in the last second to complete Image 2.",
 "s05_rattin": "first the red carpet slides in, then the two suited officials, then the blue-and-white striped player sits "
               "down defiantly in the last second to complete Image 2.",
 "s05_goal": "first the field and goal slide in, then the row of white-shirted defenders, then the navy-blue player "
             "dribbles past them with pixel afterimages toward the goal in the last second to complete Image 2.",
 "s02_map": "first the pixel sea-wave texture slides in across the middle, then the lower-left landmass with the "
            "sky-blue-and-white highlighted country snaps into place, then the upper-right landmasses with the "
            "red-and-blue highlighted isles snap into place, and finally the cream dashed route line extends dash by "
            "dash across the ocean from lower-left to upper-right, connecting them in the last second to complete Image 2.",
 "s04_ruler": "first the big green continent landmass and the tiny two-island cluster assemble piece by piece, then the "
              "very short solid cream arc draws quickly from the mainland coast to the small islands, and then the "
              "extremely long cream dashed arc slowly extends dash by dash from the islands toward the upper-right "
              "corner until it runs off the edge of the frame in the last second to complete Image 2.",
 "s05_9802": "first the green pitch and the white goal frame with the crowd wall slide in, then the red goalkeeper and "
             "the sky-blue-and-white striped shooter slide into place, and in the final second the shooter kicks and the "
             "ball streaks with a pixel afterimage trail into the far top corner while the keeper dives the other way, "
             "completing Image 2.",
}
prompt = HEAD + ORDER[sid] + TAIL
p = {"model": "doubao-seedance-2-0-260128", "prompt": prompt,
     "metadata": {"content": [
         {"type": "image_url", "image_url": {"url": first}, "role": "first_frame"},
         {"type": "image_url", "image_url": {"url": last}, "role": "last_frame"}],
         "resolution": "720p", "ratio": "16:9", "generate_audio": False, "duration": dur}}
json.dump(p, open(f"{ROOT}/shots/sdpayload_{sid}.json", "w", encoding="utf-8"), ensure_ascii=False)
print(f"seedance payload {sid}: dur={dur}s prompt={len(prompt)}chars")
