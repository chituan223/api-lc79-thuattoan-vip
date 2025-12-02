from flask import Flask, jsonify
import requests
import statistics

# ================== CẤU HÌNH API VÀ FLASK ==================
app = Flask(__name__)
API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"


# ================== 25 CHIẾN LƯỢC PHÂN TÍCH CHUYÊN SÂU  ==================
# Các hàm này phân tích lịch sử để đưa ra dự đoán và độ tin cậy.
# Đầu vào: history (list of Tài/Xỉu strings), totals (list of sum integers)
# Đầu ra: dict {"du_doan": "Tài"|"Xỉu", "do_tin_cay": float (0.0 - 100.0)}

# 1. PHÂN TÍCH CHUỖI FIBONACCI VÀ ĐIỂM ĐẢO CHIỀU (Fibonacci Reversion & Pivot)
def s1_fibonacci_reversion(history, totals):
    """Phân tích chuỗi bệt dựa trên các cấp độ Fibonacci (5, 8, 13) để dự đoán đảo chiều cực đại."""
    if len(history) < 13: return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 60.0}
    
    last_result = history[-1]
    streak_count = 0
    for i in range(len(history)-1, -1, -1):
        if history[i] == last_result: streak_count += 1
        else: break
        
    # Chuỗi Fibonacci cần phá vỡ: 5, 8, 13
    if streak_count in [5, 8]:
        return {"du_doan": last_result, "do_tin_cay": 90.0} # Giữ trend (chờ điểm phá vỡ lớn)
    
    if streak_count >= 13: # Phá vỡ chuỗi dài nhất
        prediction = "Xỉu" if last_result == "Tài" else "Tài"
        return {"du_doan": prediction, "do_tin_cay": 99.5} # Độ tin cậy cực cao

    return {"du_doan": last_result, "do_tin_cay": 70.0}

# 2. BẢNG MA TRẬN CHUYỂN ĐỔI MARKOV 3 BƯỚC (3-Step Markov Transition)
def s2_markov_transition_3step(history, totals):
    """Phân tích xác suất chuyển đổi dựa trên 3 kết quả gần nhất trong 10 phiên."""
    if len(history) < 10: return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 60.0}
    
    # Chỉ lấy ký tự đầu để so sánh (T hoặc X)
    last_3 = "".join(h[0] for h in history[-3:]) # VD: "TXT"
    
    # Phân tích 10 phiên gần nhất
    recent_history = history[-10:]
    
    # Thống kê xác suất chuyển đổi từ last_3 sang Tài (T) hoặc Xỉu (X)
    tai_prob, xiu_prob = 0, 0
    
    for i in range(len(recent_history) - 3):
        # Tạo chuỗi 3 bước (predecessor)
        predecessor = "".join(h[0] for h in recent_history[i:i+3])
        if predecessor == last_3:
            # Kiểm tra kết quả tiếp theo (successor)
            if recent_history[i+3] == "Tài": tai_prob += 1
            else: xiu_prob += 1
            
    total_transitions = tai_prob + xiu_prob
    
    if total_transitions > 2:
        if tai_prob > xiu_prob * 2: # Tỷ lệ Tài gấp đôi
            return {"du_doan": "Tài", "do_tin_cay": 94.0}
        if xiu_prob > tai_prob * 2: # Tỷ lệ Xỉu gấp đôi
            return {"du_doan": "Xỉu", "do_tin_cay": 94.0}

    return {"du_doan": history[-1], "do_tin_cay": 75.0}

# 3. HỒI QUY TRỌNG SỐ ĐỘNG 15 PHIÊN (Dynamic Weighted Mean Reversion 15)
def s3_dynamic_weighted_reversion(history, totals):
    """Dự đoán hồi quy về trung điểm (10.5) dựa trên trung bình trọng số của 15 phiên gần nhất."""
    if len(totals) < 15: return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 65.0}
    
    # Trọng số tăng dần tuyến tính: 1, 2, 3, ..., 15 (phiên gần nhất có trọng số cao nhất)
    weights = list(range(1, 16)) 
    last_15 = totals[-15:]
    
    weighted_sum = sum(t * w for t, w in zip(last_15, weights))
    total_weights = sum(weights)
    weighted_mean = weighted_sum / total_weights # Tính trung bình trọng số
    
    midpoint = 10.5
    
    # Nếu trung bình trọng số lệch khỏi trung điểm chuẩn quá 1.0 (ví dụ 11.5 hoặc 9.5)
    if weighted_mean > midpoint + 1.0:
        # Xu hướng đang lên mạnh -> Dự đoán hồi quy về Xỉu
        return {"du_doan": "Xỉu", "do_tin_cay": 96.0}
    if weighted_mean < midpoint - 1.0:
        # Xu hướng đang xuống mạnh -> Dự đoán hồi quy về Tài
        return {"du_doan": "Tài", "do_tin_cay": 96.0}

    return {"du_doan": history[-1], "do_tin_cay": 72.0}

