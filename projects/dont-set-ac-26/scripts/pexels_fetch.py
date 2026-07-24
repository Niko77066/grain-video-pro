#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pexels 空镜检索下载(footage 声部,纯氛围)。dedup by id;写 manifest。UA 必带。"""
import json,os,subprocess,urllib.request,urllib.parse
KEY=os.environ["PEXELS_API_KEY"]
OUT="projects/dont-set-ac-26/compose/assets/broll"
os.makedirs(OUT,exist_ok=True)
# (shot_id, section, query, desc)
NEEDS=[
("s03_sweat_room","sec01","man sweating hot at home summer","夏天闷热屋里、擦汗/不适的人"),
("s06_thermo_q","sec02","air conditioner remote temperature display closeup","空调遥控器/温度显示屏特写"),
("s07_climates","sec02","heat haze hot summer city street","干热/暑气氛围空镜"),
("s09_sweat_sci","sec02","sweat drops on skin macro closeup","皮肤汗珠微距(高湿蒸发不掉)"),
("s10_vulnerable","sec02","elderly woman sitting at home warm","居家老人(热脆弱人群)"),
("s12_ac_running","sec03","air conditioner blowing air vent indoor","空调出风口运行/百叶"),
("s17_public_bldg","sec04","modern office building glass exterior","写字楼玻璃幕墙外景(公共建筑)"),
("s19_intro","sec05","hand holding air conditioner remote control","伸手拿空调遥控器"),
("s21_tip_wind","sec05","ceiling fan air circulation indoor room","室内送风/循环(风向tip)"),
("s24_cozy_home","sec06","cozy living room evening warm light","傍晚居家舒适客厅"),
]
used=set(); manifest=[]
for sid,sec,q,desc in NEEDS:
    try:
        url=f"https://api.pexels.com/videos/search?query={urllib.parse.quote(q)}&per_page=10&orientation=landscape&size=medium"
        req=urllib.request.Request(url,headers={"Authorization":KEY,"User-Agent":"Mozilla/5.0"})
        d=json.load(urllib.request.urlopen(req,timeout=30))
        got=False
        for v in d.get("videos",[]):
            if v["id"] in used: continue
            if not (4<=v["duration"]<=45): continue
            hd=[f for f in v["video_files"] if f.get("quality")=="hd" and 1280<=f.get("width",0)<=2560]
            if not hd: continue
            link=sorted(hd,key=lambda f:f["width"])[0]["link"]
            subprocess.run(["curl","-sS","-A","Mozilla/5.0","-e","https://www.pexels.com/","-L",link,"-o",f"{OUT}/{sid}.mp4"],check=True,timeout=180)
            used.add(v["id"])
            manifest.append({"shot":sid,"file":f"{sid}.mp4","source":f"https://www.pexels.com/video/{v['id']}/","id":v['id'],"license":"pexels","section":sec,"desc":desc,"dur_s":v["duration"]})
            print(f"{sid}: id{v['id']} {v['duration']}s {sorted(hd,key=lambda f:f['width'])[0]['width']}w ✓")
            got=True; break
        if not got:
            manifest.append({"shot":sid,"file":None,"gap":True,"query":q,"desc":desc,"section":sec})
            print(f"{sid}: ❌ 无合适素材(记 gap)")
    except Exception as e:
        print(f"{sid}: ERR {str(e)[:80]}")
        manifest.append({"shot":sid,"file":None,"error":str(e)[:80],"query":q,"desc":desc,"section":sec})
json.dump({"provider":"pexels","assets":manifest,"gaps":[m['shot'] for m in manifest if m.get('gap') or m.get('error')]},
          open(f"{OUT}/manifest.json","w"),ensure_ascii=False,indent=1)
print("GAPS:",[m['shot'] for m in manifest if m.get('gap') or m.get('error')])
print("PEXELS_DONE",len([m for m in manifest if m.get('file')]),"/",len(NEEDS))
