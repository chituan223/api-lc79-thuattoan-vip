import requests
import time
import threading
from flask import Flask, jsonify
from datetime import datetime

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

# Lưu lịch sử
history_full = []  # Lịch sử đầy đủ
dice_history = []  # Lịch sử xúc xắc
sum_history = []  # Lịch sử tổng điểm

# ===============================
# 5 THUẬT TOÁN MỚI - ĐẢM BẢO HOẠT ĐỘNG
# ===============================

def algo_1_simple_count(history):
    """Thuật toán 1: Đếm đơn giản - Đảo chiều khi lệch"""
    if len(history) < 3:
        return 1, 50.0, "Chưa đủ dữ liệu, dự đoán mặc định TÀI"
    
    recent = history[-10:] if len(history) >= 10 else history
    tai = sum(recent)
    xiu = len(recent) - tai
    
    # Tính độ lệch
    total = len(recent)
    tai_percent = (tai / total) * 100
    
    # Độ tin cậy tăng theo độ lệch
    confidence = 50.0 + abs(tai_percent - 50.0) * 0.8
    confidence = min(confidence, 88.0)
    
    # Dự đoán: Lệch về phía nào thì dự đoán ngược lại
    if tai > xiu + 1:
        prediction = 0  # Xỉu
        reason = f"{total} ván gần: Tài {tai} ({tai_percent:.0f}%) > Xỉu {xiu}. Dự đoán XỈU"
    elif xiu > tai + 1:
        prediction = 1  # Tài
        reason = f"{total} ván gần: Xỉu {xiu} ({100-tai_percent:.0f}%) > Tài {tai}. Dự đoán TÀI"
    else:
        prediction = 1 - history[-1]
        confidence = 58.0
        reason = f"Cân bằng ({tai}T-{xiu}X). Dự đoán đảo chiều"
    
    return prediction, round(confidence, 1), reason


def algo_2_streak_break(history):
    """Thuật toán 2: Phá chuỗi - Đếm chuỗi và dự đoán đảo"""
    if len(history) < 2:
        return 0, 50.0, "Chưa đủ dữ liệu, dự đoán mặc định XỈU"
    
    last = history[-1]
    streak = 1
    
    # Đếm chuỗi
    for i in range(len(history) - 2, max(-1, len(history) - 8), -1):
        if history[i] == last:
            streak += 1
        else:
            break
    
    # Tính confidence dựa trên độ dài chuỗi
    if streak >= 5:
        confidence = 85.0
    elif streak == 4:
        confidence = 78.0
    elif streak == 3:
        confidence = 71.0
    elif streak == 2:
        confidence = 64.0
    else:
        confidence = 57.0
    
    # Dự đoán
    if streak >= 3:
        prediction = 1 - last
        result_name = "TÀI" if prediction == 1 else "XỈU"
        last_name = "TÀI" if last == 1 else "XỈU"
        reason = f"Chuỗi {streak} {last_name} liên tiếp. Phá chuỗi → {result_name}"
    else:
        prediction = last
        result_name = "TÀI" if prediction == 1 else "XỈU"
        reason = f"Chuỗi ngắn ({streak}). Tiếp tục → {result_name}"
    
    return prediction, round(confidence, 1), reason


def algo_3_wave_analysis(history):
    """Thuật toán 3: Phân tích sóng - So sánh gần vs xa"""
    if len(history) < 8:
        return 1, 52.0, "Chưa đủ dữ liệu, dự đoán TÀI"
    
    # Chia làm 2 nửa
    mid = len(history) // 2
    first_half = history[:mid]
    second_half = history[mid:]
    
    tai_first = sum(first_half)
    tai_second = sum(second_half)
    
    percent_first = (tai_first / len(first_half)) * 100
    percent_second = (tai_second / len(second_half)) * 100
    
    diff = abs(percent_second - percent_first)
    confidence = 55.0 + diff * 0.6
    confidence = min(confidence, 83.0)
    
    # Xu hướng đang tăng → dự đoán giảm
    if percent_second > percent_first + 10:
        prediction = 0
        reason = f"Nửa đầu: {percent_first:.0f}% Tài. Nửa sau: {percent_second:.0f}% Tài (tăng). Dự đoán XỈU"
    elif percent_second < percent_first - 10:
        prediction = 1
        reason = f"Nửa đầu: {percent_first:.0f}% Tài. Nửa sau: {percent_second:.0f}% Tài (giảm). Dự đoán TÀI"
    else:
        prediction = 1 if percent_second < 50 else 0
        reason = f"Xu hướng ổn định ({percent_second:.0f}% Tài). Dự đoán điều chỉnh"
    
    return prediction, round(confidence, 1), reason


