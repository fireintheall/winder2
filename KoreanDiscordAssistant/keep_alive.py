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
    app.run(host='0.0.0.0', port=5000)  # 포트를 5000으로 설정


def keep_alive():
    t = Thread(target=run)
    t.start()
