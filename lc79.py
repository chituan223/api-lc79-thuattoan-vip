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
    "mode": "INIT",
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
# 🧠 ENGINE TỔNG – KHÔNG BAO GIỜ NO BET
# =========================================================
def predict_engine(history, totals):
    n = len(history)

    # =====================================================
    # 🔰 GIAI ĐOẠN 1: BOOTSTRAP (1–4 phiên)
    # =====================================================
    if n < 5:
        avg = sum(totals) / len(totals) if totals else 10.5
        return ("Tài" if avg >= 11 else "Xỉu"), 50, "BOOT", "BOOTSTRAP"

    # =====================================================
    # 🔰 GIAI ĐOẠN 2: MINI PENTTER (5–19 phiên)
    # =====================================================
    if n < 20:
        seq = ['T' if x == 'Tài' else 'X' for x in history]
        recent = seq[-5:]
        t = recent.count('T')
        x = recent.count('X')
        if t != x:
            return ("Tài" if t > x else "Xỉu"), 55, "MINI5", "MINI"

        avg = sum(totals[-5:]) / 5
        return ("Tài" if avg >= 11 else "Xỉu"), 52, "AVG5", "MINI"

    # =====================================================
    # 🔰 GIAI ĐOẠN 3: PENTTER THẬT (≥ 20 phiên)
    # =====================================================
    return pentter_50_engine(history)

# =========================================================
# 🧠 PENTTER THẬT (GIỮ NGUYÊN LOGIC BẠN)
# =========================================================
def pentter_50_engine(history, min_len=3, max_len=6, min_support=3):
    seq = ['T' if x == 'Tài' else 'X' for x in history]
    stats = defaultdict(lambda: {"T": 0, "X": 0, "total": 0})

    for size in range(min_len, max_len + 1):
        for i in range(len(seq) - size):
            pattern = tuple(seq[i:i + size])
            next_val = seq[i + size]
            stats[pattern]["total"] += 1
            stats[pattern][next_val] += 1

    candidates = []
    for pattern, d in stats.items():
        if d["total"] >= min_support:
            win = max(d["T"], d["X"])
            winrate = win / d["total"]
            candidates.append({
                "pattern": pattern,
                "prediction": "Tài" if d["T"] > d["X"] else "Xỉu",
                "winrate": winrate,
                "score": winrate * d["total"]
            })

    candidates.sort(key=lambda x: (len(x["pattern"]), x["score"]), reverse=True)

    for c in candidates[:50]:
        size = len(c["pattern"])
        if tuple(seq[-size:]) == c["pattern"]:
            return c["prediction"], min(int(c["winrate"] * 100), 75), ''.join(c["pattern"]), "PENTTER"

    recent = seq[-20:]
    return ("Tài" if recent.count('T') > recent.count('X') else "Xỉu"), 58, "FREQ20", "FALLBACK"

# =========================================================
# 🔁 Thread cập nhật
# =========================================================
def background_updater():
    global last_data
    last_phien = None

    while True:
        data = get_taixiu_data()
        if data:
            phien, dice, tong, ketqua = data
            if phien != last_phien:
                history.append(ketqua)
                totals.append(tong)

                du_doan, do_tin_cay, pattern, mode = predict_engine(list(history), list(totals))

                last_data = {
                    "phien": phien,
                    "xucxac1": dice[0],
                    "xucxac2": dice[1],
                    "xucxac3": dice[2],
                    "tong": tong,
                    "ketqua": ketqua,
                    "du_doan": du_doan,
                    "do_tin_cay": do_tin_cay,
                    "pattern": pattern,
                    "mode": mode,
                    "id": "địt mẹ lc79"
                }

                print(f"[{mode}] Phiên {phien} | {ketqua} | Dự đoán: {du_doan} ({do_tin_cay}%)")
                last_phien = phien

        time.sleep(5)

# =========================================================
# 🔹 API
# =========================================================
@app.route("/api/taixiu", methods=["GET"])
def api_taixiu():
    return jsonify(last_data)

# =========================================================
# 🚀 RUN
# =========================================================
if __name__ == "__main__":
    print("🚀 API Server đang khởi động...")
    port = int(os.environ.get("PORT", 5000))
    threading.Thread(target=background_updater, daemon=True).start()
    app.run(host="0.0.0.0", port=port)
