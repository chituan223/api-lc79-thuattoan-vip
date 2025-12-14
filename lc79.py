import requests
import time
import threading
from flask import Flask, jsonify
from datetime import datetime
import math
from collections import Counter

# Thông tin API và Bot
API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
last_processed_session_id = None
app = Flask(__name__)

# Dữ liệu hiện tại của Bot
latest_data = {
    "Phiên": None,
    "Xúc xắc 1": None,
    "Xúc xắc 2": None,
    "Xúc xắc 3": None,
    "Tổng": None,
    "Kết quả": None,
    "Pattern": "",
    "Dự đoán": "Đang chờ",
    "Độ tin cậy": 0,
    "Tình trạng cầu": "Đang phân tích",
    "Lịch sử Win/Loss": {},
    "ID": "tuananh"
}

# Lịch sử và thống kê toàn cục
history_full = [] # Lịch sử kết quả (1=Tài, 0=Xỉu)
dice_history = [] # Lịch sử 3 viên xúc xắc
sum_history = [] # Lịch sử tổng điểm
prediction_history = [] # Lịch sử các lần dự đoán (pred_text, is_win, conf, phien)
win_count = 0
loss_count = 0
last_prediction = None # (pred_text, pred_conf, pred_phien)

def get_pattern_string(history, length=30):
    """Tạo chuỗi pattern T/X từ lịch sử"""
    if not history:
        return ""
    recent = history[-length:] if len(history) >= length else history
    return ''.join(['T' if x == 1 else 'X' for x in recent])

# ===============================
# ĐÁNH GIÁ TÌNH TRẠNG CẦU (BỎ ĐIỂM CẦU)
# ===============================
def evaluate_bridge_status():
    """Đánh giá tình trạng cầu dựa trên độ ổn định và tỷ lệ thắng gần đây"""
    global history_full, prediction_history
    
    if len(history_full) < 20:
        return "Đang thu thập dữ liệu (Yêu cầu >20 phiên)"
    
    # 1. Tỷ lệ Win gần đây (trọng số cao)
    recent_preds = prediction_history[-20:]
    win_rate = 0.5
    if recent_preds:
        recent_wins = sum(1 for _, is_win, _, _ in recent_preds if is_win)
        win_rate = recent_wins / len(recent_preds)
    
    # 2. Độ ổn định của cầu (Volatility Score)
    recent_20 = history_full[-20:]
    changes = sum(1 for i in range(1, len(recent_20)) if recent_20[i] != recent_20[i-1])
    volatility_score = 1 - (changes / (len(recent_20) - 1)) # 1 là ổn định nhất (dây dài, ít nhảy)
    
    # Đánh giá cuối cùng dựa trên Win Rate và Volatility
    if win_rate >= 0.80:
        if volatility_score > 0.7:
             return "cầu đẹp rủi ro thấp 🌠"
        else:
             return "cầu ổn cân nhắc ⚡"
    elif win_rate >= 0.65:
        return "cầu bịp không nên vào 🤮"
    elif win_rate >= 0.50:
        return "cầu lỏ"
    else:
        return " cầu lồn không nên vào ⚠️"

# ===============================
# 5 THUẬT TOÁN SOI CẦU CHUẨN ĐÃ LÀM LẠI
# ===============================

