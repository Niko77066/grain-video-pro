#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 timeline_fa.json(逐字戳) + spoken_text.json 构建分节 timeline，写入 timeline.json。"""
import json,re
st=json.load(open("projects/dont-set-ac-26/audio/spoken_text.json",encoding="utf-8"))
fa=json.load(open("projects/dont-set-ac-26/audio/timeline_fa.json",encoding="utf-8"))
words=fa["words"]
def norm(t): return [ch for ch in t if re.match(r"[一-鿿A-Za-z0-9]",ch)]
# 展示版（阿拉伯数字）逐节，用于大字卡/角标对照
display={
"sec01":"你家空调遥控器上那个26度的键，可能是最没必要按的一个。都说它不冷不热、还省电。可真开过一整个夏天的人都懂：26度不够凉，电费也没见省。更别说有时候一开，还一股怪味。今天把这事说清楚。26度这个数，其实从头就没那么科学。",
"sec02":"先说凉不凉。人觉得热不热，从来不是温度计上那个数说了算。世界卫生组织自己都讲，室内到底该多少度，全球压根没有统一答案，得看地方、看人，尤其看湿度。同样27度，湿度50%，你觉得刚刚好；湿度冲到80%，那感觉就像30度，又闷又黏。道理很简单：湿度一高，汗蒸发不掉，热就全憋在身上。这时候还死守26度硬扛，家里有老人、小孩、孕妇的，反而容易热出毛病。该往下调，就大胆调。",
"sec03":"再说那股怪味。空调用久了，里头的灰尘和冷凝水会长霉，本来就带点味。正常情况下，这味也就是刚开机那几十秒；风一稳、温度压下去，就闻不到了。偏偏26度尴尬。它让压缩机一会儿开、一会儿停，风忽大忽小反复吹，等于把那点霉味，一趟一趟送遍整个屋子。",
"sec04":"那问题就来了：26度既不够凉、又可能发臭，怎么就火遍全国，还进了遥控器？这其实是场误会。我特意翻了翻空调的设计规范，才搞明白：夏天的舒适温度本来就分两档，高标准是24到26度，一般标准是26到28度。26度，正好卡在两档中间。它是个折中数，不是最舒服的数。真正让它出名的，是2007年那份节能通知：公共建筑夏天空调不许低于26度。这本来是给写字楼和商场省电的规定，后来被大家当成了自己家的最佳温度。厂商一看这么多人认，顺手在遥控器上加了个键。就这么一路传到了今天。",
"sec05":"那空调到底怎么开？记住几个更聪明的动作。温度上，刚进屋别直接按26。先开到22度、风量拉满，十几分钟把屋子快速降下来，再调回你觉得舒服的度数，一般24到26。晚上睡觉往上提两度，老人小孩别低于27。风向上，出风口尽量朝上吹。冷空气会自己往下沉，全屋更均匀，也不会对着人猛灌。要是屋里又闷又黏，先开除湿，比一个劲儿降温管用。还有几个省电的小动作：短时间出门别关机，把温度调高就行，来回开关反而更费电；开一整天，用ECO模式；滤网半个月洗一次，不然既不凉，还容易吹脏东西。",
"sec06":"说到底，别跟遥控器上那个数字较劲，也别跟电费死磕。先让屋里的人舒服，才是真的会用空调。今晚就把温度调一调，试试看。",
}
sections=[];cur=0
for sid in st["order"]:
    nc=norm(st["sections"][sid])
    a=cur; b=cur+len(nc)-1
    t0=words[a]["t"][0]; t1=words[b]["t"][1]
    sections.append({"id":sid,"t":[round(t0,3),round(t1,3)],"n_chars":len(nc),
                     "text_spoken":st["sections"][sid],"text_display":display[sid]})
    cur=b+1
tl={"file":"audio/voiceover.wav","duration_s":fa["duration_s"],
    "method":"MiniMax speech-2.8-hd single-pass(audiobook_female_1,1.1,neutral) → wav2vec2-zh forced_align",
    "n_chars":fa["n_chars"],"sections":sections,"words":words,
    "note":"spoken=中文数字(对齐用/字幕)，display=阿拉伯数字(大字卡/角标)。画面cue由内容词首字戳派生，compose禁手写秒数。"}
json.dump(tl,open("projects/dont-set-ac-26/audio/timeline.json","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print(f"总时长 {fa['duration_s']}s | {len(sections)} 节")
for s in sections: print(f"  {s['id']}  {s['t'][0]:6.2f}–{s['t'][1]:6.2f}s  ({s['t'][1]-s['t'][0]:5.2f}s, {s['n_chars']}字)")
