import requests
import time
import threading
from flask import Flask, jsonify
from datetime import datetime
import math

# ===============================
# CẤU HÌNH
# ===============================
API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
last_processed_session_id = None

app = Flask(__name__)

# ===============================
# BIẾN LƯU DỮ LIỆU
# ===============================
latest_data = {
    "Phiên": None,
    "Xúc xắc 1": None,
    "Xúc xắc 2": None,
    "Xúc xắc 3": None,
    "Tổng": None,
    "Dự đoán": "Đang chờ", 
    "Độ tin cậy": 0,
    "ID": "tuananh"
}

history_full = []
dice_history = []
sum_history = []

# Lưu trữ lịch sử dự đoán và kết quả
prediction_history = []  # [(dự_đoán, kết_quả_thực_tế, độ_tin_cậy, phiên)]
win_count = 0
loss_count = 0
last_prediction = None  # Lưu dự đoán của phiên trước

# ===============================
# 5 THUẬT TOÁN CHUẨN - LOGIC THẬT
# ===============================

def algorithm_1_mean_reversion(history):
    """
    Thuật toán 1: Mean Reversion (Hồi quy trung bình)
    Logic: Khi tỷ lệ lệch xa 50%, xu hướng sẽ quay về trung bình
    """
    if len(history) < 5:
        return 1, 55.0, "Khởi động"
    
    window = min(len(history), 20)
    recent = history[-window:]
    
    tai_count = sum(recent)
    tai_ratio = tai_count / len(recent)
    
    # Tính z-score để đo độ lệch
    expected = len(recent) * 0.5
    std_dev = math.sqrt(len(recent) * 0.5 * 0.5)
    z_score = (tai_count - expected) / std_dev if std_dev > 0 else 0
    
    # Confidence tăng theo độ lệch
    confidence = 60 + min(abs(z_score) * 15, 30)
    
    # Dự đoán ngược lại khi lệch
    if z_score > 0.8:  # Quá nhiều Tài
        prediction = 0
        reason = f"Mean Reversion: {window}v có {tai_count}T ({tai_ratio:.1%}). Z-score={z_score:.2f} cao → Dự đoán XỈU"
    elif z_score < -0.8:  # Quá nhiều Xỉu
        prediction = 1
        reason = f"Mean Reversion: {window}v có {tai_count}T ({tai_ratio:.1%}). Z-score={z_score:.2f} thấp → Dự đoán TÀI"
    else:
        # Xu hướng nhẹ
        prediction = 0 if tai_ratio > 0.55 else 1
        confidence -= 5
        reason = f"Mean Reversion: {window}v có {tai_count}T ({tai_ratio:.1%}). Z-score={z_score:.2f} trung tính"
    
    return prediction, round(confidence, 1), reason


def algorithm_2_streak_probability(history):
    """
    Thuật toán 2: Streak Probability (Xác suất chuỗi)
    Logic: Chuỗi càng dài, xác suất tiếp tục giảm theo hàm mũ
    """
    if len(history) < 3:
        return 0, 56.0, "Khởi động"
    
    current = history[-1]
    streak_length = 1
    
    # Đếm chuỗi liên tiếp
    for i in range(len(history) - 2, -1, -1):
        if history[i] == current:
            streak_length += 1
        else:
            break
    
    # Xác suất tiếp tục chuỗi giảm theo 0.5^streak
    continue_prob = 0.5 ** streak_length
    break_prob = 1 - continue_prob
    
    # Confidence tăng theo độ dài chuỗi
    confidence = 55 + min(streak_length * 8, 35)
    
    if streak_length >= 4:
        prediction = 1 - current
        confidence = min(confidence + 10, 92)
        result = "TÀI" if prediction == 1 else "XỈU"
        curr_name = "TÀI" if current == 1 else "XỈU"
        reason = f"Streak: Chuỗi {streak_length} {curr_name}. P(tiếp tục)={continue_prob:.1%}, P(phá)={break_prob:.1%} → {result}"
    elif streak_length == 3:
        prediction = 1 - current
        result = "TÀI" if prediction == 1 else "XỈU"
        curr_name = "TÀI" if current == 1 else "XỈU"
        reason = f"Streak: Chuỗi 3 {curr_name}. P(tiếp tục)={continue_prob:.1%} → Có thể phá {result}"
    else:
        prediction = current
        result = "TÀI" if prediction == 1 else "XỈU"
        curr_name = "TÀI" if current == 1 else "XỈU"
        reason = f"Streak: Chuỗi ngắn {streak_length} {curr_name}. → Có thể tiếp tục {result}"
    
    return prediction, round(confidence, 1), reason


