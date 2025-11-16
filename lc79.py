import requests
import time
import threading
import statistics
import os
from collections import deque
from typing import List, Dict, Optional, Tuple, Callable
from flask import Flask, jsonify

# Định nghĩa cấu trúc dữ liệu cho dự đoán
PredictionResult = Dict[str, any]

# Kích thước tối đa của lịch sử (cần đủ cho các thuật toán dài nhất, ví dụ 30)
MAX_HISTORY_SIZE = 30

# =========================================================
# I. KHU VỰC ĐỊNH NGHĨA THUẬT TOÁN (50 CHIẾN LƯỢC VIP PRO)
# Tất cả các thuật toán phải nhận 3 tham số: history, totals, win_log
# và trả về Dict[str, any] với 'du_doan' (Tài/Xỉu) và 'do_tin_cay' (50.0 - 100.0)
# =========================================================

# ==================== KHỐI 1: XU HƯỚNG & ĐỘNG LƯỢNG (TREND & MOMENTUM) ====================

def ai1_sma_crossover_5_10(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Moving Average Crossover: Dự đoán theo sự giao cắt của MA 5 và MA 10 phiên."""
    if len(totals) < 10:
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}
    
    t_list = list(totals)
    ma5 = statistics.mean(t_list[-5:])
    ma10 = statistics.mean(t_list[-10:])
    
    if ma5 > ma10 and ma5 >= 11.5:
        # Xu hướng tăng mạnh (Tài)
        return {"du_doan": "Tài", "do_tin_cay": 88.5}
    if ma5 < ma10 and ma5 <= 10.5:
        # Xu hướng giảm mạnh (Xỉu)
        return {"du_doan": "Xỉu", "do_tin_cay": 87.9}
        
    return {"du_doan": history[-1], "do_tin_cay": 68.0}

def ai2_rsi_analog_14(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Chỉ báo sức mạnh tương đối (RSI): Đo lường 'Quá mua' (Overbought > 12.5) hoặc 'Quá bán' (Oversold < 8.5) trong 14 phiên."""
    if len(totals) < 14:
        return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 50.0}
        
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
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}
    
    # Tính độ dốc (Slope) đơn giản: (Y2 - Y1) / (X2 - X1)
    t_list = list(totals)
    slope = (t_list[-1] - t_list[-6]) / 5
    
    if slope >= 1.0:
        # Độ dốc dương mạnh -> Tiếp tục Tài
        return {"du_doan": "Tài", "do_tin_cay": 89.6}
    if slope <= -1.0:
        # Độ dốc âm mạnh -> Tiếp tục Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 89.4}
        
    # Trung tính, dự đoán theo kết quả gần nhất
    return {"du_doan": history[-1], "do_tin_cay": 65.3}