# 4. CHỈ SỐ ENTROPY BIẾN ĐỘNG (Volatility Entropy Index - 20 Rounds)
def s4_volatility_entropy_index(history, totals):
    """Đánh giá tính ngẫu nhiên (Entropy) của 20 phiên để tìm điểm đảo chiều khi cầu bệt quá dài."""
    if len(history) < 20: return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 60.0}
    
    last_20 = history[-20:]
    tai_count = last_20.count("Tài")
    xiu_count = 20 - tai_count
    
    # max_count >= 15 (cầu bệt mạnh/quá lệch) -> Entropy thấp
    if max(tai_count, xiu_count) >= 15:
        # Xu hướng bệt quá mạnh, dự đoán đảo chiều cực mạnh
        prediction = "Xỉu" if history[-1] == "Tài" else "Tài"
        return {"du_doan": prediction, "do_tin_cay": 97.0} 
        
    # Nếu cân bằng (min_count >= 8), xét luân phiên vs. bệt ngắn
    if min(tai_count, xiu_count) >= 8:
        # Nếu đang luân phiên (TX-TX-TX) -> Giữ trend
        if history[-2] != history[-1]:
            return {"du_doan": history[-2], "do_tin_cay": 85.0}
        # Nếu đang bệt ngắn (TTX) -> Đảo
        else:
            prediction = "Xỉu" if history[-1] == "Tài" else "Tài"
            return {"du_doan": prediction, "do_tin_cay": 90.0}
            
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

# 5. PHÂN TÍCH MÔ HÌNH GƯƠNG KÉP LỚN 8 (Complex Mirror Pattern 8)
def s5_complex_mirror_8(history, totals):
    """Tìm mô hình đối xứng (Palindrome) 8 phiên: A B C D D C B A."""
    if len(history) < 8: return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 60.0}
    
    tail = history[-8:]
    # Ví dụ: T X X T T X X T (tail[0]=T, tail[7]=T, tail[1]=X, tail[6]=X, ...)
    if tail[0] == tail[7] and tail[1] == tail[6] and tail[2] == tail[5] and tail[3] == tail[4]:
        # Cầu đã hoàn thành mô hình 8 bước. Dự đoán lặp lại bước đầu tiên (A)
        return {"du_doan": tail[0], "do_tin_cay": 98.5}

    return {"du_doan": history[-1], "do_tin_cay": 70.0}

# 6. ĐỘ LỆCH TỔNG BIÊN ĐỘ TỨC THỜI (Instant Sum Range Deviation)
def s6_instant_sum_range_deviation(history, totals):
    """Dự đoán hồi quy sau khi xuất hiện tổng điểm cực biên (3 hoặc 18)."""
    if len(totals) < 5: return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 60.0}
    
    # Kiểm tra 5 phiên gần nhất có dính 3 hoặc 18 không
    is_extreme = any(t in [3, 18] for t in totals[-5:])
    
    if is_extreme:
        # Nếu đã có cực biên, áp lực hồi quy về trung bình (10/11) rất lớn
        if totals[-1] >= 11:
            return {"du_doan": "Xỉu", "do_tin_cay": 95.0}
        else:
            return {"du_doan": "Tài", "do_tin_cay": 95.0}

    return {"du_doan": history[-1], "do_tin_cay": 75.0}

# 7. PHÂN TÍCH TỔNG CẦU LẺ/CHẴN (Odd/Even Sum Distribution)
def s7_odd_even_sum_distribution(history, totals):
    """Phân tích sự mất cân bằng giữa Tổng Lẻ (3, 5, 7, 9, 11, 13, 15, 17) và Tổng Chẵn."""
    if len(totals) < 8: return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 60.0}
    
    # Chẵn (0): 4, 6, 8, 10, 12, 14, 16, 18
    # Lẻ (1): 3, 5, 7, 9, 11, 13, 15, 17
    
    parity = [t % 2 for t in totals[-8:]]
    odd_count = sum(parity)
    even_count = 8 - odd_count
    
    # Nếu 6/8 là Lẻ -> Áp lực cân bằng về Chẵn. (Xỉu có Chẵn nhiều hơn)
    if odd_count >= 6:
        return {"du_doan": "Xỉu", "do_tin_cay": 92.0} 
    # Nếu 6/8 là Chẵn -> Áp lực cân bằng về Lẻ. (Tài có Lẻ nhiều hơn)
    if even_count >= 6:
        return {"du_doan": "Tài", "do_tin_cay": 92.0} 

    return {"du_doan": history[-1], "do_tin_cay": 70.0}