def algorithm_3_conditional_probability(history):
    """
    Thuật toán 3: Conditional Probability (Xác suất có điều kiện)
    Logic: P(next|current state) dựa trên lịch sử chuyển trạng thái
    """
    if len(history) < 8:
        return 1, 57.0, "Khởi động"
    
    # Ma trận chuyển tiếp
    transitions = {
        'T->T': 0, 'T->X': 0,
        'X->T': 0, 'X->X': 0
    }
    
    for i in range(len(history) - 1):
        curr_state = 'T' if history[i] == 1 else 'X'
        next_state = 'T' if history[i + 1] == 1 else 'X'
        key = f"{curr_state}->{next_state}"
        transitions[key] += 1
    
    current = history[-1]
    current_name = 'T' if current == 1 else 'X'
    
    if current == 1:  # Hiện tại là Tài
        total = transitions['T->T'] + transitions['T->X']
        if total > 0:
            prob_tai = transitions['T->T'] / total
            prob_xiu = transitions['T->X'] / total
        else:
            prob_tai = prob_xiu = 0.5
    else:  # Hiện tại là Xỉu
        total = transitions['X->T'] + transitions['X->X']
        if total > 0:
            prob_tai = transitions['X->T'] / total
            prob_xiu = transitions['X->X'] / total
        else:
            prob_tai = prob_xiu = 0.5
    
    # Confidence dựa trên độ chắc chắn
    confidence = 58 + abs(prob_tai - prob_xiu) * 60
    confidence = min(confidence, 88)
    
    prediction = 1 if prob_tai > prob_xiu else 0
    result = "TÀI" if prediction == 1 else "XỈU"
    
    reason = f"Conditional: Từ {current_name} → P(T)={prob_tai:.1%}, P(X)={prob_xiu:.1%}. Ma trận: {transitions} → {result}"
    
    return prediction, round(confidence, 1), reason


def algorithm_4_moving_average_crossover(history):
    """
    Thuật toán 4: Moving Average Crossover
    Logic: So sánh MA ngắn hạn vs dài hạn để xác định xu hướng
    """
    if len(history) < 12:
        return 0, 58.0, "Khởi động"
    
    # MA ngắn (5 ván) vs MA dài (10 ván)
    ma_short = sum(history[-5:]) / 5
    ma_long = sum(history[-10:]) / 10
    
    # Tính momentum
    momentum = ma_short - ma_long
    
    # Tính độ lệch so với 0.5
    deviation_short = abs(ma_short - 0.5)
    deviation_long = abs(ma_long - 0.5)
    
    # Confidence tăng khi có xu hướng rõ
    confidence = 60 + abs(momentum) * 100 + (deviation_short + deviation_long) * 20
    confidence = min(confidence, 87)
    
    # Quyết định dựa trên crossover và mean reversion
    if momentum > 0.15:  # MA ngắn cao hơn nhiều
        prediction = 0  # Đảo chiều xuống
        reason = f"MA Crossover: MA5={ma_short:.2f}, MA10={ma_long:.2f}. Momentum={momentum:.3f} (cao) → Điều chỉnh XỈU"
    elif momentum < -0.15:  # MA ngắn thấp hơn nhiều
        prediction = 1  # Đảo chiều lên
        reason = f"MA Crossover: MA5={ma_short:.2f}, MA10={ma_long:.2f}. Momentum={momentum:.3f} (thấp) → Điều chỉnh TÀI"
    else:
        # Momentum yếu, dựa vào mean reversion
        if ma_short > 0.55:
            prediction = 0
            reason = f"MA Crossover: MA5={ma_short:.2f} cao → XỈU"
        elif ma_short < 0.45:
            prediction = 1
            reason = f"MA Crossover: MA5={ma_short:.2f} thấp → TÀI"
        else:
            prediction = 1 - history[-1]
            confidence -= 8
            reason = f"MA Crossover: MA5={ma_short:.2f} trung tính → Đảo chiều"
    
    return prediction, round(confidence, 1), reason