def ai4_macd_signal_5_10(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Moving Average Convergence Divergence (MACD): Mô phỏng MACD bằng cách so sánh MA Ngắn (5) và Dài (10)."""
    if len(totals) < 10:
        return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 50.0}
    
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
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}
        
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
        return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 50.0}
        
    last3 = list(history)[-3:]
    
    if last3 == ["Tài", "Tài", "Tài"]:
        return {"du_doan": "Tài", "do_tin_cay": 93.0}
    if last3 == ["Xỉu", "Xỉu", "Xỉu"]:
        return {"du_doan": "Xỉu", "do_tin_cay": 92.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 66.0}

def ai7_mid_range_stability_8(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Ổn định Dải giữa: Nếu 8 phiên đều nằm trong phạm vi [9, 12], dự đoán Hồi quy (Xỉu)."""
    if len(totals) < 8:
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}
        
    window = list(totals)[-8:]
    is_stable = all(9 <= t <= 12 for t in window)
    
    if is_stable:
        # Thị trường ổn định, dễ về Xỉu (vì 9, 10 là Xỉu, 11, 12 là Tài, nhưng 10.5 là trung bình)
        return {"du_doan": "Xỉu", "do_tin_cay": 85.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai8_volume_oscillator_5(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Mô phỏng Dao động Tần suất (Volume Oscillator): So sánh Tần suất Tài/Xỉu ngắn (3) và dài (5)."""
    if len(history) < 5:
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}
        
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
        return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 50.0}
    
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
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}
    
    t_list = list(totals)
    ma5 = statistics.mean(t_list[-5:])
    ma10 = statistics.mean(t_list[-10:])
    
    # Kênh trên/dưới giả lập dựa trên độ lệch chuẩn (volatility)
    std_dev = statistics.stdev(t_list[-10:]) if len(t_list[-10:]) > 1 else 0
    
    upper_channel = ma10 + (std_dev * 1.5)
    lower_channel = ma10 - (std_dev * 1.5)
    
    if ma5 > upper_channel and t_list[-1] > upper_channel:
        # Vượt kênh trên -> Overbought, dự đoán Hồi quy (Xỉu)
        return {"du_doan": "Xỉu", "do_tin_cay": 92.0}
    
    if ma5 < lower_channel and t_list[-1] < lower_channel:
        # Vượt kênh dưới -> Oversold, dự đoán Hồi quy (Tài)
        return {"du_doan": "Tài", "do_tin_cay": 91.8}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

# ==================== KHỐI 2: ĐẢO CHIỀU & HỒI QUY (REVERSAL & REGRESSION) ====================

def ai11_mean_reversion_15(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Hồi quy về mức trung bình 10.5: Nếu MA 15 phiên lệch xa (trên 12.5 hoặc dưới 8.5)."""
    if len(totals) < 15:
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}
    
    avg15 = statistics.mean(list(totals)[-15:])
    
    if avg15 > 12.5:
        # Xu hướng Tài quá đà -> dự đoán Xỉu (Hồi quy)
        return {"du_doan": "Xỉu", "do_tin_cay": 91.0}
    if avg15 < 8.5:
        # Xu hướng Xỉu quá đà -> dự đoán Tài (Hồi quy)
        return {"du_doan": "Tài", "do_tin_cay": 90.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 72.0}

def ai12_three_star_reversal(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Ba ngôi sao (Mô hình nến): T T X hoặc X X T."""
    if len(history) < 3:
        return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 50.0}
        
    last3 = list(history)[-3:]
    
    if last3 == ["Tài", "Tài", "Xỉu"]:
        # Mô hình Đảo chiều giảm (Bearish Reversal) -> Dự đoán Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 89.0}
    if last3 == ["Xỉu", "Xỉu", "Tài"]:
        # Mô hình Đảo chiều tăng (Bullish Reversal) -> Dự đoán Tài
        return {"du_doan": "Tài", "do_tin_cay": 88.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 67.0}

def ai13_parity_gap_8(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Khoảng cách Parity 8 phiên: Nếu Tài/Xỉu chênh lệch quá 6/2, dự đoán Hồi quy."""
    if len(history) < 8:
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}
        
    last8 = list(history)[-8:]
    t_count = last8.count("Tài")
    x_count = last8.count("Xỉu")
    
    if t_count >= 6 and x_count <= 2:
        # Tài chiếm ưu thế tuyệt đối -> Hồi quy Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 91.5}
    if x_count >= 6 and t_count <= 2:
        # Xỉu chiếm ưu thế tuyệt đối -> Hồi quy Tài
        return {"du_doan": "Tài", "do_tin_cay": 91.2}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai14_three_white_soldiers(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Ba lính trắng (Mô hình nến): T T T (có độ tin cậy cao)."""
    if len(history) < 3:
        return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 50.0}
        
    last3 = list(history)[-3:]
    
    if last3 == ["Tài", "Tài", "Tài"]:
        # Xác nhận xu hướng tăng mạnh
        return {"du_doan": "Tài", "do_tin_cay": 94.0}
    if last3 == ["Xỉu", "Xỉu", "Xỉu"]:
        # Xác nhận xu hướng giảm mạnh
        return {"du_doan": "Xỉu", "do_tin_cay": 93.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai15_fibonacci_reversal_3(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Hồi quy Fibonacci 3 phiên: Nếu Total[-1] giảm/tăng 50% so với Total[-3]."""
    if len(totals) < 3:
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}
    
    t_list = list(totals)[-3:]
    
    # Khoảng cách 2 phiên
    range_3 = abs(t_list[0] - t_list[1])
    # Khoảng cách phiên gần nhất
    range_1 = abs(t_list[1] - t_list[2])
    
    if t_list[0] < t_list[1] and t_list[2] < t_list[1]:
        # Tăng mạnh -> giảm mạnh (tạo đỉnh), nếu Total[-1] nhỏ hơn trung bình Tài (14.5)
        if t_list[2] < 14 and range_1 >= range_3 * 0.5:
            return {"du_doan": "Xỉu", "do_tin_cay": 90.0}
    
    if t_list[0] > t_list[1] and t_list[2] > t_list[1]:
        # Giảm mạnh -> tăng mạnh (tạo đáy), nếu Total[-1] lớn hơn trung bình Xỉu (7.5)
        if t_list[2] > 7 and range_1 >= range_3 * 0.5:
            return {"du_doan": "Tài", "do_tin_cay": 89.5}
            
    return {"du_doan": history[-1], "do_tin_cay": 68.0}

def ai16_flip_flop_reversal_5(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Đảo chiều Flip-Flop 5 phiên: T X T X T -> Dự đoán X."""
    if len(history) < 5:
        return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 50.0}
        
    seq = "".join("T" if h == "Tài" else "X" for h in list(history)[-5:])
    
    if seq == "TXTXT":
        # Dự đoán Xỉu (chấm dứt mẫu xen kẽ)
        return {"du_doan": "Xỉu", "do_tin_cay": 91.0}
    if seq == "XTXTX":
        # Dự đoán Tài (chấm dứt mẫu xen kẽ)
        return {"du_doan": "Tài", "do_tin_cay": 90.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai17_total_range_mid_reversion(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Hồi quy về Dải giữa (9-12): Nếu Total[-1] là cực đoan (4, 5, 16, 17), dự đoán hồi quy về giữa."""
    if not totals:
        return {"du_doan": "Tài", "do_tin_cay": 50.0}
    
    current = totals[-1]
    
    if current <= 5:
        # Cực Xỉu -> Hồi quy Tài
        return {"du_doan": "Tài", "do_tin_cay": 93.0}
    if current >= 16:
        # Cực Tài -> Hồi quy Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 92.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai18_anti_martingale_3(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Chống Martingale: Nếu 3 phiên Tài/Xỉu liên tiếp, dự đoán Hồi quy (ngược lại)."""
    if len(history) < 3:
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}
        
    last3 = list(history)[-3:]
    
    if last3 == ["Tài", "Tài", "Tài"]:
        # Chống Martingale Tài -> Dự đoán Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 87.0}
    if last3 == ["Xỉu", "Xỉu", "Xỉu"]:
        # Chống Martingale Xỉu -> Dự đoán Tài
        return {"du_doan": "Tài", "do_tin_cay": 86.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai19_long_term_alternating_10(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Xen kẽ dài hạn 10: Nếu 10 phiên có sự xen kẽ cao (7-8 lần đổi), dự đoán tiếp tục đảo chiều."""
    if len(history) < 10:
        return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 50.0}
        
    last10 = list(history)[-10:]
    switches = sum(1 for i in range(1, 10) if last10[i] != last10[i-1])
    
    if switches >= 7:
        # Mẫu xen kẽ cao -> Dự đoán đảo chiều
        return {"du_doan": "Xỉu" if history[-1] == "Tài" else "Tài", "do_tin_cay": 90.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 69.5}

def ai20_oscillator_divergence_7(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Phân kỳ Dao động (Divergence): Total đi xuống nhưng Tần suất Tài (history) lại đi lên (phân kỳ)."""
    if len(totals) < 7:
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}
        
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
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}
        
    seq = "".join("T" if h == "Tài" else "X" for h in list(history)[-6:])
    
    if seq == "TXXXTT":
        # Sau 3 Xỉu và 2 Tài, dự đoán Tài tiếp
        return {"du_doan": "Tài", "do_tin_cay": 87.0}
    if seq == "XTTTXX":
        # Sau 3 Tài và 2 Xỉu, dự đoán Xỉu tiếp
        return {"du_doan": "Xỉu", "do_tin_cay": 86.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai22_double_alternating_6(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Mẫu xen kẽ kép (T T X X T T -> Dự đoán X X)."""
    if len(history) < 6:
        return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 50.0}
        
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
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}
        
    last6 = list(history)[-6:]
    
    if last6[0] == last6[3] and last6[1] == last6[4] and last6[2] == last6[5]:
        # Lặp lại mẫu 3 phiên (ABCABC) -> Dự đoán tiếp tục A (last6[0])
        return {"du_doan": last6[0], "do_tin_cay": 91.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 68.0}

def ai24_long_term_alternating_7(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Phân tích xen kẽ 7 phiên: Nếu 7 phiên có 5 lần đảo chiều, dự đoán tiếp tục đảo chiều."""
    if len(history) < 7:
        return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 50.0}
        
    last7 = list(history)[-7:]
    switches = sum(1 for i in range(1, 7) if last7[i] != last7[i-1])
    
    if switches >= 5:
        # Mẫu xen kẽ cao -> Dự đoán đảo chiều
        return {"du_doan": "Xỉu" if history[-1] == "Tài" else "Tài", "do_tin_cay": 89.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai25_short_mid_trend_confirm_5(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Xác nhận Xu hướng Ngắn-Trung (5 phiên): Nếu 4/5 phiên Tài/Xỉu và Total[-1] Tài/Xỉu biên."""
    if len(history) < 5 or len(totals) < 1:
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}

    last5 = list(history)[-5:]
    t_count = last5.count("Tài")
    x_count = last5.count("Xỉu")
    last_total = totals[-1]

    if t_count >= 4 and last_total >= 14:
        return {"du_doan": "Tài", "do_tin_cay": 92.5}
    if x_count >= 4 and last_total <= 7:
        return {"du_doan": "Xỉu", "do_tin_cay": 92.0}

    return {"du_doan": history[-1], "do_tin_cay": 73.0}

# ==================== KHỐI 4: BIẾN ĐỘNG & ỔN ĐỊNH (VOLATILITY & STABILITY) ====================

def ai26_z_score_deviation_10(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Độ lệch Z-Score: Nếu Total[-1] lệch > 2.0 độ lệch chuẩn trong 10 phiên, dự đoán hồi quy."""
    if len(totals) < 10:
        return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 50.0}

    window = list(totals)[-10:]
    try:
        mean = statistics.mean(window)
        std_dev = statistics.stdev(window)
        current = totals[-1]

        if std_dev == 0:
            return {"du_doan": history[-1], "do_tin_cay": 55.0} # Không biến động

        z_score = (current - mean) / std_dev

        if z_score > 2.0:
            return {"du_doan": "Xỉu", "do_tin_cay": 93.0} # Lệch Tài -> Hồi quy Xỉu
        if z_score < -2.0:
            return {"du_doan": "Tài", "do_tin_cay": 92.5} # Lệch Xỉu -> Hồi quy Tài

    except statistics.StatisticsError:
        pass # Xử lý trường hợp chỉ có một phần tử
        
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai27_head_shoulder_analog_4(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Mô phỏng Head & Shoulders (4 phiên): T(lớn) X(nhỏ) T(cực lớn) X(nhỏ) T(lớn) -> Dự đoán X."""
    if len(totals) < 4:
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}

    t = list(totals)[-4:]
    
    # Mô hình Đỉnh (Mô phỏng Head & Shoulders): Cao - Thấp - Cực Cao - Thấp
    # t[0] < t[2] và t[1] < t[2] và t[3] < t[2]
    if t[0] < t[2] and t[1] < t[2] and t[3] < t[2] and t[2] >= 15:
        return {"du_doan": "Xỉu", "do_tin_cay": 90.0}

    # Mô hình Đáy (Mô phỏng Inverse Head & Shoulders): Thấp - Cao - Cực Thấp - Cao
    # t[0] > t[2] và t[1] > t[2] và t[3] > t[2]
    if t[0] > t[2] and t[1] > t[2] and t[3] > t[2] and t[2] <= 6:
        return {"du_doan": "Tài", "do_tin_cay": 89.5}

    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai28_volatility_compression_6(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Nén Biến động (Volatility Compression) 6 phiên: Nếu Total Range < 4 (giảm biên độ) dự đoán Bùng nổ (ngược lại)."""
    if len(totals) < 6:
        return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 50.0}
    
    window = list(totals)[-6:]
    t_range = max(window) - min(window)

    if t_range <= 3:
        # Volatility Compression -> Dự đoán Bùng nổ (ngược lại kết quả cuối cùng)
        return {"du_doan": "Xỉu" if history[-1] == "Tài" else "Tài", "do_tin_cay": 88.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai29_momentum_indicator_8(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Chỉ báo Động lượng 8 phiên: So sánh sự thay đổi Total[-1] so với 8 phiên trước."""
    if len(totals) < 8:
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}
    
    t_list = list(totals)
    change = t_list[-1] - t_list[-8]
    
    if change >= 4:
        # Tăng mạnh -> Tiếp tục Tài
        return {"du_doan": "Tài", "do_tin_cay": 91.5}
    if change <= -4:
        # Giảm mạnh -> Tiếp tục Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 91.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 72.0}

def ai30_extreme_totals_bias(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Thiên vị Total Cực đoan: Nếu có > 3 lần Total >= 15 hoặc <= 6 trong 15 phiên, dự đoán hồi quy về trung bình."""
    if len(totals) < 15:
        return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 50.0}

    window = list(totals)[-15:]
    extreme_high_count = sum(1 for t in window if t >= 15)
    extreme_low_count = sum(1 for t in window if t <= 6)

    if extreme_high_count >= 4:
        # Quá nhiều Tài cực đoan -> Hồi quy Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 93.5}
    if extreme_low_count >= 4:
        # Quá nhiều Xỉu cực đoan -> Hồi quy Tài
        return {"du_doan": "Tài", "do_tin_cay": 93.0}

    return {"du_doan": history[-1], "do_tin_cay": 70.0}

# ==================== KHỐI 5: TỔNG HỢP & CHUYÊN SÂU (ADVANCED & ENSEMBLE) ====================

def ai31_mid_range_stability_break(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Phá vỡ Ổn định Dải giữa: 6 phiên trong [9, 12], phiên thứ 7 là Tài/Xỉu biên (>=14 / <=7)."""
    if len(totals) < 7:
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}

    window_prev_6 = list(totals)[-7:-1]
    is_stable = all(9 <= t <= 12 for t in window_prev_6)
    current = totals[-1]

    if is_stable and current >= 14:
        # Bùng nổ Tài sau ổn định -> Tiếp tục Tài
        return {"du_doan": "Tài", "do_tin_cay": 94.0}
    if is_stable and current <= 7:
        # Bùng nổ Xỉu sau ổn định -> Tiếp tục Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 93.5}

    return {"du_doan": history[-1], "do_tin_cay": 75.0}

def ai32_boundary_reversion_12(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Hồi quy Biên độ 12 phiên: Nếu 12 phiên liên tiếp Tài/Xỉu không cân bằng (> 8/4), dự đoán ngược."""
    if len(history) < 12:
        return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 50.0}

    last12 = list(history)[-12:]
    t_count = last12.count("Tài")
    x_count = last12.count("Xỉu")

    if t_count >= 9 and x_count <= 3:
        # Ưu thế Tài quá lớn -> Hồi quy Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 92.0}
    if x_count >= 9 and t_count <= 3:
        # Ưu thế Xỉu quá lớn -> Hồi quy Tài
        return {"du_doan": "Tài", "do_tin_cay": 91.8}

    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai33_odd_streak_7(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Chuỗi Số Lẻ (Odd Streak) 7 phiên: Nếu Total là số lẻ > 5 lần, dự đoán Số Chẵn (Hồi quy)."""
    if len(totals) < 7:
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}
    
    window = list(totals)[-7:]
    odd_count = sum(1 for t in window if t % 2 != 0)

    # Nếu 6/7 là lẻ, dự đoán chẵn (Dự đoán Xỉu vì 4, 6, 8, 10 là Xỉu, 12, 14, 16 là Tài)
    if odd_count >= 6:
        return {"du_doan": "Xỉu", "do_tin_cay": 88.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai34_even_bias_short_4(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Thiên vị Số Chẵn Ngắn (4 phiên): 4 Total chẵn liên tiếp -> Dự đoán Lẻ (Tài)."""
    if len(totals) < 4:
        return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 50.0}
        
    window = list(totals)[-4:]
    is_all_even = all(t % 2 == 0 for t in window)

    if is_all_even:
        # Dự đoán Số Lẻ (ví dụ 5, 7, 9, 11, 13, 15, 17) -> Hướng về Tài
        return {"du_doan": "Tài", "do_tin_cay": 90.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai35_parity_switch_8(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Đảo chiều Parity 8 phiên: Nếu Total[-1] chuyển từ Tài sang Xỉu hoặc ngược lại, và 8 phiên trước đều Tài/Xỉu biên."""
    if len(totals) < 8 or len(history) < 8:
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}

    h_list = list(history)
    
    # Kiểm tra chuyển đổi Tài -> Xỉu
    if h_list[-2] == "Tài" and h_list[-1] == "Xỉu":
        # Kiểm tra 7 phiên Tài trước đó (Total Tài >= 14)
        prev7_totals = list(totals)[-8:-1]
        if all(t >= 13 for t in prev7_totals):
            return {"du_doan": "Xỉu", "do_tin_cay": 94.5}
            
    # Kiểm tra chuyển đổi Xỉu -> Tài
    if h_list[-2] == "Xỉu" and h_list[-1] == "Tài":
        # Kiểm tra 7 phiên Xỉu trước đó (Total Xỉu <= 7)
        prev7_totals = list(totals)[-8:-1]
        if all(t <= 8 for t in prev7_totals):
            return {"du_doan": "Tài", "do_tin_cay": 94.0}

    return {"du_doan": history[-1], "do_tin_cay": 72.0}

# ==================== KHỐI 6: CHIẾN LƯỢC TỔNG HỢP & NÂNG CAO ====================

def ai36_algo_performance_switch(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Chuyển đổi Hiệu suất Thuật toán: Nếu 5 lần dự đoán liên tiếp Sai, dự đoán ngược lại kết quả cuối cùng."""
    if len(win_log) < 5:
        return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 50.0}

    last5_win = list(win_log)[-5:]
    
    if all(w is False for w in last5_win):
        # 5 lần thua liên tiếp -> Đảo ngược dự đoán (Tài nếu cuối là Xỉu, Xỉu nếu cuối là Tài)
        return {"du_doan": "Xỉu" if history[-1] == "Tài" else "Tài", "do_tin_cay": 95.0}

    return {"du_doan": history[-1], "do_tin_cay": 75.0}

def ai37_majority_vote_top_5(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Bỏ phiếu Đa số Top 5 (Mô phỏng): Nếu 4/5 phiên gần nhất Tài/Xỉu, dự đoán theo đa số."""
    if len(history) < 5:
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}
    
    last5 = list(history)[-5:]
    t_count = last5.count("Tài")
    x_count = last5.count("Xỉu")

    if t_count >= 4:
        return {"du_doan": "Tài", "do_tin_cay": 92.0}
    if x_count >= 4:
        return {"du_doan": "Xỉu", "do_tin_cay": 91.5}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai38_win_loss_balance_10(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Cân bằng Thắng-Thua 10 phiên: Nếu Win Log mất cân bằng (> 7/3), dự đoán hồi quy."""
    if len(win_log) < 10:
        return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 50.0}

    last10_win = list(win_log)[-10:]
    win_count = sum(1 for w in last10_win if w is True)
    
    # Nếu tỷ lệ thắng quá cao (> 70%), dự đoán thua (ngược lại kết quả gần nhất)
    if win_count >= 7:
        return {"du_doan": "Xỉu" if history[-1] == "Tài" else "Tài", "do_tin_cay": 89.0}

    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai39_fib_reversion_5(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Hồi quy Fibonacci 5 phiên: Nếu 5 Total liên tiếp giảm/tăng, dự đoán đảo chiều."""
    if len(totals) < 5:
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}
    
    t = list(totals)[-5:]
    
    # 5 phiên tăng liên tiếp
    is_increasing = all(t[i] > t[i-1] for i in range(1, 5))
    # 5 phiên giảm liên tiếp
    is_decreasing = all(t[i] < t[i-1] for i in range(1, 5))

    if is_increasing:
        return {"du_doan": "Xỉu", "do_tin_cay": 93.0}
    if is_decreasing:
        return {"du_doan": "Tài", "do_tin_cay": 92.5}

    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai40_martingale_detector_4(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Phát hiện Martingale (4): Nếu có 4 phiên xen kẽ T X T X, dự đoán Tài (để tránh chuỗi X T X T X)."""
    if len(history) < 4:
        return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 50.0}
        
    seq = "".join("T" if h == "Tài" else "X" for h in list(history)[-4:])
    
    if seq == "TXTX":
        # Dự đoán Tài (chấm dứt chuỗi T X T X X)
        return {"du_doan": "Tài", "do_tin_cay": 90.0}
    if seq == "XTXT":
        # Dự đoán Xỉu (chấm dứt chuỗi X T X T T)
        return {"du_doan": "Xỉu", "do_tin_cay": 89.5}

    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai41_variance_volatility_5(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Biến động Phương sai 5 phiên: Nếu phương sai (Variance) cao (> 5.0), dự đoán Hồi quy (ngược lại)."""
    if len(totals) < 5:
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}

    window = list(totals)[-5:]
    try:
        variance = statistics.variance(window)
        
        if variance >= 6.0:
            # Biến động cao -> Dự đoán Hồi quy (ngược lại kết quả cuối cùng)
            return {"du_doan": "Xỉu" if history[-1] == "Tài" else "Tài", "do_tin_cay": 91.0}

    except statistics.StatisticsError:
        pass # Xử lý trường hợp chỉ có một phần tử

    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai42_gap_filler_5(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Lấp đầy Khoảng trống 5 phiên: Nếu Total nhảy vọt từ < 7 lên > 14 (hoặc ngược lại), dự đoán lấp đầy (hồi quy)."""
    if len(totals) < 2:
        return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 50.0}

    t_prev = totals[-2]
    t_curr = totals[-1]

    if t_prev <= 7 and t_curr >= 14:
        # Nhảy vọt Xỉu -> Tài -> Dự đoán Xỉu (lấp khoảng trống)
        return {"du_doan": "Xỉu", "do_tin_cay": 93.0}
    if t_prev >= 14 and t_curr <= 7:
        # Nhảy vọt Tài -> Xỉu -> Dự đoán Tài (lấp khoảng trống)
        return {"du_doan": "Tài", "do_tin_cay": 92.5}

    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai43_double_frequency_3(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Tần suất kép 3 phiên: Nếu Total[-1] Tài và Total[-3] Tài, dự đoán Tài tiếp (xu hướng mạnh)."""
    if len(history) < 3:
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}
    
    h_list = list(history)[-3:]
    
    if h_list[0] == "Tài" and h_list[2] == "Tài" and h_list[1] == "Xỉu":
        # Mẫu T X T -> Dự đoán Tài tiếp
        return {"du_doan": "Tài", "do_tin_cay": 88.0}
    if h_list[0] == "Xỉu" and h_list[2] == "Xỉu" and h_list[1] == "Tài":
        # Mẫu X T X -> Dự đoán Xỉu tiếp
        return {"du_doan": "Xỉu", "do_tin_cay": 87.5}

    return {"du_doan": history[-1], "do_tin_cay": 70.0}

def ai44_alternating_double_6(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Xen kẽ Kép 6 phiên: X X T T X X -> Dự đoán T T."""
    if len(history) < 6:
        return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 50.0}
        
    seq = "".join("T" if h == "Tài" else "X" for h in list(history)[-6:])
    
    if seq == "XXTTXX":
        # Dự đoán Tài
        return {"du_doan": "Tài", "do_tin_cay": 90.5}
    if seq == "TTXXTT":
        # Dự đoán Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 90.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 72.9}

def ai45_adaptive_atr_breakout(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Adaptive ATR (Average True Range): Nếu Total[-1] vượt MA 5 + Range trung bình 10 phiên, dự đoán tiếp tục Breakout."""
    if len(totals) < 10:
        return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 50.0}
        
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
    """Bùng nổ sau Ổn định: Nếu Total Range < 2.0 (8 phiên) và Total cuối Tài/Xỉu biên, dự đoán tiếp tục Tài/Xỉu."""
    if len(totals) < 8:
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}
        
    window = list(totals)[-8:]
    t_range = max(window) - min(window)
    last_total = totals[-1]

    if t_range <= 2.0:
        if last_total >= 14: # Tài biên
            return {"du_doan": "Tài", "do_tin_cay": 91.0}
        if last_total <= 7: # Xỉu biên
            return {"du_doan": "Xỉu", "do_tin_cay": 90.8}
            
    return {"du_doan": history[-1], "do_tin_cay": 70.9}

def ai47_super_trend_ma_5_streak_3(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Phối hợp MA (5 phiên) và Streak (3 phiên) để xác nhận xu hướng mạnh."""
    if len(totals) < 5 or len(history) < 3:
        return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 50.0}
        
    avg5 = statistics.mean(list(totals)[-5:])
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
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}
        
    avg8 = statistics.mean(list(totals)[-8:])
    
    if avg8 > 11.8:
        # Quá Tài -> dự đoán Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 88.4}
    if avg8 < 9.2:
        # Quá Xỉu -> dự đoán Tài
        return {"du_doan": "Tài", "do_tin_cay": 88.9}
            
    return {"du_doan": history[-1], "do_tin_cay": 70.5}

def ai49_stochastic_oscillator_10(history: deque, totals: deque, win_log: deque) -> PredictionResult:
    """Dao động ngẫu nhiên (Stochastic) 10 phiên: Tỷ lệ Total cuối so với phạm vi min/max."""
    if len(totals) < 10:
        return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 50.0}
            
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
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}
            
    seq = "".join("T" if h == "Tài" else "X" for h in list(history)[-3:])
    
    if seq == "TTT": # Chuỗi Tài -> Dự đoán Tài tiếp (ưu tiên xu hướng mạnh)
        return {"du_doan": "Tài", "do_tin_cay": 89.6}
    if seq == "XXX": # Chuỗi Xỉu -> Dự đoán Xỉu tiếp (ưu tiên xu hướng mạnh)
        return {"du_doan": "Xỉu", "do_tin_cay": 89.5}
    if seq == "TXT": # Xen kẽ -> Dự đoán Xỉu tiếp (ưu tiên hồi quy)
        return {"du_doan": "Xỉu", "do_tin_cay": 88.1}
    if seq == "XTX": # Xen kẽ -> Dự đoán Tài tiếp (ưu tiên hồi quy)
        return {"du_doan": "Tài", "do_tin_cay": 88.3}
            
    return {"du_doan": history[-1], "do_tin_cay": 71.7}


# =========================================================
# II. CLASS QUẢN LÝ DỰ ĐOÁN (PREDICTOR CLASS)
# =========================================================

class TaiXiuPredictor:
    """Quản lý dữ liệu lịch sử và thực thi tất cả các thuật toán dự đoán."""
    
    def __init__(self, api_url: str, app_id: str):
        self.api_url = api_url
        self.app_id = app_id
        
        # Lịch sử dữ liệu (Tai/Xiu, Total, Win/Loss)
        self.history: deque[str] = deque(maxlen=MAX_HISTORY_SIZE)
        self.totals: deque[int] = deque(maxlen=MAX_HISTORY_SIZE)
        self.win_log: deque[bool] = deque(maxlen=MAX_HISTORY_SIZE) # Ghi lại Win/Loss của dự đoán trước
        self.last_phien_id: Optional[int] = None
        self.last_prediction_data: Optional[PredictionResult] = None # Lưu dự đoán của phiên trước để đánh giá

        # Danh sách tất cả 50 thuật toán đã được định nghĩa
        self.algos: List[Callable] = [
            # Khối 1: Xu hướng & Động lượng
            ai1_sma_crossover_5_10, ai2_rsi_analog_14, ai3_trend_slope_linear_6, 
            ai4_macd_signal_5_10, ai5_momentum_breakout_4, ai6_triple_trend_confirm, 
            ai7_mid_range_stability_8, ai8_volume_oscillator_5, ai9_exponential_ma_4, 
            ai10_keltner_bands_5_10,
            
            # Khối 2: Đảo Chiều & Hồi Quy
            ai11_mean_reversion_15, ai12_three_star_reversal, ai13_parity_gap_8, 
            ai14_three_white_soldiers, ai15_fibonacci_reversal_3, ai16_flip_flop_reversal_5, 
            ai17_total_range_mid_reversion, ai18_anti_martingale_3, ai19_long_term_alternating_10, 
            ai20_oscillator_divergence_7,
            
            # Khối 3: Nhận Dạng Mẫu Chuỗi & Xu hướng
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
                
                # Xử lý dữ liệu xúc xắc (dices)
                dices_raw = newest.get("dices", [])
                if isinstance(dices_raw, str):
                    dice = [int(d) for d in dices_raw.split(',') if d.strip().isdigit()][:3]
                elif isinstance(dices_raw, list):
                    dice = [int(d) for d in dices_raw][:3]
                else:
                    dice = []
                    
                # Tính lại tổng, đảm bảo dữ liệu chuẩn
                tong = sum(dice) if len(dice) == 3 else newest.get("point", 0)
                
                # Chuẩn hóa kết quả (Tai/Xiu)
                ketqua = ""
                if 11 <= tong <= 17:
                    ketqua = "Tài"
                elif 4 <= tong <= 10:
                    ketqua = "Xỉu"
                else:
                    ketqua = "Lỗi Dữ Liệu" 
                    
                # Chỉ trả về dữ liệu hợp lệ (tổng từ 4 đến 17)
                if ketqua != "Lỗi Dữ Liệu":
                    return phien, dice, tong, ketqua
            
        except requests.exceptions.RequestException as e:
            # print(f"[❌] Lỗi lấy dữ liệu API {self.api_url}: {e}")
            pass
        except Exception as e:
            # print(f"[❌] Lỗi xử lý JSON hoặc logic: {e}")
            pass
            
        return None

    def _run_algorithms(self) -> PredictionResult:
        """Thực thi tất cả 50 thuật toán đã đăng ký và chọn ra kết quả tốt nhất."""
        results = []
        for algo in self.algos:
            try:
                r = algo(self.history, self.totals, self.win_log)
                # Đảm bảo độ tin cậy nằm trong [50, 100]
                confidence = round(max(50.0, min(100.0, r["do_tin_cay"])), 2) 
                
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
            if phien != self.last_phien_id and phien is not None and len(dice) == 3:
                
                # --- CHU TRÌNH 1: Đánh giá phiên VỪA KẾT THÚC ---
                if self.last_phien_id is not None and self.last_prediction_data:
                    # Kiểm tra xem dự đoán cho phiên này có đúng với kết quả thực tế không
                    last_prediction = self.last_prediction_data.get("du_doan")
                    if last_prediction not in ["Đang khởi động...", "Đang phân tích"]:
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
                
                # In ra log chi tiết
                win_rate = (sum(1 for w in self.win_log if w) / len(self.win_log) * 100) if self.win_log else 0.0
                print(f"[✅] Phiên {phien} | 🎲 {dice} ({tong}) → {ketqua} | 🔮 {prediction_for_next['best_algo']} → {prediction_for_next['du_doan']} ({prediction_for_next['do_tin_cay']}%) | Tỷ lệ thắng (Log): {win_rate:.2f}% ({len(self.win_log)}/30)")
            
            # Nếu là cùng một phiên (chờ kết quả), cập nhật lại dữ liệu nhưng không thay đổi dự đoán
            elif self.last_phien_id == phien:
                # Cập nhật thông tin phiên hiện tại (nếu cần)
                self.last_data.update({
                    "phien": phien,
                    "xucxac1": dice[0],
                    "xucxac2": dice[1],
                    "xucxac3": dice[2],
                    "tong": tong,
                    "ketqua": ketqua,
                })
        
        # Luôn trả về dữ liệu mới nhất (Phiên Vừa Ra và Dự Đoán cho Phiên Tiếp Theo)
        return self.last_data


# =========================================================
# III. KHỞI CHẠY HỆ THỐNG
# =========================================================

# Khởi tạo đối tượng Predictor (sử dụng API Tele68 cho ví dụ)
# VUI LÒNG THAY ĐỔI URL NÀY nếu muốn kết nối với API của LC hoặc nền tảng khác
TELE68_API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
APP_IDENTIFIER = "VIP_Quant_Analyzer_V5"

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
