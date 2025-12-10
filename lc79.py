import requests
import time
import threading
from flask import Flask, jsonify
from datetime import datetime
import statistics
from collections import deque
from typing import List, Tuple, Dict, Deque, Any
import math

# ===============================
# CẤU HÌNH & BIẾN TOÀN CỤC
# ===============================
API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
last_processed_session_id = None

app = Flask(__name__)

# Khai báo cấu trúc dữ liệu cho kết quả dự đoán (giả định)
PredictionResult = Dict[str, Any]

# Lưu lịch sử 30 phiên gần nhất (cần tối thiểu 20 cho thuật toán V8.0)
# Mỗi phần tử là: {'total': int, 'tai_xiu': str, 'dices': [d1, d2, d3]}
HISTORY_QUEUE: Deque[dict] = deque(maxlen=30) 

# BIẾN LƯU DỮ LIỆU TRẢ RA API
latest_data = {
    "Phiên": None,
    "Xúc xắc 1": None,
    "Xúc xắc 2": None,
    "Xúc xắc 3": None,
    "Tổng": None,
    "Dự đoán": "Đang chờ", 
    "Độ tin cậy": 0.0,      
    "ID": "tuananh"
}

# =========================================================
# I. KHU VỰC ĐỊNH NGHĨA HÀM HỖ TRỢ CHUNG (Từ thuật toán V8.0)
# =========================================================

def _get_result_type(total: int, is_triplet: bool) -> str:
    """Xác định kết quả là Tài, Xỉu hay Bão."""
    if is_triplet:
        return "Bão"
    elif 11 <= total <= 17:
        return "Tài"
    elif 4 <= total <= 10:
        return "Xỉu"
    return "Lỗi Dữ Liệu"

def _get_momentum_bias(history_tx: List[str], totals: List[int]) -> str:
    """Xác định xu hướng ngắn hạn (3 phiên) để làm dự đoán mặc định khi không có tín hiệu mạnh."""
    if len(history_tx) < 3:
        return history_tx[-1] if history_tx else "Tài"
    
    h_list = history_tx[-3:]
    
    count_tai = h_list.count("Tài")
    count_xiu = h_list.count("Xỉu")

    if count_tai >= 2:
        return "Tài"
    elif count_xiu >= 2:
        return "Xỉu"
    
    # Nếu cân bằng, dự đoán ngược lại kết quả cuối cùng (Nguyên tắc Hồi quy yếu)
    return "Xỉu" if history_tx[-1] == "Tài" else "Tài"

def _extract_sequences(history: Deque[dict]) -> Tuple[List[str], List[int], List[int], List[int]]:
    """Tách history_queue thành các chuỗi riêng biệt."""
    history_tx = [d['tai_xiu'] for d in history if d['tai_xiu'] in ["Tài", "Xỉu"]]
    totals = [d['total'] for d in history]
    parities = [d['total'] % 2 for d in history] # 0 = Chẵn, 1 = Lẻ
    
    # Total Bias: > 10.5 là Tài, < 10.5 là Xỉu
    total_bias = [t - 10.5 for t in totals]
    return history_tx, totals, parities, total_bias

# =========================================================
# II. KHU VỰC ĐỊNH NGHĨA 10 CHIẾN LƯỢC VIP PRO (V8.0)
# (Đã được chuyển từ yêu cầu của bạn)
# =========================================================

# --- KHỐI 1: PHÂN TÍCH LỰC (FORCE ANALYSIS) ---

