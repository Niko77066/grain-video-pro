#!/usr/bin/env python3
# 从火山 TTS response.json 的逐字字幕构建 audio/timeline.json（分节区间 + 逐字轴）
# 用法: python3 build_timeline.py <duration_s(ffprobe实测)>
import json, re, sys

dur = float(sys.argv[1])
d = json.load(open('response.json'))
subs = d['subtitle']['sentences']

# 冻结旁白四拍（须与 script.md 逐字一致）
secs_text = {
 "sec01": "你以为删掉的 AI 聊天记录，可能还有一份，存在别人手里。",
 "sec02": "《纽约时报》正在跟 OpenAI 打版权官司。最近提交的一份文件里，指控了一件事：OpenAI 内部建了一个数据库，存着七千八百万条用户对话，名义上做了去标识处理，用来自查侵权。文件还说，法院要求移交的两千万条聊天记录样本，交上来是不可用的；另有几十亿条输出，涉嫌被删除。",
 "sec03": "去标识，不等于匿名。七千八百万条对话放在一起，把一个人拼出来，没那么难。这也不是哪一家的事：只要对话用明文存在服务器上，你按下删除，删掉的只是你手机里那一份。",
 "sec04": "规矩在变。昨天开始施行的《AI 拟人化互动服务管理办法》，让交互数据的加密，从最佳实践变成了法定义务；不满十四岁的用户，还要监护人点头。技术上有更彻底的做法，叫密态计算：数据全程加密着算，服务商自己也看不到明文。你半夜跟 AI 说的那些话，值得这个待遇。",
}
norm = lambda s: re.sub("[^一-鿿A-Za-z0-9]", "", s)
order = ["sec01", "sec02", "sec03", "sec04"]
need = {k: len(norm(v)) for k, v in secs_text.items()}

sections, words = [], []
si, acc, sec_start = 0, 0, None
for sent in subs:
    st, et = sent['start_time'] / 1000, sent['end_time'] / 1000
    if sec_start is None:
        sec_start = st
    acc += len(norm(sent['text']))
    for w in sent.get('words', []):
        if norm(w['text']):
            words.append({"w": w['text'], "t": [round(w['start_time'] / 1000, 3), round(w['end_time'] / 1000, 3)]})
    if si < len(order) and acc >= need[order[si]]:
        sections.append({"id": order[si], "t": [round(sec_start, 3), round(et, 3)]})
        si += 1; acc = 0; sec_start = None

json.dump({"duration_s": dur, "sections": sections, "words": words},
          open('timeline.json', 'w'), ensure_ascii=False, indent=1)

prev = 0.0
for s in sections:
    print(f"  {s['id']}: [{s['t'][0]:6.2f},{s['t'][1]:6.2f}] {s['t'][1]-s['t'][0]:5.2f}s  gap {s['t'][0]-prev:.2f}s")
    prev = s['t'][1]
print(f"  tail {dur-prev:.2f}s | total {dur}s | words {len(words)} | sections {len(sections)}")