def algorithm_5_dice_statistical_analysis(dice_hist, sum_hist):
    """
    Thuật toán 5: Dice Statistical Analysis
    Logic: Phân tích thống kê chi tiết từng viên xúc xắc và tổng điểm
    """
    if len(sum_hist) < 5:
        return 1, 59.0, "Khởi động"
    
    window = min(len(sum_hist), 10)
    recent_sums = sum_hist[-window:]
    
    # Tính các chỉ số thống kê
    mean_sum = sum(recent_sums) / len(recent_sums)
    variance = sum((x - mean_sum) ** 2 for x in recent_sums) / len(recent_sums)
    std_dev = math.sqrt(variance)
    
    # Z-score cho tổng điểm (kỳ vọng = 10.5)
    expected_mean = 10.5
    z_score = (mean_sum - expected_mean) / (std_dev + 0.1)
    
    # Phân tích phân phối số
    if len(dice_hist) >= 5:
        recent_dice = dice_hist[-5:]
        all_numbers = []
        for dice_set in recent_dice:
            all_numbers.extend(dice_set)
        
        # Đếm tần suất từng số
        freq = {i: all_numbers.count(i) for i in range(1, 7)}
        high_count = sum(freq.get(i, 0) for i in [4, 5, 6])
        low_count = sum(freq.get(i, 0) for i in [1, 2, 3])
        
        # Chi-square test để kiểm tra độ lệch
        expected_freq = len(all_numbers) / 6
        chi_square = sum((freq[i] - expected_freq) ** 2 / expected_freq for i in range(1, 7))
        
        # Tính expected sum dựa trên phân phối
        expected_next = sum(i * freq[i] for i in range(1, 7)) / len(all_numbers) * 3
    else:
        freq = {}
        chi_square = 0
        expected_next = mean_sum
        high_count = low_count = 0
    
    # Confidence dựa trên độ lệch và biến động
    confidence = 62 + min(abs(z_score) * 12, 25) + min(chi_square, 10)
    confidence = min(confidence, 89)
    
    # Quyết định đa yếu tố
    factors_tai = 0
    factors_xiu = 0
    
    # Yếu tố 1: Mean reversion
    if mean_sum > 11.5:
        factors_xiu += 3
    elif mean_sum < 9.5:
        factors_tai += 3
    elif mean_sum > 10.5:
        factors_xiu += 1
    else:
        factors_tai += 1
    
    # Yếu tố 2: Expected next sum
    if expected_next > 11:
        factors_xiu += 2
    elif expected_next < 10:
        factors_tai += 2
    
    # Yếu tố 3: Phân phối số
    if high_count > low_count * 1.3:
        factors_xiu += 2  # Nhiều số cao, có thể điều chỉnh
    elif low_count > high_count * 1.3:
        factors_tai += 2
    
    # Yếu tố 4: Xu hướng gần đây
    if len(recent_sums) >= 3:
        recent_trend = recent_sums[-1] - recent_sums[-3]
        if recent_trend > 2:
            factors_xiu += 1
        elif recent_trend < -2:
            factors_tai += 1
    
    # Quyết định cuối
    if factors_tai > factors_xiu:
        prediction = 1
        reason = f"Dice Stats: Mean={mean_sum:.2f}, StdDev={std_dev:.2f}, Z={z_score:.2f}, Chi²={chi_square:.1f}, Next={expected_next:.1f}. Factors: T({factors_tai})>X({factors_xiu}) → TÀI"
    else:
        prediction = 0
        reason = f"Dice Stats: Mean={mean_sum:.2f}, StdDev={std_dev:.2f}, Z={z_score:.2f}, Chi²={chi_square:.1f}, Next={expected_next:.1f}. Factors: X({factors_xiu})>T({factors_tai}) → XỈU"
    
    return prediction, round(confidence, 1), reason


