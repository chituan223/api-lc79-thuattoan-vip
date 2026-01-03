from flask import Flask, jsonify
import requests, time, threading, os
from collections import deque, defaultdict

app = Flask(__name__)

# =========================================================
# 💾 HISTORY
# =========================================================
history = deque(maxlen=1000)
totals  = deque(maxlen=1000)

last_data = {
    "phien": None,
    "ketqua": "",
    "du_doan": "",
    "do_tin_cay": 0,
    "pattern": "",
    "mode": "INIT",
    "id": "địt mẹ lc79"
}

# =========================================================
# 🔹 API
# =========================================================
def get_taixiu_data():
    url = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
    try:
        r = requests.get(url, timeout=8).json()
        d = r["list"][0]
        tong = d.get("point", sum(d.get("dices", [1,2,3])))
        raw = d.get("resultTruyenThong", "").upper()
        kq = "Tài" if raw=="TAI" else "Xỉu" if raw=="XIU" else ("Tài" if tong>=11 else "Xỉu")
        return d["id"], kq, tong
    except:
        return None

# =========================================================
# 🔧 UTILS
# =========================================================
def to_TX(seq):
    return ['T' if x=='Tài' else 'X' for x in seq]

def to_blocks(seq):
    blocks=[]
    cur=seq[0]; cnt=1
    for s in seq[1:]:
        if s==cur: cnt+=1
        else:
            blocks.append((cur,cnt))
            cur=s; cnt=1
    blocks.append((cur,cnt))
    return blocks

# =========================================================
# 🧠 GROUP 1 – BLOCK PENTTER
# =========================================================
def block_pentter(seq):
    blocks = to_blocks(seq)
    vote={"Tài":0.0,"Xỉu":0.0}

    for size in range(3,7):
        for i in range(len(blocks)-size):
            pat = tuple(blocks[i:i+size])
            next_b = blocks[i+size][0]
            if tuple(blocks[-size:])==pat:
                weight = size * blocks[i+size][1]
                vote["Tài" if next_b=='T' else "Xỉu"] += weight

    return vote, "BLOCK"

# =========================================================
# 🧠 GROUP 2 – SEQUENCE SHAPE
# =========================================================
def sequence_pentter(seq):
    vote={"Tài":0.0,"Xỉu":0.0}
    for size in range(4,9):
        cur = seq[-size:]
        hits=[]
        for i in range(len(seq)-size):
            if seq[i:i+size]==cur:
                hits.append(seq[i+size])
        if len(hits)>=2:
            w = len(hits)*size
            if hits.count('T')>hits.count('X'):
                vote["Tài"]+=w
            else:
                vote["Xỉu"]+=w
    return vote, "SEQ"

# =========================================================
# 🧠 GROUP 3 – TRANSITION
# =========================================================
def transition_pentter(seq):
    vote={"Tài":0.0,"Xỉu":0.0}
    for size in range(3,6):
        cur = seq[-size:]
        t=x=0
        for i in range(len(seq)-size):
            if seq[i:i+size]==cur:
                if seq[i+size]=='T': t+=1
                else: x+=1
        if t+x>=3:
            w=(t+x)*size
            vote["Tài" if t>x else "Xỉu"]+=w
    return vote, "TRANS"

# =========================================================
# 🧠 GROUP 4 – STREAK PRESSURE
# =========================================================
def pressure_pentter(seq):
    vote={"Tài":0.0,"Xỉu":0.0}
    tail=seq[-10:]
    t=tail.count('T'); x=tail.count('X')
    if t>=7: vote["Xỉu"]+=t
    if x>=7: vote["Tài"]+=x
    if abs(t-x)>=4:
        vote["Tài" if t>x else "Xỉu"]+=abs(t-x)*2
    return vote, "PRESS"

# =========================================================
# 🧠 MASTER ENGINE (NHIỀU THUẬT TOÁN)
# =========================================================
def multi_pentter_engine(history):
    if len(history)<10:
        return None,0,"","INIT"

    seq = to_TX(history)
    total_vote={"Tài":0.0,"Xỉu":0.0}
    used=[]

    for func in [block_pentter, sequence_pentter, transition_pentter, pressure_pentter]:
        v, name = func(seq)
        if v["Tài"]>0 or v["Xỉu"]>0:
            total_vote["Tài"]+=v["Tài"]
            total_vote["Xỉu"]+=v["Xỉu"]
            used.append(name)

    if total_vote["Tài"]==0 and total_vote["Xỉu"]==0:
        return ("Tài" if seq.count('T')>=seq.count('X') else "Xỉu"),55,"FREQ","FALLBACK"

    if total_vote["Tài"]>=total_vote["Xỉu"]:
        conf=int(total_vote["Tài"]/(total_vote["Tài"]+total_vote["Xỉu"])*100)
        return "Tài",min(conf,75),"+".join(used),"PENTTER"
    else:
        conf=int(total_vote["Xỉu"]/(total_vote["Tài"]+total_vote["Xỉu"])*100)
        return "Xỉu",min(conf,75),"+".join(used),"PENTTER"

# =========================================================
# 🔁 BACKGROUND
# =========================================================
def background():
    global last_data
    last=None
    while True:
        d=get_taixiu_data()
        if d:
            phien,kq,tong=d
            if phien!=last:
                history.append(kq)
                totals.append(tong)

                du_doan,conf,pat,mode = multi_pentter_engine(list(history))

                last_data={
                    "phien":phien,
                    "ketqua":kq,
                    "du_doan":du_doan,
                    "do_tin_cay":conf,
                    "pattern":pat,
                    "mode":mode,
                    "id":"địt mẹ lc79"
                }
                print(f"[{mode}] {phien} | {kq} | {du_doan} | {conf}% | {pat}")
                last=phien
        time.sleep(5)

# =========================================================
# 🌐 API
# =========================================================
@app.route("/api/taixiu")
def api():
    return jsonify(last_data)

# =========================================================
# 🚀 RUN
# =========================================================
if __name__=="__main__":
    threading.Thread(target=background,daemon=True).start()
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