def v8_ai1_rsi_analog_reversion_14(total_bias: List[int], history_tx: List[str]) -> PredictionResult:
    """RSI Analog 14 phiên: Phát hiện vùng quá mua/quá bán (Tài/Xỉu quá mức) dựa trên độ lệch total (Total Bias)."""
    if len(total_bias) < 14:
        return {"du_doan": _get_momentum_bias(history_tx, total_bias), "do_tin_cay": 50.0, "ly_do": "RSI: Thiếu dữ liệu (14)"}
    
    window = total_bias[-14:]
    
    gain = sum(t for t in window if t > 0)
    loss = sum(abs(t) for t in window if t < 0)
    
    if loss == 0 and gain > 0: rs = 100
    elif gain == 0 and loss > 0: rs = 0
    elif gain == 0 and loss == 0: rs = 50.0
    else: rs = gain / loss
    
    rsi = 100 - (100 / (1 + rs))

    if rsi >= 75:
        return {"du_doan": "Xỉu", "do_tin_cay": 93.5 + (rsi - 75) * 0.5, "ly_do": f"RSI Analog: Quá mua (RSI={rsi:.2f} >= 75). Dự đoán hồi quy Xỉu."}
    if rsi <= 25:
        return {"du_doan": "Tài", "do_tin_cay": 93.0 + (25 - rsi) * 0.5, "ly_do": f"RSI Analog: Quá bán (RSI={rsi:.2f} <= 25). Dự đoán hồi quy Tài."}
        
    return {"du_doan": "Tài" if rsi > 50 else "Xỉu", "do_tin_cay": 75.0, "ly_do": f"RSI Analog: Trung tính (RSI={rsi:.2f}). Dự đoán theo bias RSI."}

def v8_ai2_wma_macd_divergence_10_3(totals: List[int], history_tx: List[str]) -> PredictionResult:
    """Phân kỳ MACD WMA 10-3: Phát hiện sự phân kỳ giữa WMA nhanh và tín hiệu Tài/Xỉu."""
    if len(totals) < 10:
        return {"du_doan": _get_momentum_bias(history_tx, totals), "do_tin_cay": 50.0, "ly_do": "MACD: Thiếu dữ liệu (10)"}
    
    def calculate_wma(data: List[int], period: int) -> float:
        if len(data) < period: return 0.0
        window = data[-period:]
        weights = list(range(1, period + 1))
        return sum(p * w for p, w in zip(window, weights)) / sum(weights)

    wma_10 = calculate_wma(totals, 10)
    wma_3 = calculate_wma(totals, 3)

    macd_line = wma_3 - wma_10
    
    if len(totals) < 12:
        return {"du_doan": _get_momentum_bias(history_tx, totals), "do_tin_cay": 60.0, "ly_do": "MACD: Cần 3 giá trị MACD để tính Signal Line."}
        
    macd_history = []
    for i in range(3, 11): 
        macd_history.append(calculate_wma(totals[:len(totals)-i+10], 3) - calculate_wma(totals[:len(totals)-i+10], 10))

    signal_line = calculate_wma(macd_history[-3:], 3)

    if totals[-1] < totals[-2] and macd_line > signal_line and macd_line > macd_history[-2]:
        return {"du_doan": "Tài", "do_tin_cay": 90.0, "ly_do": "MACD Divergence: Phân kỳ tăng (Giá giảm, Động lượng tăng). Dự đoán Tài."}
    
    if totals[-1] > totals[-2] and macd_line < signal_line and macd_line < macd_history[-2]:
        return {"du_doan": "Xỉu", "do_tin_cay": 89.5, "ly_do": "MACD Divergence: Phân kỳ giảm (Giá tăng, Động lượng giảm). Dự đoán Xỉu."}

    if macd_line > signal_line and macd_history[-2] < macd_history[-3]:
        return {"du_doan": "Tài", "do_tin_cay": 85.0, "ly_do": "MACD Crossover: MACD cắt lên Signal. Dự đoán Tài."}
    if macd_line < signal_line and macd_history[-2] > macd_history[-3]:
        return {"du_doan": "Xỉu", "do_tin_cay": 84.5, "ly_do": "MACD Crossover: MACD cắt xuống Signal. Dự đoán Xỉu."}
        
    return {"du_doan": _get_momentum_bias(history_tx, totals), "do_tin_cay": 65.0, "ly_do": "MACD: Trung tính. Dự đoán theo bias ngắn."}

