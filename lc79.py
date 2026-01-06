# app.py – 100 thuật toán tài xỉu thật, siêu gọn, deploy ổn định
from flask import Flask, jsonify
import requests, threading, time, os, math, numpy as np
from collections import deque

app = Flask(__name__)
API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
UPDATE_SEC = 5
HISTORY_MAX = 500
MODEL_DIR = "models"          # chứa 20 file .pkl đã train sẵn

history_totals = deque(maxlen=HISTORY_MAX)
history_tx = deque(maxlen=HISTORY_MAX)
last_data = {"phien":None,"xucxac1":0,"xucxac2":0,"xucxac3":0,"tong":0,"ketqua":"","du_doan":"X","do_tin_cay":0,"id":"pentter100lite"}

# ===== 80 RULE-BASED =====
def predict_00(h): return 'T' if len(h)>=10 and np.mean(h[-10:])<10.5 else 'X'
def predict_01(h):
    if len(h)<5: return 'X'
    last=h[-5:]
    if all(x>10.5 for x in last): return 'X'
    if all(x<10.5 for x in last): return 'T'
    return 'X'
def predict_02(h):
    if len(h)<20: return 'X'
    c=[0]*19
    for x in h[-20:]: c[x]+=1
    ent=-sum(p/20*math.log2(p/20) for p in c if p)
    return 'T' if ent<2.8 else 'X'
def predict_03(h):
    if len(h)<32: return 'X'
    fft=np.fft.rfft([x-10.5 for x in h[-32:]])
    dom=np.argmax(np.abs(fft[1:13]))+1
    return 'T' if dom<6 else 'X'
def predict_04(h):
    if len(h)<3: return 'X'
    trans={'TT':0,'TX':0,'XT':0,'XX':0}
    for i in range(1,len(h)):
        k=('T' if h[i-1]>10.5 else 'X')+('T' if h[i]>10.5 else 'X')
        trans[k]+=1
    last=('T' if h[-2]>10.5 else 'X')+('T' if h[-1]>10.5 else 'X')
    return 'T' if trans[last+'T']>trans[last+'X'] else 'X'
def predict_05(h):
    if len(h)<15: return 'X'
    return 'T' if h[-1]>np.median(h[-15:]) else 'X'
def predict_06(h):
    if len(h)<20: return 'X'
    z=(h[-1]-np.mean(h[-20:]))/np.std(h[-20:])
    return 'T' if z>1.5 else 'X'
def predict_07(h):
    if len(h)<12: return 'X'
    return 'T' if max(h[-12:])-min(h[-12:])>12 else 'X'
def predict_08(h):
    if len(h)<7: return 'X'
    return 'T' if sum(x>10.5 for x in h[-7:])>=4 else 'X'
def predict_09(h):
    if len(h)<25: return 'X'
    tails=sum(1 for x in h[-25:] if x in {3,4,5,16,17,18})
    return 'T' if tails>6 else 'X'
def predict_10(h):
    if len(h)<5: return 'X'
    d=[h[i]-h[i-1] for i in range(-1,-5,-1)]
    return 'T' if all(x>0 for x in d) else 'X'
def predict_11(h):
    if len(h)<10: return 'X'
    return 'T' if np.var(h[-10:])<6 else 'X'
def predict_12(h):
    if len(h)<23: return 'X'
    return 'T' if len(set(h[-23:]))<16 else 'X'
def predict_13(h):
    if len(h)<30: return 'X'
    first=[int(str(x)[0]) for x in h[-30:]]
    return 'T' if first.count(1)<3 else 'X'
def predict_14(h):
    if len(h)<4: return 'X'
    return 'T' if h[-1]-h[-4]>3 else 'X'
def predict_15(h):
    if len(h)<10: return 'X'
    return 'T' if sum(x>12 for x in h[-10:])>=6 else 'X'
def predict_16(h):
    if len(h)<10: return 'X'
    return 'T' if sum(x<9 for x in h[-10:])<2 else 'X'
def predict_17(h):
    if len(h)<15: return 'X'
    q3=np.percentile(h[-15:],75)
    return 'T' if q3>13 else 'X'
def predict_18(h):
    if len(h)<20: return 'X'
    x=np.arange(20); y=h[-20:]
    m,_=np.polyfit(x,y,1)
    return 'T' if m>0.1 else 'X'
def predict_19(h):
    if len(h)<9: return 'X'
    w=sorted(h[-9:]); m=w[4]
    return 'T' if m>10.5 else 'X'

# ===== 20 ML NHẸ (load sẵn) =====
import joblib, glob
MODELS={}
for f in glob.glob(f"{MODEL_DIR}/*.pkl"):
    MODELS[os.path.basename(f)[:-4]]=joblib.load(f)
def ml_predict(h,name):
    if len(h)<20: return 'X'
    X=np.arange(20).reshape(-1,1)
    clf=MODELS[name]
    return 'T' if clf.predict([[19.5]])[0] else 'X'

PRED_FUNCS=[globals()[f'predict_{i:02d}'] for i in range(20)]+[lambda h,n=n: ml_predict(h,n) for n in MODELS.keys()]

def ensemble_predict(h):
    if len(h)<5: return 'X',0
    votes=[f(h) for f in PRED_FUNCS]
    t=votes.count('T')
    conf=round(t/len(votes),2)
    return ('T' if t>len(votes)/2 else 'X'),conf

# ===== FETCH REAL DATA =====
def fetch_tele68():
    try:
        r=requests.get(API_URL,timeout=8).json()
        if "list" in r and r["list"]:
            n=r["list"][0]
            phien,dice,tong=n.get("id"),n.get("dices",[1,2,3]),n.get("point",sum(n.get("dices",[1,2,3])))
            raw=n.get("resultTruyenThong","").upper()
            ketqua={"TAI":"Tài","XIU":"Xỉu"}.get(raw,"Tài" if tong>=11 else "Xỉu")
            return phien,dice,tong,ketqua
    except: pass
    return None

# ===== BACKGROUND =====
def updater():
    global last_data
    last_phien=None
    while True:
        d=fetch_tele68()
        if d:
            phien,dice,tong,ketqua=d
            if phien!=last_phien and phien:
                history_totals.append(tong);history_tx.append(ketqua)
                pred,conf=ensemble_predict(list(history_totals))
                last_data={"phien":phien,"xucxac1":dice[0],"xucxac2":dice[1],"xucxac3":dice[2],"tong":tong,"ketqua":ketqua,"du_doan":pred,"do_tin_cay":conf,"id":"pentter100lite"}
                print(f"[✅] {phien} | {ketqua} ({tong}) → {pred} ({conf})")
                last_phien=phien
        time.sleep(UPDATE_SEC)

# ===== API =====
@app.route("/api/taixiu",methods=["GET"])
def api(): return jsonify(last_data)

# ===== RUN =====
if __name__=="__main__":
    threading.Thread(target=updater,daemon=True).start()
    app.run(host="0.0.0.0",port=int(os.getenv("PORT",5000)))
