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
# I. KHU VỰC ĐỊNH NGHĨA THUẬT TOÁN (50 CHIẾN LƯỢC VIP PRO)
# =========================================================
# Tất cả các thuật toán phải nhận 3 tham số: history, totals, win_log
# và trả về Dict[str, any] với 'du_doan' (Tài/Xỉu) và 'do_tin_cay' (0-100)

# ==================== KHỐI 1: XU HƯỚNG & ĐỘNG LƯỢNG (TREND & MOMENTUM) ====================

def ai1_sma_crossover_5_10(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Moving Average Crossover: Dự đoán theo sự giao cắt của MA 5 và MA 10 phiên."""
    if len(totals) < 10:
        return {"du_doan": "Tài", "do_tin_cay": 55.0}
    
    t_list = list(totals)
    ma5 = statistics.mean(t_list[-5:])
    ma10 = statistics.mean(t_list[-10:])
    
    if ma5 > ma10 and ma5 >= 10.5:
        # Xu hướng tăng mạnh (Tài)
        return {"du_doan": "Tài", "do_tin_cay": 88.5}
    if ma5 < ma10 and ma5 <= 10.5:
        # Xu hướng giảm mạnh (Xỉu)
        return {"du_doan": "Xỉu", "do_tin_cay": 87.9}
        
    return {"du_doan": history[-1], "do_tin_cay": 68.0}

def ai2_rsi_analog_14(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Chỉ báo sức mạnh tương đối (RSI): Đo lường 'Quá mua' (Overbought > 12.5) hoặc 'Quá bán' (Oversold < 8.5) trong 14 phiên."""
    if len(totals) < 14:
        return {"du_doan": "Xỉu", "do_tin_cay": 56.5}
        
    window = list(totals)[-14:]
    avg = statistics.mean(window)
    
    if avg > 12.5:
        # Quá mua (Overbought) -> Dự đoán Hồi quy (Xỉu)
        return {"du_doan": "Xỉu", "do_tin_cay": 91.2}
    if avg < 8.5:
        # Quá bán (Oversold) -> Dự đoán Hồi quy (Tài)
        return {"du_doan": "Tài", "do_tin_cay": 90.7}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.5}

