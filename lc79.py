from flask import Flask, jsonify
import requests
import time
import threading
from collections import deque, defaultdict
import os
import math
import hashlib
from typing import List, Tuple

app = Flask(__name__)

# =========================================================
# 💾 Bộ nhớ tạm – lưu trữ lịch sử phiên
# =========================================================
history = deque(maxlen=1000)
totals = deque(maxlen=1000)
last_data = {
    "phien": None,
    "xucxac1": 0,
    "xucxac2": 0,
    "xucxac3": 0,
    "tong": 0,
    "ketqua": "",
    "du_doan": "Chờ dữ liệu...",
    "do_tin_cay": 0,
    "id": "trí tuệ ai 2025"
}

# =========================================================
# 🔷 bản thuat toan ai cua tuan anh - tri tue 2025
# =========================================================
class TaiXiuReal30Algorithms:
    """30 thuật toán thật - không random"""
    
    # === 30 REAL ALGORITHMS ===
    
    # 1. CORE PATTERN RECOGNITION
    @staticmethod
    def ALGO_01_pattern_continuation(history: List[str]) -> Tuple[str, float]:
        """Nhận diện pattern tiếp diễn"""
        if len(history) < 4: return 'T', 0.51
        
        # Tìm pattern 3 lần phổ biến nhất
        pattern_size = 3
        pattern_counts = defaultdict(int)
        
        for i in range(len(history) - pattern_size):
            pattern = ''.join(history[i:i+pattern_size])
            next_val = history[i+pattern_size]
            pattern_counts[f"{pattern}->{next_val}"] += 1
        
        current_pattern = ''.join(history[-pattern_size:])
        best_match = None
        max_count = 0
        
        for key, count in pattern_counts.items():
            if key.startswith(current_pattern + "->"):
                if count > max_count:
                    max_count = count
                    best_match = key.split('->')[1]
        
        if best_match and max_count >= 2:
            confidence = 0.58 + min(0.07, max_count * 0.01)
            return best_match, confidence
        
        return 'T', 0.52
    
    # 2. FREQUENCY BALANCE
    @staticmethod
    def ALGO_02_frequency_balance(history: List[str]) -> Tuple[str, float]:
        """Cân bằng tần suất"""
        if len(history) < 15: return 'T', 0.51
        
        tai_count = history.count('T')
        tai_ratio = tai_count / len(history)
        
        # Lý thuyết: T=0.4815, X=0.5185
        theoretical_tai = 104/216
        
        if tai_ratio > theoretical_tai + 0.08:
            confidence = 0.59 + min(0.06, (tai_ratio - theoretical_tai - 0.08) * 0.3)
            return 'X', confidence
        elif tai_ratio < theoretical_tai - 0.08:
            confidence = 0.59 + min(0.06, (theoretical_tai - tai_ratio - 0.08) * 0.3)
            return 'T', confidence
        
        return 'T', 0.53
    
    # 3. STREAK ANALYSIS
    @staticmethod
    def ALGO_03_streak_analysis(history: List[str]) -> Tuple[str, float]:
        """Phân tích chuỗi liên tiếp"""
        if len(history) < 6: return 'T', 0.51
        
        current_val = history[-1]
        streak_length = 1
        
        for i in range(2, min(7, len(history)) + 1):
            if history[-i] == current_val:
                streak_length += 1
            else:
                break
        
        if streak_length >= 5:
            return 'X' if current_val == 'T' else 'T', 0.64
        elif streak_length >= 4:
            return 'X' if current_val == 'T' else 'T', 0.60
        elif streak_length >= 3:
            return 'X' if current_val == 'T' else 'T', 0.57
        
        return current_val, 0.54
    
    # 4. SESSION TREND
    @staticmethod
    def ALGO_04_session_trend(history: List[str]) -> Tuple[str, float]:
        """Xu hướng session"""
        if len(history) < 20: return 'T', 0.51
        
        session_size = 10
        num_sessions = len(history) // session_size
        
        if num_sessions >= 2:
            # Session hiện tại
            current_session = history[-session_size:]
            tai_current = current_session.count('T')
            
            # Session trước
            prev_session = history[-(session_size*2):-session_size]
            tai_prev = prev_session.count('T')
            
            if tai_prev >= 8 and tai_current <= 3:
                # Đã đảo chiều mạnh
                return 'X', 0.62
            elif tai_prev <= 3 and tai_current >= 8:
                return 'T', 0.62
            elif tai_current > tai_prev + 2:
                return 'T', 0.57
            elif tai_current < tai_prev - 2:
                return 'X', 0.57
        
        return 'T', 0.53
    
    # 5. MOMENTUM DETECTION
    @staticmethod
    def ALGO_05_momentum_detection(history: List[str]) -> Tuple[str, float]:
        """Phát hiện động lượng"""
        if len(history) < 10: return 'T', 0.51
        
        # Tính momentum 5 phiên gần nhất
        momentum = 0
        for i in range(1, 6):
            if i < len(history):
                if history[-i] == 'T':
                    momentum += 1
                else:
                    momentum -= 1
        
        if momentum >= 4:
            return 'T', 0.59
        elif momentum <= -4:
            return 'X', 0.59
        elif momentum >= 2:
            return 'T', 0.56
        elif momentum <= -2:
            return 'X', 0.56
        
        return 'T', 0.53
    
    # 6. VOLATILITY ADAPTIVE
    @staticmethod
    def ALGO_06_volatility_adaptive(history: List[str]) -> Tuple[str, float]:
        """Thích ứng biến động"""
        if len(history) < 12: return 'T', 0.51
        
        # Tính volatility
        changes = 0
        for i in range(1, 12):
            if i < len(history):
                if history[-i] != history[-(i+1)]:
                    changes += 1
        
        volatility = changes / 11
        
        if volatility > 0.7:
            # High volatility -> reversal
            next_val = 'X' if history[-1] == 'T' else 'T'
            confidence = 0.58 + min(0.05, (volatility - 0.7) * 0.1)
            return next_val, confidence
        elif volatility < 0.3:
            # Low volatility -> continuation
            confidence = 0.60 + min(0.05, (0.3 - volatility) * 0.2)
            return history[-1], confidence
        
        return 'T', 0.54
    
    # 7. BINARY SEQUENCE
    @staticmethod
    def ALGO_07_binary_sequence(history: List[str]) -> Tuple[str, float]:
        """Chuỗi nhị phân"""
        if len(history) < 8: return 'T', 0.51
        
        binary = ''.join(['1' if h == 'T' else '0' for h in history])
        
        if len(binary) >= 8:
            last_8 = binary[-8:]
            
            # Kiểm tra các pattern đặc biệt
            if '11111' in last_8:
                return 'X', 0.63
            elif '00000' in last_8:
                return 'T', 0.63
            
            ones = last_8.count('1')
            if ones >= 6:
                return 'X', 0.58
            elif ones <= 2:
                return 'T', 0.58
        
        return 'T', 0.52
    
    # 8. WEIGHTED MEMORY
    @staticmethod
    def ALGO_08_weighted_memory(history: List[str]) -> Tuple[str, float]:
        """Bộ nhớ có trọng số"""
        if not history: return 'T', 0.50
        
        total_weight = 0
        tai_weight = 0
        
        # Trọng số giảm dần theo hàm mũ
        for i, result in enumerate(reversed(history)):
            weight = 1.0 / (1.5 ** i)  # Exponential decay
            total_weight += weight
            
            if result == 'T':
                tai_weight += weight
        
        tai_ratio = tai_weight / total_weight
        
        if tai_ratio > 0.55:
            confidence = 0.57 + min(0.04, (tai_ratio - 0.55) * 0.3)
            return 'T', confidence
        elif tai_ratio < 0.45:
            confidence = 0.57 + min(0.04, (0.45 - tai_ratio) * 0.3)
            return 'X', confidence
        
        return 'T', 0.53
    
    # 9. CYCLE PREDICTION
    @staticmethod
    def ALGO_09_cycle_prediction(history: List[str]) -> Tuple[str, float]:
        """Dự đoán chu kỳ"""
        if len(history) < 15: return 'T', 0.51
        
        # Tìm chu kỳ từ 2 đến 5
        for cycle_len in range(2, 6):
            if len(history) >= cycle_len * 3:
                # Kiểm tra 3 chu kỳ liên tiếp
                cycle1 = history[-cycle_len*3:-cycle_len*2]
                cycle2 = history[-cycle_len*2:-cycle_len]
                cycle3 = history[-cycle_len:]
                
                if cycle1 == cycle2 == cycle3:
                    # Tìm thấy chu kỳ
                    return cycle1[0], 0.68
        
        # Kiểm tra pattern ABAB
        if len(history) >= 8:
            last_8 = history[-8:]
            if (last_8[0] == last_8[2] == last_8[4] == last_8[6] and
                last_8[1] == last_8[3] == last_8[5] == last_8[7]):
                return last_8[0], 0.64
        
        return 'T', 0.52
    
    # 10. ENTROPY OPTIMIZATION
    @staticmethod
    def ALGO_10_entropy_optimization(history: List[str]) -> Tuple[str, float]:
        """Tối ưu entropy"""
        if len(history) < 10: return 'T', 0.51
        
        def calculate_entropy(seq):
            t_count = seq.count('T')
            p_t = t_count / len(seq)
            p_x = 1 - p_t
            
            entropy = 0
            if p_t > 0:
                entropy -= p_t * math.log2(p_t + 1e-10)
            if p_x > 0:
                entropy -= p_x * math.log2(p_x + 1e-10)
            return entropy
        
        current_entropy = calculate_entropy(history)
        
        # Tính entropy cho cả hai khả năng
        entropy_if_t = calculate_entropy(history + ['T'])
        entropy_if_x = calculate_entropy(history + ['X'])
        
        # Chọn khả năng giảm entropy nhiều nhất
        reduction_t = current_entropy - entropy_if_t
        reduction_x = current_entropy - entropy_if_x
        
        if reduction_t > reduction_x:
            confidence = 0.56 + min(0.06, reduction_t * 1.8)
            return 'T', confidence
        else:
            confidence = 0.56 + min(0.06, reduction_x * 1.8)
            return 'X', confidence
    
    # 11. MARKOV CHAIN
    @staticmethod
    def ALGO_11_markov_chain(history: List[str]) -> Tuple[str, float]:
        """Markov chain bậc 2"""
        if len(history) < 8: return 'T', 0.51
        
        transitions = defaultdict(lambda: {'T': 0, 'X': 0})
        
        for i in range(len(history) - 2):
            state = ''.join(history[i:i+2])
            next_val = history[i+2]
            transitions[state][next_val] += 1
        
        current_state = ''.join(history[-2:])
        
        if current_state in transitions:
            counts = transitions[current_state]
            total = counts['T'] + counts['X']
            
            if total >= 3:
                if counts['T'] > counts['X']:
                    ratio = counts['T'] / total
                    confidence = 0.58 + min(0.05, (ratio - 0.5) * 0.4)
                    return 'T', confidence
                else:
                    ratio = counts['X'] / total
                    confidence = 0.58 + min(0.05, (ratio - 0.5) * 0.4)
                    return 'X', confidence
        
        return 'T', 0.52
    
    # 12. FIBONACCI SUPPORT
    @staticmethod
    def ALGO_12_fibonacci_support(history: List[str]) -> Tuple[str, float]:
        """Hỗ trợ Fibonacci"""
        if len(history) < 13: return 'T', 0.51
        
        fib_levels = [1, 2, 3, 5, 8, 13]
        current_level = len(history) % len(fib_levels)
        fib_value = fib_levels[current_level]
        
        lookback = min(fib_value, len(history))
        segment = history[-lookback:]
        tai_ratio = segment.count('T') / lookback
        
        # Fibonacci retracement levels
        if tai_ratio > 0.618:  # 61.8%
            return 'X', 0.60
        elif tai_ratio < 0.382:  # 38.2%
            return 'T', 0.60
        elif tai_ratio > 0.5:
            return 'T', 0.56
        else:
            return 'X', 0.56
    
    # 13. TIME SIGNATURE
    @staticmethod
    def ALGO_13_time_signature(history: List[str]) -> Tuple[str, float]:
        """Chữ ký thời gian"""
        timestamp = int(time.time())
        
        # Sử dụng các digit của timestamp
        digits = [int(d) for d in str(timestamp) if d.isdigit()]
        digit_sum = sum(digits)
        
        if digit_sum % 7 == 0:
            return 'T', 0.55
        elif digit_sum % 5 == 0:
            return 'X', 0.55
        elif digit_sum % 3 == 0:
            return 'T', 0.53
        else:
            return 'X', 0.53
    
    # 14. LENGTH PATTERN
    @staticmethod
    def ALGO_14_length_pattern(history: List[str]) -> Tuple[str, float]:
        """Pattern độ dài"""
        length = len(history)
        
        if length % 7 == 0:
            return 'T', 0.55
        elif length % 11 == 0:
            return 'X', 0.55
        elif length % 4 == 0:
            # Kiểm tra số nguyên tố
            if length in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]:
                return 'T', 0.54
            else:
                return 'X', 0.54
        elif length % 3 == 0:
            return 'T', 0.53
        else:
            return 'X', 0.53
    
    # 15. HASH PREDICTION
    @staticmethod
    def ALGO_15_hash_prediction(history: List[str]) -> Tuple[str, float]:
        """Dự đoán từ hash"""
        if not history: return 'T', 0.50
        
        history_str = ''.join(history)
        hash_val = hashlib.md5(history_str.encode()).hexdigest()
        
        # Lấy 2 ký tự cuối
        last_chars = hash_val[-2:]
        last_int = int(last_chars, 16)
        
        if last_int % 3 == 0:
            return 'T', 0.54
        elif last_int % 5 == 0:
            return 'X', 0.54
        elif last_int % 2 == 0:
            return 'T', 0.52
        else:
            return 'X', 0.52
    
    # 16. ALTERNATING FLOW
    @staticmethod
    def ALGO_16_alternating_flow(history: List[str]) -> Tuple[str, float]:
        """Dòng chảy đan xen"""
        if len(history) < 6: return 'T', 0.51
        
        # Kiểm tra 6 phiên gần nhất có đan xen không
        alternating = True
        for i in range(1, 6):
            if i < len(history):
                if history[-i] == history[-(i+1)]:
                    alternating = False
                    break
        
        if alternating:
            # Đang đan xen -> tiếp tục đan xen
            next_val = 'X' if history[-1] == 'T' else 'T'
            return next_val, 0.65
        
        return 'T', 0.52
    
    # 17. MIRROR REFLECTION
    @staticmethod
    def ALGO_17_mirror_reflection(history: List[str]) -> Tuple[str, float]:
        """Phản chiếu gương"""
        if len(history) < 6: return 'T', 0.51
        
        last_6 = history[-6:]
        
        # Kiểm tra đối xứng
        if (last_6[0] == last_6[5] and 
            last_6[1] == last_6[4] and 
            last_6[2] == last_6[3]):
            return last_6[2], 0.63
        
        return 'T', 0.52
    
    # 18. CLUSTER IDENTIFICATION
    @staticmethod
    def ALGO_18_cluster_identification(history: List[str]) -> Tuple[str, float]:
        """Nhận diện cụm"""
        if len(history) < 12: return 'T', 0.51
        
        pattern_size = 4
        clusters = defaultdict(list)
        
        for i in range(len(history) - pattern_size):
            pattern = ''.join(history[i:i+pattern_size])
            clusters[pattern].append(i)
        
        current_pattern = ''.join(history[-pattern_size:])
        
        if current_pattern in clusters:
            positions = clusters[current_pattern]
            if len(positions) >= 2:
                # Tính khoảng cách trung bình
                intervals = [positions[i] - positions[i-1] for i in range(1, len(positions))]
                avg_interval = sum(intervals) / len(intervals)
                
                # Kiểm tra có trong chu kỳ không
                last_pos = positions[-1]
                current_pos = len(history) - pattern_size
                
                if current_pos - last_pos >= avg_interval * 0.8:
                    # Tìm kết quả phổ biến
                    next_vals = []
                    for pos in positions:
                        if pos + pattern_size < len(history):
                            next_vals.append(history[pos + pattern_size])
                    
                    if next_vals:
                        t_count = next_vals.count('T')
                        if t_count >= len(next_vals) * 0.7:
                            return 'T', 0.62
                        elif t_count <= len(next_vals) * 0.3:
                            return 'X', 0.62
        
        return 'T', 0.52
    
    # 19. REVERSAL SIGNAL
    @staticmethod
    def ALGO_19_reversal_signal(history: List[str]) -> Tuple[str, float]:
        """Tín hiệu đảo chiều"""
        if len(history) < 12: return 'T', 0.51
        
        # Tìm các điểm đổi
        change_points = []
        for i in range(1, min(12, len(history))):
            if history[-i] != history[-(i+1)]:
                change_points.append(i)
        
        if len(change_points) >= 3:
            # Tính khoảng cách trung bình
            intervals = [change_points[i] - change_points[i-1] for i in range(1, len(change_points))]
            avg_interval = sum(intervals) / len(intervals)
            
            # Kiểm tra có sắp đổi không
            last_change = change_points[0]
            if last_change >= avg_interval * 0.8:
                return 'X' if history[-1] == 'T' else 'T', 0.60
        
        return history[-1], 0.55
    
    # 20. MOVING AVERAGE CROSS
    @staticmethod
    def ALGO_20_moving_average_cross(history: List[str]) -> Tuple[str, float]:
        """Giao cắt trung bình động"""
        if len(history) < 15: return 'T', 0.51
        
        # MA ngắn (5 phiên)
        short_ma = 0
        if len(history) >= 5:
            short_segment = history[-5:]
            short_ma = short_segment.count('T') / 5
        
        # MA dài (10 phiên)
        long_ma = 0
        if len(history) >= 10:
            long_segment = history[-10:]
            long_ma = long_segment.count('T') / 10
        
        if short_ma > long_ma + 0.15:
            return 'T', 0.58
        elif short_ma < long_ma - 0.15:
            return 'X', 0.58
        elif short_ma > long_ma:
            return 'T', 0.55
        else:
            return 'X', 0.55
    
    # 21. EXPONENTIAL SMOOTHING
    @staticmethod
    def ALGO_21_exponential_smoothing(history: List[str]) -> Tuple[str, float]:
        """Làm mũ hàm mũ"""
        if not history: return 'T', 0.50
        
        smoothed = 0.5
        alpha = 0.3
        
        for result in history:
            value = 1 if result == 'T' else 0
            smoothed = alpha * value + (1 - alpha) * smoothed
        
        if smoothed > 0.58:
            return 'T', 0.57 + min(0.04, (smoothed - 0.58) * 0.3)
        elif smoothed < 0.42:
            return 'X', 0.57 + min(0.04, (0.42 - smoothed) * 0.3)
        
        return 'T' if smoothed > 0.5 else 'X', 0.54
    
    # 22. STANDARD DEVIATION
    @staticmethod
    def ALGO_22_standard_deviation(history: List[str]) -> Tuple[str, float]:
        """Độ lệch chuẩn"""
        if len(history) < 12: return 'T', 0.51
        
        values = [1 if h == 'T' else 0 for h in history]
        mean = sum(values) / len(values)
        
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = math.sqrt(variance)
        
        if std_dev < 0.25:
            # Rất ổn định -> continuation
            return history[-1], 0.59
        elif std_dev > 0.75:
            # Rất biến động -> reversal
            return 'X' if history[-1] == 'T' else 'T', 0.57
        
        return 'T', 0.53
    
    # 23. Z-SCORE ANALYSIS
    @staticmethod
    def ALGO_23_zscore_analysis(history: List[str]) -> Tuple[str, float]:
        """Phân tích Z-score"""
        if len(history) < 10: return 'T', 0.51
        
        recent = history[-8:]
        values = [1 if h == 'T' else 0 for h in recent]
        
        mean = sum(values) / len(values)
        std_dev = math.sqrt(sum((x - mean) ** 2 for x in values) / len(values))
        
        if std_dev > 0:
            last_z = (values[-1] - mean) / std_dev
            
            if last_z > 1.5:
                return 'X', 0.58
            elif last_z < -1.5:
                return 'T', 0.58
        
        return 'T', 0.52
    
    # 24. CORRELATION TREND
    @staticmethod
    def ALGO_24_correlation_trend(history: List[str]) -> Tuple[str, float]:
        """Xu hướng tương quan"""
        if len(history) < 10: return 'T', 0.51
        
        values = [1 if h == 'T' else 0 for h in history]
        
        # Tính auto-correlation lag 1
        corr_sum = 0
        for i in range(1, len(values)):
            corr_sum += values[i] * values[i-1]
        
        correlation = corr_sum / (len(values) - 1)
        
        if correlation > 0.65:
            return history[-1], 0.60
        elif correlation < 0.35:
            return 'X' if history[-1] == 'T' else 'T', 0.59
        
        return 'T', 0.53
    
    # 25. PATTERN MATRIX
    @staticmethod
    def ALGO_25_pattern_matrix(history: List[str]) -> Tuple[str, float]:
        """Ma trận pattern"""
        if len(history) < 6: return 'T', 0.51
        
        patterns_3 = {
            'TTT': 'X', 'TTX': 'T', 'TXT': 'X', 'TXX': 'T',
            'XTT': 'X', 'XTX': 'T', 'XXT': 'X', 'XXX': 'T'
        }
        
        last_3 = ''.join(history[-3:])
        if last_3 in patterns_3:
            return patterns_3[last_3], 0.59
        
        patterns_2 = {
            'TT': 'X', 'TX': 'T', 'XT': 'X', 'XX': 'T'
        }
        
        last_2 = ''.join(history[-2:])
        if last_2 in patterns_2:
            return patterns_2[last_2], 0.56
        
        return 'T', 0.52
    
    # 26. SEQUENCE FORECAST
    @staticmethod
    def ALGO_26_sequence_forecast(history: List[str]) -> Tuple[str, float]:
        """Dự báo chuỗi"""
        if len(history) < 10: return 'T', 0.51
        
        seq_length = 4
        seq_counts = defaultdict(int)
        
        for i in range(len(history) - seq_length + 1):
            seq = ''.join(history[i:i+seq_length])
            seq_counts[seq] += 1
        
        if seq_counts:
            # Tìm chuỗi phổ biến nhất
            max_seq = max(seq_counts.items(), key=lambda x: x[1])
            if max_seq[1] >= 2:
                return max_seq[0][0], 0.60
        
        return 'T', 0.52
    
    # 27. TRANSITION PROBABILITY
    @staticmethod
    def ALGO_27_transition_probability(history: List[str]) -> Tuple[str, float]:
        """Xác suất chuyển tiếp"""
        if len(history) < 12: return 'T', 0.51
        
        matrix = defaultdict(lambda: {'T': 0, 'X': 0})
        
        for i in range(len(history) - 1):
            current = history[i]
            next_val = history[i+1]
            matrix[current][next_val] += 1
        
        last = history[-1]
        if last in matrix:
            counts = matrix[last]
            total = counts['T'] + counts['X']
            
            if total >= 4:
                if counts['T'] > counts['X']:
                    ratio = counts['T'] / total
                    return 'T', 0.57 + min(0.04, (ratio - 0.5) * 0.3)
                else:
                    ratio = counts['X'] / total
                    return 'X', 0.57 + min(0.04, (ratio - 0.5) * 0.3)
        
        return 'T', 0.52
    
    # 28. PATTERN CONSISTENCY
    @staticmethod
    def ALGO_28_pattern_consistency(history: List[str]) -> Tuple[str, float]:
        """Độ nhất quán pattern"""
        if len(history) < 15: return 'T', 0.51
        
        pattern_size = 3
        pattern_results = defaultdict(list)
        
        for i in range(len(history) - pattern_size):
            pattern = ''.join(history[i:i+pattern_size])
            next_val = history[i+pattern_size]
            pattern_results[pattern].append(next_val)
        
        current_pattern = ''.join(history[-pattern_size:])
        
        if current_pattern in pattern_results:
            results = pattern_results[current_pattern]
            if len(results) >= 3:
                t_ratio = results.count('T') / len(results)
                
                if t_ratio >= 0.75:
                    return 'T', 0.64
                elif t_ratio <= 0.25:
                    return 'X', 0.64
                elif t_ratio > 0.6:
                    return 'T', 0.59
                elif t_ratio < 0.4:
                    return 'X', 0.59
        
        return 'T', 0.52
    
    # 29. ENTROPY TREND
    @staticmethod
    def ALGO_29_entropy_trend(history: List[str]) -> Tuple[str, float]:
        """Xu hướng entropy"""
        if len(history) < 10: return 'T', 0.51
        
        window = 8
        if len(history) >= window:
            segment = history[-window:]
            t_count = segment.count('T')
            p_t = t_count / window
            
            entropy = 0
            if p_t > 0:
                entropy -= p_t * math.log2(p_t + 1e-10)
            if (1 - p_t) > 0:
                entropy -= (1 - p_t) * math.log2(1 - p_t + 1e-10)
            
            if entropy < 0.35:
                return segment[-1], 0.60
            elif entropy > 0.95:
                return 'X' if segment[-1] == 'T' else 'T', 0.58
        
        return 'T', 0.52
    
    # 30. ENSEMBLE DECISION
    @staticmethod
    def ALGO_30_ensemble_decision(history: List[str]) -> Tuple[str, float]:
        """Quyết định tổng hợp"""
        if len(history) < 8: return 'T', 0.51
        
        # Sử dụng 5 phương pháp cốt lõi
        methods = [
            TaiXiuReal30Algorithms.ALGO_01_pattern_continuation,
            TaiXiuReal30Algorithms.ALGO_02_frequency_balance,
            TaiXiuReal30Algorithms.ALGO_03_streak_analysis,
            TaiXiuReal30Algorithms.ALGO_05_momentum_detection,
            TaiXiuReal30Algorithms.ALGO_10_entropy_optimization
        ]
        
        predictions = []
        confidences = []
        
        for method in methods:
            pred, conf = method(history)
            predictions.append(pred)
            confidences.append(conf)
        
        # Weighted voting
        vote_t = sum(conf for pred, conf in zip(predictions, confidences) if pred == 'T')
        vote_x = sum(conf for pred, conf in zip(predictions, confidences) if pred == 'X')
        
        total_votes = vote_t + vote_x
        
        if vote_t > vote_x:
            final_conf = vote_t / total_votes
            return 'T', min(0.65, final_conf)
        else:
            final_conf = vote_x / total_votes
            return 'X', min(0.65, final_conf)
    
    # === MAIN PREDICTION METHOD ===
    @staticmethod
    def get_prediction(history: List[str]) -> Tuple[str, float]:
        """Phương pháp dự đoán chính"""
        if len(history) < 5:
            return 'T', 0.51
        
        # Sử dụng ALGO_30 (ensemble) làm phương pháp chính
        return TaiXiuReal30Algorithms.ALGO_30_ensemble_decision(history)

