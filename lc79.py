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
history = deque(maxlen=1000)  # Lưu 'T' hoặc 'X'
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
    "id": "địt mẹ lc79"
}

# =========================================================
# 🔷 TAI XIỂU PREDICTION ENGINE - CẢI TIẾN
# =========================================================
class TaiXiuPredictionEngine:
    """Engine dự đoán Tài Xỉu thông minh"""
    
    @staticmethod
    def analyze_pattern_continuation(history: List[str]) -> Tuple[str, float]:
        """Phân tích pattern tiếp diễn"""
        if len(history) < 4: 
            return 'T' if len(history) % 2 == 0 else 'X', 0.52
        
        last_3 = ''.join(history[-3:])
        patterns = {
            'TTT': ('X', 0.65), 'TTX': ('T', 0.60), 'TXT': ('X', 0.58), 'TXX': ('T', 0.62),
            'XTT': ('X', 0.58), 'XTX': ('T', 0.62), 'XXT': ('X', 0.60), 'XXX': ('T', 0.65)
        }
        
        if last_3 in patterns:
            return patterns[last_3]
        
        # Xu hướng đảo chiều nếu chuỗi dài
        if len(set(history[-4:])) == 1:  # 4 cái giống nhau
            return 'X' if history[-1] == 'T' else 'T', 0.70
        
        return history[-1], 0.55
    
    @staticmethod
    def analyze_frequency_balance(history: List[str]) -> Tuple[str, float]:
        """Cân bằng tần suất"""
        if len(history) < 10:
            return 'T' if len(history) % 3 == 0 else 'X', 0.53
        
        tai_count = history.count('T')
        xiu_count = len(history) - tai_count
        
        if tai_count > xiu_count + 3:
            return 'X', 0.60 + min(0.10, (tai_count - xiu_count - 3) * 0.02)
        elif xiu_count > tai_count + 3:
            return 'T', 0.60 + min(0.10, (xiu_count - tai_count - 3) * 0.02)
        
        return 'T' if tai_count <= xiu_count else 'X', 0.55
    
    @staticmethod
    def analyze_streak_trend(history: List[str]) -> Tuple[str, float]:
        """Phân tích xu hướng chuỗi"""
        if len(history) < 5:
            return 'T' if len(history) % 2 == 0 else 'X', 0.52
        
        current = history[-1]
        streak = 1
        
        for i in range(2, min(6, len(history)) + 1):
            if history[-i] == current:
                streak += 1
            else:
                break
        
        if streak >= 4:
            return 'X' if current == 'T' else 'T', 0.68
        elif streak >= 3:
            return 'X' if current == 'T' else 'T', 0.62
        elif streak >= 2:
            return 'X' if current == 'T' else 'T', 0.58
        
        return current, 0.55
    
    @staticmethod
    def analyze_momentum(history: List[str]) -> Tuple[str, float]:
        """Phân tích động lượng"""
        if len(history) < 8:
            return 'T' if len(history) % 3 == 0 else 'X', 0.53
        
        # Động lượng 5 phiên
        momentum = 0
        for i in range(1, 6):
            if i < len(history):
                momentum += 1 if history[-i] == 'T' else -1
        
        if momentum >= 3:
            return 'X', 0.60
        elif momentum <= -3:
            return 'T', 0.60
        elif momentum >= 1:
            return 'X', 0.56
        elif momentum <= -1:
            return 'T', 0.56
        
        return 'T' if momentum >= 0 else 'X', 0.54
    
    @staticmethod
    def analyze_clustering(history: List[str]) -> Tuple[str, float]:
        """Phân tích cụm"""
        if len(history) < 15:
            return 'T' if len(history) % 4 == 0 else 'X', 0.53
        
        # Phân tích cụm 3 phiên
        clusters = defaultdict(int)
        for i in range(len(history) - 2):
            cluster = ''.join(history[i:i+3])
            clusters[cluster] += 1
        
        current_cluster = ''.join(history[-3:])
        
        # Tìm cluster phổ biến nhất
        if clusters:
            max_cluster = max(clusters.items(), key=lambda x: x[1])
            if max_cluster[1] >= 3:
                return max_cluster[0][0], 0.63
        
        return history[-1], 0.55
    
    @staticmethod
    def analyze_time_based(history: List[str]) -> Tuple[str, float]:
        """Phân tích dựa trên thời gian"""
        timestamp = int(time.time())
        
        # Sử dụng giây hiện tại
        second = timestamp % 60
        
        if second % 7 == 0:
            return 'T', 0.57
        elif second % 5 == 0:
            return 'X', 0.57
        elif second % 3 == 0:
            return 'T', 0.55
        elif second % 2 == 0:
            return 'X', 0.54
        
        return 'T' if second % 2 == 0 else 'X', 0.53
    
    @staticmethod
    def analyze_random_walk(history: List[str]) -> Tuple[str, float]:
        """Phân tích random walk"""
        if len(history) < 10:
            return 'T' if len(history) % 3 == 0 else 'X', 0.52
        
        # Tính tổng random walk
        walk = 0
        changes = 0
        for i in range(1, len(history)):
            if history[i] != history[i-1]:
                changes += 1
                walk += 1 if history[i] == 'T' else -1
            else:
                walk += 0.5 if history[i] == 'T' else -0.5
        
        change_ratio = changes / (len(history) - 1)
        
        if change_ratio > 0.7:  # Thay đổi nhiều
            return 'X' if history[-1] == 'T' else 'T', 0.60
        elif change_ratio < 0.3:  # Ổn định
            return history[-1], 0.62
        
        return 'T' if walk > 0 else 'X', 0.55
    
    @staticmethod
    def get_prediction(history: List[str]) -> Tuple[str, float]:
        """Lấy dự đoán tổng hợp"""
        if len(history) < 5:
            return 'T' if len(history) % 2 == 0 else 'X', 0.51
        
        # Sử dụng tất cả các phương pháp
        methods = [
            TaiXiuPredictionEngine.analyze_pattern_continuation,
            TaiXiuPredictionEngine.analyze_frequency_balance,
            TaiXiuPredictionEngine.analyze_streak_trend,
            TaiXiuPredictionEngine.analyze_momentum,
            TaiXiuPredictionEngine.analyze_clustering,
            TaiXiuPredictionEngine.analyze_time_based,
            TaiXiuPredictionEngine.analyze_random_walk
        ]
        
        predictions = []
        confidences = []
        
        for method in methods:
            try:
                pred, conf = method(history)
                predictions.append(pred)
                confidences.append(conf)
            except:
                pass
        
        if not predictions:
            return 'T', 0.50
        
        # Weighted voting
        vote_t = sum(conf for pred, conf in zip(predictions, confidences) if pred == 'T')
        vote_x = sum(conf for pred, conf in zip(predictions, confidences) if pred == 'X')
        
        total_votes = vote_t + vote_x
        
        if total_votes == 0:
            return 'T', 0.50
        
        if vote_t > vote_x:
            final_conf = vote_t / total_votes
            return 'T', min(0.75, final_conf)
        else:
            final_conf = vote_x / total_votes
            return 'X', min(0.75, final_conf)

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
    
    print("[⚙️] Khởi động engine dự đoán...")
    
    while True:
        data = get_taixiu_data()
        if data:
            phien, dice, tong, ketqua = data
            
            if phien != last_phien and phien is not None: 
                # Lưu vào lịch sử (đúng định dạng)
                history_symbol = 'T' if ketqua == 'Tài' else 'X'
                history.append(history_symbol)
                totals.append(tong)
                
                # Hiển thị thống kê
                if len(history) > 0:
                    tai_count = list(history).count('T')
                    xiu_count = len(history) - tai_count
                    print(f"[📊] Thống kê: Tài={tai_count}, Xỉu={xiu_count}, Tỉ lệ Tài={tai_count/len(history)*100:.1f}%")

                # Thực hiện dự đoán với engine cải tiến
                try:
                    du_doan, do_tin_cay = TaiXiuPredictionEngine.get_prediction(list(history))
                    du_doan_text = "Tài" if du_doan == 'T' else "Xỉu"
                except Exception as e:
                    print(f"[❌] Lỗi engine: {e}")
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
                    "do_tin_cay": round(do_tin_cay * 100, 1),
                    "id": "địt mẹ lc79"
                }

                print(f"[✅] Phiên {phien}: {ketqua} ({tong}) | Dự đoán: {du_doan_text} ({do_tin_cay:.1%})")
                last_phien = phien
        
        time.sleep(5)