# ===============================
# TỔNG HỢP DỰ ĐOÁN
# ===============================
def calculate_prediction():
    global history_full, dice_history, sum_history
    
    if len(history_full) < 3:
        return "TÀI", 50.0
    
    results = []
    weights = []
    
    # Chạy 5 thuật toán
    algos = [
        algorithm_1_mean_reversion(history_full),
        algorithm_2_streak_probability(history_full),
        algorithm_3_conditional_probability(history_full),
        algorithm_4_moving_average_crossover(history_full),
        algorithm_5_dice_statistical_analysis(dice_history, sum_history)
    ]
    
    for pred, conf, _ in algos:
        results.append(pred)
        weights.append(conf)
    
    # Tính điểm có trọng số
    tai_score = sum(w for r, w in zip(results, weights) if r == 1)
    xiu_score = sum(w for r, w in zip(results, weights) if r == 0)
    
    total = tai_score + xiu_score
    if total == 0:
        return "TÀI", 50.0
    
    if tai_score > xiu_score:
        final = "TÀI"
        conf = (tai_score / total) * 100
    else:
        final = "XỈU"
        conf = (xiu_score / total) * 100
    
    conf = max(55, min(conf, 92))
    
    return final, round(conf, 1)


def get_win_loss_stats():
    """Tính toán thống kê Win/Loss"""
    global win_count, loss_count, prediction_history
    
    if win_count + loss_count == 0:
        return {
            "Tổng dự đoán": 0,
            "Win": 0,
            "Loss": 0,
            "Tỷ lệ Win": "0%",
            "Chuỗi hiện tại": "Chưa có dữ liệu"
        }
    
    total = win_count + loss_count
    win_rate = (win_count / total) * 100
    
    # Tính chuỗi hiện tại
    current_streak = 0
    streak_type = None
    
    if len(prediction_history) > 0:
        last_result = prediction_history[-1][1]  # True = Win, False = Loss
        streak_type = "Win" if last_result else "Loss"
        
        for i in range(len(prediction_history) - 1, -1, -1):
            if prediction_history[i][1] == last_result:
                current_streak += 1
            else:
                break
    
    streak_text = f"{current_streak} {streak_type} liên tiếp" if streak_type else "Chưa có"
    
    # Lấy 10 kết quả gần nhất
    recent_10 = []
    for i in range(min(10, len(prediction_history))):
        idx = len(prediction_history) - 1 - i
        pred, result, conf, phien = prediction_history[idx]
        recent_10.append({
            "Phiên": phien,
            "Dự đoán": pred,
            "Kết quả": "Win ✓" if result else "Loss ✗",
            "Độ tin cậy": conf
        })
    
    return {
        "Tổng dự đoán": total,
        "Win": win_count,
        "Loss": loss_count,
        "Tỷ lệ Win": f"{win_rate:.1f}%",
        "Chuỗi hiện tại": streak_text,
        "10 kết quả gần nhất": recent_10
    }


