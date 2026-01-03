from flask import Flask, jsonify
import requests, threading, time, os
from collections import deque

app = Flask(__name__)

# =========================================================
# 💾 HISTORY
# =========================================================
history = deque(maxlen=1000)

last_data = {
    "phien": None,
    "xucxac1": 0,
    "xucxac2": 0,
    "xucxac3": 0,
    "tong": 0,
    "ketqua": "",
    "du_doan": None,
    "do_tin_cay": 0,
    "pentter": None,
    "id": "lc79"
}

# =========================================================
# 🔹 API TELE68
# =========================================================
def get_taixiu_data():
    url = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
    try:
        r = requests.get(url, timeout=8).json()
        d = r["list"][0]

        dices = d.get("dices", [1,2,3])
        x1, x2, x3 = dices
        tong = d.get("point", x1+x2+x3)

        raw = d.get("resultTruyenThong","").upper()
        kq = "Tài" if raw=="TAI" else "Xỉu" if raw=="XIU" else ("Tài" if tong>=11 else "Xỉu")

        return d["id"], kq, tong, x1, x2, x3
    except:
        return None

# =========================================================
# 🔧 BLOCK UTILS
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
# 🧠 PENTTER 01 → 25 (GIỮ NGUYÊN)
# =========================================================
def pentter_01(h):
    if len(h)<6: return None,0
    b=to_blocks(h)
    if len(b)>=3 and b[-2][1]>=3 and b[-1][1]==1:
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),62
    return None,0

def pentter_02(h):
    if len(h)<7: return None,0
    b=to_blocks(h)
    if len(b)>=4 and b[-3][1]>=3 and b[-2][1]==1 and b[-1][1]==1:
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),64
    return None,0

def pentter_03(h):
    if len(h)<8: return None,0
    b=to_blocks(h)
    if len(b)>=4 and [x[1] for x in b[-4:]]==[3,1,1,1]:
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),65
    return None,0

def pentter_04(h):
    if len(h)<7: return None,0
    b=to_blocks(h)
    if len(b)>=3 and b[-3][1]>=4 and b[-2][1]==1:
        return ("Xỉu" if b[-2][0]=='T' else "Tài"),63
    return None,0

def pentter_05(h):
    if len(h)<8: return None,0
    b=to_blocks(h)
    if len(b)>=4 and b[-4][1]>=4 and b[-3][1]==1 and b[-2][1]==1:
        return ("Xỉu" if b[-2][0]=='T' else "Tài"),66
    return None,0

def pentter_06(h):
    if len(h)<9: return None,0
    b=to_blocks(h)
    if len(b)>=5 and b[-5][1]>=3 and all(x[1]==1 for x in b[-4:]):
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),67
    return None,0

def pentter_07(h):
    if len(h)<8: return None,0
    b=to_blocks(h)
    if len(b)>=3 and b[-2][1]==1 and b[-1][1]==2:
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),61
    return None,0

def pentter_08(h):
    if len(h)<9: return None,0
    b=to_blocks(h)
    if len(b)>=4 and [x[1] for x in b[-4:]]==[2,1,1,2]:
        return ("Xỉu" if b[-1][0]=='T' else "Tài"),64
    return None,0

def pentter_09(h):
    if len(h)<10: return None,0
    b=to_blocks(h)
    if len(b)>=5 and b[-3][1]>=3 and b[-2][1]==1 and b[-1][1]==2:
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),66
    return None,0

def pentter_10(h):
    if len(h)<10: return None,0
    b=to_blocks(h)
    if len(b)>=4 and b[-4][1]>=5 and b[-3][1]==1:
        return ("Xỉu" if b[-3][0]=='T' else "Tài"),68
    return None,0

def pentter_11(h):
    if len(h)<12: return None,0
    b=to_blocks(h)
    if len(b)>=3 and b[-2][1]>=5 and b[-1][1]==1:
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),70
    return None,0

def pentter_12(h):
    if len(h)<14: return None,0
    b=to_blocks(h)
    if len(b)>=4 and b[-3][1]>=5 and b[-2][1]==1 and b[-1][1]==1:
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),71
    return None,0

def pentter_13(h):
    if len(h)<15: return None,0
    b=to_blocks(h)
    if len(b)>=5 and b[-5][1]>=4 and sum(x[1] for x in b[-4:])<=5:
        return ("Xỉu" if b[-1][0]=='T' else "Tài"),69
    return None,0

def pentter_14(h):
    if len(h)<16: return None,0
    b=to_blocks(h)
    if len(b)>=4 and b[-4][1]>=6 and b[-3][1]==1:
        return ("Xỉu" if b[-3][0]=='T' else "Tài"),72
    return None,0

