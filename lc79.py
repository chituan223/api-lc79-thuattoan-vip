# Ví dụ trong file lc79.py

from flask import Flask
app = Flask(__name__)

# Đây là cách bạn định nghĩa đường dẫn:
@app.route('/taixiumd5', methods=['GET', 'POST'])
def taixiu_md5():
    # Logic xử lý của bạn ở đây
    return "Đây là endpoint /taixiumd5"

# Hoặc bạn có thể thêm tiền tố (prefix) 'api' nếu muốn:
@app.route('/api/taixiumd5', methods=['GET', 'POST'])
def api_taixiu_md5():
    # Logic xử lý khác
    return "Đây là endpoint /api/taixiumd5"
