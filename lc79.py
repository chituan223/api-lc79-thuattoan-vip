from flask import Flask, jsonify
import requests
import time
import threading
from collections import deque, defaultdict
import os

app = Flask(__name__)

# =========================================================
# 💾 Bộ nhớ lịch sử
# =========================================================
history = deque(maxlen=1000)   # 'Tài' / 'Xỉu'
totals  = deque(maxlen=1000)

last_data = {
    "phien": None,
    "xucxac1": 0,
    "xucxac2": 0,
    "xucxac3": 0,
    "tong": 0,
    "ketqua": "",
    "du_doan": "Chờ dữ liệu...",
    "do_tin_cay": 0,
    "pattern": None,
    "id": "địt mẹ lc79"
}

# =========================================================
# 🔹 API Tele68
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

            raw = newest.get("resultTruyenThong", "").upper()
            if raw == "TAI":
                ketqua = "Tài"
            elif raw == "XIU":
                ketqua = "Xỉu"
            else:
                ketqua = "Tài" if tong >= 11 else "Xỉu"

            return phien, dice, tong, ketqua
    except Exception as e:
        print(f"[❌] Lỗi API: {e}")
    return None

# =========================================================
# 🧠 PENTTER THẬT – KHAI THÁC 50 PATTERN TỐT NHẤT
# =========================================================
def pentter_50_engine(history, min_len=3, max_len=6, min_support=3):
    """
    history: ['Tài','Xỉu',...]
    return: du_doan, do_tin_cay, pattern
    """

    if len(history) < 20:
        return None, 0, None

    # Chuẩn hóa về T / X
    seq = ['T' if x == 'Tài' else 'X' for x in history]

    stats = defaultdict(lambda: {"T": 0, "X": 0, "total": 0})

    # 1️⃣ Thu thập TẤT CẢ pattern
    for size in range(min_len, max_len + 1):
        for i in range(len(seq) - size):
            pattern = tuple(seq[i:i + size])
            next_val = seq[i + size]
            stats[pattern]["total"] += 1
            stats[pattern][next_val] += 1

    # 2️⃣ Xếp hạng pattern → chính là “50 thuật toán”
    ranked_patterns = []

    for pattern, data in stats.items():
        if data["total"] < min_support:
            continue
        win = max(data["T"], data["X"])
        winrate = win / data["total"]
        score = winrate * data["total"]   # vừa chính xác vừa đủ dữ liệu

        ranked_patterns.append({
            "pattern": pattern,
            "winrate": winrate,
            "score": score,
            "prediction": "Tài" if data["T"] > data["X"] else "Xỉu"
        })

    if not ranked_patterns:
        return None, 50, None

    # 🔥 TOP 50 PATTERN TỐT NHẤT
    ranked_patterns.sort(key=lambda x: x["score"], reverse=True)
    top50 = ranked_patterns[:50]

    # 3️⃣ So khớp pattern hiện tại
    best = None
    for p in top50:
        size = len(p["pattern"])
        if tuple(seq[-size:]) == p["pattern"]:
            best = p
            break

    if not best:
        return None, 55, None

    confidence = int(best["winrate"] * 100)
    confidence = min(confidence, 75)  # không ảo

    return best["prediction"], confidence, ''.join(best["pattern"])

# =========================================================
# 🔁 Thread cập nhật dữ liệu
# =========================================================
def background_updater():
    global last_data
    last_phien = None

    while True:
        data = get_taixiu_data()
        if data:
            phien, dice, tong, ketqua = data

            if phien != last_phien and phien is not None:
                history.append(ketqua)
                totals.append(tong)

                du_doan, do_tin_cay, pattern = pentter_50_engine(list(history))

                last_data = {
                    "phien": phien,
                    "xucxac1": dice[0],
                    "xucxac2": dice[1],
                    "xucxac3": dice[2],
                    "tong": tong,
                    "ketqua": ketqua,
                    "du_doan": du_doan if du_doan else "NO BET",
                    "do_tin_cay": do_tin_cay,
                    "pattern": pattern,
                    "id": "địt mẹ lc79"
                }

                print(
                    f"[✅] Phiên {phien} | {ketqua} ({tong}) | "
                    f"Dự đoán: {du_doan} | Tin cậy: {do_tin_cay}% | Pattern: {pattern}"
                )

                last_phien = phien

        time.sleep(5)

# =========================================================
# 🔹 API Endpoint
# =========================================================
@app.route("/api/taixiu", methods=["GET"])
def api_taixiu():
    return jsonify(last_data)

# =========================================================
# 🚀 Chạy Server
# =========================================================
if __name__ == "__main__":
    print("🚀 API Server đang khởi động...")
    port = int(os.environ.get("PORT", 5000))

    threading.Thread(target=background_updater, daemon=True).start()

    app.run(host="0.0.0.0", port=port)
