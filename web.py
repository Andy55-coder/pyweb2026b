import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from flask import Flask, render_template, request
from datetime import datetime
import random

# ================= Firebase 初始化 =================
if not firebase_admin._apps:

    firebase_config = os.getenv('FIREBASE_CONFIG')

    if firebase_config:
        cred_dict = json.loads(firebase_config)
        cred = credentials.Certificate(cred_dict)
    else:
        cred = credentials.Certificate('serviceAccountKey.json')

    firebase_admin.initialize_app(cred)

# ================= Flask =================
app = Flask(__name__)

# ================= 首頁 =================
@app.route("/")
def index():
    link = "<h1>歡迎進入黃彥璋的網頁</h1>"
    link += "<a href=/mis>課程</a><hr>"
    link += "<a href=/today>今天日期</a><hr>"
    link += "<a href=/about>關於彥璋</a><hr>"
    link += "<a href=/welcome?u=彥璋&dep=靜宜資管>GET傳</a><hr>"
    link += "<a href=/account>POST傳值(帳號密碼)</a><hr>"
    link += "<a href=/math>簡易計算機</a><hr>"
    link += "<a href=/cup>擲茭</a><hr>"
    link += "<a href=/read>讀取Firestore資料</a><hr>"
    link += "<a href=/search>🔥老師查詢系統</a><hr>"
    return link


# ================= Firestore 讀取 =================
@app.route("/read")
def read():
    db = firestore.client()
    result = ""

    docs = (
        db.collection("靜宜資管")
        .order_by("lab", direction=firestore.Query.DESCENDING)
        .limit(3)
        .get()
    )

    for doc in docs:
        result += str(doc.to_dict()) + "<br>"

    return result


# ================= 🔥 Firestore 查詢 =================
@app.route("/search", methods=["GET", "POST"])
def search():
    db = firestore.client()

    if request.method == "POST":
        keyword = request.form.get("keyword", "").strip()

        if not keyword:
            return "請輸入查詢內容<br><a href='/search'>返回</a>"

        docs = (
            db.collection("靜宜資管")
            .order_by("name")
            .start_at([keyword])
            .end_at([keyword + "\uf8ff"])
            .get()
        )

        result = ""

        for doc in docs:
            user = doc.to_dict()
            result += f"{user['name']}老師的研究室在 {user['lab']}<br>"

        if not result:
            result = "查無資料<br>"

        return result + '<br><a href="/search">再查一次</a>'

    return """
    <h2>老師查詢系統 (Firestore)</h2>
    <form method="POST">
        請輸入老師名字：
        <input type="text" name="keyword">
        <input type="submit" value="查詢">
    </form>
    <br>
    <a href="/">回首頁</a>
    """


# ================= 其他功能 =================
@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>回首頁</a>"


@app.route("/today")
def today():
    now = datetime.now()
    now_str = f"{now.year}年{now.month}月{now.day}日"
    return render_template("today.html", datetime=now_str)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/welcome")
def welcome():
    x = request.values.get("u")
    y = request.values.get("dep")
    return render_template("welcome.html", name=x, dep=y)


@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form.get("user")
        pwd = request.form.get("pwd")
        return f"帳號：{user} 密碼：{pwd}"
    return render_template("account.html")


@app.route("/math", methods=["GET", "POST"])
def math():
    if request.method == "POST":
        x = int(request.form["x"])
        y = int(request.form["y"])
        opt = request.form["opt"]

        if opt == "/" and y == 0:
            result = "除數不能等於0"
        else:
            match opt:
                case "+": result = x + y
                case "-": result = x - y
                case "*": result = x * y
                case "/": result = x / y
                case _: result = "未知運算"

        return render_template("math.html", x=x, y=y, opt=opt, result=result)

    return render_template("math.html")


@app.route('/cup')
def cup():
    action = request.values.get("action")
    result = None

    if action == 'toss':
        x1 = random.randint(0, 1)
        x2 = random.randint(0, 1)

        if x1 != x2:
            msg = "聖筊"
        elif x1 == 0:
            msg = "笑筊"
        else:
            msg = "陰筊"

        result = {
            "cup1": "/static/" + str(x1) + ".jpg",
            "cup2": "/static/" + str(x2) + ".jpg",
            "message": msg
        }

    return render_template('cup.html', result=result)


# ================= 啟動 =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)