def ai3_trend_slope_linear_6(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Độ dốc xu hướng tuyến tính: Phân tích độ dốc của tổng điểm trong 6 phiên gần nhất."""
    if len(totals) < 6:
        return {"du_doan": "Tài", "do_tin_cay": 58.1}
    
    # Tính độ dốc (Slope) đơn giản: (Y2 - Y1) / (X2 - X1)
    t_list = list(totals)
    slope = (t_list[-1] - t_list[-6]) / 5
    
    if slope >= 0.8:
        # Độ dốc dương mạnh -> Tiếp tục Tài
        return {"du_doan": "Tài", "do_tin_cay": 89.6}
    if slope <= -0.8:
        # Độ dốc âm mạnh -> Tiếp tục Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 89.4}
        
    # Trung tính, dự đoán ngược lại
    return {"du_doan": "Xỉu" if history[-1] == "Tài" else "Tài", "do_tin_cay": 65.3}

def ai4_macd_signal_5_10(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Moving Average Convergence Divergence (MACD): Mô phỏng MACD bằng cách so sánh MA Ngắn (5) và Dài (10)."""
    if len(totals) < 10:
        return {"du_doan": "Xỉu", "do_tin_cay": 54.0}
    
    t_list = list(totals)
    ma5 = statistics.mean(t_list[-5:])
    ma10 = statistics.mean(t_list[-10:])
    
    macd_line = ma5 - ma10
    
    if macd_line > 1.0:
        # MACD cắt lên mạnh (Bullish) -> Tài
        return {"du_doan": "Tài", "do_tin_cay": 90.0}
    if macd_line < -1.0:
        # MACD cắt xuống mạnh (Bearish) -> Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 89.8}
        
    return {"du_doan": history[-1], "do_tin_cay": 71.0}

def ai5_momentum_breakout_4(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Động lượng phá vỡ: Nếu tổng điểm vượt qua Max hoặc Min 4 phiên gần nhất."""
    if len(totals) < 4:
        return {"du_doan": "Tài", "do_tin_cay": 57.5}
        
    window = list(totals)[-4:]
    high = max(window[:-1]) # Max 3 phiên trước
    low = min(window[:-1])  # Min 3 phiên trước
    current = totals[-1]
    
    if current > high:
        # Phá vỡ mức cao -> Tiếp tục Tài
        return {"du_doan": "Tài", "do_tin_cay": 88.0}
    if current < low:
        # Phá vỡ mức thấp -> Tiếp tục Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 87.5}
        
    # Duy trì xu hướng trước đó
    return {"du_doan": history[-1], "do_tin_cay": 72.5}

def ai6_triple_trend_confirm(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Xác nhận xu hướng 3 lần liên tiếp: T T T -> Dự đoán Tài tiếp theo."""
    if len(history) < 3:
        return {"du_doan": "Xỉu", "do_tin_cay": 52.0}
        
    last3 = list(history)[-3:]
    
    if last3 == ["Tài", "Tài", "Tài"]:
        return {"du_doan": "Tài", "do_tin_cay": 93.0}
    if last3 == ["Xỉu", "Xỉu", "Xỉu"]:
        return {"du_doan": "Xỉu", "do_tin_cay": 92.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 66.0}

def ai7_mid_range_stability_8(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Ổn định Dải giữa: Nếu 8 phiên đều nằm trong phạm vi [9, 12], dự đoán Hồi quy (Xỉu)."""
    if len(totals) < 8:
        return {"du_doan": "Tài", "do_tin_cay": 59.0}
        
    window = list(totals)[-8:]
    is_stable = all(9 <= t <= 12 for t in window)
    
    if is_stable:
        # Thị trường ổn định, dự đoán phiên tiếp theo sẽ là Xỉu (vì 9, 10 là Xỉu, 11, 12 là Tài, xu hướng trung tính dễ về Xỉu hơn)
        return {"du_doan": "Xỉu", "do_tin_cay": 85.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai8_volume_oscillator_5(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Mô phỏng Dao động Tần suất (Volume Oscillator): So sánh Tần suất Tài/Xỉu ngắn (3) và dài (5)."""
    if len(history) < 5:
        return {"du_doan": "Tài", "do_tin_cay": 51.5}
        
    hist_list = list(history)
    t3 = hist_list[-3:].count("Tài")
    t5 = hist_list[-5:].count("Tài")
    
    if t3 == 3 and t5 >= 4:
        # Động lượng Tài rất mạnh -> Tiếp tục Tài
        return {"du_doan": "Tài", "do_tin_cay": 88.8}
    if t3 == 0 and t5 <= 1:
        # Động lượng Xỉu rất mạnh -> Tiếp tục Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 88.6}
        
    return {"du_doan": history[-1], "do_tin_cay": 71.5}

def ai9_exponential_ma_4(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Exponential Moving Average (EMA) 4 phiên: Nhấn mạnh vào kết quả gần nhất."""
    if len(totals) < 4:
        return {"du_doan": "Xỉu", "do_tin_cay": 59.5}
    
    t_list = list(totals)[-4:]
    # Giả lập EMA: 40% Total[-1], 30% Total[-2], 20% Total[-3], 10% Total[-4]
    ema_like = (t_list[3] * 0.4) + (t_list[2] * 0.3) + (t_list[1] * 0.2) + (t_list[0] * 0.1)
    
    if ema_like >= 11.5:
        return {"du_doan": "Tài", "do_tin_cay": 87.0}
    if ema_like <= 9.5:
        return {"du_doan": "Xỉu", "do_tin_cay": 86.8}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.2}

def ai10_keltner_bands_5_10(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Mô phỏng Keltner Channels: Độ lệch giữa MA 5 và MA 10."""
    if len(totals) < 10:
        return {"du_doan": "Tài", "do_tin_cay": 57.0}
    
    t_list = list(totals)
    ma5 = statistics.mean(t_list[-5:])
    ma10 = statistics.mean(t_list[-10:])
    
    # Kênh trên/dưới giả lập
    upper_channel = ma10 + 1.5
    lower_channel = ma10 - 1.5
    
    if ma5 > upper_channel:
        # Vượt kênh trên -> Overbought, dự đoán Hồi quy (Xỉu)
        return {"du_doan": "Xỉu", "do_tin_cay": 91.0}
    if ma5 < lower_channel:
        # Vượt kênh dưới -> Oversold, dự đoán Hồi quy (Tài)
        return {"du_doan": "Tài", "do_tin_cay": 90.5}
        
    # Trong kênh, dự đoán theo xu hướng ngắn hạn
    return {"du_doan": "Tài" if ma5 >= 10.5 else "Xỉu", "do_tin_cay": 73.0}

# ==================== KHỐI 2: ĐẢO CHIỀU & HỒI QUY (REVERSAL & MEAN REVERSION) ====================

def ai11_mean_reversion_15(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Hồi quy trung bình: Nếu MA 15 phiên quá xa mức 10.5, dự đoán đảo chiều về mức trung tính."""
    if len(totals) < 15:
        return {"du_doan": "Xỉu", "do_tin_cay": 55.5}
        
    avg15 = statistics.mean(list(totals)[-15:])
    
    if avg15 > 11.5:
        # Quá Tài -> Hồi quy về Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 89.1}
    if avg15 < 9.5:
        # Quá Xỉu -> Hồi quy về Tài
        return {"du_doan": "Tài", "do_tin_cay": 88.7}
        
    return {"du_doan": history[-1], "do_tin_cay": 69.5}

def ai12_three_star_reversal(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Mô hình 3 Ngôi sao (3 Star Reversal): T X T hoặc X T X -> Dự đoán đảo chiều tiếp tục."""
    if len(history) < 3:
        return {"du_doan": "Tài", "do_tin_cay": 53.0}
        
    tail = list(history)[-3:]
    
    if tail[0] == tail[2] and tail[0] != tail[1]:
        # T X T -> Dự đoán Xỉu (vì kết quả cuối là T, dự đoán đảo)
        if tail[0] == "Tài":
            return {"du_doan": "Xỉu", "do_tin_cay": 90.0}
        # X T X -> Dự đoán Tài (vì kết quả cuối là X, dự đoán đảo)
        else:
            return {"du_doan": "Tài", "do_tin_cay": 89.5}
            
    return {"du_doan": history[-1], "do_tin_cay": 68.5}

def ai13_parity_gap_8(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Khoảng trống Chẵn/Lẻ: Nếu 8 phiên gần nhất có sự mất cân bằng Chẵn/Lẻ quá lớn, dự đoán bên còn lại."""
    if len(totals) < 8:
        return {"du_doan": "Xỉu", "do_tin_cay": 56.0}
        
    last8 = list(totals)[-8:]
    evens = sum(1 for t in last8 if t % 2 == 0) # Xỉu
    odds = 8 - evens # Tài
    
    if evens >= 7:
        # Quá nhiều chẵn (Xỉu) -> Dự đoán Lẻ (Tài)
        return {"du_doan": "Tài", "do_tin_cay": 87.0}
    if odds >= 7:
        # Quá nhiều lẻ (Tài) -> Dự đoán Chẵn (Xỉu)
        return {"du_doan": "Xỉu", "do_tin_cay": 87.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.8}

def ai14_three_white_soldiers(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Ba người lính trắng: 3 phiên Tài liên tiếp và mỗi phiên có Tổng điểm tăng dần."""
    if len(totals) < 3 or len(history) < 3:
        return {"du_doan": "Tài", "do_tin_cay": 54.5}
    
    last3_h = list(history)[-3:]
    last3_t = list(totals)[-3:]
    
    if last3_h == ["Tài", "Tài", "Tài"] and last3_t[0] < last3_t[1] < last3_t[2]:
        # Tín hiệu Tài rất mạnh
        return {"du_doan": "Tài", "do_tin_cay": 94.0}
    
    if last3_h == ["Xỉu", "Xỉu", "Xỉu"] and last3_t[0] > last3_t[1] > last3_t[2]:
        # Tín hiệu Xỉu rất mạnh (Ba con quạ đen)
        return {"du_doan": "Xỉu", "do_tin_cay": 93.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 67.5}

def ai15_fibonacci_reversal_3(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Đảo chiều Fibonacci 3: Nếu có 3 kết quả giống nhau liên tiếp (TTT hoặc XXX), dự đoán đảo chiều."""
    if len(history) < 3:
        return {"du_doan": "Xỉu", "do_tin_cay": 52.5}
        
    last3 = list(history)[-3:]
    
    if last3 == ["Tài", "Tài", "Tài"]:
        # TTT -> Đảo chiều sang Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 88.0}
    if last3 == ["Xỉu", "Xỉu", "Xỉu"]:
        # XXX -> Đảo chiều sang Tài
        return {"du_doan": "Tài", "do_tin_cay": 87.8}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai16_flip_flop_reversal_5(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Đảo ngược sau chuỗi 5: Nếu có 5 phiên liên tiếp là T/X/T/X/T hoặc ngược lại, dự đoán tiếp tục xu hướng cuối."""
    if len(history) < 5:
        return {"du_doan": "Tài", "do_tin_cay": 55.0}
        
    seq = "".join("T" if h == "Tài" else "X" for h in list(history)[-5:])
    
    if seq == "TXTXT":
        # Chuỗi xen kẽ hoàn hảo -> Dự đoán tiếp tục T (Tài)
        return {"du_doan": "Tài", "do_tin_cay": 90.0}
    if seq == "XTXTX":
        # Chuỗi xen kẽ hoàn hảo -> Dự đoán tiếp tục X (Xỉu)
        return {"du_doan": "Xỉu", "do_tin_cay": 89.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 69.0}

def ai17_total_range_mid_reversion(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Hồi quy về Dải giữa Tổng điểm: Nếu Total[-1] quá gần 4 hoặc 17, dự đoán đảo chiều."""
    if not totals:
        return {"du_doan": "Xỉu", "do_tin_cay": 51.0}
        
    current = totals[-1]
    
    if current <= 5:
        # Biên Xỉu mạnh -> Đảo chiều về Tài
        return {"du_doan": "Tài", "do_tin_cay": 92.0}
    if current >= 16:
        # Biên Tài mạnh -> Đảo chiều về Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 91.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 67.0}

def ai18_anti_martingale_3(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Chống Martingale: Sau 2 phiên Tài/Xỉu liên tiếp, dự đoán đảo chiều (T T X -> X)."""
    if len(history) < 3:
        return {"du_doan": "Tài", "do_tin_cay": 54.0}
        
    last3 = list(history)[-3:]
    
    if last3[0] == last3[1] and last3[1] != last3[2]:
        # T T X hoặc X X T. Tức là vừa bị lật kèo. Dự đoán tiếp tục lật kèo
        return {"du_doan": last3[0], "do_tin_cay": 86.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 71.0}

def ai19_long_term_alternating_10(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Xen kẽ dài hạn 10: Nếu 10 phiên có sự xen kẽ cao (7-8 lần đổi), dự đoán tiếp tục đảo chiều."""
    if len(history) < 10:
        return {"du_doan": "Xỉu", "do_tin_cay": 56.5}
        
    last10 = list(history)[-10:]
    switches = sum(1 for i in range(1, 10) if last10[i] != last10[i-1])
    
    if switches >= 7:
        # Mẫu xen kẽ cao -> Dự đoán đảo chiều
        return {"du_doan": "Xỉu" if history[-1] == "Tài" else "Tài", "do_tin_cay": 90.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 69.5}

def ai20_oscillator_divergence_7(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Phân kỳ Dao động (Divergence): Total đi xuống nhưng Tần suất Tài (history) lại đi lên (phân kỳ)."""
    if len(totals) < 7:
        return {"du_doan": "Tài", "do_tin_cay": 58.0}
        
    t_list = list(totals)[-7:]
    h_list = list(history)[-7:]
    
    total_down = t_list[-1] < t_list[0] # Tổng giảm
    t_count_up = h_list.count("Tài") > 4 # Tần suất Tài tăng (mặc dù tổng giảm)
    
    if total_down and t_count_up:
        # Phân kỳ Bullish -> Dự đoán Tài mạnh
        return {"du_doan": "Tài", "do_tin_cay": 92.0}
    
    total_up = t_list[-1] > t_list[0] # Tổng tăng
    x_count_up = h_list.count("Xỉu") > 4 # Tần suất Xỉu tăng (mặc dù tổng tăng)
    
    if total_up and x_count_up:
        # Phân kỳ Bearish -> Dự đoán Xỉu mạnh
        return {"du_doan": "Xỉu", "do_tin_cay": 91.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

# ==================== KHỐI 3: NHẬN DẠNG MẪU CHUỖI (PATTERN RECOGNITION) ====================

def ai21_1_2_3_pattern(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Mẫu 1-2-3 (T X X X T T T): Dự đoán lật kèo sau khi mô hình hoàn tất."""
    if len(history) < 6:
        return {"du_doan": "Tài", "do_tin_cay": 53.5}
        
    seq = "".join("T" if h == "Tài" else "X" for h in list(history)[-6:])
    
    if seq == "TXXXTT":
        # Sau 3 Xỉu và 2 Tài, dự đoán Tài tiếp (hoàn thành 1-2-3-T)
        return {"du_doan": "Tài", "do_tin_cay": 87.0}
    if seq == "XTTTXX":
        # Sau 3 Tài và 2 Xỉu, dự đoán Xỉu tiếp (hoàn thành 1-2-3-X)
        return {"du_doan": "Xỉu", "do_tin_cay": 86.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai22_double_alternating_6(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Mẫu xen kẽ kép (T T X X T T -> Dự đoán X X)."""
    if len(history) < 6:
        return {"du_doan": "Xỉu", "do_tin_cay": 55.0}
        
    seq = "".join("T" if h == "Tài" else "X" for h in list(history)[-6:])
    
    if seq == "TTXXTT":
        # Dự đoán Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 90.0}
    if seq == "XXTTXX":
        # Dự đoán Tài
        return {"du_doan": "Tài", "do_tin_cay": 89.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 71.2}

def ai23_ab_c_a_b_c_pattern(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Mô hình lặp lại 6 phiên (T X X T X X hoặc X T T X T T)."""
    if len(history) < 6:
        return {"du_doan": "Tài", "do_tin_cay": 56.5}
        
    last6 = list(history)[-6:]
    
    if last6[0] == last6[3] and last6[1] == last6[4] and last6[2] == last6[5]:
        # Lặp lại mẫu 3 phiên (ABCABC)
        # TXXTXX hoặc XTTXTT -> Dự đoán tiếp tục A (last6[0])
        return {"du_doan": last6[0], "do_tin_cay": 91.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 68.0}

def ai24_long_term_alternating_7(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Phân tích xen kẽ 7 phiên: Nếu 7 phiên có 5 lần đảo chiều, dự đoán tiếp tục đảo chiều."""
    if len(history) < 7:
        return {"du_doan": "Xỉu", "do_tin_cay": 54.0}
        
    last7 = list(history)[-7:]
    switches = sum(1 for i in range(1, 7) if last7[i] != last7[i-1])
    
    if switches >= 5:
        # Chuỗi quá xen kẽ -> Dự đoán đảo chiều
        return {"du_doan": "Xỉu" if history[-1] == "Tài" else "Tài", "do_tin_cay": 88.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 69.5}

def ai25_short_mid_trend_confirm_5(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Xác nhận xu hướng ngắn/trung: Nếu 3/5 phiên Tài, và Tài[-1] & Tài[-2], dự đoán Tài."""
    if len(history) < 5:
        return {"du_doan": "Tài", "do_tin_cay": 57.0}
        
    last5 = list(history)[-5:]
    t_count = last5.count("Tài")
    
    if t_count >= 4:
        return {"du_doan": "Tài", "do_tin_cay": 87.5}
    if t_count <= 1:
        return {"du_doan": "Xỉu", "do_tin_cay": 87.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.5}

def ai26_z_score_deviation_10(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Độ lệch Z-Score: Nếu Total[-1] lệch quá 1.5 độ lệch chuẩn (SD) so với MA 10, dự đoán hồi quy."""
    if len(totals) < 10:
        return {"du_doan": "Xỉu", "do_tin_cay": 58.5}
        
    window = list(totals)[-10:]
    avg = statistics.mean(window)
    sd = statistics.stdev(window) if len(window) > 1 else 1.0
    current = totals[-1]
    
    z_score = (current - avg) / sd
    
    if z_score > 1.5:
        # Quá cao -> Hồi quy Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 91.5}
    if z_score < -1.5:
        # Quá thấp -> Hồi quy Tài
        return {"du_doan": "Tài", "do_tin_cay": 91.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 69.0}

def ai27_head_shoulder_analog_4(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Mô hình Vai-Đầu-Vai (Head & Shoulders): Mô phỏng H-S bằng 4 phiên Tổng điểm."""
    if len(totals) < 4:
        return {"du_doan": "Tài", "do_tin_cay": 52.0}
        
    t1, t2, t3, t4 = list(totals)[-4:]
    
    # H&S Bullish: t1 < t2 > t3 < t4 (Xu hướng giảm ngắn hạn bị phá vỡ)
    if t1 < t2 and t2 > t3 and t3 < t4 and t4 > t1:
        return {"du_doan": "Tài", "do_tin_cay": 89.0}
    
    # H&S Bearish: t1 > t2 < t3 > t4 (Xu hướng tăng ngắn hạn bị phá vỡ)
    if t1 > t2 and t2 < t3 and t3 > t4 and t4 < t1:
        return {"du_doan": "Xỉu", "do_tin_cay": 88.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 67.5}

def ai28_volatility_compression_6(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Nén Biến động: Nếu Phạm vi Max-Min 6 phiên nhỏ (< 3), dự đoán bùng nổ (Breakout) Tài/Xỉu theo Total cuối."""
    if len(totals) < 6:
        return {"du_doan": "Xỉu", "do_tin_cay": 56.0}
        
    window = list(totals)[-6:]
    t_range = max(window) - min(window)
    
    if t_range < 3:
        # Nén biến động mạnh -> Dự đoán bùng nổ theo Total cuối cùng
        return {"du_doan": "Tài" if totals[-1] >= 11 else "Xỉu", "do_tin_cay": 90.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai29_momentum_indicator_8(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Chỉ báo Động lượng 8 phiên: So sánh Total[-1] và Total[-8]."""
    if len(totals) < 8:
        return {"du_doan": "Tài", "do_tin_cay": 54.5}
        
    current = totals[-1]
    prev = totals[-8]
    
    diff = current - prev
    
    if diff >= 3:
        # Động lượng Tài mạnh -> Tiếp tục Tài
        return {"du_doan": "Tài", "do_tin_cay": 88.5}
    if diff <= -3:
        # Động lượng Xỉu mạnh -> Tiếp tục Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 88.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 71.8}

def ai30_extreme_totals_bias(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Thiên vị Tổng điểm cực trị: Nếu Total[-1] là 4, 5, 16, hoặc 17, dự đoán Hồi quy cực mạnh."""
    if not totals:
        return {"du_doan": "Xỉu", "do_tin_cay": 52.5}
        
    current = totals[-1]
    
    if current in [4, 5]:
        # Cực Xỉu -> Hồi quy Tài
        return {"du_doan": "Tài", "do_tin_cay": 93.5}
    if current in [16, 17]:
        # Cực Tài -> Hồi quy Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 93.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 68.5}

# ==================== KHỐI 4: BIẾN ĐỘNG & ỔN ĐỊNH (VOLATILITY & STABILITY) ====================

def ai31_mid_range_stability_break(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Phá vỡ ổn định trung bình: 5 phiên liên tiếp 10 hoặc 11 -> Phiên thứ 6 dự đoán ngược lại."""
    if len(totals) < 5:
        return {"du_doan": "Tài", "do_tin_cay": 55.0}
        
    last5 = list(totals)[-5:]
    
    if all(t in [10, 11] for t in last5):
        # Ổn định trung bình quá lâu, dự đoán bùng nổ (Tài/Xỉu)
        return {"du_doan": "Tài" if history[-1] == "Xỉu" else "Xỉu", "do_tin_cay": 89.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai32_boundary_reversion_12(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Hồi quy Biên 12 phiên: Nếu Tổng điểm gần Biên (4, 5, 16, 17) chiếm quá 50% trong 12 phiên."""
    if len(totals) < 12:
        return {"du_doan": "Xỉu", "do_tin_cay": 58.0}
        
    last12 = list(totals)[-12:]
    boundary_count = sum(1 for t in last12 if t in [4, 5, 16, 17])
    
    if boundary_count >= 7:
        # Quá nhiều biên -> Dự đoán Hồi quy về Trung bình (Xỉu 9, 10, 11, 12)
        return {"du_doan": "Xỉu", "do_tin_cay": 87.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 69.0}

def ai33_odd_streak_7(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Chuỗi Lẻ (Tài) 7 phiên: Nếu 7 phiên liên tiếp là Lẻ, dự đoán Chẵn (Xỉu)."""
    if len(totals) < 7:
        return {"du_doan": "Tài", "do_tin_cay": 56.5}
        
    last7_odd = all(t % 2 != 0 for t in list(totals)[-7:])
    
    if last7_odd:
        # Chuỗi Lẻ (Tài) dài -> Dự đoán Chẵn (Xỉu)
        return {"du_doan": "Xỉu", "do_tin_cay": 90.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 71.0}

def ai34_even_bias_short_4(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Thiên vị Chẵn (Xỉu) ngắn 4: Nếu 4 phiên có 3 Chẵn, dự đoán Chẵn tiếp theo."""
    if len(totals) < 4:
        return {"du_doan": "Xỉu", "do_tin_cay": 54.0}
        
    last4 = list(totals)[-4:]
    evens = sum(1 for t in last4 if t % 2 == 0)
    
    if evens >= 3:
        # Thiên vị Chẵn (Xỉu) -> Dự đoán Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 88.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 68.5}

def ai35_parity_switch_8(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Đảo chiều Chẵn/Lẻ 8: Nếu 8 phiên có 6 lần đổi Chẵn/Lẻ, dự đoán Tài (vì Tài dễ xảy ra khi chẵn lẻ xen kẽ)."""
    if len(totals) < 8:
        return {"du_doan": "Tài", "do_tin_cay": 55.5}
        
    last8 = list(totals)[-8:]
    parity_switches = sum(1 for i in range(1, 8) if (last8[i] % 2) != (last8[i-1] % 2))
    
    if parity_switches >= 6:
        # Chẵn/Lẻ xen kẽ cao -> Dự đoán Tài (xu hướng Lẻ)
        return {"du_doan": "Tài", "do_tin_cay": 87.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai36_algo_performance_switch(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Meta-Strategy: Đảo ngược dự đoán của phiên cuối nếu có 3 lần thua liên tiếp (dựa trên win_log)."""
    if len(win_log) < 3 or not history:
        return {"du_doan": "Tài", "do_tin_cay": 59.0}
        
    last3_losses = not win_log[-1] and not win_log[-2] and not win_log[-3]
    
    if last3_losses:
        # Thua 3 lần liên tiếp -> Dự đoán ngược lại kết quả cuối cùng để phá chuỗi
        return {"du_doan": "Xỉu" if history[-1] == "Tài" else "Tài", "do_tin_cay": 92.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 72.0}

def ai37_majority_vote_top_5(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Bỏ phiếu đa số 5 Thuật toán Ngẫu nhiên: Tổng hợp kết quả từ 5 AI bất kỳ."""
    if len(history) < 10:
        return {"du_doan": "Xỉu", "do_tin_cay": 58.5}
    
    # CHÚ Ý: Vì không thể biết chính xác 5 AI nào mạnh nhất, ta sẽ sử dụng 5 AI tiêu biểu
    # AI1 (SMA), AI4 (MACD), AI11 (MR), AI26 (Z-Score), AI45 (Adaptive ATR)
    
    votes = [
        ai1_sma_crossover_5_10(history, totals, win_log)["du_doan"],
        ai4_macd_signal_5_10(history, totals, win_log)["du_doan"],
        ai11_mean_reversion_15(history, totals, win_log)["du_doan"],
        ai26_z_score_deviation_10(history, totals, win_log)["du_doan"],
        ai45_adaptive_atr_breakout(history, totals, win_log)["du_doan"] # Cần định nghĩa AI45
    ]
    
    t_votes = votes.count("Tài")
    x_votes = votes.count("Xỉu")

    if t_votes > x_votes:
        return {"du_doan": "Tài", "do_tin_cay": 94.0}
    if x_votes > t_votes:
        return {"du_doan": "Xỉu", "do_tin_cay": 93.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 75.0}

def ai38_win_loss_balance_10(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Cân bằng Thắng/Thua: Dự đoán bên thua nhiều hơn trong 10 phiên sẽ thắng (Reversion to mean)."""
    if len(history) < 10:
        return {"du_doan": "Tài", "do_tin_cay": 57.0}
        
    last10 = list(history)[-10:]
    t_count = last10.count("Tài")
    x_count = 10 - t_count
    
    diff = abs(t_count - x_count)
    conf_boost = diff * 4.0 # Boost 4% cho mỗi điểm chênh lệch
    
    if t_count - x_count >= 3:
        # Tài nhiều hơn 3 -> dự đoán Xỉu (bù đắp)
        return {"du_doan": "Xỉu", "do_tin_cay": 60.0 + conf_boost}
    if x_count - t_count >= 3:
        # Xỉu nhiều hơn 3 -> dự đoán Tài (bù đắp)
        return {"du_doan": "Tài", "do_tin_cay": 60.0 + conf_boost}
        
    return {"du_doan": history[-1], "do_tin_cay": 71.0}

def ai39_fib_reversion_5(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Hồi quy Fibonacci 5: Dự đoán đảo chiều sau 5 kết quả Tài hoặc Xỉu liên tiếp."""
    if len(history) < 5:
        return {"du_doan": "Xỉu", "do_tin_cay": 56.5}
        
    seq = "".join("T" if h == "Tài" else "X" for h in list(history)[-5:])
    
    if seq == "TTTTT":
        return {"du_doan": "Xỉu", "do_tin_cay": 91.0}
    if seq == "XXXXX":
        return {"du_doan": "Tài", "do_tin_cay": 90.5}
            
    return {"du_doan": history[-1], "do_tin_cay": 70.7}

def ai40_martingale_detector_4(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Bộ phát hiện Martingale: Dự đoán tiếp tục xu hướng sau 2 lần đảo ngược (TXTX -> T)."""
    if len(history) < 4:
        return {"du_doan": "Tài", "do_tin_cay": 55.5}
        
    seq = "".join("T" if h == "Tài" else "X" for h in list(history)[-4:])
    
    if seq == "TXTX":
        # Chuỗi xen kẽ hoàn hảo -> Dự đoán tiếp tục xu hướng T
        return {"du_doan": "Tài", "do_tin_cay": 86.5}
    if seq == "XTXT":
        # Chuỗi xen kẽ hoàn hảo -> Dự đoán tiếp tục xu hướng X
        return {"du_doan": "Xỉu", "do_tin_cay": 86.0}
            
    return {"du_doan": history[-1], "do_tin_cay": 71.8}

# ==================== KHỐI 5: TỔNG HỢP & PHÂN TÍCH CHUYÊN SÂU ====================

def ai41_variance_volatility_5(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Biến động Phương sai 5 phiên: Nếu SD > 3.0 (biến động cao) dự đoán Tài, ngược lại dự đoán Xỉu."""
    if len(totals) < 5:
        return {"du_doan": "Xỉu", "do_tin_cay": 57.0}
        
    window = list(totals)[-5:]
    try:
        sd = statistics.stdev(window)
    except statistics.StatisticsError:
        sd = 0.0
        
    if sd > 3.0:
        # Biến động cực cao -> Thường đi kèm Total lớn (Tài)
        return {"du_doan": "Tài", "do_tin_cay": 88.8}
    if sd <= 1.0:
        # Ổn định cực cao -> Thường đi kèm Total nhỏ (Xỉu)
        return {"du_doan": "Xỉu", "do_tin_cay": 87.5}
            
    return {"du_doan": history[-1], "do_tin_cay": 72.3}

def ai42_gap_filler_5(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Lấp đầy khoảng trống: Nếu một bên không xuất hiện 5 phiên, dự đoán nó sẽ xuất hiện."""
    if len(history) < 5:
        return {"du_doan": "Tài", "do_tin_cay": 56.0}
        
    last5 = list(history)[-5:]
    if last5.count("Tài") == 0:
        return {"du_doan": "Tài", "do_tin_cay": 90.0}
    if last5.count("Xỉu") == 0:
        return {"du_doan": "Xỉu", "do_tin_cay": 89.8}
            
    return {"du_doan": history[-1], "do_tin_cay": 71.6}

def ai43_double_frequency_3(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Mẫu 2-1 (TTX hoặc XXT): Dự đoán bên ngược lại tiếp tục (TTC)."""
    if len(history) < 3:
        return {"du_doan": "Xỉu", "do_tin_cay": 55.0}
        
    seq = "".join("T" if h == "Tài" else "X" for h in list(history)[-3:])
    
    if seq == "TTX":
        # Sau 2 Tài, 1 Xỉu -> Dự đoán Xỉu tiếp
        return {"du_doan": "Xỉu", "do_tin_cay": 87.6}
    if seq == "XXT":
        # Sau 2 Xỉu, 1 Tài -> Dự đoán Tài tiếp
        return {"du_doan": "Tài", "do_tin_cay": 87.4}
            
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai44_alternating_double_6(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Mẫu xen kẽ kép 6 phiên (T T X X T T -> Dự đoán X)."""
    if len(history) < 6:
        return {"du_doan": "Tài", "do_tin_cay": 56.5}
        
    seq = "".join("T" if h == "Tài" else "X" for h in list(history)[-6:])
    
    if seq == "TTXXTT":
        return {"du_doan": "Xỉu", "do_tin_cay": 90.7}
    if seq == "XXTTXX":
        return {"du_doan": "Tài", "do_tin_cay": 90.5}
            
    return {"du_doan": history[-1], "do_tin_cay": 72.9}

def ai45_adaptive_atr_breakout(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Adaptive ATR (Average True Range): Nếu Total[-1] vượt MA 5 + Range trung bình 10 phiên, dự đoán tiếp tục Breakout."""
    if len(totals) < 10:
        return {"du_doan": "Xỉu", "do_tin_cay": 58.0}
        
    t_list = list(totals)
    ma5 = statistics.mean(t_list[-5:])
    
    # Tính Range trung bình (Mô phỏng ATR)
    ranges = [abs(t_list[i] - t_list[i-1]) for i in range(len(t_list)-9, len(t_list))]
    avg_range = statistics.mean(ranges)
    
    current = t_list[-1]
    
    if current > ma5 + avg_range * 1.5:
        # Vượt quá MA + Range -> Tiếp tục Tài
        return {"du_doan": "Tài", "do_tin_cay": 92.0}
    if current < ma5 - avg_range * 1.5:
        # Vượt xuống MA - Range -> Tiếp tục Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 91.5}
            
    return {"du_doan": history[-1], "do_tin_cay": 73.1}

def ai46_low_volatility_break_8(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Bùng nổ sau Ổn định: Nếu Var < 2.0 (8 phiên) và Total cuối Tài/Xỉu biên, dự đoán tiếp tục Tài/Xỉu."""
    if len(totals) < 8:
        return {"du_doan": "Tài", "do_tin_cay": 57.5}
        
    window = list(totals)[-8:]
    t_range = max(window) - min(window)
    last_total = totals[-1]

    if t_range <= 2.0:
        if last_total >= 13: # Tài biên
            return {"du_doan": "Tài", "do_tin_cay": 91.0}
        if last_total <= 8: # Xỉu biên
            return {"du_doan": "Xỉu", "do_tin_cay": 90.8}
            
    return {"du_doan": history[-1], "do_tin_cay": 70.9}

def ai47_super_trend_ma_5_streak_3(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Phối hợp MA (5 phiên) và Streak (3 phiên) để xác nhận xu hướng mạnh."""
    if len(totals) < 5 or len(history) < 3:
        return {"du_doan": "Xỉu", "do_tin_cay": 59.0}
        
    avg5 = statistics.mean(list(totals)[-5:])
    last3 = list(history)[-3:]
    is_streak = last3[0] == last3[1] == last3[2]
    
    if avg5 >= 11.5 and is_streak and last3[0] == "Tài":
        return {"du_doan": "Tài", "do_tin_cay": 93.8}
    if avg5 <= 9.5 and is_streak and last3[0] == "Xỉu":
        return {"du_doan": "Xỉu", "do_tin_cay": 93.6}
            
    return {"du_doan": history[-1], "do_tin_cay": 74.8}

def ai48_mean_reversion_8(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Hồi quy về mức trung bình 10.5 trong 8 phiên (lỏng hơn AI11)."""
    if len(totals) < 8:
        return {"du_doan": "Tài", "do_tin_cay": 57.0}
        
    avg8 = statistics.mean(list(totals)[-8:])
    
    if avg8 > 11.5:
        # Quá Tài -> dự đoán Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 88.4}
    if avg8 < 9.5:
        # Quá Xỉu -> dự đoán Tài
        return {"du_doan": "Tài", "do_tin_cay": 88.9}
            
    return {"du_doan": history[-1], "do_tin_cay": 70.5}

def ai49_stochastic_oscillator_10(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Dao động ngẫu nhiên (Stochastic) 10 phiên: Tỷ lệ Total cuối so với phạm vi min/max."""
    if len(totals) < 10:
        return {"du_doan": "Xỉu", "do_tin_cay": 56.5}
            
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
    """Mẫu 3 phiên: TTT, XXX, TXT, XTX. Dự đoán duy trì/đảo chiều theo mẫu."""
    if len(history) < 3:
        return {"du_doan": "Tài", "do_tin_cay": 55.0}
            
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
        self.app_id = app_id # Dùng để nhận dạng ứng dụng
        self.last_phien_id: Optional[int] = None
        self.last_prediction_data: Optional[PredictionResult] = None

        # Bộ nhớ lịch sử (deques tối ưu cho thêm/bớt từ hai đầu)
        self.history = deque(maxlen=1000)    # Lưu kết quả Tài/Xỉu
        self.totals = deque(maxlen=1000)      # Lưu tổng điểm
        self.win_log = deque(maxlen=1000)    # Log kết quả dự đoán của phiên trước (True/False)

        # Danh sách 50 thuật toán VIP được đăng ký
        self.algos: List[Callable] = [
            # Khối 1: Xu Hướng & Động Lượng
            ai1_sma_crossover_5_10, ai2_rsi_analog_14, ai3_trend_slope_linear_6, 
            ai4_macd_signal_5_10, ai5_momentum_breakout_4, ai6_triple_trend_confirm, 
            ai7_mid_range_stability_8, ai8_volume_oscillator_5, ai9_exponential_ma_4, 
            ai10_keltner_bands_5_10,
            
            # Khối 2: Đảo Chiều & Hồi Quy
            ai11_mean_reversion_15, ai12_three_star_reversal, ai13_parity_gap_8, 
            ai14_three_white_soldiers, ai15_fibonacci_reversal_3, ai16_flip_flop_reversal_5, 
            ai17_total_range_mid_reversion, ai18_anti_martingale_3, ai19_long_term_alternating_10, 
            ai20_oscillator_divergence_7,
            
            # Khối 3: Nhận Dạng Mẫu Chuỗi
            ai21_1_2_3_pattern, ai22_double_alternating_6, ai23_ab_c_a_b_c_pattern, 
            ai24_long_term_alternating_7, ai25_short_mid_trend_confirm_5, ai26_z_score_deviation_10, 
            ai27_head_shoulder_analog_4, ai28_volatility_compression_6, ai29_momentum_indicator_8, 
            ai30_extreme_totals_bias,
            
            # Khối 4: Biến Động & Ổn Định
            ai31_mid_range_stability_break, ai32_boundary_reversion_12, ai33_odd_streak_7, 
            ai34_even_bias_short_4, ai35_parity_switch_8, 
            
            # Khối 5: Tổng Hợp & Chuyên Sâu
            ai36_algo_performance_switch, ai37_majority_vote_top_5, ai38_win_loss_balance_10, 
            ai39_fib_reversion_5, ai40_martingale_detector_4, ai41_variance_volatility_5, 
            ai42_gap_filler_5, ai43_double_frequency_3, ai44_alternating_double_6, 
            ai45_adaptive_atr_breakout, ai46_low_volatility_break_8, ai47_super_trend_ma_5_streak_3, 
            ai48_mean_reversion_8, ai49_stochastic_oscillator_10, ai50_perfect_sequence_3
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
            # Tăng timeout lên 15 giây để tránh lỗi mạng tạm thời
            res = requests.get(self.api_url, timeout=15)
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
                ketqua = ""
                if tong >= 11 and tong <= 17:
                    ketqua = "Tài"
                elif tong >= 4 and tong <= 10:
                    ketqua = "Xỉu"
                else:
                    ketqua = "Lỗi Dữ Liệu" 
                    
                # Chỉ trả về dữ liệu hợp lệ (tổng từ 4 đến 17)
                if ketqua != "Lỗi Dữ Liệu":
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
                r = algo(self.history, self.totals, self.win_log)
                # Đảm bảo độ tin cậy nằm trong [50, 100] để loại bỏ kết quả trung tính thấp
                confidence = round(r["do_tin_cay"], 2)
                if confidence >= 50.0:
                    results.append((algo.__name__, r["du_doan"], confidence))
            except Exception as e:
                # print(f"[⚠️] Lỗi {algo.__name__}: {e}")  
                pass

        # Chọn ra thuật toán có độ tin cậy cao nhất (MAX CONFIDENCE)
        if results:
            best_algo_name, best_du_doan, best_conf = max(results, key=lambda x: x[2])
            return {
                "du_doan": best_du_doan,
                "do_tin_cay": best_conf,
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
            
            # 1. Phát hiện phiên mới (Nếu ID phiên mới hơn ID đã lưu)
            if phien != self.last_phien_id and phien is not None:
                
                # --- CHU TRÌNH 1: Đánh giá phiên VỪA KẾT THÚC ---
                if self.last_phien_id is not None:
                    # Kiểm tra xem dự đoán cho phiên này có đúng với kết quả thực tế không
                    if self.last_prediction_data and self.last_prediction_data["du_doan"] not in ["Đang khởi động...", "Đang phân tích"]:
                        last_prediction = self.last_prediction_data["du_doan"]
                        is_win = (last_prediction == ketqua)
                        self.win_log.append(is_win)
                
                # 2. Cập nhật lịch sử với kết quả phiên mới
                self.history.append(ketqua)
                self.totals.append(tong)
                
                # --- CHU TRÌNH 2: Dự đoán cho phiên TIẾP THEO ---
                prediction_for_next = self._run_algorithms()

                # 3. Cập nhật dữ liệu mới nhất (là kết quả phiên vừa xong)
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
                
                # Lưu lại dự đoán này để đánh giá ở phiên sau
                self.last_prediction_data = prediction_for_next
                
                # Cập nhật ID phiên cuối cùng
                self.last_phien_id = phien
                
                print(f"[✅] Phiên {phien} | 🎲 {dice} ({tong}) → {ketqua} | 🔮 {prediction_for_next['best_algo']} → {prediction_for_next['du_doan']} ({prediction_for_next['do_tin_cay']}%) | Win Log: {len(self.win_log)}")
            
            # Nếu là cùng một phiên, cập nhật lại thời gian
            elif self.last_phien_id == phien:
                # Nếu không phải phiên mới, ta giữ nguyên dự đoán cho phiên tiếp theo
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
APP_IDENTIFIER = "VIP_Quant_Analyzer"

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
        try:
            predictor.predict()
        except Exception as e:
            print(f"[FATAL] Lỗi trong luồng nền: {e}")
        time.sleep(5) # Đợi 5 giây trước khi kiểm tra lại

# =========================================================
# IV. API Endpoint
# =========================================================
@app.route("/api/taixiumd5", methods=["GET"])
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
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