def v8_ai3_volatility_squeeze_15(totals: List[int], history_tx: List[str]) -> PredictionResult:
    """Phát hiện Volatility Squeeze 15 phiên: Khi dải Total co hẹp quá mức, dự đoán bùng nổ."""
    if len(totals) < 15:
        return {"du_doan": _get_momentum_bias(history_tx, totals), "do_tin_cay": 50.0, "ly_do": "Squeeze: Thiếu dữ liệu (15)"}
    
    window = totals[-15:]
    
    try:
        std_dev = statistics.stdev(window)
    except statistics.StatisticsError:
        return {"du_doan": _get_momentum_bias(history_tx, totals), "do_tin_cay": 60.0, "ly_do": "Squeeze: Độ lệch chuẩn không tính được."}

    true_range = max(window) - min(window)
    
    if std_dev < 1.0 and true_range <= 3:
        prediction = history_tx[-1]
        return {"du_doan": prediction, "do_tin_cay": 92.0, "ly_do": f"Volatility Squeeze: STD < 1.0 và Range <= 3. Dự đoán bùng nổ theo hướng {prediction}."}
    
    return {"du_doan": _get_momentum_bias(history_tx, totals), "do_tin_cay": 65.0, "ly_do": "Squeeze: Độ biến động ổn định. Dự đoán theo bias ngắn."}


# --- KHỐI 2: PHÂN TÍCH TƯƠNG QUAN VÀ SÓNG ---

def v8_ai4_fibonacci_reversal_7(totals: List[int], history_tx: List[str]) -> PredictionResult:
    """Hồi quy Fibonacci 7 phiên: Nếu Total vượt quá 61.8% độ biến động gần nhất, dự đoán hồi quy."""
    if len(totals) < 7:
        return {"du_doan": _get_momentum_bias(history_tx, totals), "do_tin_cay": 50.0, "ly_do": "Fib Reversal: Thiếu dữ liệu (7)"}
    
    window = totals[-7:]
    max_total = max(window)
    min_total = min(window)
    total_range = max_total - min_total
    current = totals[-1]

    if total_range < 2:
        return {"du_doan": _get_momentum_bias(history_tx, totals), "do_tin_cay": 60.0, "ly_do": "Fib Reversal: Biến động quá hẹp."}

    retracement_level_tai = max_total - (total_range * 0.618)
    retracement_level_xiu = min_total + (total_range * 0.618)
    
    if history_tx[-1] == "Tài" and current > retracement_level_xiu and history_tx[-2] == "Xỉu":
        return {"du_doan": "Tài", "do_tin_cay": 88.0, "ly_do": f"Fib Reversal: Phục hồi Tài vượt 61.8% ({current:.2f} > {retracement_level_xiu:.2f}). Dự đoán TĂNG."}
    
    if history_tx[-1] == "Xỉu" and current < retracement_level_tai and history_tx[-2] == "Tài":
        return {"du_doan": "Xỉu", "do_tin_cay": 87.5, "ly_do": f"Fib Reversal: Giảm Xỉu vượt 61.8% ({current:.2f} < {retracement_level_tai:.2f}). Dự đoán GIẢM."}

    return {"du_doan": _get_momentum_bias(history_tx, totals), "do_tin_cay": 65.0, "ly_do": "Fib Reversal: Trong vùng thoái lui an toàn. Dự đoán theo bias ngắn."}

def v8_ai5_even_odd_divergence_8(history_tx: List[str], parities: List[int]) -> PredictionResult:
    """Phân kỳ Chẵn/Lẻ: Nếu chuỗi Tài/Xỉu đang tăng nhưng chuỗi Chẵn/Lẻ lại đang đảo chiều."""
    if len(parities) < 8:
        return {"du_doan": _get_momentum_bias(history_tx, history_tx), "do_tin_cay": 50.0, "ly_do": "Parity Div: Thiếu dữ liệu (8)"}
        
    last_4_tx = history_tx[-4:]
    last_4_parity = parities[-4:]
    
    is_tai_trend = last_4_tx.count("Tài") >= 3
    is_xiu_trend = last_4_tx.count("Xỉu") >= 3

    is_parity_reversion = (last_4_parity.count(0) >= 3 and last_4_parity[-1] == 0) or \
                          (last_4_parity.count(1) >= 3 and last_4_parity[-1] == 1)
                          
    if is_tai_trend and is_parity_reversion and last_4_parity[-1] == 0:
        return {"du_doan": "Xỉu", "do_tin_cay": 91.0, "ly_do": "Parity Div: Tài tăng nhưng Chẵn liên tục ra (Ngoại lai Parity). Dự đoán đảo chiều Xỉu."}
    
    if is_xiu_trend and is_parity_reversion and last_4_parity[-1] == 1:
        return {"du_doan": "Tài", "do_tin_cay": 90.5, "ly_do": "Parity Div: Xỉu giảm nhưng Lẻ liên tục ra (Ngoại lai Parity). Dự đoán đảo chiều Tài."}

    return {"du_doan": _get_momentum_bias(history_tx, history_tx), "do_tin_cay": 65.0, "ly_do": "Parity Div: Không có phân kỳ rõ ràng. Dự đoán theo bias ngắn."}