def algo_1_super_pattern(history):
    """Thuật toán 1: Super Pattern - Soi cầu dựa trên pattern 2-3-4-5 bước (Trọng số cao)"""
    if len(history) < 15:
        return history[-1] if history else 1, 55.0, "Init"
    
    votes = {'T': 0, 'X': 0}
    
    # Soi pattern 5, 4, 3, 2 bước
    for length, weight in [(5, 6), (4, 4), (3, 3), (2, 2)]:
        if len(history) >= length + 2:
            p = tuple(history[-length:])
            # Tìm các mẫu khớp và kết quả tiếp theo
            matches = [history[i+length] for i in range(len(history) - length - 1) if tuple(history[i:i+length]) == p]
            
            # Chỉ tính nếu có từ 3 mẫu khớp trở lên
            if len(matches) >= 3:
                t = sum(matches)
                x = len(matches) - t
                total_matches = len(matches)
                
                # Tính độ tin cậy của vote này
                conf_factor = abs(t - x) / total_matches # Độ chênh lệch
                
                if t > x:
                    # Tăng vote và scale theo số lượng mẫu
                    votes['T'] += weight * conf_factor * (total_matches / 3) 
                else:
                    votes['X'] += weight * conf_factor * (total_matches / 3)
    
    total_vote_score = votes['T'] + votes['X']
    
    if total_vote_score == 0:
        # Nếu không có mẫu nào đủ tin cậy, follow ván trước (55%)
        return history[-1], 55, "Pattern vote: Không tìm thấy mẫu đủ tin cậy"
        
    if votes['T'] > votes['X']:
        # Base confidence 60 + bonus from vote ratio
        conf = 60 + min(35, (votes['T'] / total_vote_score) * 40)
        return 1, round(conf, 1), f"Pattern vote: T={votes['T']:.1f} X={votes['X']:.1f}"
    elif votes['X'] > votes['T']:
        conf = 60 + min(35, (votes['X'] / total_vote_score) * 40)
        return 0, round(conf, 1), f"Pattern vote: T={votes['T']:.1f} X={votes['X']:.1f}"
    else:
        return history[-1], 55, "Pattern vote: Cân bằng"


def algo_2_chain_analysis(history):
    """Thuật toán 2: Chain Analysis - Phân tích chuỗi Markov 2 bước"""
    if len(history) < 15:
        return history[-1] if history else 0, 60.0, "Init"
    
    # Ma trận chuyển 2 bước
    trans = {}
    for i in range(len(history) - 2):
        state = (history[i], history[i+1])
        next_v = history[i+2]
        if state not in trans:
            trans[state] = {'T': 0, 'X': 0}
        if next_v == 1:
            trans[state]['T'] += 1
        else:
            trans[state]['X'] += 1
    
    curr_state = tuple(history[-2:])
    
    if curr_state in trans:
        t = trans[curr_state]['T']
        x = trans[curr_state]['X']
        total = t + x
        
        # Yêu cầu ít nhất 3 mẫu để đưa ra dự đoán mạnh
        if total >= 3:
            if t > x:
                # Scale confidence more aggressively
                return 1, min(65 + (t - x) / total * 50, 93), f"Chain: {curr_state} → T={t} X={x}"
            else:
                return 0, min(65 + (x - t) / total * 50, 93), f"Chain: {curr_state} → T={t} X={x}"
    
    # Fallback Chain 1 bước
    trans_1 = {'T': {'T': 0, 'X': 0}, 'X': {'T': 0, 'X': 0}}
    for i in range(len(history) - 1):
        curr = 'T' if history[i] == 1 else 'X'
        next_v = 'T' if history[i+1] == 1 else 'X'
        trans_1[curr][next_v] += 1
    
    curr = 'T' if history[-1] == 1 else 'X'
    t = trans_1[curr]['T']
    x = trans_1[curr]['X']
    
    if t + x >= 5: # Yêu cầu 5 mẫu cho Chain 1
        return (1 if t > x else 0), min(60 + abs(t - x) * 3, 85), f"Chain-1: {curr} → T={t} X={x}"
    
    return history[-1], 58, "Chain yếu/không đủ mẫu"