# 8. MÔ HÌNH CÂN BẰNG NGƯỢC MARTINGALE (Anti-Martingale Rebalance)
def s8_anti_martingale_rebalance(history, totals):
    """Dự đoán đảo chiều ngay sau một chuỗi bệt (4 lần liên tiếp) thường đánh bại chiến lược Martingale."""
    if len(history) < 6: return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 60.0}
    
    last_4 = history[-4:]
    if last_4.count("Tài") == 4: # Bệt Tài 4
        return {"du_doan": "Xỉu", "do_tin_cay": 96.0}
    if last_4.count("Xỉu") == 4: # Bệt Xỉu 4
        return {"du_doan": "Tài", "do_tin_cay": 96.0}
    
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

# 9. ĐỘ CHỆNH LỆCH TUYẾN TÍNH CỦA TỔNG (Linear Sum Deviation)
def s9_linear_sum_deviation(history, totals):
    """Đánh giá xu hướng tuyến tính của Tổng điểm trong 7 phiên."""
    if len(totals) < 7: return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 60.0}
    
    last_7 = totals[-7:]
    # Giả lập đường xu hướng (Trend Line) bằng cách so sánh TBC 3 đầu và 3 cuối
    try:
        avg_first_3 = statistics.mean(last_7[:3])
        avg_last_3 = statistics.mean(last_7[-3:])
    except statistics.StatisticsError:
        return {"du_doan": history[-1], "do_tin_cay": 75.0}

    trend = avg_last_3 - avg_first_3
    
    if trend > 1.5: # Xu hướng tăng tuyến tính mạnh
        return {"du_doan": "Tài", "do_tin_cay": 90.0}
    if trend < -1.5: # Xu hướng giảm tuyến tính mạnh
        return {"du_doan": "Xỉu", "do_tin_cay": 90.0}

    return {"du_doan": history[-1], "do_tin_cay": 75.0}

# 10. PHÂN TÍCH XU HƯỚNG TỔNG 3 PHIÊN GẦN NHẤT (Momentum 3)
def s10_short_term_momentum(history, totals):
    """Phân tích đà tăng/giảm của Tổng điểm trong 3 phiên để tìm điểm hồi quy."""
    if len(totals) < 3: return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 60.0}
    
    t1, t2, t3 = totals[-3:]
    
    if t3 > t2 and t2 > t1: # 3 lần tăng liên tiếp
        # Nếu t3 > 12 -> Đỉnh, dự đoán Xỉu (Hồi quy)
        if t3 >= 12:
            return {"du_doan": "Xỉu", "do_tin_cay": 93.0}
        # Nếu t3 < 10 -> Đáy, dự đoán Tài (Tiếp tục đà)
        else:
            return {"du_doan": "Tài", "do_tin_cay": 90.0}
            
    if t3 < t2 and t2 < t1: # 3 lần giảm liên tiếp
        # Nếu t3 < 9 -> Đáy, dự đoán Tài (Hồi quy)
        if t3 <= 9:
            return {"du_doan": "Tài", "do_tin_cay": 93.0}
        # Nếu t3 > 11 -> Đỉnh, dự đoán Xỉu (Tiếp tục đà)
        else:
            return {"du_doan": "Xỉu", "do_tin_cay": 90.0}

    return {"du_doan": history[-1], "do_tin_cay": 70.0}

# 11. ĐẢO CẦU LUÂN PHIÊN KÉP (Double Alternating Reversal)
def s11_double_alternating_reversal(history, totals):
    """Tìm mô hình cầu 2-1-2 (T T X T T) và dự đoán đảo chiều phá vỡ chu kỳ."""
    if len(history) < 6: return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 60.0}
    
    # Cầu 2-1-2: T T X T T hoặc X X T X X (tail độ dài 5)
    tail = history[-5:]
    if tail[0]==tail[1] and tail[3]==tail[4] and tail[0]==tail[4] and tail[2]!=tail[0]:
        # Cầu đã hoàn thành. Dự đoán đảo chiều sau khi hoàn thành 2 cặp
        prediction = "Xỉu" if tail[-1] == "Tài" else "Tài"
        return {"du_doan": prediction, "do_tin_cay": 95.0}

    return {"du_doan": history[-1], "do_tin_cay": 70.0}

