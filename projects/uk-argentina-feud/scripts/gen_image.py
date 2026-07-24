#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gate 2 静帧：pixel-chronicle 版 collage 静帧（GPT-Image-2, 16:9）。
halftone→16-bit pixel；严守 无文字/数字/真人脸/队徽；战争镜禁残骸血腥。"""
import json, sys

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
BASE = ("retro 16-bit pixel-art (SNES/Genesis era) cut-and-assembled like a paper collage; "
        "flat aged-yellow paper field (#C9A876) with subtle uncoated paper fiber and faint CRT scanlines; "
        "chunky pixels with ordered dithering, thin warm-cream keylines around each cut pixel-sprite group, "
        "soft low-opacity drop shadows; horizontal 16:9 locked frame, subject in middle 70 percent, "
        "generous flat color-field negative space, 3 to 6 large separable pixel groups for assemble-from-empty")
AVOID = ("Avoid: no typography, no readable letters, no numerals, no logos, no team crests, no jersey names or numbers, "
         "no real recognizable faces, no photoreal, no glossy 3D, no camera UI, no watermark, no clutter")

PROMPTS = {
 "s01_banner": f"A finished 16:9 editorial still, {BASE}. Visual proposition: rows of pixel-art crowd silhouettes in a stadium stand raise a large blank sky-blue-and-white cloth banner. Constraint: instantly reads as a crowd hoisting one big banner. {AVOID}.",
 "s01_1806":   f"A finished 16:9 editorial still, {BASE}. Visual proposition: an old weathered account ledger book lies open with fanning aged pages, a quill pen and ink pot resting on it, evoking a very old debt/account. Accent gilt #C9932B page edges. Constraint: reads as an ancient account book being opened. {AVOID}.",
 "s03_invade": f"A finished 16:9 editorial still, {BASE}. Visual proposition: a column of generic red-coated pixel soldiers advances up a colonial town street while townspeople silhouettes on flat rooftops tip cauldrons to pour fire down to repel them. Pixel colonial buildings. Constraint: an urban assault repelled from rooftops. No blood, no gore. {AVOID}.",
 "s03_trade":  f"A finished 16:9 editorial still, {BASE}. Visual proposition: cattle, stacked wheat sacks and cargo crates being loaded onto a pixel steamship at a dock and a steam train, goods flowing out (an informal empire of trade). Constraint: beef and grain shipped out en masse. {AVOID}.",
 "s04_belgrano": f"A finished 16:9 editorial still, {BASE}. Visual proposition: a lone warship in dark silhouette on a cold open sea, a faint submarine periscope wake line approaching — tense and ominous. Cold blue palette. Constraint: a warship shadowed at sea, ominous but BLOODLESS. No wreck, no sinking, no explosion, no bodies, no debris. {AVOID}.",
 "s04_sheffield": f"A finished 16:9 editorial still, {BASE}. Visual proposition: a sea-skimming missile with a motion trail streaks toward a distant warship silhouette over the sea, restrained. Constraint: a missile about to reach a ship, tense not gory. No blast, no fire debris, no bodies. {AVOID}.",
 "s05_rattin": f"A finished 16:9 editorial still, {BASE}. Visual proposition: a defiant footballer in a blue-and-white striped kit sits down stubbornly on a red carpet strip while two generic officials stand beside him. Constraint: a player defiantly sitting on a red carpet. {AVOID}.",
 "s05_hand":   f"A finished 16:9 editorial still, {BASE}. Visual proposition: a footballer in a DARK NAVY BLUE kit leaps and punches the ball into the goal with a raised fist, while a red-shirted pixel goalkeeper reaches up too late; pixel stadium crowd tiles behind. Small red arrow accents mark the fist-ball contact. Constraint: the raised fist meeting the ball (a hand-ball goal) unmistakable in silhouette. {AVOID}.",
 "s05_goal":   f"A finished 16:9 editorial still, {BASE}. Visual proposition: a footballer in a DARK NAVY BLUE kit dribbles the ball and slaloms past a row of four or five white-shirted defender sprites left behind, pixel motion-afterimages tracing the run toward the goal. Constraint: one player weaving past a line of defenders. {AVOID}.",
 "s02_map":    f"A finished 16:9 editorial still, {BASE}. Visual proposition: a pixel paper-craft map of the Atlantic Ocean made of pixel sea-wave tiles; in the lower-left corner the cut-out landmass silhouette of Argentina highlighted in sky-blue and white; in the upper-right corner the cut-out landmass silhouettes of the British Isles highlighted in red and blue; between the two landmasses one warm-cream DASHED arc shipping-route line curves across the pixel ocean waves connecting them. Constraint: two highlighted landmasses linked by one dashed route arc over a pixel sea, ABSOLUTELY NO place-name labels, no letters, no numbers anywhere on the map. {AVOID}.",
 "s04_ruler":  f"A finished 16:9 editorial still, {BASE}. Visual proposition: a pixel paper-craft map close-up: the south-eastern corner of the South American continent occupies the left side, a tiny cluster of small islands (an archipelago of two main islands) sits in the pixel sea to its right; one VERY SHORT solid warm-cream measuring arc connects the mainland coast to the small islands; a second EXTREMELY LONG warm-cream DASHED arc starts at the same small islands and stretches far toward the upper-right corner, running off the edge of the frame; both arcs share identical line thickness so the short-versus-long contrast is stark. Constraint: one short arc and one very long arc leaving the frame, same stroke width, dramatic length contrast, ABSOLUTELY NO labels, no letters, no numbers on the map. {AVOID}.",
 "s05_9802":   f"A finished 16:9 editorial still, {BASE}. Visual proposition: a pixel football penalty moment: flat green pixel grass pitch with a white goal frame; on the goal line a RED-kit pixel goalkeeper dives fully stretched to one side; at the penalty spot a footballer in a SKY-BLUE-AND-WHITE STRIPED kit has just finished his shooting follow-through; the ball flies with a pixel motion-afterimage trail toward the far top corner of the goal, away from the diving keeper; behind the goal a wall of pixel stadium crowd color-block tiles. Constraint: keeper diving one way, ball streaking to the opposite top corner, blank kits with no numbers. {AVOID}.",
}
sel = sys.argv[1:] if len(sys.argv) > 1 else list(PROMPTS)
for sid in sel:
    p = {"model": "gpt-image-2", "prompt": PROMPTS[sid], "quality": "medium",
         "output_format": "png", "size": "1280x720", "n": 1}
    json.dump(p, open(f"{ROOT}/anchors/imgpayload_{sid}.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(f"payload {sid}: {len(PROMPTS[sid])} chars")
