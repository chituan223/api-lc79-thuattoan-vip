from flask import Flask, jsonify
import requests
import time
import threading
from collections import deque
import os

app = Flask(__name__)

# =========================================================
# 💾 Cấu hình & Lưu trữ
# =========================================================
history = deque(maxlen=2000) # Cần lịch sử dài để tính xác suất Markov
last_data = {
    "phien": None, "ketqua": "", "du_doan": "Đang học Markov...", 
    "do_tin_cay": 0, "thuat_toan": "Markov-Bayes"
}

# =========================================================
# 🧮 CORE: MARKOV CHAIN & BAYESIAN ENGINE
# =========================================================
def calculate_markov_probability(data_sequence):
    """
    Tính toán Ma trận chuyển đổi trạng thái (Transition Matrix)
    Để xem sau TÀI thì bao nhiêu % ra XỈU, bao nhiêu % ra TÀI.
    """
    if len(data_sequence) < 20: return 0.5, 0.5 # Chưa đủ dữ liệu
    
    # Đếm số lần chuyển đổi trạng thái
    trans_T_T = 0 # Tài -> Tài
    trans_T_X = 0 # Tài -> Xỉu
    trans_X_T = 0 # Xỉu -> Tài
    trans_X_X = 0 # Xỉu -> Xỉu
    
    for i in range(len(data_sequence) - 1):
        current = data_sequence[i]
        next_val = data_sequence[i+1]
        
        if current == "Tài":
            if next_val == "Tài": trans_T_T += 1
            else: trans_T_X += 1
        else: # current == "Xỉu"
            if next_val == "Tài": trans_X_T += 1
            else: trans_X_X += 1
            
    # Tính xác suất có điều kiện (Conditional Probability)
    # P(Next=Tài | Current=Tài)
    total_T = trans_T_T + trans_T_X
    prob_T_next_T = (trans_T_T / total_T) if total_T > 0 else 0.5
    prob_T_next_X = (trans_T_X / total_T) if total_T > 0 else 0.5
    
    # P(Next=Tài | Current=Xỉu)
    total_X = trans_X_T + trans_X_X
    prob_X_next_T = (trans_X_T / total_X) if total_X > 0 else 0.5
    prob_X_next_X = (trans_X_X / total_X) if total_X > 0 else 0.5
    
    return {
        "T_to_T": prob_T_next_T, "T_to_X": prob_T_next_X,
        "X_to_T": prob_X_next_T, "X_to_X": prob_X_next_X
    }

def master_ai_engine(history_list):
    # Cần tối thiểu 50 phiên để ma trận ổn định
    if len(history_list) < 50:
        return {"du_doan": "Thu thập mẫu...", "do_tin_cay": 0}

    h = list(history_list)
    last_result = h[-1] # Kết quả phiên gần nhất
    
    # 1. TÍNH TOÁN MARKOV (Xác suất toán học thuần túy)
    matrix = calculate_markov_probability(h)
    
    markov_score_T = 0.0
    markov_score_X = 0.0
    
    if last_result == "Tài":
        # Nếu vừa ra Tài, xem xác suất lịch sử nó về gì tiếp theo
        markov_score_T = matrix["T_to_T"] * 100 # Xác suất bệt Tài
        markov_score_X = matrix["T_to_X"] * 100 # Xác suất bẻ Xỉu
    else:
        # Nếu vừa ra Xỉu
        markov_score_T = matrix["X_to_T"] * 100 # Xác suất bẻ Tài
        markov_score_X = matrix["X_to_X"] * 100 # Xác suất bệt Xỉu

    # 2. KẾT HỢP PATTERN WEIGHTS (Các mẫu hình nến đặc biệt)
    # Markov cho xu hướng tổng thể, Pattern bắt điểm gãy cục bộ
    s = "".join(["T" if x == "Tài" else "X" for x in h[-20:]]) # Lấy 20 phiên gần nhất soi pattern
    
    pat_bonus_T = 0
    pat_bonus_X = 0
    
    # Logic Bệt Cục Bộ (Local Streak)
    streak = 1
    for i in range(len(h)-2, -1, -1):
        if h[i] == h[-1]: streak += 1
        else: break
        
    # Nếu bệt quá dài, Markov thường báo bệt tiếp, nhưng thực tế cần giảm điểm (Mean Reversion)
    if streak >= 6: 
        if last_result == "Tài": pat_bonus_X += (streak * 15) # Cộng điểm cho bẻ
        else: pat_bonus_T += (streak * 15)

    # Các mẫu đảo chiều kinh điển (3-1, 1-1)
    if s.endswith("TTTX"): pat_bonus_T += 40
    if s.endswith("XXXT"): pat_bonus_X += 40
    if s.endswith("TXT"): pat_bonus_X += 30
    if s.endswith("XTX"): pat_bonus_T += 30

    # 3. TỔNG HỢP (FUSION)
    # Trọng số: 70% Markov (Xu hướng dài) + 30% Pattern (Biến động ngắn)
    final_score_T = (markov_score_T * 2) + pat_bonus_T
    final_score_X = (markov_score_X * 2) + pat_bonus_X
    
    total = final_score_T + final_score_X
    if total == 0: return {"du_doan": "Chờ...", "do_tin_cay": 0}
    
    diff = abs(final_score_T - final_score_X)
    
    # Nếu chênh lệch quá thấp (Markov bảo 50/50), không đánh
    if diff < 30: 
        return {"du_doan": "Cầu cân (Né)", "do_tin_cay": 0}

    predict = "Tài" if final_score_T > final_score_X else "Xỉu"
    confidence = (max(final_score_T, final_score_X) / total) * 100
    
    return {
        "du_doan": predict,
        "do_tin_cay": round(min(confidence, 98), 2),
        "markov_stats": matrix # Trả về để debug xem xác suất thực
    }

# =========================================================
# 🔹 API Fetching & Server (Giữ nguyên cấu trúc chuẩn)
# =========================================================
def get_taixiu_data():
    url = "https://wtxmd52.tele68.com/v1/txmd5/sessions" 
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if "list" in data and len(data["list"]) > 0:
                item = data["list"][0]
                # Logic lấy kết quả chuẩn từ server
                res_str = item.get("resultTruyenThong", "")
                if not res_str: # Fallback nếu API đổi cấu trúc
                    dice_sum = item.get("point", 0)
                    res_str = "TAI" if dice_sum >= 11 else "XIU"
                
                return item["id"], res_str.title() if res_str.title() in ["Tài", "Xỉu"] else ("Tài" if item.get("point") >= 11 else "Xỉu")
    except: pass
    return None, None

def background_task():
    global last_data
    current_phien = None
    while True:
        phien, kq = get_taixiu_data()
        if phien and phien != current_phien:
            history.append(kq)
            # Chạy thuật toán Markov
            ai_res = master_ai_engine(history)
            
            last_data = {
                "phien": phien,
                "ketqua_phien_truoc": kq,
                "du_doan_tiep_theo": ai_res["du_doan"],
                "do_tin_cay": ai_res["do_tin_cay"],
                "thuat_toan": "Markov Adaptive v2.0"
            }
            print(f"Phiên {phien}: Ra {kq} -> Dự đoán tiếp: {ai_res['du_doan']} ({ai_res['do_tin_cay']}%)")
            current_phien = phien
        time.sleep(3)

@app.route("/api/taixiumd5")
def get_pred():
    return jsonify(last_data)

if __name__ == "__main__":
    threading.Thread(target=background_task, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)

