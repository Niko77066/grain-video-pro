#!/usr/bin/env python3
# G1 独立回转写校验：faster-whisper 转写 voiceover.mp3，与冻结旁白比对字级吻合度。
# TTS 自带字幕不能自证，本脚本是独立证据源。
import re, difflib
from faster_whisper import WhisperModel

secs = [
 "你以为删掉的 AI 聊天记录，可能还有一份，存在别人手里。",
 "《纽约时报》正在跟 OpenAI 打版权官司。最近提交的一份文件里，指控了一件事：OpenAI 内部建了一个数据库，存着七千八百万条用户对话，名义上做了去标识处理，用来自查侵权。文件还说，法院要求移交的两千万条聊天记录样本，交上来是不可用的；另有几十亿条输出，涉嫌被删除。",
 "去标识，不等于匿名。七千八百万条对话放在一起，把一个人拼出来，没那么难。这也不是哪一家的事：只要对话用明文存在服务器上，你按下删除，删掉的只是你手机里那一份。",
 "规矩在变。昨天开始施行的《AI 拟人化互动服务管理办法》，让交互数据的加密，从最佳实践变成了法定义务；不满十四岁的用户，还要监护人点头。技术上有更彻底的做法，叫密态计算：数据全程加密着算，服务商自己也看不到明文。你半夜跟 AI 说的那些话，值得这个待遇。",
]
norm = lambda s: re.sub("[^一-鿿A-Za-z0-9]", "", s)
ref = norm("".join(secs))

print("加载 faster-whisper small 模型…", flush=True)
model = WhisperModel("small", device="cpu", compute_type="int8")
segments, info = model.transcribe("voiceover.mp3", language="zh", beam_size=5,
                                  initial_prompt="以下是普通话简体中文的新闻播报内容。")
hyp_raw = "".join(s.text for s in segments)
# 繁转简，消除评测器繁体噪声
try:
    import opencc
    hyp_raw = opencc.OpenCC('t2s').convert(hyp_raw)
    print("(已 opencc 繁转简)")
except Exception as e:
    print(f"(opencc 不可用：{e}；繁简差异将计入噪声)")
open('hyp.txt', 'w').write(hyp_raw)
hyp = norm(hyp_raw)

ratio = difflib.SequenceMatcher(None, ref, hyp).ratio()
print("\n=== 独立回转写结果 ===")
print("HYP 原文:", hyp_raw.strip())
print(f"\nREF {len(ref)} 字 | HYP {len(hyp)} 字 | 字级吻合度 = {ratio:.4f}  (阈值 0.95)")
print("\n=== 差异明细（数字被转阿拉伯数字属正常，非 TTS 错）===")
sm = difflib.SequenceMatcher(None, ref, hyp)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag != 'equal':
        print(f"  [{tag}] REF'{ref[i1:i2]}' → HYP'{hyp[j1:j2]}'")
print("\nG1 时长门另核 ffprobe；本门=词准确率。" + ("初判 PASS" if ratio >= 0.95 else "初判需人工复核（可能数字格式差异）"))