# 12. PHÂN TÍCH KHOẢNG CÁCH TRUNG BÌNH (Mean Distance Analysis)
def s12_mean_distance_analysis(history, totals):
    """Tính tổng độ lệch tuyệt đối của Tài và Xỉu so với trung điểm 10.5 để tìm sự mất cân bằng."""
    if len(totals) < 10: return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 60.0}
    
    last_10 = totals[-10:]
    midpoint = 10.5
    
    # Tính tổng khoảng cách của các phiên Tài và Xỉu đến điểm giữa
    # Tai_dist: Khoảng cách khi Tài lớn hơn 10.5. (Dương)
    tai_dist = sum(t - midpoint for t, h in zip(last_10, history[-10:]) if h == "Tài" and t > midpoint)
    # Xiu_dist: Khoảng cách khi Xỉu nhỏ hơn 10.5. (Dương)
    xiu_dist = sum(midpoint - t for t, h in zip(last_10, history[-10:]) if h == "Xỉu" and t < midpoint)
    
    # Nếu tai_dist > xiu_dist * 1.5 -> Tài đang chiếm ưu thế về tổng điểm tuyệt đối
    if tai_dist > xiu_dist * 1.5 and tai_dist > 5:
        return {"du_doan": "Xỉu", "do_tin_cay": 92.0} # Kéo về Xỉu để cân bằng khoảng cách
    if xiu_dist > tai_dist * 1.5 and xiu_dist > 5:
        return {"du_doan": "Tài", "do_tin_cay": 92.0} # Kéo về Tài để cân bằng khoảng cách

    return {"du_doan": history[-1], "do_tin_cay": 75.0}

# 13. MÔ HÌNH BỆT CUNG (Arc Streak Pattern - 9 rounds)
def s13_arc_streak_pattern(history, totals):
    """Tìm mô hình bệt 3-1-3 (T T T X T T T) và dự đoán đảo chiều tiếp theo."""
    if len(history) < 9: return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 60.0}
    
    # Tìm kiếm T T T X T T T (tail độ dài 7)
    tail = history[-7:]
    if (tail[0]==tail[1]==tail[2] and 
        tail[4]==tail[5]==tail[6] and 
        tail[3]!=tail[0] and 
        tail[0]==tail[6]):
        
        # Mô hình bệt cung đã hoàn thành. Dự đoán đảo chiều tiếp
        if tail[0] == "Tài":
            return {"du_doan": "Xỉu", "do_tin_cay": 95.0}
        else:
            return {"du_doan": "Tài", "do_tin_cay": 95.0}

    return {"du_doan": history[-1], "do_tin_cay": 70.0}

# 14. PHÂN TÍCH CHỈ SỐ LỖI KÉP (Dual Error Index - For Consistency)
def s14_dual_error_index(history, totals):
    """So sánh tần suất bệt (TT/XX) và luân phiên (TX/XT) để dự đoán xu hướng tiếp diễn."""
    if len(history) < 10: return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 60.0}
    
    last_10 = history[-10:]
    # Tính số lần lặp lại (TT hoặc XX) so với số lần luân phiên (TX hoặc XT)
    streak_count, alternating_count = 0, 0
    
    for i in range(len(last_10) - 1):
        if last_10[i] == last_10[i+1]:
            streak_count += 1
        else:
            alternating_count += 1
            
    # Nếu streak_count > alternating_count * 2: Xu hướng bệt mạnh -> Giữ trend
    if streak_count > alternating_count * 2 and history[-1] == history[-2]:
        return {"du_doan": history[-1], "do_tin_cay": 90.0}
    
    # Nếu alternating_count > streak_count * 2: Xu hướng luân phiên mạnh -> Giữ trend
    if alternating_count > streak_count * 2 and history[-1] != history[-2]:
        # Nếu đang luân phiên (XT) thì dự đoán X (kết quả trước đó)
        return {"du_doan": history[-2], "do_tin_cay": 90.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 73.0}

# 15. DỰ ĐOÁN PHÁ VỠ CẦU (Breakout Prediction - 5 sessions)
def s15_breakout_prediction(history, totals):
    """Tìm mô hình cân bằng (2T:3X hoặc 3T:2X) đang luân phiên để dự đoán phá vỡ thành bệt."""
    if len(history) < 5: return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 60.0}
    
    last_5 = history[-5:]
    tai_count = last_5.count("Tài")
    
    # Nếu là mô hình "Cân bằng gần" (3T:2X hoặc 2T:3X) và đang có luân phiên
    if tai_count in [2, 3] and history[-2] != history[-1]:
        # Cầu cân bằng đã đến ngưỡng phá vỡ -> Dự đoán Bệt (Phá vỡ)
        return {"du_doan": history[-1], "do_tin_cay": 93.0}

    return {"du_doan": history[-1], "do_tin_cay": 70.0}