def algo_4_zigzag_detector(history):
    """Thuật toán 4: Phát hiện zigzag - Đổi chiều liên tục"""
    if len(history) < 5:
        return 0, 51.0, "Chưa đủ dữ liệu, dự đoán XỈU"
    
    recent = history[-6:] if len(history) >= 6 else history
    
    # Đếm số lần đổi chiều
    changes = 0
    for i in range(1, len(recent)):
        if recent[i] != recent[i-1]:
            changes += 1
    
    change_rate = (changes / (len(recent) - 1)) * 100
    
    # Confidence dựa trên tỷ lệ đổi chiều
    if change_rate >= 80:
        confidence = 79.0
        prediction = 1 - history[-1]
        reason = f"Tỷ lệ đổi chiều: {change_rate:.0f}%. Zigzag cao, tiếp tục đổi"
    elif change_rate >= 60:
        confidence = 68.0
        prediction = 1 - history[-1]
        reason = f"Tỷ lệ đổi chiều: {change_rate:.0f}%. Khá cao, dự đoán đổi"
    elif change_rate <= 20:
        confidence = 73.0
        prediction = history[-1]
        reason = f"Tỷ lệ đổi chiều: {change_rate:.0f}%. Thấp, tiếp tục xu hướng"
    else:
        confidence = 61.0
        prediction = 1 - history[-1]
        reason = f"Tỷ lệ đổi chiều: {change_rate:.0f}%. Trung bình"
    
    result_name = "TÀI" if prediction == 1 else "XỈU"
    reason += f" → {result_name}"
    
    return prediction, round(confidence, 1), reason


def algo_5_sum_prediction(dice_hist, sum_hist):
    """Thuật toán 5: Dự đoán từ tổng điểm"""
    if len(sum_hist) < 3:
        return 1, 53.0, "Chưa đủ dữ liệu điểm, dự đoán TÀI"
    
    recent_sums = sum_hist[-5:] if len(sum_hist) >= 5 else sum_hist
    avg_sum = sum(recent_sums) / len(recent_sums)
    
    # Tính độ lệch so với 10.5
    deviation = abs(avg_sum - 10.5)
    confidence = 56.0 + deviation * 4.5
    confidence = min(confidence, 86.0)
    
    # Phân tích số xuất hiện
    high_nums = 0
    low_nums = 0
    
    if len(dice_hist) >= 3:
        for dice in dice_hist[-3:]:
            for num in dice:
                if num >= 4:
                    high_nums += 1
                else:
                    low_nums += 1
    
    # Dự đoán
    if avg_sum >= 12.0:
        prediction = 0
        reason = f"Điểm TB: {avg_sum:.1f} (cao). Số cao/thấp: {high_nums}/{low_nums}. Dự đoán XỈU"
    elif avg_sum <= 9.0:
        prediction = 1
        reason = f"Điểm TB: {avg_sum:.1f} (thấp). Số cao/thấp: {high_nums}/{low_nums}. Dự đoán TÀI"
    elif avg_sum > 10.5:
        prediction = 0
        reason = f"Điểm TB: {avg_sum:.1f} (hơi cao). Dự đoán điều chỉnh XỈU"
    else:
        prediction = 1
        reason = f"Điểm TB: {avg_sum:.1f} (hơi thấp). Dự đoán điều chỉnh TÀI"
    
    return prediction, round(confidence, 1), reason


