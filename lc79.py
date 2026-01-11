from flask import Flask, jsonify
import requests, threading, time, os, math
from collections import deque

app = Flask(__name__)

# Cấu hình
API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
UPDATE_SEC = 5
HISTORY_MAX = 1000

# Bộ nhớ
history_totals = deque(maxlen=HISTORY_MAX)
history_tx = deque(maxlen=HISTORY_MAX)
last_data = {
    "phien": None, "xucxac1": 0, "xucxac2": 0, "xucxac3": 0,
    "tong": 0, "ketqua": "", "du_doan": "Đang khởi động 50 Pentter...", 
    "do_tin_cay": 0, "id": "pentter50real"
}

# ========== CÔNG CỤ TOÁN HỌC THUẦN PYTHON ==========
def get_mean(data):
    return sum(data) / len(data) if data else 0

def get_var(data):
    if len(data) < 2: return 0
    mu = get_mean(data)
    return sum((x - mu) ** 2 for x in data) / len(data)

def get_std(data):
    return math.sqrt(get_var(data))

def get_median(data):
    if not data: return 0
    s = sorted(data)
    n = len(s)
    return s[n//2] if n % 2 != 0 else (s[n//2-1] + s[n//2]) / 2

# ========== NHÓM 1: 20 RULE-BASED (LOGIC CƠ BẢN) ==========
def predict_00(h): return 'T' if len(h)>=10 and get_mean(h[-10:])<10.5 else 'X'
def predict_01(h):
    if len(h)<5: return 'X'
    last=h[-5:]
    if all(x>10.5 for x in last): return 'X'
    if all(x<10.5 for x in last): return 'T'
    return 'X'
def predict_02(h):
    if len(h)<20: return 'X'
    try:
        c = {}
        for x in h[-20:]: c[x] = c.get(x, 0) + 1
        ent = -sum((p/20)*math.log2(p/20) for p in c.values())
        return 'T' if ent<2.8 else 'X'
    except: return 'X'
def predict_03(h):
    if len(h)<10: return 'X'
    diffs = [h[i] - h[i-1] for i in range(1, len(h))]
    return 'T' if diffs.count(1) > diffs.count(-1) else 'X'
def predict_04(h):
    if len(h)<3: return 'X'
    trans={'TT':0,'TX':0,'XT':0,'XX':0}
    for i in range(1,len(h)):
        k=('T' if h[i-1]>10.5 else 'X')+('T' if h[i]>10.5 else 'X')
        if k in trans: trans[k]+=1
    last_s=('T' if h[-2]>10.5 else 'X')+('T' if h[-1]>10.5 else 'X')
    return 'T' if trans.get(last_s+'T',0)>trans.get(last_s+'X',0) else 'X'
def predict_05(h):
    if len(h)<15: return 'X'
    return 'T' if h[-1]>get_median(h[-15:]) else 'X'
def predict_06(h):
    if len(h)<20: return 'X'
    std = get_std(h[-20:])
    if std == 0: return 'X'
    z=(h[-1]-get_mean(h[-20:]))/std
    return 'T' if z>1.2 else 'X'
def predict_07(h):
    if len(h)<12: return 'X'
    return 'T' if max(h[-12:])-min(h[-12:])>12 else 'X'
def predict_08(h):
    if len(h)<7: return 'X'
    return 'T' if sum(x>10.5 for x in h[-7:])>=4 else 'X'
def predict_09(h):
    if len(h)<25: return 'X'
    tails=sum(1 for x in h[-25:] if x in {3,4,5,16,17,18})
    return 'T' if tails>5 else 'X'
def predict_10(h):
    if len(h)<5: return 'X'
    d=[h[i]-h[i-1] for i in range(-1,-4,-1)]
    return 'T' if all(x>0 for x in d) else 'X'
def predict_11(h):
    if len(h)<10: return 'X'
    return 'T' if get_var(h[-10:])<7 else 'X'
def predict_12(h):
    if len(h)<23: return 'X'
    return 'T' if len(set(h[-23:]))<15 else 'X'
def predict_13(h):
    if len(h)<30: return 'X'
    first=[int(str(int(x))[0]) for x in h[-30:]]
    return 'T' if first.count(1)<4 else 'X'
def predict_14(h):
    if len(h)<4: return 'X'
    return 'T' if h[-1]-h[-4]>4 else 'X'
def predict_15(h):
    if len(h)<10: return 'X'
    return 'T' if sum(x>12 for x in h[-10:])>=5 else 'X'
def predict_16(h):
    if len(h)<10: return 'X'
    return 'T' if sum(x<9 for x in h[-10:])<3 else 'X'
def predict_17(h):
    if len(h)<15: return 'X'
    s = sorted(h[-15:])
    q3 = s[int(len(s)*0.75)]
    return 'T' if q3>12 else 'X'
def predict_18(h):
    if len(h)<5: return 'X'
    return 'T' if sum(h[-5:]) > 52 else 'X'
def predict_19(h):
    if len(h)<9: return 'X'
    w=sorted(h[-9:]); m=w[4]
    return 'T' if m>10 else 'X'

# ========== NHÓM 2: 30 LOGIC MA TRẬN (THAY THẾ ML/JOBLIB) ==========
# Dùng các thuật toán băm (hashing) và nhịp đối xứng
def predict_matrix(h, step):
    if len(h) < 10: return 'X'
    # Tạo logic dựa trên tổng trọng số động của từng nhịp
    val = sum(h[-i] * (step + i) for i in range(1, 6))
    return 'T' if (val % 2 == 0) else 'X'

# ========== TỔNG HỢP ĐỒNG THUẬN 50 THUẬT TOÁN ==========
PRED_FUNCS = [globals()[f'predict_{i:02d}'] for i in range(20)]
for i in range(20, 50): # Thêm 30 logic ma trận
    PRED_FUNCS.append(lambda h, s=i: predict_matrix(h, s))



def ensemble_predict(h):
    if len(h) < 5: return 'X', 0
    votes = []
    for f in PRED_FUNCS:
        try:
            votes.append(f(h))
        except:
            votes.append('X')
    
    t_count = votes.count('T')
    conf = round(t_count / len(votes), 2)
    return ('T' if t_count > 25 else 'X'), conf

# ========== FETCH & UPDATE ==========
def fetch_tele68():
    try:
        r = requests.get(API_URL, timeout=8).json()
        if "list" in r and r["list"]:
            n = r["list"][0]
            phien = n.get("id")
            dice = n.get("dices", [1, 2, 3])
            tong = n.get("point", sum(dice))
            raw = n.get("resultTruyenThong", "").upper()
            ketqua = "Tài" if raw == "TAI" or tong >= 11 else "Xỉu"
            return phien, dice, tong, ketqua
    except: pass
    return None

def updater():
    global last_data
    last_phien = None
    while True:
        try:
            d = fetch_tele68()
            if d:
                phien, dice, tong, ketqua = d
                if phien != last_phien and phien:
                    history_totals.append(tong)
                    history_tx.append(ketqua)
                    pred, conf = ensemble_predict(list(history_totals))
                    last_data = {
                        "phien": phien, "xucxac1": dice[0], "xucxac2": dice[1], "xucxac3": dice[2],
                        "tong": tong, "ketqua": ketqua, "du_doan": pred, "do_tin_cay": conf, 
                        "id": "pentter50real"
                    }
                    print(f"[🔥] {phien}: {ketqua} ({tong}) -> {pred} ({int(conf*100)}%)")
                    last_phien = phien
        except: pass
        time.sleep(UPDATE_SEC)

@app.route("/api/taixiu", methods=["GET"])
def api(): return jsonify(last_data)

if __name__ == "__main__":
    # Chạy updater
    threading.Thread(target=updater, daemon=True).start()
    # Chạy Server
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
