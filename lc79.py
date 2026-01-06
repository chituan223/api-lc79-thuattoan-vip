from flask import Flask, jsonify
import requests
import time
import threading
import os
import statistics
import math
from typing import List, Dict, Any
from collections import deque

app = Flask(__name__)

# =========================================================
# 🧠 Thuật toán Ma Trận Logic (TaiXiuProEngine)
# =========================================================
class TaiXiuProEngine:
    def __init__(self):
        self.strategies = self._initialize_massive_strategies()

    def _initialize_massive_strategies(self) -> List[Dict]:
        rules = []
        # 1. Nhóm vật lý cực hạn (Biên 3-5 hoặc 16-18)
        rules.append({"loai": "PHYSICS", "cond": "SUM_LE_5", "action": "Tài", "weight": 110, "name": "Biên cực thấp"})
        rules.append({"loai": "PHYSICS", "cond": "SUM_GE_16", "action": "Xỉu", "weight": 110, "name": "Biên cực cao"})

        # 2. Nhóm Bệt (Streaks 3-15 tay)
        for i in range(3, 16):
            rules.append({"loai": "STREAK", "mo_hinh": "Tài", "len": i, "action": "Tài" if i < 8 else "Xỉu", "weight": 60 + i, "name": f"Bệt Tài {i}"})
            rules.append({"loai": "STREAK", "mo_hinh": "Xỉu", "len": i, "action": "Xỉu" if i < 8 else "Tài", "weight": 60 + i, "name": f"Bệt Xỉu {i}"})

        # 3. Nhóm Cầu chu kỳ (Patterns)
        patterns = ["1-1", "2-2", "3-3", "2-1", "1-2"]
        for p in patterns:
            for length in [4, 6, 8]:
                rules.append({"loai": "PATTERN", "mo_hinh": p, "len": length, "weight": 75, "name": f"Cầu {p} ({length}p)"})

        # 4. Nhóm Tần suất (Frequency Bias)
        for window in [10, 20]:
            rules.append({"loai": "FREQ", "window": window, "target": "Tài", "threshold": 0.65, "action": "Xỉu", "weight": 80, "name": "Quá tải Tài"})
            rules.append({"loai": "FREQ", "window": window, "target": "Xỉu", "threshold": 0.65, "action": "Tài", "weight": 80, "name": "Quá tải Xỉu"})

        return rules

    def _calculate_entropy(self, data: List[int]) -> float:
        if not data: return 0
        p_tai = data.count(1) / len(data)
        p_xiu = 1 - p_tai
        if p_tai == 0 or p_xiu == 0: return 0
        return -(p_tai * math.log2(p_tai) + p_xiu * math.log2(p_xiu))

    def predict_v6(self, history_tx: List[int], history_points: List[int]) -> Dict[str, Any]:
        if len(history_tx) < 20:
            return {"advice": "Nạp dữ liệu...", "conf": 0, "signal": "WAIT", "entropy": 0, "ly_do": []}

        votes_tai = 0.0
        votes_xiu = 0.0
        matched_details = []
        entropy = self._calculate_entropy(history_tx[-20:])
        
        for rule in self.strategies:
            is_match = False
            target_action = ""

            if rule["loai"] == "PHYSICS":
                if rule["cond"] == "SUM_LE_5" and history_points[-1] <= 5:
                    is_match, target_action = True, "Tài"
                elif rule["cond"] == "SUM_GE_16" and history_points[-1] >= 16:
                    is_match, target_action = True, "Xỉu"

            elif rule["loai"] == "STREAK":
                sub = history_tx[-rule["len"]:]
                val = 1 if rule["mo_hinh"] == "Tài" else 0
                if all(x == val for x in sub):
                    is_match, target_action = True, rule["action"]

            elif rule["loai"] == "FREQ":
                sub = history_tx[-rule["window"]:]
                rate = sub.count(1 if rule["target"] == "Tài" else 0) / rule["window"]
                if rate >= rule["threshold"]:
                    is_match, target_action = True, rule["action"]

            if is_match:
                if target_action == "Tài": votes_tai += rule["weight"]
                else: votes_xiu += rule["weight"]
                matched_details.append(rule["name"])

        total_votes = votes_tai + votes_xiu
        if total_votes == 0: return {"advice": "Hòa", "conf": 50, "signal": "SKIP", "entropy": entropy, "ly_do": []}

        prob_tai = (votes_tai / total_votes) * 100
        prob_xiu = (votes_xiu / total_votes) * 100
        final_prediction = "Tài" if prob_tai > prob_xiu else "Xỉu"
        confidence = max(prob_tai, prob_xiu)

        signal = "BỎ QUA"
        if entropy > 0.98: signal = "NHIỄU (NGHỈ)"
        elif confidence >= 85: signal = "LỆNH VIP"
        elif confidence >= 70: signal = "VÀO TIỀN"

        return {
            "advice": final_prediction,
            "conf": round(confidence, 2),
            "signal": signal,
            "entropy": round(entropy, 3),
            "ly_do": list(set(matched_details))[:3]
        }

# =========================================================
# 💾 Bộ nhớ & Engine
# =========================================================
engine = TaiXiuProEngine()
history_bits = deque(maxlen=100)
history_points = deque(maxlen=100)

last_data = {
    "phien": None, "dice": [0,0,0], "tong": 0, "ketqua": "",
    "du_doan": "Chờ...", "do_tin_cay": 0, "status": "WAIT", "entropy": 0
}

# =========================================================
# 🔹 API Data Fetching
# =========================================================
def get_taixiu_data():
    url = "https://wtxmd52.tele68.com/v1/txmd5/sessions" 
    try:
        res = requests.get(url, timeout=8)
        data = res.json()
        if "list" in data and len(data["list"]) > 0:
            newest = data["list"][0]
            phien = newest.get("id")
            # API này đôi khi dùng "dices" hoặc tự tính từ "dice"
            dice_raw = newest.get("dice", "1,1,1")
            dice = [int(x) for x in dice_raw.split(",")]
            tong = newest.get("point", sum(dice))
            ketqua = "Tài" if tong >= 11 else "Xỉu"
            return phien, dice, tong, ketqua
    except Exception as e:
        print(f"Lỗi: {e}")
    return None

def background_updater():
    global last_data
    last_phien = None
    while True:
        data = get_taixiu_data()
        if data:
            phien, dice, tong, ketqua = data
            if phien != last_phien: 
                history_bits.append(1 if ketqua == "Tài" else 0)
                history_points.append(tong)

                # Chạy AI Dự đoán
                prediction = engine.predict_v6(list(history_bits), list(history_points))

                last_data = {
                    "phien": phien,
                    "xucxac": dice,
                    "tong": tong,
                    "ketqua": ketqua,
                    "du_doan": prediction["advice"],
                    "do_tin_cay": prediction["conf"],
                    "tin_hieu": prediction["signal"],
                  
                }
                print(f"[{phien}] {ketqua}({tong}) -> AI: {prediction['advice']} ({prediction['conf']}%)")
                last_phien = phien
        time.sleep(4)

@app.route("/api/taixiu", methods=["GET"])
def api_taixiu():
    return jsonify(last_data)

if __name__ == "__main__":
    threading.Thread(target=background_updater, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
