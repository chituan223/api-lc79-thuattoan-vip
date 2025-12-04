from flask import Flask
# (Bạn có thể cân nhắc đổi tên file thành api.py hoặc index.py để tuân thủ quy ước chung)

app = Flask(__name__) # <--- Vercel tìm thấy biến 'app' này

@app.route('/...')
def my_api():
    return '...'

# KHÔNG cần dòng này khi deploy lên Vercel:
# if __name__ == '__main__':
#     app.run()
