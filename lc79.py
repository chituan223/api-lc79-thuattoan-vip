from flask import Flask, jsonify
import requests
import statistics

app = Flask(__name__)

API_URL = "https://wtxmd52.tele68.com/v1/txmd5/sessions"


def fetch_sessions():
    try:
        res = requests.get(API_URL, timeout=5)
        data = res.json()
        if "list" not in data:
            return []
        # Lấy tối đa 20 phiên mới nhất (ra kết quả rồi)
        return data["list"][:20]
    except Exception as e:
        print("API Error:", e)
        return []

def convert_sessions(sessions):
    # Kết xuất lịch sử các phiên đã ra  
    history = []
    totals = []
    rows = []
    for item in sessions:
        dices = item.get("dices", [0, 0, 0])
        tong = sum(dices)
        label = "Tài" if tong >= 11 else "Xỉu"
        history.append(label)
        totals.append(tong)
        rows.append({
            "phien": item.get("id"),
            "xuc_xac": dices,
            "tong": tong,
            "cua": label,
            "duDoan": item.get("resultTruyenThong", ""),
        })
    return history, totals, rows

# --- Các thuật toán dự đoán cho PHIÊN KẾ TIẾP ---

def predictor_trend(history):
    if len(history) < 5:
        return {"du_doan": None, "do_tin_cay": 60.0, "bao_cau": "Chưa đủ dữ liệu"}
    last = history[-1]
    if history[-5:] == [last]*5:
        alt = "Xỉu" if last == "Tài" else "Tài"
        return {"du_doan": alt, "do_tin_cay": 98.0, "bao_cau": None}
    if history[-3:] == [last]*3:
        return {"du_doan": last, "do_tin_cay": 82.0, "bao_cau": None}
    return {"du_doan": last, "do_tin_cay": 68.0, "bao_cau": "Cầu không rõ ràng"}

def predictor_pattern_3(history):
    if len(history) < 6:
        return {"du_doan": None, "do_tin_cay": 59.0, "bao_cau": "Chưa đủ dữ liệu"}
    last_3 = "".join(h[0] for h in history[-3:])
    recent = history[-10:]
    tai, xiu = 0,0
    for i in range(len(recent)-3):
        patt = "".join(h[0] for h in recent[i:i+3])
        if patt == last_3:
            if recent[i+3][0] == "T":
                tai += 1
            else:
                xiu += 1
    tong = tai + xiu
    if tong > 2:
        if tai > xiu * 2:
            return {"du_doan": "Tài", "do_tin_cay": 93.5, "bao_cau": None}
        if xiu > tai * 2:
            return {"du_doan": "Xỉu", "do_tin_cay": 93.5, "bao_cau": None}
    return {"du_doan": history[-1], "do_tin_cay": 75.5, "bao_cau": "Không có pattern rõ"}

def predictor_mean_reversion(history, totals):
    if len(totals) < 15:
        return {"du_doan": None, "do_tin_cay": 61.0, "bao_cau": "Thiếu dữ liệu tổng"}
    weights = list(range(1,16))
    last = totals[-15:]
    mean = sum(v*w for v,w in zip(last,weights))/sum(weights)
    if mean > 11.7:
        return {"du_doan": "Xỉu", "do_tin_cay": 94.5, "bao_cau": None}
    if mean < 9.3:
        return {"du_doan": "Tài", "do_tin_cay": 94.5, "bao_cau": None}
    return {"du_doan": history[-1], "do_tin_cay": 72.0, "bao_cau": "Mean gần mốc chuẩn"}

def predictor_entropy_20(history):
    if len(history) < 20:
        return {"du_doan": None, "do_tin_cay": 62.0, "bao_cau": "Chưa đủ dữ liệu"}
    t = history[-20:].count("Tài")
    x = 20 - t
    if max(t,x) >= 16:
        alt = "Xỉu" if history[-1] == "Tài" else "Tài"
        return {"du_doan": alt, "do_tin_cay": 97.7, "bao_cau": None}
    if min(t,x) >= 8:
        if history[-1] != history[-2]:
            return {"du_doan": history[-2], "do_tin_cay": 87.0, "bao_cau": None}
        alt = "Xỉu" if history[-1] == "Tài" else "Tài"
        return {"du_doan": alt, "do_tin_cay": 93.0, "bao_cau": None}
    return {"du_doan": history[-1], "do_tin_cay": 70.0, "bao_cau": "Cầu chưa rõ"}