def algo_3_wave_trend(history):
    """Thuật toán 3: Wave Trend - Soi xu hướng sóng (dựa trên MA)"""
    if len(history) < 15:
        return history[-1] if history else 1, 60.0, "Init"
    
    r3 = sum(history[-3:]) / 3
    r5 = sum(history[-5:]) / 5
    r8 = sum(history[-8:]) / 8
    r12 = sum(history[-12:]) / 12
    
    # Xu hướng ngắn hạn (Tốc độ thay đổi)
    short_trend = r3 - r5
    
    curr = history[-1]
    
    # 1. Cực đoan (Reverse) - Trọng số cao
    if r3 >= 1.0: # 3 ván đều Tài
        return 0, 90, f"3 ván toàn Tài ({r3:.0%}) → Soi XỈU mạnh"
    elif r3 <= 0.0: # 3 ván đều Xỉu
        return 1, 90, f"3 ván toàn Xỉu ({1-r3:.0%}) → Soi TÀI mạnh"
    
    # 2. Trend cùng chiều mạnh → Follow
    if short_trend > 0.3 and r5 > 0.7:
        return 1, min(75 + short_trend * 30, 92), f"Sóng Tài tăng mạnh (ST={short_trend:.2f}) → Soi TÀI"
    elif short_trend < -0.3 and r5 < 0.3:
        return 0, min(75 - short_trend * 30, 92), f"Sóng Xỉu giảm mạnh (ST={short_trend:.2f}) → Soi XỈU"
    
    # 3. Đảo chiều sau trend dài
    if r8 > 0.7 and short_trend < -0.2:
        return 0, 80, f"Sau trend Tài dài (R8>0.7), đảo chiều ngắn hạn → Soi XỈU"
    elif r8 < 0.3 and short_trend > 0.2:
        return 1, 80, f"Sau trend Xỉu dài (R8<0.3), đảo chiều ngắn hạn → Soi TÀI"
    
    # 4. Follow hiện tại nếu trend yếu
    return curr, 65, f"Sóng yếu → Follow {curr}"


def algo_4_streak_master(history):
    """Thuật toán 4: Streak Master - Bậc thầy soi chuỗi"""
    if len(history) < 10:
        return history[-1] if history else 0, 60.0, "Init"
    
    curr = history[-1]
    streak = 1
    for i in range(len(history)-2, -1, -1):
        if history[i] == curr:
            streak += 1
        else:
            break
    
    # Phân tích lịch sử chuỗi
    all_streaks = []
    temp = 1
    for i in range(1, len(history)):
        if history[i] == history[i-1]:
            temp += 1
        else:
            all_streaks.append(temp)
            temp = 1
    all_streaks.append(temp) # Chuỗi cuối cùng
    
    if not all_streaks:
        return history[-1], 60, "No streak data"
    
    avg_streak = sum(all_streaks) / len(all_streaks)
    max_streak = max(all_streaks)
    
    curr_name = "TÀI" if curr == 1 else "XỈU"
    opposite = 1 - curr
    
    # LOGIC SOI CHUỖI:
    if streak >= 6:  # Chuỗi rất dài
        return opposite, min(80 + streak * 3, 95), f"Chuỗi {streak} {curr_name} quá dài → Soi đảo chiều"
    
    elif streak >= max_streak and max_streak >= 3:  # Đạt max lịch sử
        return opposite, min(75 + (streak - max_streak + 1) * 5, 90), f"Chuỗi {streak} đạt max {max_streak} → Soi phá chuỗi"
    
    elif streak >= avg_streak * 2 and avg_streak >= 2:  # Gấp đôi TB
        return opposite, min(70 + (streak - avg_streak) * 4, 88), f"Chuỗi {streak} >> TB {avg_streak:.1f} → Soi phá"
    
    elif streak <= 2:  # Chuỗi ngắn → Follow
        return curr, 70, f"Chuỗi {streak} {curr_name} ngắn → Soi tiếp tục"
    
    else:  # Chuỗi trung bình → Follow
        return curr, 65, f"Chuỗi {streak} {curr_name} TB → Soi tiếp tục"


