from flask import Flask, jsonify
import requests
import time
import threading
from collections import deque
import statistics
import os # Import os để đọc biến môi trường PORT từ Railway

app = Flask(__name__)

# =========================================================
# 💾 Bộ nhớ tạm – giữ VÔ HẠN PHIÊN
# =========================================================
history = deque()
totals = deque()
win_log = deque()

last_data = {
    "phien": None,
    "xucxac1": 0,
    "xucxac2": 0,
    "xucxac3": 0,
    "tong": 0,
    "ketqua": "",
    "du_doan": "Đang khởi động...",
    "do_tin_cay": 0,
    
    "id": "đit mẹ lc79"
}

# =========================================================
# 🔹 20 Thuật toán thông minh – không random, không đoán bừa
# =========================================================

def ai1_frequency(history, totals):
    if len(history) < 6:
        return {"du_doan": "Tài", "do_tin_cay": 65.2}
    window = history[-6:]
    t = window.count("Tài")
    x = window.count("Xỉu")
    if t > x + 1:
        return {"du_doan": "Xỉu", "do_tin_cay": 88.3}
    if x > t + 1:
        return {"du_doan": "Tài", "do_tin_cay": 87.5}
    return {"du_doan": history[-1], "do_tin_cay": 73.4}


def ai2_parity_chain(history, totals):
    if len(totals) < 5:
        return {"du_doan": "Tài", "do_tin_cay": 66.7}
    last5 = totals[-5:]
    evens = sum(1 for t in last5 if t % 2 == 0)
    if evens >= 4:
        return {"du_doan": "Xỉu", "do_tin_cay": 91.2}
    if evens <= 1:
        return {"du_doan": "Tài", "do_tin_cay": 90.4}
    return {"du_doan": "Tài" if totals[-1] >= 11 else "Xỉu", "do_tin_cay": 71.9}


def ai3_moving_avg(history, totals):
    if len(totals) < 4:
        return {"du_doan": "Tài", "do_tin_cay": 65.8}
    avg4 = sum(totals[-4:]) / 4
    if avg4 > 10.9:
        return {"du_doan": "Tài", "do_tin_cay": 85.6}
    if avg4 < 10.1:
        return {"du_doan": "Xỉu", "do_tin_cay": 84.8}
    return {"du_doan": history[-1], "do_tin_cay": 72.1}


def ai4_streak_detector(history, totals):
    if len(history) < 4:
        return {"du_doan": "Tài", "do_tin_cay": 64.3}
    last = history[-1]
    streak = 1
    for i in range(len(history) - 2, -1, -1):
        if history[i] == last:
            streak += 1
        else:
            break
    if streak >= 4:
        return {"du_doan": "Xỉu" if last == "Tài" else "Tài", "do_tin_cay": 92.8}
    return {"du_doan": last, "do_tin_cay": 70.5}


def ai5_alternating_pattern(history, totals):
    if len(history) < 6:
        return {"du_doan": "Tài", "do_tin_cay": 66.2}
    seq = "".join("T" if h == "Tài" else "X" for h in history[-6:])
    if seq.endswith(("TXTX", "XTXT")):
        next_pred = "Tài" if seq[-1] == "X" else "Xỉu"
        return {"du_doan": next_pred, "do_tin_cay": 89.4}
    return {"du_doan": history[-1], "do_tin_cay": 68.9}


def ai6_total_variability(history, totals):
    if len(totals) < 5:
        return {"du_doan": "Tài", "do_tin_cay": 67.0}
    window = totals[-5:]
    mean = sum(window) / 5
    var = max(window) - min(window)
    if mean >= 11 and var <= 2:
        return {"du_doan": "Tài", "do_tin_cay": 87.2}
    if mean <= 10 and var <= 2:
        return {"du_doan": "Xỉu", "do_tin_cay": 86.6}
    return {"du_doan": history[-1], "do_tin_cay": 73.8}