def v8_ai6_max_min_retest_12(totals: List[int], history_tx: List[str]) -> PredictionResult:
    """Kiểm tra Kiểm tra lại (Retest) Total Max/Min trong 12 phiên."""
    if len(totals) < 12:
        return {"du_doan": _get_momentum_bias(history_tx, totals), "do_tin_cay": 50.0, "ly_do": "Retest: Thiếu dữ liệu (12)"}
    
    window = totals[-12:]
    current = totals[-1]
    
    max_total = max(window[:-1])
    max_count = window[:-1].count(max_total)

    min_total = min(window[:-1])
    min_count = window[:-1].count(min_total)
    
    if current == max_total and max_count >= 2:
        return {"du_doan": "Xỉu", "do_tin_cay": 94.0, "ly_do": f"Max/Min Retest: Total={current} chạm lại Max cũ ({max_total}). Dự đoán Hồi quy Xỉu."}
    
    if current == min_total and min_count >= 2:
        return {"du_doan": "Tài", "do_tin_cay": 93.5, "ly_do": f"Max/Min Retest: Total={current} chạm lại Min cũ ({min_total}). Dự đoán Hồi quy Tài."}

    return {"du_doan": history_tx[-1], "do_tin_cay": 70.0, "ly_do": "Max/Min Retest: Không có tín hiệu Retest. Dự đoán bám xu hướng gần nhất."}

# --- KHỐI 3: PHÂN TÍCH CHUỖI & ĐỊNH LƯỢNG ---

def v8_ai7_streak_reversion_entropy_10(history_tx: List[str]) -> PredictionResult:
    """Entropy Chuỗi: Đo lường độ ngẫu nhiên/lộn xộn trong 10 phiên. Dự đoán gãy chuỗi nếu Entropy thấp/cao quá mức."""
    if len(history_tx) < 10:
        return {"du_doan": _get_momentum_bias(history_tx, history_tx), "do_tin_cay": 50.0, "ly_do": "Entropy: Thiếu dữ liệu (10)"}
    
    window = history_tx[-10:]
    n = len(window)
    
    count_tai = window.count("Tài")
    count_xiu = window.count("Xỉu")
    
    if count_tai == 0 or count_xiu == 0:
        prediction = "Xỉu" if count_tai > 0 else "Tài"
        return {"du_doan": prediction, "do_tin_cay": 95.0, "ly_do": f"Entropy: Chuỗi liên tục 10 kỳ. Dự đoán GÃY sang {prediction}."}
    
    p_tai = count_tai / n
    p_xiu = count_xiu / n

    # Tính Shannon Entropy (H)
    # math.log2(0) gây lỗi nếu p_tai/p_xiu = 0, nhưng đã xử lý trường hợp này ở trên.
    entropy = -(p_tai * math.log2(p_tai) + p_xiu * math.log2(p_xiu))

    if entropy < 0.6:
        prediction = "Xỉu" if count_tai > count_xiu else "Tài"
        return {"du_doan": prediction, "do_tin_cay": 87.0, "ly_do": f"Entropy: Chuỗi quá tập trung (H={entropy:.2f}). Dự đoán Hồi quy {prediction}."}
        
    if entropy > 0.98:
        return {"du_doan": _get_momentum_bias(history_tx, history_tx), "do_tin_cay": 70.0, "ly_do": f"Entropy: Quá ngẫu nhiên (H={entropy:.2f}). Dự đoán theo bias ngắn."}
        
    return {"du_doan": _get_momentum_bias(history_tx, history_tx), "do_tin_cay": 60.0, "ly_do": "Entropy: Trung tính. Dự đoán theo bias ngắn."}

