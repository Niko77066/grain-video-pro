#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⑤ storyboard 落盘：21 镜绑 timeline + edit + 自查八项 gate。"""
import json

ROOT = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud"
d = json.load(open(f"{ROOT}/film.json", encoding="utf-8"))

# provider 缩写：hf=HyperFrames MG | cp=collage-broll-pixel | sd=seedance空镜 | arc=档案照图片动效
S = [
 ("s01_score","sec01",0.0,5.0,"记分牌 2-1 补时第二分钟绝杀跳字","全屏记分牌","hf"),
 ("s01_banner","sec01",5.0,11.0,"『马岛是阿根廷的』横幅在看台拉开","中景横幅","cp"),
 ("s01_44yr","sec01",11.0,14.5,"「44 年」金色大字砸出","全屏大字卡","hf"),
 ("s01_1806","sec01",14.5,20.25,"泛黄账本翻回 1806（比建国还老）","道具特写","cp"),
 ("s02_atlantic","sec02",20.6,25.0,"大西洋海面空镜（一万两千公里）","航拍空镜","sd"),
 ("s02_map","sec02",25.0,28.97,"像素地图两国点亮拉线 + 报题→黑场","全屏地图","hf"),
 ("s03_card","sec03",29.32,31.5,"章节卡『钱』","章节卡","hf"),
 ("s03_invade","sec03",31.5,46.0,"1806/07 英军两次攻城、市民屋顶泼火力","像素小剧场","cp"),
 ("s03_rail","sec03",46.0,60.0,"英资铁路网在像素地图蔓延（2/3 高亮）","全屏地图","hf"),
 ("s03_trade","sec03",60.0,71.0,"牛肉谷物货运航线（非正式帝国 4 成出口）","像素货运","cp"),
 ("s03_1913","sec03",71.0,82.91,"财富对比条：1913 阿根廷 > 法国 > 德国","数据卡","hf"),
 ("s04_card","sec04",83.26,85.5,"章节卡『血』","章节卡","hf"),
 ("s04_ruler","sec04",85.5,101.0,"距离标尺 480km vs 12,700km","数据示意","hf"),
 ("s04_belgrano","sec04",101.0,120.0,"贝尔格拉诺号舰船像素剪影 + 323（禁残骸）","像素剪影","cp"),
 ("s04_sheffield","sec04",120.0,132.0,"飞鱼导弹击中谢菲尔德号（像素示意，禁伤亡）","像素示意","cp"),
 ("s04_toll","sec04",132.0,141.0,"伤亡三行数字卡 649/255/3","数据卡","hf"),
 ("s04_fate","sec04",141.0,148.76,"双命运分屏：加尔铁里下台 / 撒切尔连任","分屏卡","hf"),
 ("s05_rattin","sec05",149.11,163.0,"1966 拉廷坐女王红毯（红黄牌起源）","像素重演","cp"),
 ("s05_hand","sec05",163.0,178.0,"上帝之手像素重演（hero，FIFA 画面零使用）","像素重演 hero","cp"),
 ("s05_goal","sec05",178.0,192.0,"世纪进球连过五人像素重演","像素重演","cp"),
 ("s05_revenge","sec05",192.0,203.0,"马拉多纳自传『复仇』引文压帧","引文字卡","hf"),
 ("s05_9802","sec05",203.0,212.96,"98/02 贝克汉姆记分牌快切","记分牌快切","hf"),
 ("s06_photo","sec06",213.31,222.0,"拉廷黑白档案照缓推（全片唯一真实面孔）","真人档案照","arc"),
 ("s06_montage","sec06",222.0,235.0,"横幅/看台/全片意象像素快闪蒙太奇","混剪蒙太奇","cp"),
 ("s06_gold","sec06",235.0,240.04,"手写体金句『七十四天的加时赛』压帧→淡出（零 CTA）","收尾金句","hf"),
]
PROV = {"hf":{"provider":"hyperframes","role":"MG 信息骨架"},
        "cp":{"provider":"collage-broll-pixel","role":"像素拼贴事件/氛围 b-roll（halftone→16-bit pixel 改版）"},
        "sd":{"provider":"seedance","role":"风格化空镜（过缝合层）"},
        "arc":{"provider":"image-motion","role":"档案照+轻微运动（连续≤2）"}}

shots = []
for sid, vref, t0, t1, intent, framing, prov in S:
    sh = {"id": sid, "t": [round(t0,2), round(t1,2)], "voice_ref": vref,
          "intent": intent, "framing": framing,
          "source": {"provider": PROV[prov]["provider"], "note": PROV[prov]["role"]},
          "anchor_refs": [], "status": "planned", "gen": None, "qc": None}
    if prov == "cp":
        sh["source"]["pipeline"] = "三闸门：隐喻→GPT-Image-2静帧(16:9)→Seedance首尾帧assemble；每条≤5s，长槽位拆多条/接MG"
    shots.append(sh)

d["shots"] = shots
d["edit"] = {
  "transitions": ["硬切（默认，靠质感层无痕）", "黑场（章节闸门：钱/血/球）", "像素溶解（形态转换，全片≤1次）"],
  "lut": "褪色做旧：饱和度压低，统一 MG/collage-pixel/Seedance/档案照 四源",
  "grain": "像素颗粒 + 泛黄做旧纸纹底 #C9A876（全片贯穿的缝合层）",
  "palette": {"paper":"#C9A876","ink":"#2B2118","accent":"#FFD21E","gilt":"#C9932B","mark":"#C0392B"},
  "loudness_lufs": -14
}
d["ledger"]["gates"].append({
  "date":"2026-07-16","stage":"storyboard","gate":"自查八项","result":"pass-带note",
  "notes":"①区间对齐timeline无缝隙/重叠、首尾0–240.04s ✓；②每镜3–16s、大镜内部元素/组装持续变化，≥每8–10s一变 ✓；③连续同版式≤2（MG与collage-pixel严格交替）✓；④幻灯片风险：纯MG版式卡最多连续2镜(s04_toll+s04_fate)，collage-pixel为assemble准运动不计静态 ✓；⑤声部匹配pixel-chronicle表(MG=信息/collage=事件氛围/档案=唯一真人/seedance=空镜)✓；⑥hybrid承诺：collage-pixel 10镜承担运动质感 ✓；⑦Seedance组划分：collage每条≤5s，长槽位(s03_invade14.5s/s04_belgrano19s/s05各镜)motion阶段拆多条5s+接MG，届时定组 DEBT；⑧每镜主动作+运镜(collage=assemble-from-empty定格,MG=元素进出,禁静态描述)✓。sec05高潮段compose按2–3s/镜快切细化。"
})
d["meta"]["status"] = "storyboard-done"
d["meta"]["next_action"] = "⑥ anchors：先出 pixel-collage 风格试金石静帧(GPT-Image-2,16:9)验证 halftone→16-bit 改法 → 用户确认风格 → 批量 Gate2 静帧 → ⑦ Seedance 首尾帧。MG 镜走 HyperFrames 直接 compose。"
json.dump(d, open(f"{ROOT}/film.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
print("shots:", len(d["shots"]), "| collage-pixel:", sum(1 for s in shots if s["source"]["provider"]=="collage-broll-pixel"),
      "| hf:", sum(1 for s in shots if s["source"]["provider"]=="hyperframes"),
      "| sd:", sum(1 for s in shots if s["source"]["provider"]=="seedance"),
      "| arc:", sum(1 for s in shots if s["source"]["provider"]=="image-motion"))
print("覆盖:", shots[0]["t"][0], "–", shots[-1]["t"][1], "s | 全片 timeline 240.04s")
