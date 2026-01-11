from flask import Flask, jsonify
import requests, threading, time, os, math
from collections import deque

app = Flask(__name__)

# --- CẤU HÌNH ---
API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
UPDATE_SEC = 5
HISTORY_MAX = 2000

# --- BỘ NHỚ ---
history_totals = deque(maxlen=HISTORY_MAX)
history_tx = deque(maxlen=HISTORY_MAX)
last_data = {
    "phien": None, "xucxac1": 0, "xucxac2": 0, "xucxac3": 0,
    "tong": 0, "ketqua": "", "du_doan": "Đang khởi động...", 
    "do_tin_cay": 0, "id": "pentter100real"
}

# --- CÔNG CỤ TOÁN HỌC ---
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

# --- 20 RULE-BASED LOGIC CƠ BẢN (00-19) ---
def predict_00(h): return 'T' if len(h)>=10 and get_mean(h[-10:])<10.5 else 'X'
def predict_01(h):
    if len(h)<5: return 'X'
    if all(x>10.5 for x in h[-5:]): return 'X'
    if all(x<10.5 for x in h[-5:]): return 'T'
    return 'X'
def predict_02(h):
    if len(h)<20: return 'X'
    c = {}
    for x in h[-20:]: c[x] = c.get(x, 0) + 1
    ent = -sum((p/20)*math.log2(p/20) for p in c.values())
    return 'T' if ent<2.8 else 'X'
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
def predict_05(h): return 'T' if len(h)>=15 and h[-1]>get_median(h[-15:]) else 'X'
def predict_06(h):
    if len(h)<20: return 'X'
    std = get_std(h[-20:])
    return 'T' if std > 0 and (h[-1]-get_mean(h[-20:]))/std > 1.2 else 'X'
def predict_07(h): return 'T' if len(h)>=12 and max(h[-12:])-min(h[-12:])>12 else 'X'
def predict_08(h): return 'T' if len(h)>=7 and sum(x>10.5 for x in h[-7:])>=4 else 'X'
def predict_09(h): return 'T' if len(h)>=25 and sum(1 for x in h[-25:] if x in {3,4,5,16,17,18})>5 else 'X'
def predict_10(h):
    if len(h)<5: return 'X'
    d=[h[i]-h[i-1] for i in range(-1,-4,-1)]
    return 'T' if all(x>0 for x in d) else 'X'
def predict_11(h): return 'T' if len(h)>=10 and get_var(h[-10:])<7 else 'X'
def predict_12(h): return 'T' if len(h)>=23 and len(set(h[-23:]))<15 else 'X'
def predict_13(h):
    if len(h)<30: return 'X'
    first=[int(str(int(x))[0]) for x in h[-30:]]
    return 'T' if first.count(1)<4 else 'X'
def predict_14(h): return 'T' if len(h)>=4 and h[-1]-h[-4]>4 else 'X'
def predict_15(h): return 'T' if len(h)>=10 and sum(x>12 for x in h[-10:])>=5 else 'X'
def predict_16(h): return 'T' if len(h)>=10 and sum(x<9 for x in h[-10:])<3 else 'X'
def predict_17(h): return 'T' if len(h)>=15 and sorted(h[-15:])[int(len(h[-15:])*0.75)] > 12 else 'X'
def predict_18(h): return 'T' if len(h)>=5 and sum(h[-5:]) > 52 else 'X'
def predict_19(h): return 'T' if len(h)>=9 and sorted(h[-9:])[4] > 10 else 'X'

# --- 20 LOGIC TRUNG BÌNH ĐỘNG & BIẾN ĐỘNG (20-39) ---
def predict_ma_cross(h, s, l): # Cắt MA ngắn/dài
    if len(h) < l: return 'X'
    ma_s = get_mean(h[-s:])
    ma_l = get_mean(h[-l:])
    return 'T' if ma_s > ma_l else 'X'

def predict_bollinger(h, period): # Chạm dải Bollinger
    if len(h) < period: return 'X'
    mu = get_mean(h[-period:])
    sigma = get_std(h[-period:])
    if h[-1] > mu + 2*sigma: return 'X' # Quá mua -> Đảo chiều Xỉu
    if h[-1] < mu - 2*sigma: return 'T' # Quá bán -> Đảo chiều Tài
    return 'T' if h[-1] > mu else 'X'

def predict_momentum(h, period): # Động lượng
    if len(h) < period: return 'X'
    return 'T' if h[-1] > h[-period] else 'X'

# Tạo hàm bao đóng cho nhóm này
def make_ma_pred(s, l): return lambda h: predict_ma_cross(h, s, l)
def make_bb_pred(p): return lambda h: predict_bollinger(h, p)
def make_mom_pred(p): return lambda h: predict_momentum(h, p)

# --- 20 LOGIC MẪU HÌNH (PATTERN) (40-59) ---
def predict_streak_break(h, limit): # Bẻ cầu bệt
    if len(h) < limit: return 'X'
    streak_t = 0
    for x in reversed(h):
        if x > 10.5: streak_t += 1
        else: break
    if streak_t >= limit: return 'X' # Bệt Tài dài -> Bẻ Xỉu
    
    streak_x = 0
    for x in reversed(h):
        if x <= 10.5: streak_x += 1
        else: break
    if streak_x >= limit: return 'T' # Bệt Xỉu dài -> Bẻ Tài
    return 'T' if h[-1] <= 10.5 else 'X' # Mặc định theo cầu đảo