def v8_ai8_auto_correlation_lag_3_15(history_tx: List[str]) -> PredictionResult:
    """Tự Tương Quan (Auto-Correlation) Lag 3 trong 15 phiên: Kiểm tra tính lặp lại của mẫu T-X."""
    if len(history_tx) < 15:
        return {"du_doan": _get_momentum_bias(history_tx, history_tx), "do_tin_cay": 50.0, "ly_do": "ACF: Thiếu dữ liệu (15)"}

    window = [1 if r == "Tài" else -1 for r in history_tx[-15:]]
    n = len(window)
    
    mean_val = statistics.mean(window)
    
    numerator = sum((window[i] - mean_val) * (window[i-3] - mean_val) for i in range(3, n))
    denominator = sum((x - mean_val)**2 for x in window)

    if denominator == 0:
        return {"du_doan": _get_momentum_bias(history_tx, history_tx), "do_tin_cay": 60.0, "ly_do": "ACF: Biến động bằng 0."}
        
    acf_lag_3 = numerator / denominator

    if acf_lag_3 > 0.4:
        prediction = history_tx[-3]
        return {"du_doan": prediction, "do_tin_cay": 91.0, "ly_do": f"ACF Lag 3: Tương quan Dương mạnh ({acf_lag_3:.2f}). Dự đoán lặp lại {prediction}."}
    
    if acf_lag_3 < -0.4:
        prediction = "Xỉu" if history_tx[-3] == "Tài" else "Tài"
        return {"du_doan": prediction, "do_tin_cay": 90.5, "ly_do": f"ACF Lag 3: Tương quan Âm mạnh ({acf_lag_3:.2f}). Dự đoán đảo ngược {prediction}."}

    return {"du_doan": _get_momentum_bias(history_tx, history_tx), "do_tin_cay": 65.0, "ly_do": "ACF: Không có tính lặp lại rõ ràng. Dự đoán theo bias ngắn."}

def v8_ai9_market_profile_10(totals: List[int], history_tx: List[str]) -> PredictionResult:
    """Phân Tích Hồ Sơ Thị Trường (Market Profile) 10 phiên: Xác định Total thường xuyên xuất hiện (Value Area)."""
    if len(totals) < 10:
        return {"du_doan": _get_momentum_bias(history_tx, totals), "do_tin_cay": 50.0, "ly_do": "Profile: Thiếu dữ liệu (10)"}
        
    window = totals[-10:]
    current = totals[-1]

    counts = {}
    for t in window:
        counts[t] = counts.get(t, 0) + 1
        
    poc = max(counts, key=counts.get)
    poc_count = counts[poc]
    
    total_count = len(window)
    sorted_totals = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    
    cumulative_count = 0
    value_area_totals = []
    
    for total, count in sorted_totals:
        cumulative_count += count
        value_area_totals.append(total)
        if cumulative_count / total_count >= 0.70:
            break
            
    if current not in value_area_totals:
        if current > poc:
            return {"du_doan": "Xỉu", "do_tin_cay": 89.0, "ly_do": f"Profile: Total={current} ngoài Value Area. Dự đoán Hồi quy về POC={poc}."}
        else:
            return {"du_doan": "Tài", "do_tin_cay": 88.5, "ly_do": f"Profile: Total={current} ngoài Value Area. Dự đoán Hồi quy về POC={poc}."}

    if current == poc and poc_count >= 4:
        prediction = _get_result_type(poc, False)
        return {"du_doan": prediction, "do_tin_cay": 85.0, "ly_do": f"Profile: Total={current} chạm POC ({poc}). Dự đoán bám dính {prediction}."}
        
    return {"du_doan": _get_momentum_bias(history_tx, totals), "do_tin_cay": 65.0, "ly_do": "Profile: Trong Value Area. Dự đoán theo bias ngắn."}

