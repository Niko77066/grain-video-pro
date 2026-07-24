#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""大量 ≤3s 空镜素材检索下载(每内容点多个相关素材，供快切)。存 broll2/。"""
import json, os, urllib.request, urllib.parse, subprocess

KEY = os.environ["PEXELS_API_KEY"]
ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
OUT = f"{ROOT}/compose/assets/broll2"; os.makedirs(OUT, exist_ok=True)

# 每内容点 2 个关键词，各取 1 条
NEEDS = {
    "ocean1":"atlantic ocean waves aerial","ocean2":"stormy dark sea",
    "stadium1":"soccer stadium crowd night","stadium2":"football fans cheering flags",
    "city1":"buenos aires aerial city","city2":"south america city street old",
    "building1":"spanish colonial architecture","building2":"old european town square",
    "train1":"vintage steam train","cargo1":"cargo ship port loading","cattle1":"cattle herd farm","grain1":"wheat grain field harvest",
    "warship1":"navy warship at sea","warship2":"military ship ocean grey",
    "greysea1":"cold grey stormy ocean","island1":"remote rocky island cliffs",
    "london1":"london street rain","london2":"london aerial thames",
    "memorial1":"war memorial cemetery","crowd1":"crowd celebrating street",
    "airport1":"airport arrivals people","flag1":"argentina flag waving",
}
ok=0
for name,q in NEEDS.items():
    try:
        url=f"https://api.pexels.com/videos/search?query={urllib.parse.quote(q)}&per_page=5&orientation=landscape&size=medium"
        req=urllib.request.Request(url,headers={"Authorization":KEY,"User-Agent":"Mozilla/5.0"})
        d=json.load(urllib.request.urlopen(req,timeout=30))
        for v in d.get("videos",[]):
            if 3<=v["duration"]<=60:
                hd=[f for f in v["video_files"] if f.get("quality")=="hd" and 1280<=f.get("width",0)<=2560]
                if hd:
                    link=sorted(hd,key=lambda f:f["width"])[0]["link"]
                    subprocess.run(["curl","-sS","-A","Mozilla/5.0","-e","https://www.pexels.com/","-L",link,"-o",f"{OUT}/{name}.mp4"],check=True,timeout=180)
                    print(f"{name}: id{v['id']} {v['duration']}s ✓"); ok+=1; break
    except Exception as e:
        print(f"{name}: ERR {str(e)[:50]}")
print(f"BULK_DONE {ok}/{len(NEEDS)}")
