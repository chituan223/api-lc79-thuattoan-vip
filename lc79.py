from flask import Flask, jsonify
import requests
import time
import threading
from collections import deque
import os

app = Flask(__name__)

# =========================================================
# 💾 HISTORY
# =========================================================
history = deque(maxlen=1000)
totals  = deque(maxlen=1000)

last_data = {
    "phien": None,
    "xucxac1": 0,
    "xucxac2": 0,
    "xucxac3": 0,
    "tong": 0,
    "ketqua": "",
    "du_doan": "Chờ dữ liệu...",
    "do_tin_cay": 0,
    "id": "địt mẹ lc79"
}

# =========================================================
# 🔹 API TELE68
# =========================================================
def get_taixiu_data():
    url = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
    try:
        res = requests.get(url, timeout=8)
        res.raise_for_status()
        data = res.json()

        if "list" in data and data["list"]:
            d = data["list"][0]
            dice = d.get("dices", [1,2,3])
            x1,x2,x3 = dice
            tong = d.get("point", x1+x2+x3)
            raw = d.get("resultTruyenThong","").upper()

            if raw=="TAI": kq="Tài"
            elif raw=="XIU": kq="Xỉu"
            else: kq="Tài" if tong>=11 else "Xỉu"

            return d.get("id"), x1,x2,x3, tong, kq
    except Exception as e:
        print("[API ERROR]",e)
    return None

# =========================================================
# 🔧 TO BLOCKS
# =========================================================
def to_blocks(h):
    if not h: return []
    seq = ['T' if x=='Tài' else 'X' for x in h]
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
# 🧠 HABYRI15 (01 → 20) – GIỮ NGUYÊN LOGIC BẠN GỬI
# =========================================================
def habyri15_01(h):
    if len(h)<7: return None,0
    b=to_blocks(h)
    if len(b)>=3 and b[-1][1]==1 and b[-2][1]>=3:
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),60
    return None,0

def habyri15_02(h):
    if len(h)<8: return None,0
    b=to_blocks(h)
    if len(b)>=4 and [x[1] for x in b[-4:]]==[1,1,1,1]:
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),62
    return None,0

def habyri15_03(h):
    if len(h)<9: return None,0
    b=to_blocks(h)
    if len(b)>=3 and b[-1][1]==2 and b[-2][1]==1:
        return ("Xỉu" if b[-1][0]=='T' else "Tài"),61
    return None,0

def habyri15_04(h):
    if len(h)<10: return None,0
    b=to_blocks(h)
    if len(b)>=4 and b[-3][1]>=4 and b[-2][1]==1:
        return ("Tài" if b[-2][0]=='X' else "Xỉu"),64
    return None,0

def habyri15_05(h):
    if len(h)<10: return None,0
    b=to_blocks(h)
    if len(b)>=5 and sum(x[1] for x in b[-5:])<=6:
        return ("Xỉu" if b[-1][0]=='T' else "Tài"),63
    return None,0

def habyri15_06(h):
    if len(h)<11: return None,0
    b=to_blocks(h)
    if len(b)>=3 and b[-1][1]==1 and b[-2][1]==1 and b[-3][1]>=4:
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),65
    return None,0

def habyri15_07(h):
    if len(h)<12: return None,0
    b=to_blocks(h)
    if len(b)>=4 and b[-4][1]>=5 and b[-3][1]==1:
        return ("Xỉu" if b[-3][0]=='T' else "Tài"),66
    return None,0

def habyri15_08(h):
    if len(h)<12: return None,0
    b=to_blocks(h)
    if len(b)>=5 and [x[1] for x in b[-5:]]==[2,1,1,1,1]:
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),64
    return None,0

def habyri15_09(h):
    if len(h)<13: return None,0
    b=to_blocks(h)
    if len(b)>=4 and b[-2][1]==2 and b[-1][1]==1:
        return ("Xỉu" if b[-1][0]=='T' else "Tài"),63
    return None,0

def habyri15_10(h):
    if len(h)<14: return None,0
    b=to_blocks(h)
    if len(b)>=5 and b[-5][1]>=4 and sum(x[1] for x in b[-4:])<=5:
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),67
    return None,0