def v8_ai10_total_divergence_3_10(totals: List[int], history_tx: List[str]) -> PredictionResult:
    """Phân kỳ Tổng Điểm: So sánh xu hướng Tài/Xỉu (TX) với xu hướng Total (T) trong 10 phiên."""
    if len(totals) < 10:
        return {"du_doan": _get_momentum_bias(history_tx, totals), "do_tin_cay": 50.0, "ly_do": "Total Div: Thiếu dữ liệu (10)"}
    
    avg5 = statistics.mean(totals[-5:])
    avg10 = statistics.mean(totals[-10:])

    tx_5 = history_tx[-5:]
    tx_trend = tx_5.count("Tài") - tx_5.count("Xỉu")

    if avg5 > avg10 + 0.5 and tx_trend <= 0:
        return {"du_doan": "Tài", "do_tin_cay": 92.0, "ly_do": "Total Div: Phân kỳ tăng (Total > TX). Total tăng sắp kéo về Tài."}

    if avg5 < avg10 - 0.5 and tx_trend >= 0:
        return {"du_doan": "Xỉu", "do_tin_cay": 91.5, "ly_do": "Total Div: Phân kỳ giảm (Total < TX). Total giảm sắp kéo về Xỉu."}

    if avg5 > avg10 and tx_trend > 0:
        return {"du_doan": "Tài", "do_tin_cay": 85.0, "ly_do": "Total Div: Cùng hướng Tăng. Dự đoán tiếp diễn Tài."}
    if avg5 < avg10 and tx_trend < 0:
        return {"du_doan": "Xỉu", "do_tin_cay": 84.5, "ly_do": "Total Div: Cùng hướng Giảm. Dự đoán tiếp diễn Xỉu."}
        
    return {"du_doan": _get_momentum_bias(history_tx, totals), "do_tin_cay": 65.0, "ly_do": "Total Div: Trung tính. Dự đoán theo bias ngắn."}

# =========================================================
# III. HÀM TỔNG HỢP VÀ BỎ PHIẾU CUỐI CÙNG (ENSEMBLE VOTING)
# =========================================================

PREDICTION_STRATEGIES = [
    v8_ai1_rsi_analog_reversion_14, v8_ai2_wma_macd_divergence_10_3, 
    v8_ai3_volatility_squeeze_15, v8_ai4_fibonacci_reversal_7, 
    v8_ai5_even_odd_divergence_8, v8_ai6_max_min_retest_12, 
    v8_ai7_streak_reversion_entropy_10, v8_ai8_auto_correlation_lag_3_15, 
    v8_ai9_market_profile_10, v8_ai10_total_divergence_3_10
]

