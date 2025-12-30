from flask import Flask, jsonify
import requests
import time
import threading
from collections import deque
import os
import math

app = Flask(__name__)

# =========================================================
# 💾 Bộ nhớ tạm – lưu trữ lịch sử phiên thực tế
# =========================================================
history = deque(maxlen=1000)

last_data = {
    "phien": None,
    "xuc_xac_1": 0,
    "xuc_xac_2": 0,
    "xuc_xac_3": 0,
    "tong": 0,
    "ketqua": "",
    "du_doan": "Khởi động AI...",
    "do_tin_cay": 0,
    "suc_manh": 0,
    "entropy": 0,
    "id": "địt mẹ lc79"
}

# =========================================================
# 🧠 CORE ALGORITHM: MACHINE LEARNING CONSENSUS (VIP PRO)
# =========================================================
def master_ai_engine(history_list):
    # Cần tối thiểu 60 phiên để tính toán Entropy và Markov chuẩn xác
    if len(history_list) < 60:
        return {"du_doan": "AI đang phân tích trạng thái...", "do_tin_cay": 0, "suc_manh": 0, "entropy": 0}

    h = list(history_list)[-60:]
    data = [1 if x == "Tài" else 0 for x in h]
    
    w_t = 0.0 # Trọng số Tài
    w_x = 0.0 # Trọng số Xỉu

    # --- LỚP 1: BAYESIAN INFERENCE (Soi chu kỳ lặp sâu 5 tầng) ---
    for length in range(2, 6): 
        curr = data[-length:]
        for i in range(len(data) - length - 1):
            if data[i:i+length] == curr:
                if data[i+length] == 1: w_t += (15.0 * length)
                else: w_x += (15.0 * length)

    # --- LỚP 2: SHANNON ENTROPY (Đo lường độ hỗn loạn) ---
    def calculate_entropy(seq):
        if not seq: return 0
        p_t = seq.count(1) / len(seq)
        p_x = 1 - p_t
        if p_t == 0 or p_x == 0: return 0
        return - (p_t * math.log2(p_t) + p_x * math.log2(p_x))

    entropy_recent = calculate_entropy(data[-15:])
    if entropy_recent < 0.5:
        if data[-1] == 1: w_t += 110.0
        else: w_x += 110.0

    # --- LỚP 3: DYNAMIC MARKOV (Xác suất chuyển trạng thái thực) ---
    transitions = {"1": {"next_1": 0, "next_0": 0}, "0": {"next_1": 0, "next_0": 0}}
    for i in range(len(data)-1):
        state = str(data[i])
        nxt = data[i+1]
        transitions[state]["next_1" if nxt == 1 else "next_0"] += 1
    
    curr_state = str(data[-1])
    w_t += (transitions[curr_state]["next_1"] * 12)
    w_x += (transitions[curr_state]["next_0"] * 12)

    # --- LỚP 4: MEAN REVERSION & STREAK ANALYSIS ---
    avg_full = sum(data) / len(data)
    if avg_full > 0.65: w_x += 130.0
    elif avg_full < 0.35: w_t += 130.0

    stk = 1
    for i in range(len(h)-2, -1, -1):
        if h[i] == h[-1]: stk += 1
        else: break
    
    if stk >= 4:
        rev_power = (stk ** 2) * (1 + entropy_recent) * 10
        if h[-1] == "Tài": w_x += rev_power
        else: w_t += rev_power

    # --- TỔNG HỢP VÀ ĐƯA RA QUYẾT ĐỊNH ---
    total_w = w_t + w_x
    diff = abs(w_t - w_x)

    if total_w == 0 or diff < 100:
        return {"du_doan": "CHỜ TÍN HIỆU", "do_tin_cay": 0, "suc_manh": 0, "entropy": round(entropy_recent, 3)}

    prediction = "Tài" if w_t > w_x else "Xỉu"
    conf = (max(w_t, w_x) / total_w) * 100

    return {
        "du_doan": prediction,
        "do_tin_cay": round(min(conf, 98.5), 2),
        "suc_manh": round(diff, 1),
        "entropy": round(entropy_recent, 3),
        "streak": stk
    }

# =========================================================
# 🔹 API Fetching (Kết nối dữ liệu Tele68)
# =========================================================
def get_taixiu_data():
    url = "https://wtxmd52.tele68.com/v1/txmd5/sessions" 
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
        if "list" in data and len(data["list"]) > 0:
            newest = data["list"][0]
            phien = newest.get("id")
            dice = newest.get("dices", [1, 2, 3])
            tong = newest.get("point", sum(dice))
            
            raw_result = newest.get("resultTruyenThong", "").upper()
            if raw_result == "TAI":
                ket_qua = "Tài"
            elif raw_result == "XIU":
                ket_qua = "Xỉu"
            else:
                ket_qua = "Tài" if tong >= 11 else "Xỉu" 
                
            return phien, dice, tong, ket_qua
    except Exception as e:
        print(f"[❌] Lỗi kết nối API: {e}")
    return None

# =========================================================
# 🔹 Thread cập nhật dữ liệu chạy ngầm
# =========================================================
def background_updater():
    global last_data
    last_phien = None
    while True:
        data = get_taixiu_data()
        if data:
            phien, dice, tong, ket_qua = data
            
            if phien != last_phien and phien is not None: 
                history.append(ket_qua)

                # Chạy AI dự đoán cho phiên tiếp theo
                ai_result = master_ai_engine(history)

                # Bóc tách 3 viên xúc xắc
                last_data = {
                    "phien": phien,
                    "xuc_xac_1": dice[0],
                    "xuc_xac_2": dice[1],
                    "xuc_xac_3": dice[2],
                    "tong": tong,
                    "ketqua": ket_qua,
                    "du_doan": ai_result["du_doan"],
                    "do_tin_cay": ai_result["do_tin_cay"],
                    "suc_manh": ai_result["suc_manh"],
                    "entropy": ai_result["entropy"],
                    "streak": ai_result.get("streak", 0),
                    "id": "địt mẹ lc79"
                }

                print(f"[✅] Phiên {phien}: {ket_qua} ({dice[0]}-{dice[1]}-{dice[2]}) | Dự báo: {ai_result['du_doan']}")
                last_phien = phien
        
        time.sleep(4)

# =========================================================
# 🔹 Server Endpoint
# =========================================================
@app.route("/api/taixiu", methods=["GET"])
def api_taixiu():
    return jsonify(last_data)

if __name__ == "__main__":
    print("🚀 API Server ML Consensus v3.1 đang khởi động...")
    threading.Thread(target=background_updater, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