def algo_5_dice_pro(dice_hist, sum_hist):
    """Thuật toán 5: Dice Pro - Chuyên gia soi xúc xắc và tổng điểm"""
    if len(sum_hist) < 10:
        return 1, 60.0, "Init"
    
    recent_10 = sum_hist[-10:]
    mean = sum(recent_10) / 10
    
    # 1. Trend tổng điểm (dựa trên 3 ván gần nhất vs 3 ván trước đó)
    near_sum = sum(recent_10[-3:]) / 3
    far_sum = sum(recent_10[-6:-3]) / 3
    trend = near_sum - far_sum
    
    # 2. Phân phối số xúc xắc
    if len(dice_hist) >= 6:
        nums = [n for d in dice_hist[-6:] for n in d]
        high = sum(1 for n in nums if n >= 4)
        low = len(nums) - high
        high_rate = high / len(nums)
    else:
        high_rate = 0.5
    
    # LOGIC SOI DICE:
    # 1. Mean cực đoan (Reverse) - Trọng số cao
    if mean >= 14.0:
        return 0, min(85 + (mean - 14.0) * 5, 95), f"Điểm TB {mean:.1f} cực cao → Soi XỈU"
    elif mean <= 7.0:
        return 1, min(85 + (7.0 - mean) * 5, 95), f"Điểm TB {mean:.1f} cực thấp → Soi TÀI"
    
    # 2. Trend mạnh
    if trend >= 2.0:
        return 1, min(75 + trend * 5, 90), f"Trend điểm +{trend:.1f} mạnh → Soi TÀI"
    elif trend <= -2.0:
        return 0, min(75 - trend * 5, 90), f"Trend điểm {trend:.1f} mạnh → Soi XỈU"
    
    # 3. Phân phối lệch
    if high_rate >= 0.75:
        return 1, min(70 + (high_rate - 0.75) * 80, 88), f"Số cao {high_rate:.0%} vượt trội → Soi TÀI"
    elif high_rate <= 0.25:
        return 0, min(70 + (0.25 - high_rate) * 80, 88), f"Số thấp {1-high_rate:.0%} vượt trội → Soi XỈU"
    
    # 4. Trung tính
    if mean > 11.5:
        return 0, 65, f"Mean {mean:.1f} hơi cao"
    elif mean < 9.5:
        return 1, 65, f"Mean {mean:.1f} hơi thấp"
        
    return (1 if history_full[-1] == 1 else 0), 60, f"Dice trung tính → Follow"


# ===============================
# TỔNG HỢP & QUYẾT ĐỊNH CUỐI CÙNG
# ===============================
def calculate_prediction():
    """Tổng hợp 5 thuật toán bằng phương pháp voting trọng số"""
    global history_full, dice_history, sum_history
    
    if len(history_full) < 5:
        return "TÀI", 50.0
    
    algos = [
        algo_1_super_pattern(history_full),
        algo_2_chain_analysis(history_full),
        algo_3_wave_trend(history_full),
        algo_4_streak_master(history_full),
        algo_5_dice_pro(dice_history, sum_history)
    ]
    
    # Trọng số dựa trên độ tin cậy
    tai = sum(conf for pred, conf, _ in algos if pred == 1)
    xiu = sum(conf for pred, conf, _ in algos if pred == 0)
    total = tai + xiu
    
    if total == 0:
        return "TÀI", 50.0

    if tai > xiu:
        # Giới hạn độ tin cậy để tránh quá ảo
        return "TÀI", min(round((tai / total) * 100, 1), 96)
    else:
        return "XỈU", min(round((xiu / total) * 100, 1), 96)


def get_win_loss_stats():
    """Tính toán thống kê Win/Loss gần nhất và tổng thể"""
    global win_count, loss_count, prediction_history
    
    total = win_count + loss_count
    if total == 0:
        return {"Tổng": 0, "Win": 0, "Loss": 0, "Tỷ lệ Win": "0%", "Chuỗi": "Chưa có"}
    
    win_rate = (win_count / total) * 100
    
    streak = 0
    streak_type = None
    
    if prediction_history:
        # Lấy kết quả của lần dự đoán thành công/thất bại cuối cùng
        last_is_win = prediction_history[-1][1] 
        streak_type = "Win" if last_is_win else "Loss"
        
        for i in range(len(prediction_history) - 1, -1, -1):
            if prediction_history[i][1] == last_is_win:
                streak += 1
            else:
                break
    
    return {
        "Tổng": total,
        "Win": win_count,
        "Loss": loss_count,
        "Tỷ lệ Win": f"{win_rate:.1f}%",
        "Chuỗi": f"{streak} {streak_type}" if streak_type else "Chưa có"
    }


