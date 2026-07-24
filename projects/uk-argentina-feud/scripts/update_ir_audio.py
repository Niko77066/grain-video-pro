#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""④ audio 开工：把 IR 从 script 推进到 audio。先写 IR 再花钱。"""
import json

P = "/Users/admin/kuleshov/.claude/worktrees/estee-lauder-night-video-7162e0/projects/uk-argentina-feud/film.json"
d = json.load(open(P, encoding="utf-8"))

# 6 节旁白（逐字复制自 script.md v2）+ 语速/表演指令
sections = [
    {"id": "sec01", "slot": "S1", "t_planned": [0.0, 24.0], "rate": "normal", "speech_rate": 0,
     "perf": "平叙开局；『马岛，是阿根廷的』放慢一字一顿；『这么说吧』贴近闲聊",
     "text": "昨天凌晨，阿根廷把英格兰踢出了世界杯，补时第二分钟绝杀。但真正上热搜的，是庆祝时拉开的那条横幅：马岛，是阿根廷的。一场四十四年前的战争，被举到了半决赛的球场上。这两个国家到底多大仇？这么说吧，这本账，比阿根廷建国还要老。",
     "status": "planned", "gen": None},
    {"id": "sec02", "slot": "S2", "t_planned": [24.0, 33.0], "rate": "normal", "speech_rate": 0,
     "perf": "口号句读做闸门感；报题后 0.5s 静默进黑场",
     "text": "什么仇什么怨。今天，英国和阿根廷。隔着一万两千公里的大西洋，掰了两百二十年的手腕。",
     "status": "planned", "gen": None},
    {"id": "sec03", "slot": "S3-S4", "t_planned": [33.0, 86.0], "rate": "normal", "speech_rate": 0,
     "perf": "『那会儿还没有阿根廷这个国家』放慢；『做到什么份上？』自问自答口气；末句『一九八二年到了』压低",
     "text": "故事得从一八〇六年说起。那会儿还没有阿根廷这个国家，这块地归西班牙管。英国军队来了两次。第一次一千六百人，直接占了布宜诺斯艾利斯，西班牙总督卷着国库跑了，最后是当地民兵把城夺回来的。第二年英国人带着七千人卷土重来，市民爬上屋顶往下泼火力，把他们打到无条件投降。就这两仗，打出了阿根廷人的民族认同。国家还没建，仇先记下了。不过往后一百年，两家主要在做生意。做到什么份上？阿根廷三分之二的铁路是英国资本修的；四成的出口，牛肉、谷物，全卖到英国。历史学家管这种关系叫“非正式帝国”。靠这套买卖，一九一三年的阿根廷，比法国和德国都富。然后，一九八二年到了。",
     "status": "planned", "gen": None},
    {"id": "sec04", "slot": "S5-S6", "t_planned": [86.0, 150.0], "rate": "normal", "speech_rate": 0,
     "perf": "全段克制低沉；『撒切尔真把舰队派来了』单句独立、带一点『没想到』；伤亡数字逐个念清不渲染；末两句短促收住",
     "text": "那年四月二日，阿根廷军政府出兵占了马岛。这片群岛，阿根廷叫马尔维纳斯，英国叫福克兰。它离阿根廷本土四百八十公里，离英国一万两千七百公里。军政府当时通胀失控，国内到处是抗议，他们赌的就是这个距离：英国不会为几座荒岛跑半个地球。撒切尔真把舰队派来了。五月二日，英国核潜艇击沉巡洋舰贝尔格拉诺将军号，三百二十三人沉进南大西洋。阿根廷整场战争阵亡六百四十九人，一半折在这一艘船上。两天后阿根廷还了一击，飞鱼导弹打中谢菲尔德号，二十人死亡，那是二战之后英国头一回有军舰被击沉。七十四天后，阿军投降。六百四十九个阿根廷人、二百五十五个英国人、三个岛民，没能回家。战败第三天，加尔铁里下台，军政府垮了。伦敦那头，撒切尔的支持率一路涨，第二年大选轻松连任。仗打完了。账没算完。",
     "status": "planned", "gen": None},
    {"id": "sec05", "slot": "S8-S9", "t_planned": [150.0, 208.0], "rate": "fast", "speech_rate": 0,
     "perf": "节奏加密（紧迫/breaking 覆写：语速 +10%）；『顺便说一句』松一口气旁枝；自传引文降速贴近耳语；『他说，这就是复仇』平实陈述不做戏剧停顿",
     "text": "一九六六年世界杯，温布利。阿根廷队长拉廷被罚下场。裁判是个德国人，听不懂西班牙语，却认定拉廷说了脏话。拉廷不服，在场上杵了快十分钟，下场的时候，一屁股坐上了女王专用的红毯。赛后英格兰主帅骂阿根廷人是动物，阿根廷人管这场球叫世纪劫案。顺便说一句，足球的红黄牌，就是这场混乱之后才发明的。二十年后，墨西哥城，马岛战争刚过去四年。马拉多纳四分钟进了两个球。第一个是用手拍进去的，上帝之手；第二个从中场连过五人，后来被评为世纪进球。很多年后他在自传里承认：赛前大家都说足球归足球、战争归战争，可我们心里清楚，他们在那边杀了很多阿根廷孩子。他说，这就是复仇。之后还有两笔账。九八年，贝克汉姆红牌，阿根廷点球淘汰英格兰；〇二年，还是贝克汉姆，一记点球扳回一城。",
     "status": "planned", "gen": None},
    {"id": "sec06", "slot": "S10-S11", "t_planned": [208.0, 236.0], "rate": "slow", "speech_rate": 0,
     "perf": "回到全片最低语速；拉廷两句之间留 0.5s 静默；末句逐字落下，收在『加时赛』后 1s 静默进音乐",
     "text": "然后就是昨天。英格兰先进球，第八十五分钟被扳平，补时被绝杀。三十九岁的梅西，送了两次助攻。有个人没能看到这场球。拉廷，六十年前坐上红毯的那位队长，上礼拜刚刚去世，八十九岁。横幅在亚特兰大的夜里拉开。对英格兰，这是一场输掉的半决赛；而阿根廷人踢的，一直是那七十四天的加时赛。",
     "status": "planned", "gen": None},
]

