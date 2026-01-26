from flask import Flask, jsonify
import requests
import time
import threading
from collections import deque
import os

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
    "id": "lc79"
}

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
                history.append(ketqua)
                totals.append(tong)

                last_data = {
                    "phien": phien,
                    "xucxac1": dice[0],
                    "xucxac2": dice[1],
                    "xucxac3": dice[2],
                    "tong": tong,
                    "ketqua": ketqua,
                    "du_doan": "Đã xóa thuật toán",
                    "do_tin_cay": 0,
                    "id": "lc79"
                }

                print(f"[✅] Phiên mới: {phien} | {ketqua} ({tong})")
                last_phien = phien

        time.sleep(5)

# =========================================================
# 🔹 API Endpoint
# =========================================================
@app.route("/api/taixiu", methods=["GET"])
def api_taixiu():
    return jsonify(last_data)

@app.route("/api/taixiumd5", methods=["GET"])
def api_taixiu_md5():
    return jsonify(last_data)

# =========================================================
# 🔹 Chạy Server
# =========================================================
if __name__ == "__main__":
    print("🚀 API Server đang khởi động...")
    port = int(os.environ.get("PORT", 5000))

    threading.Thread(
        target=background_updater,
        daemon=True
    ).start()

    app.run(host="0.0.0.0", port=port)