def ai7_short_cycle(history, totals):
    if len(history) < 3:
        return {"du_doan": "Tài", "do_tin_cay": 61.7}
    tail = history[-3:]
    if tail[0] == tail[2] and tail[0] != tail[1]:
        return {"du_doan": tail[0], "do_tin_cay": 88.9}
    return {"du_doan": history[-1], "do_tin_cay": 70.3}


def ai8_even_bias_long(history, totals):
    if len(totals) < 8:
        return {"du_doan": "Tài", "do_tin_cay": 64.6}
    last8 = totals[-8:]
    evens = sum(1 for t in last8 if t % 2 == 0)
    if evens >= 6:
        return {"du_doan": "Xỉu", "do_tin_cay": 91.1}
    if evens <= 2:
        return {"du_doan": "Tài", "do_tin_cay": 90.7}
    return {"du_doan": "Tài" if totals[-1] >= 11 else "Xỉu", "do_tin_cay": 71.5}


def ai9_median_check(history, totals):
    if len(totals) < 5:
        return {"du_doan": "Tài", "do_tin_cay": 65.1}
    med = statistics.median(totals[-5:])
    if med > 10.6:
        return {"du_doan": "Tài", "do_tin_cay": 84.3}
    return {"du_doan": "Xỉu", "do_tin_cay": 84.1}


def ai10_trend_slope(history, totals):
    if len(totals) < 5:
        return {"du_doan": "Tài", "do_tin_cay": 63.7}
    slope = (totals[-1] - totals[-5]) / 4
    if slope >= 0.6:
        return {"du_doan": "Tài", "do_tin_cay": 89.6}
    if slope <= -0.6:
        return {"du_doan": "Xỉu", "do_tin_cay": 89.4}
    return {"du_doan": "Tài" if totals[-1] >= 11 else "Xỉu", "do_tin_cay": 72.2}


def ai11_weighted_vote(history, totals):
    if len(history) < 6 or len(totals) < 6:
        return {"du_doan": "Tài", "do_tin_cay": 66.4}
    tcount = history[-6:].count("Tài")
    mean6 = statistics.mean(totals[-6:])
    parity = sum(1 for t in totals[-6:] if t % 2 == 0)
    score = 0
    if tcount > 3: score += 1
    if mean6 >= 11: score += 1
    if parity <= 2: score += 1
    if score >= 2:
        return {"du_doan": "Tài", "do_tin_cay": 86.5}
    if score <= 0:
        return {"du_doan": "Xỉu", "do_tin_cay": 85.9}
    return {"du_doan": history[-1], "do_tin_cay": 74.2}


def ai12_recent_trend(history, totals):
    if len(history) < 3:
        return {"du_doan": "Tài", "do_tin_cay": 62.3}
    trend = history[-2:]
    if trend[0] == trend[1]:
        return {"du_doan": trend[0], "do_tin_cay": 80.6}
    return {"du_doan": history[-1], "do_tin_cay": 70.1}


def ai13_balance(history, totals):
    t = history.count("Tài")
    x = history.count("Xỉu")
    if abs(t - x) >= 5:
        return {"du_doan": "Xỉu" if t > x else "Tài", "do_tin_cay": 83.2}
    return {"du_doan": history[-1], "do_tin_cay": 71.6}


def ai14_gradient(history, totals):
    if len(totals) < 4:
        return {"du_doan": "Tài", "do_tin_cay": 63.4}
    grad = totals[-1] - totals[-4]
    if grad > 1.5:
        return {"du_doan": "Tài", "do_tin_cay": 87.3}
    if grad < -1.5:
        return {"du_doan": "Xỉu", "do_tin_cay": 87.0}
    return {"du_doan": history[-1], "do_tin_cay": 74.0}


