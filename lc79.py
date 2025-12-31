from flask import Flask, jsonify
import requests
import time
import threading
from collections import deque
import os
import math

app = Flask(__name__)

# =========================================================
# 💾 Bộ nhớ tạm
# =========================================================
history = deque(maxlen=1000)

last_data = {
    "phien": None,
    "xuc_xac_1": 0,
    "xuc_xac_2": 0,
    "xuc_xac_3": 0,
    "tong": 0,
    "ketqua": "",
    "du_doan": "Đang khởi động...",
    "do_tin_cay": 0,
    "suc_manh": 0,
    "entropy": 0,
    "con_lai": 5,  # Mặc định cần gom 5 phiên
    "id": "địt mẹ lc79"
}

# =========================================================
# 🧠 CORE ALGORITHM: ML CONSENSUS (FAST MODE)
# =========================================================
def master_ai_engine(history_list):
    count = len(history_list)
    nguong_du_doan = 5
    
    # Nếu chưa đủ 5 phiên, trả về số phiên còn thiếu
    if count < nguong_du_doan:
        con_lai = nguong_du_doan - count
        return {
            "du_doan": f"Gom data ({count}/{nguong_du_doan})", 
            "do_tin_cay": 0, 
            "suc_manh": 0, 
            "entropy": 0,
            "con_lai": con_lai
        }

    h = list(history_list)[-60:]
    data = [1 if x == "Tài" else 0 for x in h]
    
    w_t = 0.0 
    w_x = 0.0 

    # --- LỚP 1: BAYESIAN INFERENCE ---
    max_range = min(6, count)
    for length in range(2, max_range): 
        curr = data[-length:]
        for i in range(len(data) - length - 1):
            if data[i:i+length] == curr:
                if data[i+length] == 1: w_t += (15.0 * length)
                else: w_x += (15.0 * length)

    # --- LỚP 2: SHANNON ENTROPY ---
    def calculate_entropy(seq):
        if len(seq) < 2: return 0.9
        p_t = seq.count(1) / len(seq)
        p_x = 1 - p_t
        if p_t == 0 or p_x == 0: return 0.1
        return - (p_t * math.log2(p_t) + p_x * math.log2(p_x))

    entropy_recent = calculate_entropy(data[-15:])
    if entropy_recent < 0.6:
        if data[-1] == 1: w_t += 100.0
        else: w_x += 100.0

    # --- LỚP 3: DYNAMIC MARKOV ---
    transitions = {"1": {"next_1": 0, "next_0": 0}, "0": {"next_1": 0, "next_0": 0}}
    for i in range(len(data)-1):
        state = str(data[i])
        nxt = data[i+1]
        transitions[state]["next_1" if nxt == 1 else "next_0"] += 1
    
    curr_state = str(data[-1])
    w_t += (transitions[curr_state].get("next_1", 0) * 15)
    w_x += (transitions[curr_state].get("next_0", 0) * 15)

    # --- LỚP 4: STREAK ANALYSIS ---
    stk = 1
    for i in range(len(h)-2, -1, -1):
        if h[i] == h[-1]: stk += 1
        else: break
    
    if stk >= 3:
        rev_power = (stk ** 2) * 15
        if h[-1] == "Tài": w_x += rev_power
        else: w_t += rev_power

    # --- TỔNG HỢP ---
    total_w = w_t + w_x
    diff = abs(w_t - w_x)

    if total_w == 0 or diff < 40:
        return {"du_doan": "CHỜ NHỊP", "do_tin_cay": 0, "suc_manh": 0, "entropy": round(entropy_recent, 3), "con_lai": 0}

    prediction = "Tài" if w_t > w_x else "Xỉu"
    conf = (max(w_t, w_x) / total_w) * 100

    return {
        "du_doan": prediction,
        "do_tin_cay": round(min(conf, 98.5), 2),
        "suc_manh": round(diff, 1),
        "entropy": round(entropy_recent, 3),
        "streak": stk,
        "con_lai": 0 # Khi đã dự đoán thì con_lai = 0
    }

# =========================================================
# 🔹 API Fetching & Background Task
# =========================================================
def get_taixiu_data():
    url = "https://wtxmd52.tele68.com/v1/txmd5/sessions" 
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        if "list" in data and len(data["list"]) > 0:
            new = data["list"][0]
            phien = new.get("id")
            dice = new.get("dices", [1, 2, 3])
            tong = new.get("point", sum(dice))
            raw = new.get("resultTruyenThong", "").upper()
            kq = "Tài" if raw == "TAI" or tong >= 11 else "Xỉu"
            return phien, dice, tong, kq
    except: pass
    return None

def background_updater():
    global last_data
    last_p = None
    while True:
        data = get_taixiu_data()
        if data:
            phien, dice, tong, kq = data
            if phien != last_p:
                history.append(kq)
                res = master_ai_engine(history)
                last_data = {
                    "phien": phien, 
                    "xuc_xac_1": dice[0], "xuc_xac_2": dice[1], "xuc_xac_3": dice[2],
                    "tong": tong, "ketqua": kq, 
                    "du_doan": res["du_doan"], 
                    "do_tin_cay": res["do_tin_cay"],
                    "suc_manh": res["suc_manh"], 
                    "entropy": res["entropy"], 
                    "streak": res.get("streak", 0),
                    "con_lai": res["con_lai"], # Trả về số phiên còn lại
                    "id": "địt mẹ lc79"
                }
                print(f"[🔥] Phiên {phien}: {kq} | Dự báo: {res['du_doan']} | Còn lại: {res['con_lai']}")
                last_p = phien
        time.sleep(4)

@app.route("/api/taixiu", methods=["GET"])
def api_taixiu():
    return jsonify(last_data)

if __name__ == "__main__":
    threading.Thread(target=background_updater, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