def predict_final_vote_ensemble(history_queue: Deque[dict]) -> PredictionResult:
    """
    Hàm tổng hợp kết quả của 10 chiến lược dự đoán (V8.0) bằng cơ chế bỏ phiếu có trọng số (Confidence).
    """
    if len(history_queue) < 20:
        return {"du_doan": "Đang chờ", "do_tin_cay": 50.0, "ly_do": "Thiếu dữ liệu lịch sử tối thiểu (cần 20 phiên)."}
        
    history_tx, totals, parities, total_bias = _extract_sequences(history_queue)
    
    votes = {"Tài": 0.0, "Xỉu": 0.0}
    total_confidence_sum = 0.0
    valid_votes_count = 0
    
    for strategy in PREDICTION_STRATEGIES:
        if strategy in [v8_ai1_rsi_analog_reversion_14]:
            result = strategy(total_bias, history_tx)
        elif strategy in [v8_ai5_even_odd_divergence_8]:
            result = strategy(history_tx, parities)
        elif strategy in [v8_ai7_streak_reversion_entropy_10, v8_ai8_auto_correlation_lag_3_15]:
            result = strategy(history_tx)
        else:
            result = strategy(totals, history_tx)
            
        prediction = result["du_doan"]
        confidence = result["do_tin_cay"]
        
        if confidence >= 70.0:
            vote_weight = confidence / 100.0
            
            if prediction == "Tài":
                votes["Tài"] += vote_weight
            elif prediction == "Xỉu":
                votes["Xỉu"] += vote_weight
            
            total_confidence_sum += confidence
            valid_votes_count += 1
            
    total_votes_weight = votes["Tài"] + votes["Xỉu"]
    
    if total_votes_weight == 0:
        default_prediction = _get_momentum_bias(history_tx, totals)
        return {"du_doan": default_prediction, "do_tin_cay": 65.0, "ly_do": "Tất cả logic trung tính. Dự đoán theo xu hướng ngắn hạn."}
        
    if votes["Tài"] > votes["Xỉu"]:
        final_prediction = "TÀI"
        ratio_confidence = votes["Tài"] / total_votes_weight
    elif votes["Xỉu"] > votes["Tài"]:
        final_prediction = "XỈU"
        ratio_confidence = votes["Xỉu"] / total_votes_weight
    else:
        final_prediction = _get_momentum_bias(history_tx, totals)
        ratio_confidence = 0.50

    avg_confidence_of_votes = total_confidence_sum / valid_votes_count if valid_votes_count > 0 else 70.0
    
    final_confidence = avg_confidence_of_votes * ratio_confidence * 1.3
    
    final_confidence = min(99.0, max(70.0, final_confidence))
    
    ly_do_tong_hop = f"TỔNG HỢP 10 LOGIC: {final_prediction} áp đảo ({votes[final_prediction]:.2f} phiếu) so với {votes['Xỉu' if final_prediction == 'TÀI' else 'Tài']:.2f} phiếu. Độ tin cậy trung bình của các phiếu là {avg_confidence_of_votes:.2f}%."

    return {
        "du_doan": final_prediction,
        "do_tin_cay": round(final_confidence, 2),
        "ly_do": ly_do_tong_hop
    }


# ===============================
# BOT NỀN – LẤY DATA & DỰ ĐOÁN 24/7
# ===============================
def fetch_data_loop():
    global last_processed_session_id, HISTORY_QUEUE, latest_data

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
                # Nếu phiên đã xử lý, đợi và tiếp tục
                time.sleep(2)
                continue

            # 3. XỬ LÝ DỮ LIỆU PHIÊN MỚI
            dices = phien.get("dices")
            tong = phien.get("point")
            
            if not dices or tong is None:
                 # Bỏ qua nếu dữ liệu không đầy đủ (ví dụ: phiên đang chạy)
                time.sleep(2)
                continue
                
            d1, d2, d3 = dices
            
            # Kiểm tra Bão (Triplet)
            is_triplet = (d1 == d2) and (d2 == d3)
            tai_xiu = _get_result_type(tong, is_triplet)

            # Cập nhật lịch sử HISTORY_QUEUE
            HISTORY_QUEUE.append({
                "total": tong,
                "tai_xiu": tai_xiu,
                "dices": dices
            })
            
            # Cập nhật ID phiên đã xử lý
            last_processed_session_id = phien_id
            
            # 4. THỰC HIỆN DỰ ĐOÁN V8.0 CHO PHIÊN TIẾP THEO
            # V8.0 sử dụng HISTORY_QUEUE để dự đoán kết quả TÀI/XỈU tiếp theo.
            prediction_result = predict_final_vote_ensemble(HISTORY_QUEUE)
            
            # 5. CẬP NHẬT DỮ LIỆU API TRẢ VỀ
            latest_data.update({
                "Phiên": phien_id,
                "Xúc xắc 1": d1,
                "Xúc xắc 2": d2,
                "Xúc xắc 3": d3,
                "Tổng": tong,
                "Dự đoán": prediction_result["du_doan"],
                "Độ tin cậy": prediction_result["do_tin_cay"],
                "ID": "tuananh"
            })

        except Exception as e:
            print(f"Lỗi nền ({datetime.now().strftime('%H:%M:%S')}):", e)
            
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
    """Trả về dữ liệu phiên mới nhất và dự đoán cho phiên kế tiếp."""
    return jsonify({
        "data": latest_data
    })


@app.route("/", methods=["GET"])
def home():
    return f""


# ===============================
# RUN SERVER
# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
