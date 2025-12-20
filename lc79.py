from flask import Flask, jsonify
import requests
import time
import threading
from collections import deque
import os

app = Flask(__name__)

# =========================================================
# 💾 Bộ nhớ lưu trữ lịch sử (Chỉ dự đoán khi len >= 20)
# =========================================================
history = deque(maxlen=1000)
totals = deque(maxlen=1000)

last_data = {
    "status": "Chờ đủ dữ liệu",
    "phien": None,
    "ketqua_gan_nhat": "",
    "du_doan": "Vui lòng đợi (0/20 phiên)",
    "do_tin_cay": "0%",
    "so_thuat_toan_khớp": 0
}

# =========================================================
# 🧠 Engine Soi Cầu Đa Tầng (Multi-Layer Pattern Engine)
# =========================================================
class UltimateEngine:
    @staticmethod
    def analyze(h, t):
        # ĐIỀU KIỆN CỨNG: Đủ 20 phiên mới soi
        if len(h) < 20:
            return f"Đang thu thập dữ liệu ({len(h)}/20)", 0, 0
        
        scores = {"T": 0, "X": 0}
        match_count = 0
        h_str = "".join(h) # Chuyển thành chuỗi để regex/pattern nhanh hơn

        # 1. Nhóm Thuật toán Bệt (15 mẫu: từ bệt 2 đến bệt 15)
        # Logic: Dưới 5 ván thì theo, trên 6 ván bắt đầu xét bẻ cầu
        streak = 1
        for i in range(len(h)-2, -1, -1):
            if h[i] == h[-1]: streak += 1
            else: break
        
        if streak < 6:
            scores[h[-1]] += (streak * 10)
            match_count += 1
        else:
            # Thuật toán bẻ cầu bệt (Mean Reversion)
            scores["T" if h[-1] == "X" else "X"] += 25
            match_count += 1

        # 2. Nhóm Cầu Đảo (Zigzag) 1-1, 1-2, 2-1 (Hơn 10 mẫu)
        if h_str.endswith("TXTX") or h_str.endswith("XTXT"):
            scores["T" if h[-1] == "X" else "X"] += 30
            match_count += 2

        # 3. Nhóm Cầu Nghiêng (Bias - 5 mẫu)
        window_10 = h[-10:]
        tai_count = window_10.count('T')
        if tai_count >= 7: scores["X"] += 20  # Nghiêng quá nhiều về Tài thì bắt đầu soi Xỉu
        elif tai_count <= 3: scores["T"] += 20
        match_count += 1

        # 4. Nhóm Cầu Đối Xứng & Gương (Mirror - 10 mẫu)
        for size in [4, 6, 8]:
            if h[-size:] == h[-size*2:-size]: # Cầu lặp lại đoạn trước
                scores[h[-1]] += 15
                match_count += 2

        # 5. Nhóm Tiến Lùi (3-2-1, 1-2-3, 4-3-2-1... - 20 mẫu)
        # Logic chuỗi điểm giảm dần hoặc tăng dần
        if h_str.endswith("TTTXXT") or h_str.endswith("XXXTTX"):
            scores["X" if h[-1] == "T" else "T"] += 40
            match_count += 5

        # 6. Thuật toán Xúc Xắc (Dice Probability)
        # Nếu tổng điểm vừa ra là cực trị (3,4 hoặc 17,18) -> Tỷ lệ hồi cực cao
        if t[-1] <= 5: 
            scores["T"] += 50
            match_count += 3
        elif t[-1] >= 16: 
            scores["X"] += 50
            match_count += 3

        # --- TỔNG HỢP ---
        final_decision = "Tài" if scores['T'] > scores['X'] else "Xỉu"
        diff = abs(scores['T'] - scores['X'])
        
        # Độ tin cậy dựa trên sự đồng thuận của các nhóm thuật toán
        confidence = min(round((diff / 120) * 100), 95)
        
        if diff < 15: # Nếu các thuật toán đang đánh nhau, không nên vào
            return "Bỏ qua (Cầu nhiễu)", 0, match_count

        return final_decision, confidence, match_count

# =========================================================
# 🔄 Background Worker: Lấy dữ liệu & Xử lý lỗi
# =========================================================
def data_fetcher():
    global last_data
    last_phien = None
    engine = UltimateEngine()
    
    # Fake User-Agent để tránh bị block API
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36"}

    while True:
        try:
            url = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
            res = requests.get(url, headers=headers, timeout=10)
            
            if res.status_code == 200:
                data = res.json()
                if "list" in data and len(data["list"]) > 0:
                    newest = data["list"][0]
                    phien = newest.get("id")
                    
                    if phien != last_phien:
                        # Lấy xúc xắc (xử lý trường hợp API trả về mảng hoặc null)
                        dices = newest.get("dices", [])
                        if not dices: # Dự phòng nếu dices bị rỗng
                            tong = newest.get("point", 10)
                        else:
                            tong = sum(dices)
                            
                        kq_char = 'T' if tong >= 11 else 'X'
                        
                        history.append(kq_char)
                        totals.append(tong)
                        
                        # Chạy thuật toán soi
                        pre, conf, matches = engine.analyze(list(history), list(totals))
                        
                        last_data = {
                            "status": "Hoạt động",
                            "phien": phien,
                            "tong": tong,
                            "ketqua": "Tài" if kq_char == 'T' else "Xỉu",
                            "du_doan": pre,
                            "do_tin_cay": f"{conf}%",
                            "thuat_toan_khop": matches,
                            "so_mau_da_lay": len(history)
                        }
                        last_phien = phien
                        print(f"[🔥] Phiên {phien} -> KQ: {kq_char} | Dự đoán ván tới: {pre} ({conf}%)")
            
        except Exception as e:
            print(f"[❌] Lỗi kết nối API: {e}")
            
        time.sleep(5) # Kiểm tra mỗi 5 giây

# =========================================================
# 🔹 Endpoints
# =========================================================
@app.route("/api/taixiu", methods=["GET"])
def get_api():
    return jsonify(last_data)

@app.route("/", methods=["GET"])
def home():
    return "Bot Soi Cầu Tài Xỉu MD5 đang chạy..."

if __name__ == "__main__":
    # Khởi động thread lấy dữ liệu
    threading.Thread(target=data_fetcher, daemon=True).start()
    
    # Chạy Flask Server
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
