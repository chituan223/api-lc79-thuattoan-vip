from flask import Flask, jsonify
import requests

app = Flask(__name__)

def get_taixiu_data():
    url = "https://wtxmd52.tele68.com/v1/txmd5/sessions"
    try:
        res = requests.get(url, timeout=8)
        res.raise_for_status()
        data = res.json()

        if "list" in data and len(data["list"]) > 0:
            newest = data["list"][0]
            dice = newest.get("dices", [1, 2, 3])
            tong = newest.get("point", sum(dice))

            raw = newest.get("resultTruyenThong", "").upper()
            if raw == "TAI":
                ketqua = "Tài"
            elif raw == "XIU":
                ketqua = "Xỉu"
            else:
                ketqua = "Tài" if tong >= 11 else "Xỉu"

            return {
                "phien": newest.get("id"),
                "xucxac1": dice[0],
                "xucxac2": dice[1],
                "xucxac3": dice[2],
                "tong": tong,
                "ketqua": ketqua,
                "du_doan": "Không có (vercel)",
                "do_tin_cay": 0,
                "id": "lc79"
            }

    except Exception as e:
        return {"error": str(e)}

    return {"error": "Không có dữ liệu"}

@app.route("/", methods=["GET"])
def taixiu():
    return jsonify(get_taixiu_data())