# =========================================================
# 🔹 API Endpoint
# =========================================================
@app.route("/api/taixiu", methods=["GET"])
def api_taixiu():
    return jsonify(last_data)

@app.route("/api/stats", methods=["GET"])
def api_stats():
    """API thống kê"""
    history_list = list(history)
    if history_list:
        tai_count = history_list.count('T')
        xiu_count = len(history_list) - tai_count
        tai_percent = (tai_count / len(history_list)) * 100 if history_list else 0
        
        # Dự đoán tiếp theo
        next_pred, confidence = TaiXiuPredictionEngine.get_prediction(history_list)
        
        return jsonify({
            "total_games": len(history_list),
            "tai_count": tai_count,
            "xiu_count": xiu_count,
            "tai_percentage": round(tai_percent, 1),
            "next_prediction": "Tài" if next_pred == 'T' else "Xỉu",
            "confidence": round(confidence * 100, 1),
            "last_10": history_list[-10:] if len(history_list) >= 10 else history_list
        })
    return jsonify({"message": "Chưa có dữ liệu"})

# =========================================================
# 🔹 Chạy Server
# =========================================================
if __name__ == "__main__":
    print("🚀 API Server đang khởi động...")
    print("🎯 TaiXiu Prediction Engine v2.0")
    print("📊 Hệ thống đã sẵn sàng phân tích và dự đoán")
    
    port = int(os.environ.get("PORT", 5000))
    
    # Khởi chạy thread cập nhật dữ liệu
    threading.Thread(target=background_updater, daemon=True).start()
    
    # Chạy Flask
    app.run(host="0.0.0.0", port=port, debug=True)