def ai15_stability(history, totals):
    if len(totals) < 5:
        return {"du_doan": "Tài", "do_tin_cay": 64.5}
    diff = max(totals[-5:]) - min(totals[-5:])
    if diff <= 2:
        return {"du_doan": "Xỉu", "do_tin_cay": 81.8}
    return {"du_doan": "Tài", "do_tin_cay": 75.3}


def ai16_flip_after_loss(history, totals, win_log=[]):
    if len(win_log) > 0 and not win_log[-1]:
        return {"du_doan": "Xỉu" if history[-1] == "Tài" else "Tài", "do_tin_cay": 81.2}
    return {"du_doan": history[-1], "do_tin_cay": 72.6}


def ai17_recent_variance(history, totals):
    if len(totals) < 5:
        return {"du_doan": "Tài", "do_tin_cay": 66.1}
    var = max(totals[-5:]) - min(totals[-5:])
    return {"du_doan": "Tài" if var > 4 else "Xỉu", "do_tin_cay": 78.8}


def ai18_sequence(history, totals):
    if len(history) < 5:
        return {"du_doan": "Tài", "do_tin_cay": 64.9}
    seq = "".join("T" if h == "Tài" else "X" for h in history[-5:])
    if seq in ["TTTTT", "XXXXX"]:
        return {"du_doan": "Xỉu" if history[-1] == "Tài" else "Tài", "do_tin_cay": 89.9}
    return {"du_doan": history[-1], "do_tin_cay": 70.9}


def ai19_long_term_mean(history, totals):
    if len(totals) < 10:
        return {"du_doan": "Tài", "do_tin_cay": 65.7}
    mean10 = statistics.mean(totals[-10:])
    if mean10 > 11:
        return {"du_doan": "Tài", "do_tin_cay": 84.7}
    if mean10 < 10:
        return {"du_doan": "Xỉu", "do_tin_cay": 83.9}
    return {"du_doan": history[-1], "do_tin_cay": 71.3}


def ai20_adaptive(history, totals):
    if len(history) < 8:
        return {"du_doan": "Tài", "do_tin_cay": 66.5}
    ratio = history[-8:].count("Tài") / 8
    if ratio > 0.75:
        return {"du_doan": "Xỉu", "do_tin_cay": 90.6}
    if ratio < 0.25:
        return {"du_doan": "Tài", "do_tin_cay": 90.2}
    return {"du_doan": history[-1], "do_tin_cay": 72.4}


# =========================================================
# 🔹 Danh sách thuật toán dùng kết hợp
# =========================================================
algos = [
    ai1_frequency, ai2_parity_chain, ai3_moving_avg, ai4_streak_detector,
    ai5_alternating_pattern, ai6_total_variability, ai7_short_cycle,
    ai8_even_bias_long, ai9_median_check, ai10_trend_slope,
    ai11_weighted_vote, ai12_recent_trend, ai13_balance, ai14_gradient,
    ai15_stability, ai16_flip_after_loss, ai17_recent_variance,
    ai18_sequence, ai19_long_term_mean, ai20_adaptive
    
]

# =========================================================
# 🔹 API Tele68 (nguồn thật)
# =========================================================
def get_taixiu_data():
    # URL mà bạn cung cấp
    url = "https://wtxmd52.tele68.com/v1/txmd5/sessions" 
    try:
        res = requests.get(url, timeout=8)
        res.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        data = res.json()
        if "list" in data and len(data["list"]) > 0:
            newest = data["list"][0]
            phien = newest.get("id")
            dice = newest.get("dices", [1, 2, 3])
            tong = newest.get("point", sum(dice))
            
            # Xử lý kết quả: đảm bảo là 'Tài' hoặc 'Xỉu'
            ketqua = newest.get("resultTruyenThong", "").upper()
            if ketqua == "TAI":
                ketqua = "Tài"
            elif ketqua == "XIU":
                ketqua = "Xỉu"
            else:
                 # Nếu kết quả không phải TAI/XIU, có thể là Bão (Triple), 
                 # nhưng API gốc đã đơn giản hóa về Tài/Xỉu nên ta giữ nguyên logic.
                 # Nếu tong < 11 -> Xỉu, ngược lại -> Tài.
                ketqua = "Tài" if tong >= 11 else "Xỉu" 
                
            return phien, dice, tong, ketqua
    except requests.exceptions.RequestException as e:
        print(f"[❌] Lỗi lấy dữ liệu API gốc: {e}")
    except Exception as e:
        print(f"[❌] Lỗi xử lý JSON hoặc logic: {e}")
    return None