# ===============================
# HÀM TÍNH DỰ ĐOÁN TỔNG HỢP
# ===============================
def calculate_final_prediction():
    """Tính dự đoán cuối cùng từ 5 thuật toán"""
    global history_full, dice_history, sum_history
    
    # Khởi tạo mặc định
    if len(history_full) < 2:
        return "TÀI", 50.0, {
            "Thông báo": "Đang thu thập dữ liệu ban đầu..."
        }
    
    algo_results = {}
    tai_score = 0.0
    xiu_score = 0.0
    total_weight = 0.0
    
    # Thuật toán 1
    try:
        pred1, conf1, reason1 = algo_1_simple_count(history_full)
        algo_results["Thuật toán 1: Đếm đơn giản"] = {
            "Dự đoán": "TÀI" if pred1 == 1 else "XỈU",
            "Độ tin cậy": conf1,
            "Lý do": reason1
        }
        if pred1 == 1:
            tai_score += conf1
        else:
            xiu_score += conf1
        total_weight += conf1
    except Exception as e:
        algo_results["Thuật toán 1: Đếm đơn giản"] = {"Lỗi": str(e)}
    
    # Thuật toán 2
    try:
        pred2, conf2, reason2 = algo_2_streak_break(history_full)
        algo_results["Thuật toán 2: Phá chuỗi"] = {
            "Dự đoán": "TÀI" if pred2 == 1 else "XỈU",
            "Độ tin cậy": conf2,
            "Lý do": reason2
        }
        if pred2 == 1:
            tai_score += conf2
        else:
            xiu_score += conf2
        total_weight += conf2
    except Exception as e:
        algo_results["Thuật toán 2: Phá chuỗi"] = {"Lỗi": str(e)}
    
    # Thuật toán 3
    try:
        pred3, conf3, reason3 = algo_3_wave_analysis(history_full)
        algo_results["Thuật toán 3: Phân tích sóng"] = {
            "Dự đoán": "TÀI" if pred3 == 1 else "XỈU",
            "Độ tin cậy": conf3,
            "Lý do": reason3
        }
        if pred3 == 1:
            tai_score += conf3
        else:
            xiu_score += conf3
        total_weight += conf3
    except Exception as e:
        algo_results["Thuật toán 3: Phân tích sóng"] = {"Lỗi": str(e)}
    
    # Thuật toán 4
    try:
        pred4, conf4, reason4 = algo_4_zigzag_detector(history_full)
        algo_results["Thuật toán 4: Phát hiện Zigzag"] = {
            "Dự đoán": "TÀI" if pred4 == 1 else "XỈU",
            "Độ tin cậy": conf4,
            "Lý do": reason4
        }
        if pred4 == 1:
            tai_score += conf4
        else:
            xiu_score += conf4
        total_weight += conf4
    except Exception as e:
        algo_results["Thuật toán 4: Phát hiện Zigzag"] = {"Lỗi": str(e)}
    
    # Thuật toán 5
    try:
        pred5, conf5, reason5 = algo_5_sum_prediction(dice_history, sum_history)
        algo_results["Thuật toán 5: Dự đoán từ điểm"] = {
            "Dự đoán": "TÀI" if pred5 == 1 else "XỈU",
            "Độ tin cậy": conf5,
            "Lý do": reason5
        }
        if pred5 == 1:
            tai_score += conf5
        else:
            xiu_score += conf5
        total_weight += conf5
    except Exception as e:
        algo_results["Thuật toán 5: Dự đoán từ điểm"] = {"Lỗi": str(e)}
    
    # Tính kết quả cuối
    if total_weight == 0:
        return "TÀI", 50.0, algo_results
    
    tai_percent = (tai_score / total_weight) * 100
    xiu_percent = (xiu_score / total_weight) * 100
    
    if tai_score > xiu_score:
        final_prediction = "TÀI"
        final_confidence = tai_percent
    else:
        final_prediction = "XỈU"
        final_confidence = xiu_percent
    
    # Đảm bảo confidence trong khoảng hợp lý
    final_confidence = max(52.0, min(final_confidence, 87.0))
    
    # Thêm tổng kết
    algo_results["Tổng kết bỏ phiếu"] = {
        "Điểm TÀI": round(tai_score, 1),
        "Điểm XỈU": round(xiu_score, 1),
        "Phần trăm TÀI": f"{tai_percent:.1f}%",
        "Phần trăm XỈU": f"{xiu_percent:.1f}%"
    }
    
    return final_prediction, round(final_confidence, 1), algo_results