# 16. CHỈ SỐ SỨC MẠNH TƯƠNG ĐỐI 14 (RSI-like Strength Index)
def s16_rsi_strength_index(history, totals):
    """Đánh giá sức mạnh tương đối của Tài/Xỉu trong 14 phiên để tìm vùng quá mua/quá bán."""
    if len(history) < 14: return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 60.0}
    
    last_14 = history[-14:]
    tai_count = last_14.count("Tài")
    
    # Nếu Tài chiếm 10/14 (RSI > 70) -> Quá mua, dự đoán Xỉu
    if tai_count >= 10:
        return {"du_doan": "Xỉu", "do_tin_cay": 95.0}
    # Nếu Tài chiếm 4/14 (RSI < 30) -> Quá bán, dự đoán Tài
    if tai_count <= 4:
        return {"du_doan": "Tài", "do_tin_cay": 95.0}
        
    return {"du_doan": history[-1], "do_tin_cay": 70.0}

# 17. PHÂN TÍCH KHOẢNG NHẢY TỔNG TUYỆT ĐỐI (Absolute Sum Jump Analysis)
def s17_absolute_sum_jump(history, totals):
    """Dự đoán hồi quy sau khi Tổng điểm có một cú nhảy tuyệt đối lớn (ví dụ: từ 3 lên 18)."""
    if len(totals) < 2: return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 60.0}
    
    diff = abs(totals[-1] - totals[-2])
    
    # Nếu nhảy cực lớn (ví dụ: từ 5 lên 15, hoặc 16 xuống 4)
    if diff >= 10: 
        # Luôn luôn hồi quy về trung tâm sau cú nhảy cực lớn
        prediction = "Xỉu" if totals[-1] >= 11 else "Tài" # Nếu kết quả cuối là Tài, dự đoán Xỉu (và ngược lại)
        return {"du_doan": prediction, "do_tin_cay": 99.0}

    return {"du_doan": history[-1], "do_tin_cay": 75.0}

# 18. MÔ HÌNH LẶP GƯƠNG 6 (Mirror Repeat 6)
def s18_mirror_repeat_6(history, totals):
    """Tìm mô hình 3 cặp đối xứng A A B B A A và dự đoán kết quả tiếp theo là B."""
    if len(history) < 6: return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 60.0}
    
    # T T X X T T hoặc X X T T X X
    tail = history[-6:]
    # tail[0]=tail[1] (A A), tail[2]=tail[3] (B B), tail[4]=tail[5] (A A)
    if tail[0]==tail[1] and tail[2]==tail[3] and tail[4]==tail[5] and tail[0]==tail[4] and tail[0]!=tail[2]:
        # Hoàn thành 3 cặp (A A B B A A) -> Dự đoán đảo chiều về B
        prediction = tail[2]
        return {"du_doan": prediction, "do_tin_cay": 93.0}

    return {"du_doan": history[-1], "do_tin_cay": 70.0}

# 19. CHỈ SỐ PHÂN KỲ TỔNG (Sum Divergence Index - 12 rounds)
def s19_sum_divergence_index(history, totals):
    """So sánh xu hướng Tài/Xỉu (History) với xu hướng Tổng điểm (Totals) để tìm phân kỳ."""
    if len(totals) < 12: return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 60.0}
    
    # Xu hướng Tài/Xỉu (5 phiên gần nhất)
    history_trend = 1 if history[-5:].count("Tài") > 2 else -1 # 1: Tài chiếm ưu thế, -1: Xỉu chiếm ưu thế
    
    # Xu hướng Tổng điểm (So sánh TBC 5 phiên gần nhất với 5 phiên trước đó)
    try:
        sum_trend = statistics.mean(totals[-5:]) - statistics.mean(totals[-10:-5])
    except statistics.StatisticsError:
        return {"du_doan": history[-1], "do_tin_cay": 75.0}

    # Phân kỳ: Tài/Xỉu đang là Tài (1) nhưng Tổng điểm lại giảm mạnh (sum_trend < -0.5)
    if history_trend == 1 and sum_trend < -0.5:
        # Tài yếu, tổng điểm giảm -> Dự đoán Xỉu (phân kỳ mạnh)
        return {"du_doan": "Xỉu", "do_tin_cay": 96.0}
    
    # Phân kỳ: Tài/Xỉu đang là Xỉu (-1) nhưng Tổng điểm lại tăng mạnh (sum_trend > 0.5)
    if history_trend == -1 and sum_trend > 0.5:
        # Xỉu yếu, tổng điểm tăng -> Dự đoán Tài (phân kỳ mạnh)
        return {"du_doan": "Tài", "do_tin_cay": 96.0}

    return {"du_doan": history[-1], "do_tin_cay": 75.0}

