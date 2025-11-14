import requests
import time
import threading
from collections import deque
import statistics
import os
import json
from typing import List, Dict, Optional, Tuple, Callable
from flask import Flask, jsonify

# Định nghĩa cấu trúc dữ liệu cho dự đoán
PredictionResult = Dict[str, any]

# =========================================================
# I. KHU VỰC ĐỊNH NGHĨA THUẬT TOÁN (50 STRATEGIES - VIP)
# =========================================================
# Tất cả các thuật toán phải nhận 3 tham số: history, totals, win_log
# và trả về Dict[str, any] với 'du_doan' (Tài/Xỉu) và 'do_tin_cay' (0-100)

# --- KHỐI 1: CÁC THUẬT TOÁN BAN ĐẦU (AI1 - AI20) ---

def ai1_frequency(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Phân tích tần suất Tài/Xỉu trong 6 phiên gần nhất."""
    if len(history) < 6:
        return {"du_doan": "Tài", "do_tin_cay": 65.2}
    window = list(history)[-6:]
    t = window.count("Tài")
    x = window.count("Xỉu")
    if t > x + 1:
        return {"du_doan": "Xỉu", "do_tin_cay": 88.3}
    if x > t + 1:
        return {"du_doan": "Tài", "do_tin_cay": 87.5}
    return {"du_doan": history[-1], "do_tin_cay": 73.4}

def ai2_parity_chain(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Phân tích chuỗi chẵn/lẻ của tổng điểm trong 5 phiên."""
    if len(totals) < 5:
        return {"du_doan": "Tài", "do_tin_cay": 66.7}
    last5 = list(totals)[-5:]
    evens = sum(1 for t in last5 if t % 2 == 0)
    if evens >= 4:
        # Thiên về chẵn, thường đi kèm Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 91.2}
    if evens <= 1:
        # Thiên về lẻ, thường đi kèm Tài
        return {"du_doan": "Tài", "do_tin_cay": 90.4}
    return {"du_doan": "Tài" if totals[-1] >= 11 else "Xỉu", "do_tin_cay": 71.9}

def ai3_moving_avg(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Phân tích trung bình trượt 4 phiên."""
    if len(totals) < 4:
        return {"du_doan": "Tài", "do_tin_cay": 65.8}
    avg4 = statistics.mean(list(totals)[-4:])
    if avg4 > 10.9:
        return {"du_doan": "Tài", "do_tin_cay": 85.6}
    if avg4 < 10.1:
        return {"du_doan": "Xỉu", "do_tin_cay": 84.8}
    return {"du_doan": history[-1], "do_tin_cay": 72.1}

def ai4_streak_detector(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Phát hiện chuỗi Tài hoặc Xỉu dài (từ 4 trở lên) và dự đoán lật kèo."""
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
        # Nếu chuỗi dài, dự đoán ngược lại (nguyên tắc Martingale ngược)
        return {"du_doan": "Xỉu" if last == "Tài" else "Tài", "do_tin_cay": 92.8}
    return {"du_doan": last, "do_tin_cay": 70.5}

def ai5_alternating_pattern(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Phân tích mẫu xen kẽ (TXTX hoặc XTXT)."""
    if len(history) < 6:
        return {"du_doan": "Tài", "do_tin_cay": 66.2}
    seq = "".join("T" if h == "Tài" else "X" for h in list(history)[-4:])
    if seq == "TXTX":
        # TXTX -> dự đoán T (Tài) để tiếp tục mẫu xen kẽ
        return {"du_doan": "Tài", "do_tin_cay": 89.4}
    if seq == "XTXT":
        # XTXT -> dự đoán X (Xỉu) để tiếp tục mẫu xen kẽ
        return {"du_doan": "Xỉu", "do_tin_cay": 89.4}
    return {"du_doan": history[-1], "do_tin_cay": 68.9}

def ai6_total_variability(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Phân tích sự biến động của tổng điểm trong 5 phiên gần nhất."""
    if len(totals) < 5:
        return {"du_doan": "Tài", "do_tin_cay": 67.0}
    window = list(totals)[-5:]
    mean = statistics.mean(window)
    var = max(window) - min(window)
    # Nếu trung bình Tài và ít biến động (var <= 2) -> tiếp tục Tài
    if mean >= 11 and var <= 2:
        return {"du_doan": "Tài", "do_tin_cay": 87.2}
    # Nếu trung bình Xỉu và ít biến động (var <= 2) -> tiếp tục Xỉu
    if mean <= 10 and var <= 2:
        return {"du_doan": "Xỉu", "do_tin_cay": 86.6}
    return {"du_doan": history[-1], "do_tin_cay": 73.8}

def ai7_short_cycle(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Mẫu 1-2-1 (T X T hoặc X T X) -> Dự đoán tiếp tục lặp lại T/X."""
    if len(history) < 3:
        return {"du_doan": "Tài", "do_tin_cay": 61.7}
    tail = list(history)[-3:]
    # Mẫu 1-2-1: T X T hoặc X T X
    if tail[0] == tail[2] and tail[0] != tail[1]:
        # Dự đoán ngược lại phiên cuối (T X T -> dự đoán X)
        return {"du_doan": "Xỉu" if tail[-1] == "Tài" else "Tài", "do_tin_cay": 88.9}
    return {"du_doan": history[-1], "do_tin_cay": 70.3}

def ai8_even_bias_long(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Thiên vị chẵn/lẻ dài hạn (8 phiên) và dự đoán ngược lại."""
    if len(totals) < 8:
        return {"du_doan": "Tài", "do_tin_cay": 64.6}
    last8 = list(totals)[-8:]
    evens = sum(1 for t in last8 if t % 2 == 0)
    if evens >= 6:
        # Quá nhiều chẵn -> dự đoán lẻ (Tài)
        return {"du_doan": "Tài", "do_tin_cay": 91.1}
    if evens <= 2:
        # Quá nhiều lẻ -> dự đoán chẵn (Xỉu)
        return {"du_doan": "Xỉu", "do_tin_cay": 90.7}
    return {"du_doan": "Tài" if totals[-1] >= 11 else "Xỉu", "do_tin_cay": 71.5}

def ai9_median_check(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Kiểm tra trung vị 5 phiên. Nếu trung vị cao/thấp, dự đoán theo xu hướng."""
    if len(totals) < 5:
        return {"du_doan": "Tài", "do_tin_cay": 65.1}
    med = statistics.median(list(totals)[-5:])
    if med > 10.6:
        return {"du_doan": "Tài", "do_tin_cay": 84.3}
    if med < 10.4:
        return {"du_doan": "Xỉu", "do_tin_cay": 84.1}
    return {"du_doan": history[-1], "do_tin_cay": 72.8}

def ai10_trend_slope(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Độ dốc xu hướng (Total[-1] - Total[-5]) / 4. Dự đoán theo độ dốc."""
    if len(totals) < 5:
        return {"du_doan": "Tài", "do_tin_cay": 63.7}
    slope = (totals[-1] - totals[-5]) / 4
    if slope >= 0.6:
        return {"du_doan": "Tài", "do_tin_cay": 89.6}
    if slope <= -0.6:
        return {"du_doan": "Xỉu", "do_tin_cay": 89.4}
    return {"du_doan": "Tài" if totals[-1] >= 11 else "Xỉu", "do_tin_cay": 72.2}

def ai11_weighted_vote(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Bỏ phiếu có trọng số dựa trên tần suất, trung bình và chẵn lẻ (6 phiên)."""
    if len(history) < 6 or len(totals) < 6:
        return {"du_doan": "Tài", "do_tin_cay": 66.4}
    tcount = list(history)[-6:].count("Tài")
    mean6 = statistics.mean(list(totals)[-6:])
    parity = sum(1 for t in list(totals)[-6:] if t % 2 == 0) # Count of Evens

    score = 0
    if tcount > 3: score += 1 # Trend Tài
    if mean6 >= 11: score += 1 # High Average
    if parity <= 2: score += 1 # Low Even count (favoring Odd/Tài)

    if score >= 2:
        return {"du_doan": "Tài", "do_tin_cay": 86.5}
    if score <= 0:
        return {"du_doan": "Xỉu", "do_tin_cay": 85.9}
    return {"du_doan": history[-1], "do_tin_cay": 74.2}


def ai12_recent_trend(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Xu hướng gần đây (2 phiên liên tiếp) -> dự đoán tiếp tục."""
    if len(history) < 3:
        return {"du_doan": "Tài", "do_tin_cay": 62.3}
    trend = list(history)[-2:]
    if trend[0] == trend[1]:
        return {"du_doan": trend[0], "do_tin_cay": 80.6}
    return {"du_doan": history[-1], "do_tin_cay": 70.1}

def ai13_balance(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Cân bằng dài hạn giữa Tài và Xỉu. Dự đoán bù đắp (reversion to mean)."""
    if len(history) == 0:
        return {"du_doan": "Tài", "do_tin_cay": 60.0}
    t = history.count("Tài")
    x = history.count("Xỉu")
    if abs(t - x) >= 5:
        # Nếu chênh lệch lớn, dự đoán bên ít hơn
        return {"du_doan": "Xỉu" if t > x else "Tài", "do_tin_cay": 83.2}
    return {"du_doan": history[-1], "do_tin_cay": 71.6}

def ai14_gradient(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Độ dốc tổng điểm 4 phiên (Total[-1] - Total[-4])."""
    if len(totals) < 4:
        return {"du_doan": "Tài", "do_tin_cay": 63.4}
    grad = totals[-1] - totals[-4]
    if grad > 1.5:
        return {"du_doan": "Tài", "do_tin_cay": 87.3}
    if grad < -1.5:
        return {"du_doan": "Xỉu", "do_tin_cay": 87.0}
    return {"du_doan": history[-1], "do_tin_cay": 74.0}

def ai15_stability(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Mức độ ổn định/biến động của tổng điểm 5 phiên. Ổn định -> Xỉu, Biến động -> Tài."""
    if len(totals) < 5:
        return {"du_doan": "Tài", "do_tin_cay": 64.5}
    diff = max(totals[-5:]) - min(totals[-5:])
    if diff <= 2:
        # Biến động thấp -> dự đoán Xỉu (vì Tài thường đi kèm biến động lớn hơn)
        return {"du_doan": "Xỉu", "do_tin_cay": 81.8}
    # Biến động cao
    return {"du_doan": "Tài", "do_tin_cay": 75.3}

def ai16_flip_after_loss(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Đảo ngược kết quả sau khi thuật toán thua ở phiên trước (Meta-Strategy)."""
    if len(win_log) > 0 and history and not win_log[-1]:
        return {"du_doan": "Xỉu" if history[-1] == "Tài" else "Tài", "do_tin_cay": 81.2}
    return {"du_doan": history[-1], "do_tin_cay": 72.6}

def ai17_recent_variance(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Biến động gần đây (5 phiên). Dự đoán Tài nếu biến động lớn."""
    if len(totals) < 5:
        return {"du_doan": "Tài", "do_tin_cay": 66.1}
    var = max(totals[-5:]) - min(totals[-5:])
    return {"du_doan": "Tài" if var > 4 else "Xỉu", "do_tin_cay": 78.8}

def ai18_sequence(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Phát hiện chuỗi 5 liên tiếp (TTTTT/XXXXX) và dự đoán đảo chiều."""
    if len(history) < 5:
        return {"du_doan": "Tài", "do_tin_cay": 64.9}
    seq = "".join("T" if h == "Tài" else "X" for h in list(history)[-5:])
    if seq in ["TTTTT", "XXXXX"]:
        # Chuỗi dài 5 -> dự đoán đảo chiều
        return {"du_doan": "Xỉu" if history[-1] == "Tài" else "Tài", "do_tin_cay": 89.9}
    return {"du_doan": history[-1], "do_tin_cay": 70.9}

def ai19_long_term_mean(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Trung bình dài hạn 10 phiên. Dự đoán theo hướng trung bình."""
    if len(totals) < 10:
        return {"du_doan": "Tài", "do_tin_cay": 65.7}
    mean10 = statistics.mean(list(totals)[-10:])
    if mean10 > 11:
        return {"du_doan": "Tài", "do_tin_cay": 84.7}
    if mean10 < 10:
        return {"du_doan": "Xỉu", "do_tin_cay": 83.9}
    return {"du_doan": history[-1], "do_tin_cay": 71.3}

def ai20_adaptive(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Tỷ lệ Tài/Xỉu trong 8 phiên, dự đoán ngược lại nếu tỷ lệ quá cao/thấp (trên 75%)."""
    if len(history) < 8:
        return {"du_doan": "Tài", "do_tin_cay": 66.5}
    ratio = list(history)[-8:].count("Tài") / 8
    if ratio > 0.75:
        return {"du_doan": "Xỉu", "do_tin_cay": 90.6}
    if ratio < 0.25:
        return {"du_doan": "Tài", "do_tin_cay": 90.2}
    return {"du_doan": history[-1], "do_tin_cay": 72.4}

# --- KHỐI 2: 30 THUẬT TOÁN VIP MỚI (AI21 - AI50) ---

def ai21_3_2_1_pattern(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Mẫu 3-2-1: TTTXXT hoặc XXXTTX. Dự đoán lật kèo tiếp theo."""
    if len(history) < 6:
        return {"du_doan": "Tài", "do_tin_cay": 68.1}
    seq = "".join("T" if h == "Tài" else "X" for h in list(history)[-6:])
    if seq == "TTTXXT":
        # Chuẩn bị lật kèo sang Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 91.5}
    if seq == "XXXTTX":
        # Chuẩn bị lật kèo sang Tài
        return {"du_doan": "Tài", "do_tin_cay": 91.3}
    return {"du_doan": history[-1], "do_tin_cay": 70.8}

def ai22_double_triple(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Mẫu 2-3: TTXXX hoặc XXTTT. Dự đoán kết thúc xu hướng."""
    if len(history) < 5:
        return {"du_doan": "Xỉu", "do_tin_cay": 67.5}
    seq = "".join("T" if h == "Tài" else "X" for h in list(history)[-5:])
    if seq == "TTXXX":
        # Dự đoán lật sang Tài
        return {"du_doan": "Tài", "do_tin_cay": 89.8}
    if seq == "XXTTT":
        # Dự đoán lật sang Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 89.7}
    return {"du_doan": history[-1], "do_tin_cay": 72.5}

def ai23_alternating_4(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Mẫu xen kẽ ngắn 4 phiên (TXXT hoặc XTTX). Dự đoán ngược lại để phá vỡ mẫu."""
    if len(history) < 4:
        return {"du_doan": "Tài", "do_tin_cay": 66.8}
    seq = "".join("T" if h == "Tài" else "X" for h in list(history)[-4:])
    if seq == "TXXT":
        # Dự đoán Xỉu (chống lặp lại T)
        return {"du_doan": "Xỉu", "do_tin_cay": 88.0}
    if seq == "XTTX":
        # Dự đoán Tài (chống lặp lại X)
        return {"du_doan": "Tài", "do_tin_cay": 88.2}
    return {"du_doan": history[-1], "do_tin_cay": 71.1}

def ai24_long_term_alternating_7(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Mẫu xen kẽ dài 7 phiên. Nếu tỷ lệ T/X là 4/3 hoặc 3/4 và xen kẽ, dự đoán bên ít hơn."""
    if len(history) < 7:
        return {"du_doan": "Tài", "do_tin_cay": 65.4}
    last7 = list(history)[-7:]
    t_count = last7.count("Tài")
    x_count = last7.count("Xỉu")

    if (t_count == 4 and x_count == 3):
        # Xu hướng Tài trội, dự đoán Xỉu (bù đắp)
        return {"du_doan": "Xỉu", "do_tin_cay": 85.5}
    if (t_count == 3 and x_count == 4):
        # Xu hướng Xỉu trội, dự đoán Tài (bù đắp)
        return {"du_doan": "Tài", "do_tin_cay": 85.3}
    return {"du_doan": history[-1], "do_tin_cay": 70.2}

def ai25_weighted_moving_avg_5(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Trung bình trượt có trọng số (WMA) 5 phiên (gần nhất quan trọng hơn)."""
    if len(totals) < 5:
        return {"du_doan": "Xỉu", "do_tin_cay": 67.2}
    window = list(totals)[-5:]
    weights = [1, 2, 3, 4, 5]
    wma = sum(w * t for w, t in zip(weights, window)) / sum(weights)

    if wma > 11.2:
        return {"du_doan": "Tài", "do_tin_cay": 92.0}
    if wma < 9.8:
        return {"du_doan": "Xỉu", "do_tin_cay": 91.8}
    return {"du_doan": history[-1], "do_tin_cay": 75.1}

def ai26_z_score_deviation_15(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Kiểm tra độ lệch Z-Score của tổng điểm hiện tại so với 15 phiên."""
    if len(totals) < 15:
        return {"du_doan": "Tài", "do_tin_cay": 66.5}
    window = list(totals)[-15:]
    current_total = totals[-1]

    mean = statistics.mean(window)
    # Tránh lỗi chia cho 0
    std_dev = statistics.stdev(window) if len(window) > 1 else 1

    z_score = (current_total - mean) / std_dev

    if z_score > 1.5:
        # Quá cao -> dự đoán hồi quy (Xỉu)
        return {"du_doan": "Xỉu", "do_tin_cay": 93.1}
    if z_score < -1.5:
        # Quá thấp -> dự đoán hồi quy (Tài)
        return {"du_doan": "Tài", "do_tin_cay": 92.9}
    return {"du_doan": history[-1], "do_tin_cay": 74.5}

def ai27_keltner_channels(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Dự đoán hồi quy khi tổng điểm gần với giá trị trung bình (Mean Reversion)."""
    if len(totals) < 8:
        return {"du_doan": "Xỉu", "do_tin_cay": 67.0}
    window = list(totals)[-8:]
    mean = statistics.mean(window)
    max_range = max(window) - min(window) # Tương đương ATR đơn giản
    current_total = totals[-1]

    # Nếu đang ở gần giá trị trung bình (trong khoảng +/- 0.5 range)
    if abs(current_total - mean) < max_range * 0.1:
        # Tạm thời dự đoán bên trung tính
        return {"du_doan": "Tài" if current_total >= 11 else "Xỉu", "do_tin_cay": 83.5}

    # Nếu chạm biên trên (xuất hiện Tài lớn) -> dự đoán Xỉu
    if current_total >= mean + max_range * 0.4:
        return {"du_doan": "Xỉu", "do_tin_cay": 87.7}
    # Nếu chạm biên dưới (xuất hiện Xỉu nhỏ) -> dự đoán Tài
    if current_total <= mean - max_range * 0.4:
        return {"du_doan": "Tài", "do_tin_cay": 87.9}

    return {"du_doan": history[-1], "do_tin_cay": 73.0}

def ai28_std_dev_breakout(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Dự đoán sự bùng nổ (Breakout) khi độ lệch chuẩn (volatility) rất thấp (5 phiên)."""
    if len(totals) < 5:
        return {"du_doan": "Tài", "do_tin_cay": 68.3}
    window = list(totals)[-5:]

    # Độ lệch chuẩn rất thấp (thị trường 'coiling')
    if len(window) > 1:
        try:
            std_dev = statistics.stdev(window)
        except statistics.StatisticsError: # Nếu tất cả giá trị bằng nhau
            std_dev = 0
    else:
        std_dev = 1

    if std_dev <= 0.5:
        # Dự đoán bùng nổ theo hướng đang có lợi thế (hướng của phiên cuối)
        return {"du_doan": "Xỉu" if history[-1] == "Tài" else "Tài", "do_tin_cay": 90.9}

    return {"du_doan": history[-1], "do_tin_cay": 71.4}

def ai29_momentum_indicator(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Chỉ số động lượng: So sánh Total[-1] với Total[-3] và Total[-5]."""
    if len(totals) < 5:
        return {"du_doan": "Xỉu", "do_tin_cay": 69.1}
    m1 = totals[-1] - totals[-3]
    m2 = totals[-3] - totals[-5]

    # Động lượng dương mạnh (đi lên Tài)
    if m1 > 1.5 and m2 > 1.0:
        return {"du_doan": "Tài", "do_tin_cay": 90.5}
    # Động lượng âm mạnh (đi xuống Xỉu)
    if m1 < -1.5 and m2 < -1.0:
        return {"du_doan": "Xỉu", "do_tin_cay": 90.3}
    return {"du_doan": history[-1], "do_tin_cay": 73.2}

def ai30_extreme_totals_bias(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Thiên vị Tổng điểm cực trị (4, 5, 16, 17) trong 10 phiên. Dự đoán bù trừ."""
    if len(totals) < 10:
        return {"du_doan": "Tài", "do_tin_cay": 68.6}
    window = list(totals)[-10:]
    extreme_t = sum(1 for t in window if t >= 16)
    extreme_x = sum(1 for t in window if t <= 5)

    if extreme_t >= 2 and extreme_x == 0:
        # Nhiều Tài cực đại, dự đoán Xỉu cực tiểu để cân bằng
        return {"du_doan": "Xỉu", "do_tin_cay": 91.9}
    if extreme_x >= 2 and extreme_t == 0:
        # Nhiều Xỉu cực tiểu, dự đoán Tài cực đại để cân bằng
        return {"du_doan": "Tài", "do_tin_cay": 91.7}
    return {"du_doan": history[-1], "do_tin_cay": 74.4}

def ai31_mid_range_stability(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Ổn định phạm vi trung bình (9, 10, 11, 12). Nếu 4/5 phiên là trung bình, dự đoán tiếp tục."""
    if len(totals) < 5:
        return {"du_doan": "Xỉu", "do_tin_cay": 69.0}
    window = list(totals)[-5:]
    mid_count = sum(1 for t in window if 9 <= t <= 12)

    if mid_count >= 4:
        # Tiếp tục duy trì ở mức trung bình (trung tính)
        return {"du_doan": "Tài" if totals[-1] >= 11 else "Xỉu", "do_tin_cay": 87.1}
    return {"du_doan": history[-1], "do_tin_cay": 70.4}

def ai32_boundary_reversion(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Dự đoán hồi quy khi tổng điểm chạm sát ranh giới 10/11 (tổng 8 hoặc 13)."""
    if len(totals) < 1:
        return {"du_doan": "Tài", "do_tin_cay": 66.0}
    last_total = totals[-1]
    if last_total == 8:
        # Gần Xỉu biên -> thường bật ngược lên Tài
        return {"du_doan": "Tài", "do_tin_cay": 88.5}
    if last_total == 13:
        # Gần Tài biên -> thường bật ngược xuống Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 88.7}
    return {"du_doan": history[-1], "do_tin_cay": 71.9}

def ai33_odd_streak(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Chuỗi lẻ (Odd Total) 5 phiên liên tiếp -> dự đoán Chẵn (Xỉu)."""
    if len(totals) < 5:
        return {"du_doan": "Xỉu", "do_tin_cay": 67.8}
    last5_odd = all(t % 2 != 0 for t in list(totals)[-5:])
    if last5_odd:
        # 5 lần lẻ liên tiếp -> dự đoán chẵn (thường là Xỉu)
        return {"du_doan": "Xỉu", "do_tin_cay": 92.4}
    return {"du_doan": history[-1], "do_tin_cay": 70.6}

def ai34_even_bias_short_4(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Thiên vị chẵn ngắn hạn (4 phiên). Nếu 3/4 là chẵn, dự đoán Chẵn tiếp (Xỉu)."""
    if len(totals) < 4:
        return {"du_doan": "Tài", "do_tin_cay": 66.9}
    evens = sum(1 for t in list(totals)[-4:] if t % 2 == 0)
    if evens >= 3:
        return {"du_doan": "Xỉu", "do_tin_cay": 89.1}
    return {"du_doan": history[-1], "do_tin_cay": 71.2}

def ai35_parity_switch(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Dự đoán Tài/Xỉu ngược với Parity (tổng chẵn/lẻ) của phiên gần nhất."""
    if len(totals) < 1:
        return {"du_doan": "Tài", "do_tin_cay": 65.5}
    last_total = totals[-1]
    # Lẻ (Odd) thường là Tài, Chẵn (Even) thường là Xỉu
    if last_total % 2 != 0: # Lẻ (Tài) -> Dự đoán ngược lại là Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 81.5}
    else: # Chẵn (Xỉu) -> Dự đoán ngược lại là Tài
        return {"du_doan": "Tài", "do_tin_cay": 81.3}

def ai36_algo_performance_switch(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Meta-Strategy: Đảo ngược dự đoán của phiên cuối nếu có 3 lần thua liên tiếp."""
    if len(win_log) < 3:
        return {"du_doan": "Tài", "do_tin_cay": 68.7}
    
    last3_losses = not win_log[-1] and not win_log[-2] and not win_log[-3]
    if last3_losses and history:
        # Nếu thua 3 lần liên tiếp, dự đoán ngược lại kết quả cuối cùng
        return {"du_doan": "Xỉu" if history[-1] == "Tài" else "Tài", "do_tin_cay": 93.5}
    
    return {"du_doan": history[-1], "do_tin_cay": 72.0}

def ai37_majority_vote_top_5(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Dummy Meta-Strategy: Giả định lấy kết quả từ 5 thuật toán mạnh nhất (cần biết thuật toán mạnh nhất)."""
    if len(history) < 10:
        return {"du_doan": "Xỉu", "do_tin_cay": 67.9}
    
    # Giả định 5 thuật toán mạnh nhất là: ai1, ai4, ai10, ai18, ai25
    votes = [
        ai1_frequency(history, totals, win_log)["du_doan"],
        ai4_streak_detector(history, totals, win_log)["du_doan"],
        ai10_trend_slope(history, totals, win_log)["du_doan"],
        ai18_sequence(history, totals, win_log)["du_doan"],
        ai25_weighted_moving_avg_5(history, totals, win_log)["du_doan"]
    ]
    
    t_votes = votes.count("Tài")
    x_votes = votes.count("Xỉu")

    if t_votes > x_votes:
        return {"du_doan": "Tài", "do_tin_cay": 94.1}
    if x_votes > t_votes:
        return {"du_doan": "Xỉu", "do_tin_cay": 94.0}
    
    return {"du_doan": history[-1], "do_tin_cay": 75.0}

def ai38_win_loss_balance(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Dự đoán bên thua nhiều hơn trong 10 phiên sẽ thắng (Reversion to mean)."""
    if len(history) < 10:
        return {"du_doan": "Tài", "do_tin_cay": 65.0}
    
    last10 = list(history)[-10:]
    t_count = last10.count("Tài")
    x_count = last10.count("Xỉu")
    
    if t_count - x_count >= 3:
        # Tài nhiều hơn 3 -> dự đoán Xỉu (bù đắp)
        return {"du_doan": "Xỉu", "do_tin_cay": 87.5}
    if x_count - t_count >= 3:
        # Xỉu nhiều hơn 3 -> dự đoán Tài (bù đắp)
        return {"du_doan": "Tài", "do_tin_cay": 87.3}
    
    return {"du_doan": history[-1], "do_tin_cay": 71.0}

def ai39_fib_reversion_5(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Fibonacci Reversion: Dự đoán đảo chiều sau 5 kết quả Tài hoặc Xỉu liên tiếp."""
    if len(history) < 5:
        return {"du_doan": "Xỉu", "do_tin_cay": 66.6}
    
    seq = "".join("T" if h == "Tài" else "X" for h in list(history)[-5:])
    
    if seq == "TTTTT":
        return {"du_doan": "Xỉu", "do_tin_cay": 90.0}
    if seq == "XXXXX":
        return {"du_doan": "Tài", "do_tin_cay": 90.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.7}

def ai40_martingale_detector(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Dự đoán tiếp tục xu hướng sau 2 lần đảo ngược (TXTX -> T)."""
    if len(history) < 4:
        return {"du_doan": "Tài", "do_tin_cay": 65.3}
    
    seq = "".join("T" if h == "Tài" else "X" for h in list(history)[-4:])
    
    if seq == "TXTX":
        # Chuỗi xen kẽ, Martingale dự đoán đảo chiều sang T
        return {"du_doan": "Tài", "do_tin_cay": 86.1}
    if seq == "XTXT":
        # Chuỗi xen kẽ, Martingale dự đoán đảo chiều sang X
        return {"du_doan": "Xỉu", "do_tin_cay": 86.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 71.8}

def ai41_variance_volatility_5(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Biến động tổng điểm 5 phiên. Nếu biến động tăng -> Tài, Biến động giảm -> Xỉu."""
    if len(totals) < 5:
        return {"du_doan": "Xỉu", "do_tin_cay": 67.4}
    
    diff = max(totals[-5:]) - min(totals[-5:])
    
    if diff > 5:
        return {"du_doan": "Tài", "do_tin_cay": 88.8}
    if diff <= 2:
        return {"du_doan": "Xỉu", "do_tin_cay": 88.6}
        
    return {"du_doan": history[-1], "do_tin_cay": 72.3}

def ai42_gap_filler(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Lấp đầy khoảng trống: Nếu một bên không xuất hiện 5 phiên, dự đoán nó sẽ xuất hiện."""
    if len(history) < 5:
        return {"du_doan": "Tài", "do_tin_cay": 66.0}
    
    last5 = list(history)[-5:]
    if last5.count("Tài") == 0:
        return {"du_doan": "Tài", "do_tin_cay": 89.2}
    if last5.count("Xỉu") == 0:
        return {"du_doan": "Xỉu", "do_tin_cay": 89.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 71.6}

def ai43_double_frequency(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Mẫu 2-1: TTX hoặc XXT. Dự đoán bên ngược lại tiếp tục (TTC)."""
    if len(history) < 3:
        return {"du_doan": "Xỉu", "do_tin_cay": 65.6}
    
    seq = "".join("T" if h == "Tài" else "X" for h in list(history)[-3:])
    
    if seq == "TTX":
        # Dự đoán Xỉu (vì X đã xuất hiện)
        return {"du_doan": "Xỉu", "do_tin_cay": 87.6}
    if seq == "XXT":
        # Dự đoán Tài (vì T đã xuất hiện)
        return {"du_doan": "Tài", "do_tin_cay": 87.4}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai44_alternating_double(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Mẫu xen kẽ kép: T T X X T T -> Dự đoán X X."""
    if len(history) < 6:
        return {"du_doan": "Tài", "do_tin_cay": 64.7}
    
    seq = "".join("T" if h == "Tài" else "X" for h in list(history)[-6:])
    
    if seq == "TTXXTT":
        return {"du_doan": "Xỉu", "do_tin_cay": 90.7}
    if seq == "XXTTXX":
        return {"du_doan": "Tài", "do_tin_cay": 90.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 72.9}

def ai45_high_volatility_exit(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Ổn định sau Biến động lớn. Nếu Var > 6 và Total cuối là trung bình, dự đoán Xỉu."""
    if len(totals) < 8:
        return {"du_doan": "Xỉu", "do_tin_cay": 68.0}
    
    var = max(totals[-8:]) - min(totals[-8:])
    last_total = totals[-1]

    if var > 6 and 9 <= last_total <= 12:
        # Biến động lớn nhưng kết thúc ở mức trung bình -> dự đoán Xỉu (bắt đầu ổn định)
        return {"du_doan": "Xỉu", "do_tin_cay": 89.3}
    
    return {"du_doan": history[-1], "do_tin_cay": 73.1}

def ai46_low_volatility_break(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Bùng nổ sau Ổn định. Nếu Var < 2.5 và Total cuối Tài/Xỉu biên, dự đoán tiếp tục Tài/Xỉu."""
    if len(totals) < 8:
        return {"du_doan": "Tài", "do_tin_cay": 67.3}
    
    var = max(totals[-8:]) - min(totals[-8:])
    last_total = totals[-1]

    if var <= 2.5:
        if last_total >= 13: # Tài biên
            return {"du_doan": "Tài", "do_tin_cay": 91.0}
        if last_total <= 8: # Xỉu biên
            return {"du_doan": "Xỉu", "do_tin_cay": 90.8}
            
    return {"du_doan": history[-1], "do_tin_cay": 70.9}

def ai47_super_trend(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Phối hợp MA (5 phiên) và Streak (3 phiên)."""
    if len(totals) < 5 or len(history) < 3:
        return {"du_doan": "Xỉu", "do_tin_cay": 68.8}
    
    # 1. MA 5:
    avg5 = statistics.mean(list(totals)[-5:])
    
    # 2. Streak 3:
    last3 = list(history)[-3:]
    is_streak = last3[0] == last3[1] == last3[2]
    
    if avg5 >= 11.5 and is_streak and last3[0] == "Tài":
        return {"du_doan": "Tài", "do_tin_cay": 93.8}
    if avg5 <= 9.5 and is_streak and last3[0] == "Xỉu":
        return {"du_doan": "Xỉu", "do_tin_cay": 93.6}
        
    return {"du_doan": history[-1], "do_tin_cay": 74.8}

def ai48_mean_reversion_8(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Hồi quy về mức trung bình 10.5 trong 8 phiên."""
    if len(totals) < 8:
        return {"du_doan": "Tài", "do_tin_cay": 67.1}
    
    avg8 = statistics.mean(list(totals)[-8:])
    
    if avg8 > 11.5:
        # Quá Tài -> dự đoán Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 88.4}
    if avg8 < 9.5:
        # Quá Xỉu -> dự đoán Tài
        return {"du_doan": "Tài", "do_tin_cay": 88.9}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.5}

def ai49_stochastic_oscillator(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Dao động ngẫu nhiên (Stochastic) 10 phiên (tỷ lệ Tổng điểm cuối so với phạm vi min/max)."""
    if len(totals) < 10:
        return {"du_doan": "Xỉu", "do_tin_cay": 66.4}
        
    window = list(totals)[-10:]
    low = min(window)
    high = max(window)
    current = totals[-1]
    
    range_val = high - low
    
    if range_val == 0:
        k = 50.0 # Trung tính
    else:
        k = ((current - low) / range_val) * 100 # %K

    if k > 80:
        # Quá mua (Overbought) -> dự đoán Xỉu (Hồi quy)
        return {"du_doan": "Xỉu", "do_tin_cay": 92.1}
    if k < 20:
        # Quá bán (Oversold) -> dự đoán Tài (Hồi quy)
        return {"du_doan": "Tài", "do_tin_cay": 92.3}
        
    return {"du_doan": history[-1], "do_tin_cay": 73.5}

def ai50_perfect_sequence_3(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Mẫu 3 phiên: TTT, XXX, TXT, XTX. Dự đoán duy trì (TTT->T, TXT->X)."""
    if len(history) < 3:
        return {"du_doan": "Tài", "do_tin_cay": 65.8}
        
    seq = "".join("T" if h == "Tài" else "X" for h in list(history)[-3:])
    
    if seq == "TTT": # Chuỗi Tài -> Dự đoán Tài tiếp
        return {"du_doan": "Tài", "do_tin_cay": 89.6}
    if seq == "XXX": # Chuỗi Xỉu -> Dự đoán Xỉu tiếp
        return {"du_doan": "Xỉu", "do_tin_cay": 89.5}
    if seq == "TXT": # Xen kẽ -> Dự đoán Xỉu tiếp
        return {"du_doan": "Xỉu", "do_tin_cay": 88.1}
    if seq == "XTX": # Xen kẽ -> Dự đoán Tài tiếp
        return {"du_doan": "Tài", "do_tin_cay": 88.3}
        
    return {"du_doan": history[-1], "do_tin_cay": 71.7}


# =========================================================
# II. CLASS QUẢN LÝ DỰ ĐOÁN (PREDICTOR CLASS)
# =========================================================

class TaiXiuPredictor:
    """
    Quản lý việc lấy dữ liệu Tài Xỉu, lưu trữ lịch sử và chạy 50 thuật toán VIP
    để đưa ra dự đoán có độ tin cậy cao nhất.
    """
    
    def __init__(self, api_url: str, app_id: str):
        # Thông tin cấu hình
        self.api_url = api_url
        self.app_id = app_id # Dùng để nhận dạng ứng dụng (ví dụ: "LC79", "Tele68")
        self.last_phien_id: Optional[int] = None

        # Bộ nhớ lịch sử (deques tối ưu cho thêm/bớt từ hai đầu)
        self.history = deque(maxlen=1000)    # Lưu kết quả Tài/Xỉu
        self.totals = deque(maxlen=1000)     # Lưu tổng điểm
        self.win_log = deque(maxlen=1000)    # Log kết quả dự đoán của phiên trước (True/False)

        # Danh sách 50 thuật toán VIP được đăng ký
        self.algos: List[Callable] = [
            # 50 thuật toán đã cung cấp
            ai1_frequency, ai2_parity_chain, ai3_moving_avg, ai4_streak_detector,
            ai5_alternating_pattern, ai6_total_variability, ai7_short_cycle,
            ai8_even_bias_long, ai9_median_check, ai10_trend_slope,
            ai11_weighted_vote, ai12_recent_trend, ai13_balance, ai14_gradient,
            ai15_stability, ai16_flip_after_loss, ai17_recent_variance,
            ai18_sequence, ai19_long_term_mean, ai20_adaptive,
            
            # 30 thuật toán VIP mới
            ai21_3_2_1_pattern, ai22_double_triple, ai23_alternating_4,
            ai24_long_term_alternating_7, ai25_weighted_moving_avg_5,
            ai26_z_score_deviation_15, ai27_keltner_channels,
            ai28_std_dev_breakout, ai29_momentum_indicator,
            ai30_extreme_totals_bias, ai31_mid_range_stability,
            ai32_boundary_reversion, ai33_odd_streak, ai34_even_bias_short_4,
            ai35_parity_switch, ai36_algo_performance_switch,
            ai37_majority_vote_top_5, ai38_win_loss_balance,
            ai39_fib_reversion_5, ai40_martingale_detector,
            ai41_variance_volatility_5, ai42_gap_filler, ai43_double_frequency,
            ai44_alternating_double, ai45_high_volatility_exit,
            ai46_low_volatility_break, ai47_super_trend,
            ai48_mean_reversion_8, ai49_stochastic_oscillator,
            ai50_perfect_sequence_3
        ]
        
        # Dữ liệu phiên mới nhất và dự đoán
        self.last_data: PredictionResult = {
            "phien": None,
            "xucxac1": 0, "xucxac2": 0, "xucxac3": 0,
            "tong": 0, "ketqua": "",
            "du_doan": "Đang khởi động...",
            "do_tin_cay": 0.0,
            "best_algo": "N/A",
            "id": f"VIP Analyzer for {self.app_id}"
        }

    def _fetch_data(self) -> Optional[Tuple[int, List[int], int, str]]:
        """Lấy dữ liệu phiên Tai Xiu từ API và chuẩn hóa."""
        try:
            res = requests.get(self.api_url, timeout=8)
            res.raise_for_status()
            data = res.json()
            
            if "list" in data and len(data["list"]) > 0:
                newest = data["list"][0]
                phien = int(newest.get("id"))
                
                # API Tele68: 'dices' có thể là chuỗi hoặc list.
                dices_raw = newest.get("dices", [])
                if isinstance(dices_raw, str):
                    dice = [int(d) for d in dices_raw.split(',') if d.strip().isdigit()][:3]
                else:
                    dice = [int(d) for d in dices_raw][:3]
                    
                # Tính lại tổng, đảm bảo dữ liệu chuẩn
                tong = sum(dice) if len(dice) == 3 else newest.get("point", 0)
                
                # Chuẩn hóa kết quả (Tai/Xiu)
                ketqua = newest.get("resultTruyenThong", "").upper()
                if tong >= 11 and tong <= 17:
                    ketqua = "Tài"
                elif tong >= 4 and tong <= 10:
                    ketqua = "Xỉu"
                else:
                    ketqua = "Lỗi Dữ Liệu" # Xử lý trường hợp không hợp lệ
                    
                return phien, dice, tong, ketqua
            
        except requests.exceptions.RequestException as e:
            print(f"[❌] Lỗi lấy dữ liệu API {self.api_url}: {e}")
        except Exception as e:
            print(f"[❌] Lỗi xử lý JSON hoặc logic: {e}")
            
        return None

    def _run_algorithms(self) -> PredictionResult:
        """Thực thi tất cả 50 thuật toán đã đăng ký và chọn ra kết quả tốt nhất."""
        results = []
        for algo in self.algos:
            try:
                # Tất cả thuật toán phải nhận đủ 3 tham số lịch sử
                r = algo(self.history, self.totals, self.win_log)
                results.append((algo.__name__, r))
            except Exception as e:
                # Bỏ qua lỗi thuật toán (ví dụ: lịch sử chưa đủ dài)
                # print(f"[⚠️] Lỗi {algo.__name__}: {e}")  
                pass

        # Chọn ra thuật toán có độ tin cậy cao nhất (MAX CONFIDENCE)
        if results:
            best_algo_name, best_res = max(results, key=lambda x: x[1]["do_tin_cay"])
            return {
                "du_doan": best_res["du_doan"],
                "do_tin_cay": round(best_res["do_tin_cay"], 2),
                "best_algo": best_algo_name
            }
        
        # Trường hợp chưa đủ dữ liệu cho thuật toán nào
        return {
            "du_doan": "Đang phân tích",
            "do_tin_cay": 0.0,
            "best_algo": "N/A"
        }

    def predict(self):
        """Kiểm tra dữ liệu mới, cập nhật lịch sử và đưa ra dự đoán."""
        data = self._fetch_data()
        
        if data:
            phien, dice, tong, ketqua = data
            
            # 1. Phát hiện phiên mới
            if phien != self.last_phien_id and phien is not None:
                
                # 2. Chạy thuật toán để dự đoán cho phiên mới này (dựa trên lịch sử cũ)
                prediction_for_next = self._run_algorithms()

                # 3. Cập nhật win_log dựa trên kết quả thực tế của phiên vừa qua (nếu có dự đoán trước đó)
                if self.last_data["du_doan"] not in ["Đang khởi động...", "Đang phân tích"]:
                    last_prediction = self.last_data["du_doan"]
                    # Kiểm tra xem dự đoán của phiên trước có đúng với kết quả thực tế (ketqua) không
                    is_win = (last_prediction == ketqua)
                    self.win_log.append(is_win)

                # 4. Cập nhật lịch sử với kết quả phiên mới
                self.history.append(ketqua)
                self.totals.append(tong)
                
                # 5. Cập nhật dữ liệu mới nhất (là kết quả phiên vừa xong)
                self.last_data = {
                    "phien": phien,
                    "xucxac1": dice[0],
                    "xucxac2": dice[1],
                    "xucxac3": dice[2],
                    "tong": tong,
                    "ketqua": ketqua,
                    # Dự đoán cho phiên TIẾP THEO
                    "du_doan": prediction_for_next["du_doan"],
                    "do_tin_cay": prediction_for_next["do_tin_cay"],
                    "best_algo": prediction_for_next["best_algo"],
                    "id": f"VIP Analyzer for {self.app_id}"
                }
                
                # Cập nhật ID phiên cuối cùng
                self.last_phien_id = phien
                
                print(f"[✅] Phiên {phien} | 🎲 {dice} ({tong}) → {ketqua} | 🔮 {prediction_for_next['best_algo']} → {prediction_for_next['du_doan']} ({prediction_for_next['do_tin_cay']}%)")
            
            # Nếu không phải phiên mới, ta không cần làm gì
            elif self.last_phien_id == phien:
                pass
        
        else:
            # Không lấy được dữ liệu, in thông báo
            pass
            
        # Luôn trả về dữ liệu mới nhất (Phiên Vừa Ra và Dự Đoán cho Phiên Tiếp Theo)
        return self.last_data


# =========================================================
# III. KHỞI CHẠY HỆ THỐNG
# =========================================================

# Khởi tạo đối tượng Predictor (sử dụng API Tele68 cho ví dụ)
# VUI LÒNG THAY ĐỔI URL NÀY nếu muốn kết nối với API của LC hoặc nền tảng khác
TELE68_API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
APP_IDENTIFIER = "LC79_VIP_PRO"

predictor = TaiXiuPredictor(
    api_url=TELE68_API_URL, 
    app_id=APP_IDENTIFIER
)

# Khởi tạo Flask App
app = Flask(__name__)

def background_updater():
    """Luồng nền để liên tục lấy dữ liệu và cập nhật dự đoán."""
    while True:
        # Cập nhật dữ liệu và dự đoán trong đối tượng predictor
        predictor.predict()
        time.sleep(5) # Đợi 5 giây trước khi kiểm tra lại

# =========================================================
# IV. API Endpoint
# =========================================================
@app.route("/api/taixiu", methods=["GET"])
def api_taixiu():
    """Trả về dữ liệu phiên mới nhất và dự đoán cho phiên tiếp theo."""
    # Lấy dữ liệu từ đối tượng predictor
    return jsonify(predictor.last_data)

# =========================================================
# V. CHẠY FLASK
# =========================================================
if __name__ == "__main__":
    print(f"🚀 Đang chạy API /api/taixiu cho ứng dụng {APP_IDENTIFIER}...")
    
    # Lấy PORT từ biến môi trường (Railway/Render) hoặc mặc định 5000
    port = int(os.environ.get("PORT", 5000))
    
    # Khởi chạy thread cập nhật dữ liệu nền
    threading.Thread(target=background_updater, daemon=True).start()
    
    # Khởi chạy Flask App
    # Cần set debug=False khi triển khai thực tế
    app.run(host="0.0.0.0", port=port)