# =========================================================
# 🔹 API Tele68 (Nguồn dữ liệu thực tế)
# =========================================================
def get_taixiu_data():
    url = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
    try:
        res = requests.get(url, timeout=8)
        res.raise_for_status()
        data = res.json()
        if "list" in data and len(data["list"]) > 0:
            newest = data["list"][0]
            phien = newest.get("id")
            dice = newest.get("dices", [1, 2, 3])
            tong = newest.get("point", sum(dice))
            
            # Xử lý kết quả Tài/Xỉu
            raw_result = newest.get("resultTruyenThong", "").upper()
            if raw_result == "TAI":
                ketqua = "Tài"
            elif raw_result == "XIU":
                ketqua = "Xỉu"
            else:
                ketqua = "Tài" if tong >= 11 else "Xỉu" 
                
            return phien, dice, tong, ketqua
    except Exception as e:
        print(f"[❌] Lỗi API: {e}")
    return None

# =========================================================
# 🔹 Thread cập nhật dữ liệu chạy ngầm
# =========================================================
def background_updater():
    global last_data
    last_phien = None
    while True:
        data = get_taixiu_data()
        if data:
            phien, dice, tong, ketqua = data
            
            if phien != last_phien and phien is not None: 
                # Lưu vào lịch sử
                history.append('T' if ketqua == 'Tài' else 'X')
                totals.append(tong)

                # Thực hiện dự đoán với thuật toán AI
                try:
                    du_doan, do_tin_cay = TaiXiuReal30Algorithms.get_prediction(list(history))
                    du_doan_text = "Tài" if du_doan == 'T' else "Xỉu"
                except Exception as e:
                    print(f"[❌] Lỗi thuật toán: {e}")
                    du_doan_text = "Đang xử lý..."
                    do_tin_cay = 0

                # Cập nhật dữ liệu trả về
                last_data = {
                    "phien": phien,
                    "xucxac1": dice[0],
                    "xucxac2": dice[1],
                    "xucxac3": dice[2],
                    "tong": tong,
                    "ketqua": ketqua,
                    "du_doan": du_doan_text,
                    "do_tin_cay": round(do_tin_cay * 100, 1),  # Chuyển sang phần trăm
                    "id": "trí tuệ ai 2025"
                }

                print(f"[✅] Phiên mới: {phien} | Kết quả: {ketqua} ({tong}) | Dự đoán: {du_doan_text} ({do_tin_cay:.1%})")
                last_phien = phien
        
        time.sleep(5) # Kiểm tra mỗi 5 giây