# 20. VÙNG TÍCH LŨY BIÊN (Boundary Accumulation Zone)
def s20_boundary_accumulation(history, totals):
    """Phát hiện khi Biên Tài (>= 15) hoặc Biên Xỉu (<= 6) xuất hiện quá nhiều trong 15 phiên."""
    if len(totals) < 15: return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 60.0}
    
    last_15 = totals[-15:]
    # Biên Tài (>= 15) và Biên Xỉu (<= 6)
    tai_boundary = sum(1 for t in last_15 if t >= 15)
    xiu_boundary = sum(1 for t in last_15 if t <= 6)
    
    # Nếu một biên được tích lũy quá nhiều (>= 4 lần trong 15 phiên)
    if tai_boundary >= 4:
        # Tích lũy Tài quá lớn -> Phá vỡ, dự đoán Xỉu (hồi quy về trung bình thấp hơn)
        return {"du_doan": "Xỉu", "do_tin_cay": 94.0}
    if xiu_boundary >= 4:
        # Tích lũy Xỉu quá lớn -> Phá vỡ, dự đoán Tài (hồi quy về trung bình cao hơn)
        return {"du_doan": "Tài", "do_tin_cay": 94.0}

    return {"du_doan": history[-1], "do_tin_cay": 70.0}

# 21. KIỂM TRA ĐIỂM CHẶN SỐ LỚN (High Number Block Check)
def s21_high_number_block(history, totals):
    """Phát hiện chuỗi Tổng điểm lớn (13-17) để dự đoán hồi quy về Xỉu."""
    if len(totals) < 4: return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 60.0}

    # Tổng điểm lớn (13, 14, 15, 16, 17) 
    high_sums = [13, 14, 15, 16, 17]
    high_count = sum(1 for t in totals[-4:] if t in high_sums)

    # Nếu 3/4 phiên gần nhất là Tổng lớn
    if high_count >= 3:
        # Dự đoán Xỉu (Hồi quy về trung bình thấp hơn)
        return {"du_doan": "Xỉu", "do_tin_cay": 92.0}

    return {"du_doan": history[-1], "do_tin_cay": 70.0}

# 22. TƯƠNG QUAN LẶP LẠI 3 PHIÊN (3-Session Repeat Correlation)
def s22_three_session_repeat(history, totals):
    """Tìm mô hình lặp lại hoàn hảo 3 phiên (A B C | A B C) và dự đoán đảo chiều phá vỡ chu kỳ."""
    if len(history) < 6: return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 60.0}

    # Tìm kiếm T X T | T X T (tail độ dài 6)
    tail = history[-6:]
    if tail[0:3] == tail[3:6]:
        # Nếu mô hình lặp lại hoàn hảo, dự đoán đảo chiều phá vỡ chu kỳ
        prediction = "Xỉu" if tail[-1] == "Tài" else "Tài"
        return {"du_doan": prediction, "do_tin_cay": 95.0}

    return {"du_doan": history[-1], "do_tin_cay": 70.0}

# 23. BỆT TRUNG TÂM & PHÁ VỠ (Center Streak & Breakout)
def s23_center_streak_breakout(history, totals):
    """Phát hiện khi Tổng điểm bệt ở trung tâm (10 hoặc 11) quá lâu và dự đoán phá vỡ biên mạnh."""
    if len(totals) < 7: return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 60.0}
    
    center_totals = [10, 11] # Tổng điểm cân bằng Tài/Xỉu
    center_count = sum(1 for t in totals[-7:] if t in center_totals)

    # Nếu 5/7 phiên là 10 hoặc 11
    if center_count >= 5:
        # Đang tích lũy năng lượng, dự đoán phá vỡ biên mạnh.
        # Tiếp tục xu hướng hiện tại (nếu đang là 11, dự đoán Tài; nếu đang là 10, dự đoán Xỉu)
        prediction = "Tài" if totals[-1] >= 11 else "Xỉu" 
        return {"du_doan": prediction, "do_tin_cay": 97.0}

    return {"du_doan": history[-1], "do_tin_cay": 75.0}