total_chars = sum(len(s["text"]) for s in sections)

d["meta"]["status"] = "audio"
d["meta"]["commitment"]["duration_s"] = 245
d["meta"]["commitment"]["tolerance_pct"] = 10
d["meta"]["commitment"]["note"] = "用户 2026-07-16 裁决允许放宽（原承诺 220s）；pixel-chronicle 实测语速 ~300 字/分，最终以 audio.timeline 真实时间戳为准"
d["meta"]["next_action"] = "④ audio 进行中：先出 sec01 音色样本（seed-audio-1.0，speech_rate=0 测速）→ ⏸ 给用户听、确认音色人设 → 以 sec01 音频作 reference 批量生成 sec02–06（sec05 加速/sec06 减速）→ 拼接 voiceover.wav → WhisperX 回转写 G1 校验（≥95% + 时长 ±10%）→ 回填 audio.timeline → ⏸ 给用户听全片旁白。素材检索/BGM 待 storyboard。"

d["audio"]["voiceover"] = {
    "engine": "seed-audio-1.0",
    "endpoint": "https://openspeech.bytedance.com/api/v3/tts/create",
    "voice_profile": "一位中文男性纪录片解说员，中年，普通话标准，冷静克制、平实零表演腔，像向一个人平静讲述而不是新闻播报，语速偏快且贯穿平稳",
    "voice_profile_note": "对标《佛得角》男声旁白 + script 基调『像对一个人讲话不像播报』+ playbook ~300字/分零表演腔；跨节逐字复用，首片确认后回填 pixel-chronicle playbook 资产化",
    "target_wpm_cn": 300,
    "total_chars": total_chars,
    "status": "planned",
    "sections": sections,
}

d["ledger"]["decisions"].append({
    "date": "2026-07-16", "stage": "script", "by": "用户",
    "decision": "script v2 通过，放行进入 ④ audio",
    "options_considered": ["打回再改"],
    "reason": "结构（钱→血→球）+ 去 AI 味自查 46/50；EP 已用 WebSearch 六源交叉核实时事锚 F01/F02/F05 为真（FIFA/ESPN/WaPo/Forbes），地基可信"
})
d["ledger"]["decisions"].append({
    "date": "2026-07-16", "stage": "audio", "by": "用户→EP",
    "decision": "时长承诺 220s → 245s（±10%），保 pixel-chronicle 冷静基调不强行提速/硬砍",
    "options_considered": ["坚持 220s（需砍约 150 字）", "强行提速念快（否：违背零表演腔冷静基调）"],
    "reason": "pixel-chronicle 实测语速 ~300字/分本就是该赛道冷静常速；对标《佛得角》244s；brief『3–4分钟带』自洽；实际以 timeline 为准"
})
d["ledger"]["gates"].append({
    "date": "2026-07-16", "stage": "audio", "gate": "时事锚事实核查（EP 主动，进音频前）",
    "result": "pass",
    "notes": "WebSearch 实测：F01 阿根廷2-1英格兰半决赛（FIFA官网+ESPN gameId760515+NBC+NPR+Yahoo+FOX 六源）；F05 拉廷7/11去世89岁（WaPo讣告）；F02 马岛横幅+FIFA或处罚（Forbes/BusinessStandard，附2014年3万瑞郎先例）。F06五角大楼邮件仍存疑但非script承重点"
})

json.dump(d, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# 校验回读
d2 = json.load(open(P, encoding="utf-8"))
print("status      :", d2["meta"]["status"])
print("duration    :", d2["meta"]["commitment"]["duration_s"], "±", d2["meta"]["commitment"]["tolerance_pct"], "%")
print("voiceover   :", d2["audio"]["voiceover"]["status"], "| sections:", len(d2["audio"]["voiceover"]["sections"]))
print("total_chars :", d2["audio"]["voiceover"]["total_chars"], "→ @300字/分 ≈", round(total_chars/300*60,1), "s")
print("decisions   :", len(d2["ledger"]["decisions"]), "| gates:", len(d2["ledger"]["gates"]))
for s in d2["audio"]["voiceover"]["sections"]:
    print(f"  {s['id']} {s['rate']:>6} {len(s['text']):>4}字  {s['perf'][:24]}")