# ===============================
# BOT NỀN – LẤY DATA 24/7
# ===============================
def fetch_data_loop():
    global last_processed_session_id
    global latest_data
    global history_full, dice_history, sum_history

    print("Bot bắt đầu thu thập dữ liệu...")
    
    while True:
        try:
            # 1. LẤY DỮ LIỆU TỪ API
            res = requests.get(API_URL, timeout=10)
            data = res.json()

            list_data = data.get("list", [])
            if not list_data:
                time.sleep(2)
                continue

            phien = list_data[0]
            phien_id = phien.get("id")
            
            # 2. KIỂM TRA PHIÊN MỚI
            if phien_id == last_processed_session_id:
                time.sleep(2)
                continue

            # 3. XỬ LÝ DỮ LIỆU PHIÊN MỚI
            dices = phien.get("dices")
            tong = phien.get("point")
            d1, d2, d3 = dices

            ket_qua = 1 if tong >= 11 else 0  # 1=TÀI, 0=XỈU
            
            # Lưu lịch sử đầy đủ
            history_full.append(ket_qua)
            if len(history_full) > 100:
                history_full.pop(0)
            
            # Lưu lịch sử xúc xắc
            dice_history.append([d1, d2, d3])
            if len(dice_history) > 50:
                dice_history.pop(0)
            
            # Lưu lịch sử tổng điểm
            sum_history.append(tong)
            if len(sum_history) > 50:
                sum_history.pop(0)
            
            # Cập nhật ID phiên đã xử lý
            last_processed_session_id = phien_id
            
            # 4. TÍNH DỰ ĐOÁN CHO PHIÊN TIẾP THEO
            final_pred, final_conf, algo_details = calculate_final_prediction()
            
            # 5. CẬP NHẬT DỮ LIỆU API TRẢ VỀ
            latest_data = {
                "Phiên": phien_id,
                "Xúc xắc 1": d1,
                "Xúc xắc 2": d2,
                "Xúc xắc 3": d3,
                "Tổng": tong,
                "Kết quả": "TÀI" if ket_qua == 1 else "XỈU",
                "Dự đoán phiên tiếp theo": final_pred,
                "Độ tin cậy": final_conf,
                "Chi tiết 5 thuật toán": algo_details,
                "Số phiên đã phân tích": len(history_full),
                "ID": "tuananh"
            }
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Phiên {phien_id}: {d1}-{d2}-{d3}={tong} ({'TÀI' if ket_qua==1 else 'XỈU'}) | Dự đoán tiếp: {final_pred} ({final_conf}%)")

        except Exception as e:
            print(f"Lỗi ({datetime.now().strftime('%H:%M:%S')}):", e)
            
        time.sleep(2)


# ===============================
# KHỞI CHẠY TIẾN TRÌNH NỀN
# ===============================
threading.Thread(target=fetch_data_loop, daemon=True).start()


# ===============================
# API CHÍNH
# ===============================
@app.route("/api/taixiumd5", methods=["GET"])
def api_data():
    return jsonify({
        "success": True,
        "data": latest_data,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })





# ===============================
# RUN SERVER
# ===============================
if __name__ == "__main__":
    print("🚀 Server đang khởi động...")
    print("📡 API: http://0.0.0.0:10000/api/taixiumd5")
    app.run(host="0.0.0.0", port=10000, debug=False)