def predictor_mirror_8(history):
    if len(history) < 16:
        return {"du_doan": None, "do_tin_cay": 61.0, "bao_cau": "Chưa đủ dữ liệu"}
    block1, block2 = history[-16:-8], history[-8:]
    if block1[::-1]==block2:
        return {"du_doan": history[-1], "do_tin_cay": 97.0, "bao_cau": None}
    return {"du_doan": None, "do_tin_cay": 61.0, "bao_cau": "Không có mô hình gương"}

def predictor_block_reverse_5(history):
    if len(history) < 10:
        return {"du_doan": None, "do_tin_cay": 62.0, "bao_cau": "Chưa đủ phiên"}
    if history[-10:-5] == history[-5:][::-1]:
        return {"du_doan": history[-1], "do_tin_cay": 92.0, "bao_cau": None}
    return {"du_doan": None, "do_tin_cay": 62.0, "bao_cau": "Không có block đảo"}

def predictor_jump_alternate(history):
    if len(history)<6:
        return {"du_doan": None, "do_tin_cay": 61.0, "bao_cau": "Chưa đủ phiên"}
    jump = all(history[-i]!=history[-i-1] for i in range(1,5))
    if jump:
        return {"du_doan": history[-2], "do_tin_cay": 91.3, "bao_cau": None}
    return {"du_doan": None, "do_tin_cay": 61.0, "bao_cau": "Luân phiên không rõ"}

def predictor_repeat_pattern(history):
    if len(history)<9:
        return {"du_doan": None, "do_tin_cay": 61.0, "bao_cau": "Chưa đủ phiên"}
    patt = history[-3:]
    for i in range(3,9,3):
        if history[-3-i:-i]!=patt:
            return {"du_doan": None, "do_tin_cay": 63.0, "bao_cau": "Không đủ pattern lặp"}
    return {"du_doan": patt[0], "do_tin_cay": 90.0, "bao_cau": None}

# ---- thêm các thuật toán mới tại đây nếu cần --- #

predictors = [
    ("Cầu bệt", predictor_trend),
    ("Pattern 3", predictor_pattern_3),
    ("Hồi quy trọng số", predictor_mean_reversion),
    ("Entropy 20 phiên", predictor_entropy_20),
    ("Gương kép 8", predictor_mirror_8),
    ("Block đảo 5", predictor_block_reverse_5),
    ("Luân phiên", predictor_jump_alternate),
    ("Lặp chuỗi 3", predictor_repeat_pattern),
    # Thêm các thuật toán mới vào đây...
]


@app.route("/")
def home():
    return jsonify({"status": "running", "api": "/api/taixiumd5"})


@app.route("/api/taixiumd5")
def taixiu_api():
    sessions = fetch_sessions()
    history, totals, rows = convert_sessions(sessions)
    # DỰ ĐOÁN CHO PHIÊN TIẾP THEO DỰA VÀO CÁC PHIÊN ĐÃ RA (KHÔNG đoán lại các phiên cũ)
    results = []
    for name, func in predictors:
        try:
            if func.__code__.co_argcount == 2:
                predict = func(history, totals)
            else:
                predict = func(history)
        except Exception as e:
            predict = {"du_doan": None, "do_tin_cay": 0, "bao_cau": f"Error: {e}"}
        row = {"thuat_toan": name}
        row.update(predict)
        results.append(row)
    return jsonify({
        "phien_moi_nhat": rows[0] if rows else {},
        "du_lieu": rows,
        "du_doan_tiep_theo": results,  # Đây là dự đoán cho phiên CHƯA RA tiếp theo!
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)