def pentter_15(h):
    if len(h)<18: return None,0
    b=to_blocks(h)
    if len(b)>=5 and b[-4][1]>=5 and b[-3][1]==1 and b[-2][1]==1:
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),73
    return None,0

def pentter_16(h):
    if len(h)<10: return None,0
    b=to_blocks(h)
    if len(b)>=3 and b[-1][1]==1 and b[-2][1]==1 and b[-3][1]>=4:
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),65
    return None,0

def pentter_17(h):
    if len(h)<11: return None,0
    b=to_blocks(h)
    if len(b)>=4 and [x[1] for x in b[-4:]]==[4,1,1,1]:
        return ("Xỉu" if b[-1][0]=='T' else "Tài"),66
    return None,0

def pentter_18(h):
    if len(h)<12: return None,0
    b=to_blocks(h)
    if len(b)>=5 and b[-5][1]>=3 and b[-4][1]==1 and b[-3][1]==1:
        return ("Xỉu" if b[-3][0]=='T' else "Tài"),67
    return None,0

def pentter_19(h):
    if len(h)<13: return None,0
    b=to_blocks(h)
    if len(b)>=4 and b[-4][1]>=5 and b[-3][1]==1 and b[-2][1]>=2:
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),68
    return None,0

def pentter_20(h):
    if len(h)<14: return None,0
    b=to_blocks(h)
    if len(b)>=5 and b[-5][1]>=6 and sum(x[1] for x in b[-4:])<=6:
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),70
    return None,0

def pentter_21(h):
    if len(h)<15: return None,0
    b=to_blocks(h)
    if len(b)>=3 and b[-2][1]>=6 and b[-1][1]==1:
        return ("Xỉu" if b[-1][0]=='T' else "Tài"),72
    return None,0

def pentter_22(h):
    if len(h)<16: return None,0
    b=to_blocks(h)
    if len(b)>=4 and b[-3][1]>=6 and b[-2][1]==1 and b[-1][1]==1:
        return ("Xỉu" if b[-1][0]=='T' else "Tài"),73
    return None,0

def pentter_23(h):
    if len(h)<17: return None,0
    b=to_blocks(h)
    if len(b)>=5 and b[-5][1]>=5 and sum(x[1] for x in b[-4:])<=5:
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),71
    return None,0

def pentter_24(h):
    if len(h)<18: return None,0
    b=to_blocks(h)
    if len(b)>=4 and b[-4][1]>=7 and b[-3][1]==1:
        return ("Xỉu" if b[-3][0]=='T' else "Tài"),74
    return None,0

def pentter_25(h):
    if len(h)<20: return None,0
    b=to_blocks(h)
    if len(b)>=5 and b[-4][1]>=6 and b[-3][1]==1 and b[-2][1]==1:
        return ("Tài" if b[-1][0]=='X' else "Xỉu"),75
    return None,0

PENTTERS = [
    pentter_01,pentter_02,pentter_03,pentter_04,pentter_05,
    pentter_06,pentter_07,pentter_08,pentter_09,pentter_10,
    pentter_11,pentter_12,pentter_13,pentter_14,pentter_15,
    pentter_16,pentter_17,pentter_18,pentter_19,pentter_20,
    pentter_21,pentter_22,pentter_23,pentter_24,pentter_25
]

# =========================================================
# 🧠 ENGINE CHỌN PENTTER MẠNH NHẤT
# =========================================================
def pentter_engine(history):
    best=None
    best_conf=0
    for i,p in enumerate(PENTTERS,1):
        r,c=p(history)
        if r and c>best_conf:
            best=r
            best_conf=c
            best_name=f"pentter_{i:02d}"
    if best:
        return best,best_conf,best_name
    return None,0,None

# =========================================================
# 🔁 BACKGROUND
# =========================================================
def background():
    last=None
    global last_data
    while True:
        d=get_taixiu_data()
        if d:
            phien,kq,tong,x1,x2,x3=d
            if phien!=last:
                history.append(kq)
                du_doan,conf,name = pentter_engine(list(history))
                last_data={
                    "phien":phien,
                    "xucxac1":x1,
                    "xucxac2":x2,
                    "xucxac3":x3,
                    "tong":tong,
                    "ketqua":kq,
                    "du_doan":du_doan,
                    "do_tin_cay":conf,
                    "pentter":name,
                    "id":"lc79"
                }
                print(last_data)
                last=phien
        time.sleep(5)

@app.route("/api/taixiu")
def api():
    return jsonify(last_data)

if __name__=="__main__":
    threading.Thread(target=background,daemon=True).start()
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
