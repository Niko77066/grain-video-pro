import warnings, glob, os, subprocess, itertools, sys
warnings.filterwarnings("ignore")
import torch, torchaudio
from speechbrain.inference.speaker import EncoderClassifier
clf = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", savedir=os.path.expanduser("~/.cache/ecapa"), run_opts={"device":"cpu"})
SP=os.path.dirname(os.path.abspath(__file__))
def cos(a,b): return float(torch.nn.functional.cosine_similarity(a,b,dim=-1).mean())
def emb_windows(mp3, n=6, win=8.0):
    dur=float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",mp3],capture_output=True,text=True).stdout)
    embs=[]
    starts=[ (dur-win)*i/(n-1) for i in range(n) ]
    for i,st in enumerate(starts):
        wav=f"/tmp/_w{i}.wav"
        subprocess.run(["ffmpeg","-nostdin","-y","-ss",f"{st:.2f}","-t",str(win),"-i",mp3,"-ar","16000","-ac","1",wav,"-loglevel","error"])
        sig,_=torchaudio.load(wav)
        embs.append(clf.encode_batch(sig).squeeze(0))
    return embs
print(f"{'voice':40s} {'min':>7} {'mean':>7}  verdict")
res=[]
for mp3 in sorted(glob.glob(SP+"/long_*.mp3")):
    name=os.path.basename(mp3)[5:-4]
    E=emb_windows(mp3)
    sims=[cos(E[i],E[j]) for i,j in itertools.combinations(range(len(E)),2)]
    mn,me=min(sims),sum(sims)/len(sims)
    res.append((name,mn,me))
    print(f"{name:40s} {mn:7.4f} {me:7.4f}  {'✅≥0.88' if mn>=0.88 else '⚠️<0.88'}")
res.sort(key=lambda x:-x[1])
print("\nrank by min:", [f'{n}:{m:.3f}' for n,m,_ in sorted(res,key=lambda x:-x[1])])