# =========================================================
# 🔹 API Endpoint
# =========================================================
@app.route("/api/taixiu", methods=["GET"])
def api_taixiu():
    return jsonify(last_data)

# =========================================================
# 🔹 API Endpoint xem lịch sử
# =========================================================
@app.route("/api/taixiu", methods=["GET"])
def api_history():
    history_list = list(history)
    totals_list = list(totals)
    return jsonify({
        "history": history_list,
        "totals": totals_list,
        "count": len(history_list)
    })

# =========================================================
# 🔹 API Endpoint xem thông tin thuật toán
# =========================================================
@app.route("/api/taixiumd5", methods=["GET"])
def api_algorithm():
    return jsonify({
        "name": "TaiXiuReal30Algorithms",
        "version": "2025.1.0",
        "author": "Tuấn Anh - Trí tuệ 2025",
        "algorithm_count": 30,
        "status": "Đang hoạt động"
    })

# =========================================================
# 🔹 Chạy Server
# =========================================================
if __name__ == "__main__":
    print("🚀 API Server đang khởi động...")
    print("📊 đã được tích hợp")
    print("🔮 Thuật toán AI đã sẵn sàng dự đoán")
    
    port = int(os.environ.get("PORT", 5000))
    
    # Khởi chạy thread cập nhật dữ liệu
    threading.Thread(target=background_updater, daemon=True).start()
    
    # Chạy Flask
    app.run(host="0.0.0.0", port=port)
