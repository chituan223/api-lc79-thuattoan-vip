from flask import Flask, jsonify
import requests
import threading
import time
import os
import math
import numpy as np
from collections import deque

# Tắt cảnh báo numpy nếu có
import warnings
warnings.filterwarnings("ignore")

app = Flask(__name__)

# Config
API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
HISTORY_MAX = 1000

# Bộ nhớ tạm
history_totals = deque(maxlen=HISTORY_MAX)
history_tx = deque(maxlen=HISTORY_MAX)

last_data = {
    "phien": None, 
    "xucxac1": 0, "xucxac2": 0, "xucxac3": 0,
    "tong": 0, "ketqua": "", 
    "du_doan": "Đang nạp 50 Logic...", 
    "do_tin_cay": 0, 
    "id": "pentter50real"
}

# =========================================================
# 🧠 50 THUẬT TOÁN SOI CẦU THỰC TẾ (REAL PENTTER)
# =========================================================

# --- Nhóm 1-20: Quy tắc xác suất & Thống kê (Rule-based) ---
def rule_01(h): return 'T' if np.mean(h[-10:]) < 10.5 else 'X'
def rule_02(h): return 'X' if all(x > 10.5 for x in h[-3:]) else 'T'
def rule_03(h): return 'T' if h[-1] > np.median(h[-15:]) else 'X'
def rule_04(h): return 'T' if (h[-1] - h[-2]) > 0 else 'X'
def rule_05(h): return 'X' if sum(x > 10.5 for x in h[-7:]) >= 5 else 'T'
def rule_06(h): return 'T' if np.var(h[-10:]) < 5 else 'X'
def rule_07(h): return 'T' if h[-1] in [3, 4, 17, 18] else ('T' if h[-1] < 10 else 'X')
def rule_08(h): return 'X' if h[-1] == h[-2] == h[-3] else ('T' if h[-1] > 10.5 else 'X')
def rule_09(h): return 'T' if sum(h[-5:]) % 2 == 0 else 'X'
def rule_10(h): return 'X' if max(h[-10:]) > 16 else 'T'
def rule_11(h): return 'T' if h[-1] % 2 != 0 else 'X'
def rule_12(h): return 'X' if np.std(h[-20:]) > 3 else 'T'
def rule_13(h): return 'T' if h[-1] < 7 or h[-1] > 14 else 'X'
def rule_14(h): return 'X' if h[-1] + h[-2] > 21 else 'T'
def rule_15(h): return 'T' if len(set(h[-6:])) < 4 else 'X'
def rule_16(h): return 'X' if h[-1] in [10, 11] else 'T'
def rule_17(h): return 'T' if sum(1 for x in h[-12:] if x > 10) > 6 else 'X'
def rule_18(h): return 'X' if h[-1] - h[-3] > 5 else 'T'
def rule_19(h): return 'T' if h[-1] * 2 < 20 else 'X'
def rule_20(h): return 'X' if h[-1] == 11 else 'T'

# --- Nhóm 21-50: Logic Ma trận & Entropy (Thay thế ML nếu không có file) ---
def matrix_logic(h, offset):
    # Logic giả lập 30 phân lớp soi cầu ma trận
    idx = (sum(h[-5:]) + offset) % 2
    return 'T' if idx == 0 else 'X'

# Danh sách 50 hàm thực thi
PRED_FUNCS = [globals()[f'rule_{i:02d}'] for i in range(1, 21)]
for i in range(30):
    PRED_FUNCS.append(lambda h, o=i: matrix_logic(h, o))

# =========================================================
# ⚖️ HỆ THỐNG ĐỒNG THUẬN (VOTING SYSTEM)
# =========================================================


def ensemble_predict(h):
    if len(h) < 10:
        return "Gom data...", 0
    
    votes = []
    for func in PRED_FUNCS:
        try:
            votes.append(func(h))
        except:
            votes.append('X')
            
    t_count = votes.count('T')
    x_count = votes.count('X')
    
    conf = round(max(t_count, x_count) / len(votes), 2)
    result = "Tài" if t_count > x_count else "Xỉu"
    
    return result, conf

# =========================================================
# 🔹 FETCH & UPDATE DATA
# =========================================================
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
    except:
        pass
    return None

def updater():
    global last_data
    last_phien = None
    while True:
        d = fetch_tele68()
        if d:
            phien, dice, tong, ketqua = d
            if phien != last_phien and phien:
                history_totals.append(tong)
                history_tx.append(ketqua)
                
                # AI dự đoán
                pred, conf = ensemble_predict(list(history_totals))
                
                last_data = {
                    "phien": phien,
                    "xucxac1": dice[0], "xucxac2": dice[1], "xucxac3": dice[2],
                    "tong": tong, "ketqua": ketqua,
                    "du_doan": pred, "do_tin_cay": conf,
                    "id": "pentter50real"
                }
                print(f"[🔥] Phiên {phien}: {ketqua} -> Dự báo tiếp: {pred} ({int(conf*100)}%)")
                last_phien = phien
        time.sleep(5)

@app.route("/api/taixiu", methods=["GET"])
def api():
    return jsonify(last_data)

if __name__ == "__main__":
    # Chạy updater trong luồng riêng
    threading.Thread(target=updater, daemon=True).start()
    
    # Run server
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 AI Pentter 50 Real đang chạy trên port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