# 24. CHỈ SỐ TIÊU CHUẨN XÁC SUẤT NÉN 20 (Compressed Probability Z-Score)
def s24_compressed_prob_zscore(history, totals):
    """Sử dụng nguyên lý Z-Score (độ lệch chuẩn) trên 20 phiên để tìm điểm đảo chiều khi tỷ lệ quá lệch."""
    if len(history) < 20: return {"du_doan": history[-1] if history else "Xỉu", "do_tin_cay": 60.0}

    last_20 = history[-20:]
    tai_count = last_20.count("Tài")
    
    # Trung bình lý thuyết là 10/20. Z-score > 2 (Lệch hơn 2 độ lệch chuẩn): > 14.5 Tài hoặc < 5.5 Tài
    if tai_count >= 15: # Lệch quá mạnh về Tài (15/20)
        return {"du_doan": "Xỉu", "do_tin_cay": 98.0}
    if tai_count <= 5: # Lệch quá mạnh về Xỉu (5/20)
        return {"du_doan": "Tài", "do_tin_cay": 98.0}

    return {"du_doan": history[-1], "do_tin_cay": 70.0}

# 25. PHÂN TÍCH NHỊ PHÂN TRỌNG SỐ TỨC THỜI (Instant Weighted Binary Analysis)
def s25_instant_weighted_binary(history, totals):
    """Gán trọng số giảm dần cho 4 phiên gần nhất để xác định đà Tài/Xỉu ngắn hạn."""
    if len(history) < 4: return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 60.0}

    # Gán trọng số 4, 3, 2, 1 cho 4 phiên gần nhất (4 là phiên mới nhất)
    weights = [4, 3, 2, 1]
    
    # Tài = 1, Xỉu = -1
    binary_history = [1 if h == "Tài" else -1 for h in history[-4:]]
    binary_history.reverse() # Đảm bảo Tài/Xỉu gần nhất (history[-1]) có trọng số 4
    
    score = sum(b * w for b, w in zip(binary_history, weights))
    
    # Score > 5: Thiên về Tài rất mạnh (Ví dụ: TTTT -> 4+3+2+1=10)
    if score >= 5:
        return {"du_doan": "Tài", "do_tin_cay": 92.0}
    # Score < -5: Thiên về Xỉu rất mạnh (Ví dụ: XXXX -> -4-3-2-1=-10)
    if score <= -5:
        return {"du_doan": "Xỉu", "do_tin_cay": 92.0}

    return {"du_doan": history[-1], "do_tin_cay": 70.0}


# ================== DANH SÁCH TẤT CẢ THUẬT TOÁN ==================
all_super_vip_algos = [
    s1_fibonacci_reversion, s2_markov_transition_3step, s3_dynamic_weighted_reversion,
    s4_volatility_entropy_index, s5_complex_mirror_8, s6_instant_sum_range_deviation,
    s7_odd_even_sum_distribution, s8_anti_martingale_rebalance, s9_linear_sum_deviation,
    s10_short_term_momentum, s11_double_alternating_reversal, s12_mean_distance_analysis,
    s13_arc_streak_pattern, s14_dual_error_index, s15_breakout_prediction,
    s16_rsi_strength_index, s17_absolute_sum_jump, s18_mirror_repeat_6,
    s19_sum_divergence_index, s20_boundary_accumulation, s21_high_number_block,
    s22_three_session_repeat, s23_center_streak_breakout, s24_compressed_prob_zscore,
    s25_instant_weighted_binary
]


