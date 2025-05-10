import os
from flask import Flask
from threading import Thread

app = Flask('')


@app.route('/')
def home():
    return "I'm alive!"


@app.route('/ping')
def ping():
    return "pong"


def run():
    # 환경 변수에서 PORT 가져오기 (기본값 5000)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


def keep_alive():
    t = Thread(target=run)
    t.start()