# ===============================
# BOT CORE
# ===============================
def fetch_loop():
    """Vòng lặp chính để lấy dữ liệu, phân tích và dự đoán"""
    global last_processed_session_id, latest_data
    global history_full, dice_history, sum_history
    global win_count, loss_count, prediction_history, last_prediction
    
    while True:
        try:
            res = requests.get(API_URL, timeout=10)
            res.raise_for_status() # Báo lỗi nếu status code không phải 200
            data = res.json()
            
            if not data.get("list"):
                time.sleep(2)
                continue
            
            phien = data["list"][0]
            phien_id = phien.get("id")
            
            # Chỉ xử lý nếu có phiên mới
            if phien_id == last_processed_session_id:
                time.sleep(2)
                continue
            
            dices = phien.get("dices")
            tong = phien.get("point")
            d1, d2, d3 = dices
            
            # 1. Tính toán kết quả
            # Tài (T) = 1 (11-17), Xỉu (X) = 0 (4-10)
            ket_qua = 1 if tong >= 11 else 0
            ket_qua_text = "TÀI" if ket_qua == 1 else "XỈU"
            
            # 2. Xử lý dự đoán cũ (nếu có)
            if last_prediction:
                pred_text, pred_conf, pred_phien = last_prediction
                # Kiểm tra nếu phiên hiện tại là phiên tiếp theo của phiên dự đoán
                if str(int(phien_id) - 1) == pred_phien:
                    is_win = pred_text == ket_qua_text
                    
                    if is_win:
                        win_count += 1
                        icon = "✓"
                    else:
                        loss_count += 1
                        icon = "✗"
                    
                    prediction_history.append((pred_text, is_win, pred_conf, pred_phien))
                    if len(prediction_history) > 200:
                        prediction_history.pop(0)
                    
                    wr = (win_count / (win_count + loss_count)) * 100
                    print(f"  └─ {icon} Soi {pred_text} | KQ {ket_qua_text} | W:{win_count} L:{loss_count} ({wr:.1f}%)")
            
            # 3. Cập nhật lịch sử
            history_full.append(ket_qua)
            if len(history_full) > 200: history_full.pop(0)
            
            dice_history.append([d1, d2, d3])
            if len(dice_history) > 100: dice_history.pop(0)
            
            sum_history.append(tong)
            if len(sum_history) > 100: sum_history.pop(0)
            
            last_processed_session_id = phien_id
            
            # 4. Tạo Pattern
            pattern_str = get_pattern_string(history_full, 30)
            
            # 5. Dự đoán phiên tiếp theo
            pred, conf = calculate_prediction()
            # Lưu dự đoán cho phiên hiện tại (dự đoán cho phiên ID + 1)
            last_prediction = (pred, conf, phien_id) 
            
            # 6. Đánh giá Tình trạng cầu
            bridge_status = evaluate_bridge_status()
            
            # 7. Thống kê
            stats = get_win_loss_stats()
            
            # 8. Cập nhật dữ liệu trả về API
            latest_data = {
                "Phiên": phien_id,
                "Xúc xắc 1": d1,
                "Xúc xắc 2": d2,
                "Xúc xắc 3": d3,
                "Tổng": tong,
                "Kết quả": ket_qua_text,
                "Pattern": pattern_str,
                "Dự đoán": pred,
                "Độ tin cậy": conf,
                "Tình trạng cầu": bridge_status,
                "Lịch sử Win/Loss": stats,
                "ID": "tuananh"
            }
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] #{phien_id}: {d1}-{d2}-{d3}={tong} {ket_qua_text} | Pattern: {pattern_str[-10:]} → Soi: {pred} ({conf}%)")
            
        except requests.exceptions.RequestException as e:
            print(f"Lỗi kết nối API: {e}")
        except Exception as e:
            print(f"Lỗi xử lý dữ liệu: {e}")
        
        time.sleep(2) # Chờ 2 giây trước khi lấy phiên mới


threading.Thread(target=fetch_loop, daemon=True).start()

@app.route("/api/taixiumd5", methods=["GET"])
def api_data():
    """Endpoint trả về dữ liệu dự đoán hiện tại dưới dạng JSON"""
    return jsonify(latest_data)

@app.route("/", methods=["GET"])
def home():
    """Trang chủ đơn giản, có thể dùng để kiểm tra API đang chạy"""
    return "Tai Xiu MD5 Prediction Bot Running. Access data at /api/taixiumd5"

if __name__ == "__main__":
    print("📡 API: http://0.0.0.0:10000/api/taixiumd5")
    # Thay đổi host và port theo môi trường chạy của bạn
    app.run(host="0.0.0.0", port=10000, debug=False)