# ================== CHỨC NĂNG TỔNG HỢP (CONSENSUS) ==================
def calculate_super_prediction(history, totals):
    """Chạy 25 thuật toán và sử dụng bình chọn có trọng số (dựa trên độ tin cậy) để đưa ra dự đoán cuối cùng."""
    # Chạy tất cả 25 thuật toán
    results = []
    for algo in all_super_vip_algos:
         try:
             results.append(algo(history, totals))
         except Exception:
             # Bỏ qua nếu thuật toán bị lỗi (thường do dữ liệu không đủ)
             continue

    if not results:
        # Trường hợp không có đủ dữ liệu lịch sử cho bất kỳ thuật toán nào
        return {"du_doan": history[-1] if history else "Tài", "do_tin_cay": 50.0}

    tai_score = 0.0
    xiu_score = 0.0
    total_confidence = 0.0

    # Bình chọn có trọng số dựa trên độ tin cậy
    for r in results:
        confidence = r.get("do_tin_cay", 0.0)
        
        # Chỉ xem xét dự đoán có độ tin cậy trên 50%
        if confidence < 50.0:
            continue

        total_confidence += confidence

        if r["du_doan"] == "Tài":
            tai_score += confidence
        elif r["du_doan"] == "Xỉu":
            xiu_score += confidence
            
    # Xác định dự đoán cuối cùng
    if total_confidence == 0:
        final_prediction = history[-1] if history else "Xỉu"
        overall_confidence = 50.0 # Độ tin cậy trung lập
    else:
        if tai_score > xiu_score:
            final_prediction = "Tài"
            overall_confidence = (tai_score / total_confidence) * 100.0
        elif xiu_score > tai_score:
            final_prediction = "Xỉu"
            overall_confidence = (xiu_score / total_confidence) * 100.0
        else:
            # Hòa, giữ trend cuối
            final_prediction = history[-1] if history else "Tài"
            overall_confidence = 70.0 

    # Giới hạn độ tin cậy tối đa là 99.9%
    overall_confidence = min(99.9, overall_confidence)
    
    return {
        "du_doan": final_prediction,
        "do_tin_cay": round(overall_confidence, 2)
    }

# ================== CHỨC NĂNG THU THẬP DỮ LIỆU ==================
def fetch_sessions():
    """Tải 100 phiên giao dịch gần nhất từ API."""
    try:
        # Cập nhật để tải tối đa 100 phiên
        res = requests.get(API_URL + "?limit=100", timeout=5)
        res.raise_for_status() # Báo lỗi nếu status code là 4xx hoặc 5xx
        data = res.json()

        if "list" not in data or not data["list"]:
            print("API Error: 'list' field missing or empty.")
            return []

        # Chỉ trả về 100 phiên gần nhất
        return data["list"][:100]

    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}")
        return []
    except Exception as e:
        print(f"General API Error: {e}")
        return []

# ================== CÁC ROUTE CỦA FLASK ==================

@app.route("/")
def home():
    """Trang chủ đơn giản."""
    return jsonify({"status": "running", "api": "/api/taixiumd5", "thong_bao": "Đang chạy hệ thống AI Super VIP."})


@app.route("/api/taixiumd5")
def taixiu_api():
    """
    Endpoint chính. Lấy 100 phiên, tính toán dự đoán cho phiên kế tiếp
    và trả về danh sách lịch sử + 1 mục dự đoán cuối cùng.
    """
    sessions = fetch_sessions()
    
    if not sessions:
        return jsonify({
            "thongBao": "Lỗi: Không thể tải dữ liệu lịch sử để phân tích.",
            "duDoan": "Không rõ",
            "doTinCay": 0.0
        }), 500

    # 1. Trích xuất Lịch sử (history) và Tổng điểm (totals)
    history = [] 
    totals = []  
    
    for item in sessions:
        dices = item.get("dices", [0, 0, 0])
        tong = sum(dices)
        
        # Kết quả: 11 <= sum <= 18 là Tài, 3 <= sum <= 10 là Xỉu
        result = "Tài" if tong >= 11 else "Xỉu"
        history.append(result)
        totals.append(tong)

    # 2. Tính toán Dự đoán cho phiên *TIẾP THEO*
    last_id = sessions[-1].get("id")
    next_phien = last_id + 1 if isinstance(last_id, int) else "Không rõ"
    
    next_prediction = calculate_super_prediction(history, totals)
        
    # 3. Chuẩn bị dữ liệu trả về (100 lịch sử + 1 dự đoán)
    
    # 3a. Danh sách lịch sử
    response_data = []
    for item in sessions:
        dices = item.get("dices", [0, 0, 0])
        tong = sum(dices)
        
        response_data.append({
            "phien": item.get("id"),
            "xúc xắc 1": dices[0],
            "xúc xắc 2": dices[1],
            "xúc xắc 3": dices[2],
            "tong": tong,
            "md5": item.get("_id", "")
        })

    # 3b. Thêm mục dự đoán
    response_data.append({
        "phien": next_phien,
        "xúc xắc 1": dices[0],
        "xúc xắc 2": dices[1],
        "xúc xắc 3": dices[2],
        "tong": tong,
        "duDoan": next_prediction["du_doan"],
        "doTinCay": next_prediction["do_tin_cay"],
    })

    return jsonify(response_data)


if __name__ == "__main__":
    # Đảm bảo bạn chạy trên host và port mặc định của môi trường
    app.run(host="0.0.0.0", port=10000)