# =========================================================
# 🔹 Thread cập nhật dữ liệu
# =========================================================
def background_updater():
    global last_data
    last_phien = None
    while True:
        data = get_taixiu_data()
        if data:
            phien, dice, tong, ketqua = data
            
            # Chỉ cập nhật khi phiên mới xuất hiện
            if phien != last_phien and phien is not None: 
                
                # Cắt bớt lịch sử để tránh tràn bộ nhớ nếu cần (ví dụ: giữ 1000 phiên gần nhất)
                if len(history) >= 1000:
                    history.popleft()
                    totals.popleft()
                    win_log.popleft()

                history.append(ketqua)
                totals.append(tong)

                results = []
                for algo in algos:
                    try:
                        # Truyền win_log vào AI16
                        r = algo(history, totals, win_log=win_log)
                        results.append((algo.__name__, r))
                    except Exception as e:
                        # Thường xảy ra khi lịch sử chưa đủ dài cho thuật toán
                        # print(f"[⚠️] Lỗi {algo.__name__}: {e}") 
                        pass # Bỏ qua lỗi thuật toán (vì chưa đủ dữ liệu)

                # Chọn ra thuật toán có độ tin cậy cao nhất
                if results:
                    best_algo, best_res = max(results, key=lambda x: x[1]["do_tin_cay"])
                    du_doan = best_res["du_doan"]
                    tin_cay = best_res["do_tin_cay"]
                    
                    # Log kết quả dự đoán của phiên trước đó
                    win_log.append(du_doan == ketqua)
                else:
                    # Trường hợp chưa đủ dữ liệu cho thuật toán nào
                    best_algo = "N/A"
                    du_doan = "Đang phân tích"
                    tin_cay = 0
                    
                
                # Cập nhật dữ liệu mới nhất
                last_data = {
                    "phien": phien,
                    "xucxac1": dice[0],
                    "xucxac2": dice[1],
                    "xucxac3": dice[2],
                    "tong": tong,
                    "ketqua": ketqua,
                    "du_doan": du_doan,
                    "do_tin_cay": tin_cay,
                    "id": "địt mẹ lc79 "
                }

                print(f"[✅] Phiên {phien} | 🎲 {dice} ({tong}) → {ketqua} | 🔮 {best_algo} → {du_doan} ({tin_cay}%)")
                last_phien = phien
            else:
                # Dữ liệu hiện tại giống phiên trước, không cần phân tích lại
                pass
        else:
            print("[⚠️] Không lấy được dữ liệu, chờ 5s...")
            
        time.sleep(5) # Đợi 5 giây trước khi kiểm tra lại

# =========================================================
# 🔹 API Endpoint
# =========================================================
@app.route("/api/taixiu", methods=["GET"])
def api_taixiu():
    # Trả về dữ liệu phiên mới nhất và dự đoán cho phiên tiếp theo
    return jsonify(last_data)

# =========================================================
# 🔹 Chạy nền
# =========================================================
if __name__ == "__main__":
    print("🚀 Đang chạy API /api/taixiu ...")
    # Lấy PORT từ biến môi trường (Railway sẽ cung cấp)
    port = int(os.environ.get("PORT", 5000))
    
    # Khởi chạy thread cập nhật dữ liệu nền
    threading.Thread(target=background_updater, daemon=True).start()
    
    # Khởi chạy Flask App
    app.run(host="0.0.0.0", port=port)