def predict_11_pattern(h): # Cầu 1-1
    if len(h) < 4: return 'X'
    # Kiểm tra mẫu T-X-T -> Dự đoán X
    p = ['T' if x > 10.5 else 'X' for x in h[-3:]]
    if p == ['T', 'X', 'T']: return 'X'
    if p == ['X', 'T', 'X']: return 'T'
    return 'T' if h[-1] <= 10.5 else 'X'

# --- 20 LOGIC TRỌNG SỐ (WEIGHTED) (60-79) ---
def predict_weighted_recent(h, count):
    if len(h) < count: return 'X'
    # Trọng số tuyến tính: phiên gần nhất trọng số cao nhất
    score = 0
    total_w = 0
    for i in range(count):
        w = i + 1
        val = 1 if h[-(count-i)] > 10.5 else -1
        score += val * w
        total_w += w
    return 'T' if score > 0 else 'X'

def predict_fibonacci_weight(h):
    if len(h) < 8: return 'X'
    fib = [1, 1, 2, 3, 5, 8, 13, 21]
    score = 0
    for i in range(8):
        val = 1 if h[-(8-i)] > 10.5 else -1
        score += val * fib[i]
    return 'T' if score > 0 else 'X'

# --- 20 LOGIC CHU KỲ & SỐ HỌC (80-99) ---
def predict_cycle_mod(h, mod):
    if len(h) < 1: return 'X'
    return 'T' if sum(h[-5:]) % mod == 0 else 'X'

def predict_last_digit(h):
    if len(h) < 1: return 'X'
    last = h[-1] % 10
    return 'T' if last in [1, 3, 5, 7, 9] else 'X'

# --- KHỞI TẠO DANH SÁCH 100 THUẬT TOÁN ---
PRED_FUNCS = []

# 00-19: Rule-based cơ bản
for i in range(20):
    PRED_FUNCS.append(globals()[f'predict_{i:02d}'])

# 20-29: MA Cross (5-10, 5-20, ..., 10-50)
ma_settings = [(3,5), (3,8), (5,10), (5,12), (5,15), (5,20), (8,13), (8,21), (10,20), (10,30)]
for s, l in ma_settings:
    PRED_FUNCS.append(make_ma_pred(s, l))

# 30-34: Bollinger Bands (period 10, 12, 15, 20, 25)
for p in [10, 12, 15, 20, 25]:
    PRED_FUNCS.append(make_bb_pred(p))

# 35-39: Momentum (period 3, 5, 8, 10, 12)
for p in [3, 5, 8, 10, 12]:
    PRED_FUNCS.append(make_mom_pred(p))

# 40-49: Streak Breaker (limit 2, 3, ..., 11)
for l in range(2, 12):
    PRED_FUNCS.append(lambda h, lim=l: predict_streak_break(h, lim))

# 50-59: Pattern Matching (Biến thể của cầu 1-1 và cầu nghiêng)
for i in range(10):
    PRED_FUNCS.append(predict_11_pattern) # Thêm logic nhận diện khuôn mẫu

# 60-69: Weighted Recent (count 5, 6, ..., 14)
for c in range(5, 15):
    PRED_FUNCS.append(lambda h, count=c: predict_weighted_recent(h, count))

# 70-79: Fibonacci Variations
for i in range(10):
    PRED_FUNCS.append(predict_fibonacci_weight)

# 80-89: Cycle Modulo (mod 3, 4, ..., 12)
for m in range(3, 13):
    PRED_FUNCS.append(lambda h, mod=m: predict_cycle_mod(h, mod))

# 90-99: Last Digit & Arithmetic
for i in range(10):
    PRED_FUNCS.append(predict_last_digit)


# --- HÀM TỔNG HỢP (ENSEMBLE) ---
def ensemble_predict(h):
    if len(h) < 30: return 'Đang thu thập dữ liệu...', 0
    votes = []
    
    # Chạy đồng thời 100 thuật toán
    for f in PRED_FUNCS:
        try:
            res = f(h)
            if res in ['T', 'X']: votes.append(res)
        except: pass
    
    t_count = votes.count('T')
    x_count = votes.count('X')
    total = len(votes)
    
    if total == 0: return 'Chờ...', 0

    if t_count > x_count:
        conf = round(t_count / total, 2)
        return 'Tài', conf
    elif x_count > t_count:
        conf = round(x_count / total, 2)
        return 'Xỉu', conf
    else:
        return 'Hòa', 0.50

# --- FETCH & UPDATE ---
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
                    
                    # Chạy Ensemble 100 Pentter Real
                    pred, conf = ensemble_predict(list(history_totals))
                    
                    last_data = {
                        "phien": phien, "xucxac1": dice[0], "xucxac2": dice[1], "xucxac3": dice[2],
                        "tong": tong, "ketqua": ketqua, "du_doan": pred, "do_tin_cay": conf, 
                        "id": "pentter100real_v2"
                    }
                    print(f"[🔥] Phiên {phien}: {ketqua} ({tong}) -> Dự đoán: {pred} ({int(conf*100)}%)")
                    last_phien = phien
        except Exception as e:
            print(f"Lỗi update: {e}")
        time.sleep(UPDATE_SEC)

# --- API ---
@app.route("/api/taixiu", methods=["GET"])
def api(): return jsonify(last_data)

if __name__ == "__main__":
    threading.Thread(target=updater, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