def habyri15_11(h):
    if len(h)<15: return None,0
    b=to_blocks(h)
    if len(b)>=3 and b[-1][1]==1 and b[-2][1]>=5:
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),68
    return None,0

def habyri15_12(h):
    if len(h)<16: return None,0
    b=to_blocks(h)
    if len(b)>=4 and b[-3][1]>=6 and b[-2][1]==1:
        return ("Xỉu" if b[-2][0]=='T' else "Tài"),69
    return None,0

def habyri15_13(h):
    if len(h)<17: return None,0
    b=to_blocks(h)
    if len(b)>=5 and sum(x[1] for x in b[-3:])<=3:
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),64
    return None,0

def habyri15_14(h):
    if len(h)<18: return None,0
    b=to_blocks(h)
    if len(b)>=4 and b[-4][1]>=7 and b[-3][1]==1:
        return ("Xỉu" if b[-3][0]=='T' else "Tài"),70
    return None,0

def habyri15_15(h):
    if len(h)<18: return None,0
    b=to_blocks(h)
    if len(b)>=5 and b[-1][1]==2 and b[-2][1]==1:
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),63
    return None,0

def habyri15_16(h):
    if len(h)<19: return None,0
    b=to_blocks(h)
    if len(b)>=6 and b[-6][1]>=4 and sum(x[1] for x in b[-5:])<=6:
        return ("Xỉu" if b[-1][0]=='T' else "Tài"),71
    return None,0

def habyri15_17(h):
    if len(h)<20: return None,0
    b=to_blocks(h)
    if len(b)>=4 and b[-2][1]==1 and b[-1][1]==1:
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),60
    return None,0

def habyri15_18(h):
    if len(h)<20: return None,0
    b=to_blocks(h)
    if len(b)>=5 and b[-5][1]>=6:
        return ("Xỉu" if b[-1][0]=='T' else "Tài"),72
    return None,0

def habyri15_19(h):
    if len(h)<22: return None,0
    b=to_blocks(h)
    if len(b)>=6 and sum(x[1] for x in b[-4:])<=4:
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),66
    return None,0

def habyri15_20(h):
    if len(h)<25: return None,0
    b=to_blocks(h)
    if len(b)>=7 and b[-7][1]>=5:
        return ("Xỉu" if b[-1][0]=='T' else "Tài"),75
    return None,0

HABYRI_LIST = [
    habyri15_01, habyri15_02, habyri15_03, habyri15_04, habyri15_05,
    habyri15_06, habyri15_07, habyri15_08, habyri15_09, habyri15_10,
    habyri15_11, habyri15_12, habyri15_13, habyri15_14, habyri15_15,
    habyri15_16, habyri15_17, habyri15_18, habyri15_19, habyri15_20
]

# =========================================================
# 🧠 ENGINE CHỌN HABYRI MẠNH NHẤT
# =========================================================
def habyri_engine(history):
    best_pred=None
    best_conf=0
    for f in HABYRI_LIST:
        p,c=f(history)
        if p and c>best_conf:
            best_pred=p
            best_conf=c
    if best_pred:
        return best_pred, best_conf
    return None,0

# =========================================================
# 🔁 BACKGROUND
# =========================================================
def background_updater():
    global last_data
    last_phien=None
    while True:
        d=get_taixiu_data()
        if d:
            phien,x1,x2,x3,tong,kq=d
            if phien!=last_phien:
                history.append(kq)
                totals.append(tong)

                du_doan,conf = habyri_engine(list(history))

                last_data={
                    "phien":phien,
                    "xucxac1":x1,
                    "xucxac2":x2,
                    "xucxac3":x3,
                    "tong":tong,
                    "ketqua":kq,
                    "du_doan":du_doan if du_doan else "NO BET",
                    "do_tin_cay":conf,
                    "id":"địt mẹ lc79"
                }

                print(f"[HABYRI] {phien} | {kq} | {du_doan} | {conf}%")
                last_phien=phien
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
    threading.Thread(target=background_updater,daemon=True).start()
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