# ===============================
# BOT THU THẬP DỮ LIỆU
# ===============================
def fetch_loop():
    global last_processed_session_id, latest_data
    global history_full, dice_history, sum_history
    global win_count, loss_count, prediction_history, last_prediction
    
    while True:
        try:
            res = requests.get(API_URL, timeout=10)
            data = res.json()
            
            if not data.get("list"):
                time.sleep(2)
                continue
            
            phien = data["list"][0]
            phien_id = phien.get("id")
            
            if phien_id == last_processed_session_id:
                time.sleep(2)
                continue
            
            dices = phien.get("dices")
            tong = phien.get("point")
            d1, d2, d3 = dices
            
            ket_qua = 1 if tong >= 11 else 0
            ket_qua_text = "TÀI" if ket_qua == 1 else "XỈU"
            
            # Kiểm tra dự đoán trước đó
            if last_prediction is not None:
                pred_text, pred_conf, pred_phien = last_prediction
                
                # So sánh dự đoán với kết quả thực tế
                is_win = pred_text == ket_qua_text
                
                if is_win:
                    win_count += 1
                    result_icon = "✓ WIN"
                else:
                    loss_count += 1
                    result_icon = "✗ LOSS"
                
                # Lưu vào lịch sử
                prediction_history.append((pred_text, is_win, pred_conf, pred_phien))
                
                # Giới hạn lịch sử 100 phiên
                if len(prediction_history) > 100:
                    prediction_history.pop(0)
                
                print(f"    └─ Kết quả dự đoán phiên #{pred_phien}: {result_icon} (Dự đoán: {pred_text}, Thực tế: {ket_qua_text})")
            
            # Lưu lịch sử
            history_full.append(ket_qua)
            if len(history_full) > 100:
                history_full.pop(0)
            
            dice_history.append([d1, d2, d3])
            if len(dice_history) > 50:
                dice_history.pop(0)
            
            sum_history.append(tong)
            if len(sum_history) > 50:
                sum_history.pop(0)
            
            last_processed_session_id = phien_id
            
            # Tính dự đoán cho phiên TIẾP THEO
            pred, conf = calculate_prediction()
            
            # Lưu dự đoán này để kiểm tra ở phiên sau
            last_prediction = (pred, conf, phien_id)
            
            # Lấy thống kê Win/Loss
            stats = get_win_loss_stats()
            
            # Cập nhật
            latest_data = {
                "Phiên": phien_id,
                "Xúc xắc 1": d1,
                "Xúc xắc 2": d2,
                "Xúc xắc 3": d3,
                "Tổng": tong,
                "Kết quả": ket_qua_text,
                "Dự đoán phiên tiếp theo": pred,
                "Độ tin cậy": conf,
                "Đã phân tích": len(history_full),
                "Lịch sử Win/Loss": stats,
                "ID": "tuananh"
            }
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] #{phien_id}: {d1}-{d2}-{d3}={tong} ({ket_qua_text}) | Dự đoán tiếp: {pred} ({conf}%) | W/L: {win_count}/{loss_count}")
            
        except Exception as e:
            print(f"Lỗi: {e}")
        
        time.sleep(2)


threading.Thread(target=fetch_loop, daemon=True).start()

# ===============================
# API
# ===============================
@app.route("/api/taixiumd5", methods=["GET"])
def api_data():
    return jsonify(latest_data)

@app.route("/", methods=["GET"])
def home():
    return ""

if __name__ == "__main__":
    print("=" * 70)
    print("🎯 HỆ THỐNG DỰ ĐOÁN TÀI XỈU - THEO DÕI WIN/LOSS")
    print("=" * 70)
    print("📊 5 thuật toán:")
    print("   1. Mean Reversion (Hồi quy trung bình)")
    print("   2. Streak Probability (Xác suất chuỗi)")
    print("   3. Conditional Probability (Xác suất điều kiện)")
    print("   4. MA Crossover (Trung bình động)")
    print("   5. Dice Statistics (Thống kê xúc xắc)")
    print("=" * 70)
    print("📈 Theo dõi: Win/Loss, Tỷ lệ thắng, Chuỗi hiện tại")
    print("📡 API: http://0.0.0.0:10000/api/taixiumd5")
    print("=" * 70)
    app.run(host="0.0.0.0", port=10000, debug=False)
