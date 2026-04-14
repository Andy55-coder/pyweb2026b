import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request
from datetime import datetime
import random

# --- Firebase 初始化：支援本地檔案與 Vercel 環境變數 ---
if os.path.exists('serviceAccountKey.json'):
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 部署到 Vercel 時，請在 Settings -> Environment Variables 設定 FIREBASE_CONFIG
    firebase_config = os.getenv('FIREBASE_CONFIG')
    if firebase_config:
        cred_dict = json.loads(firebase_config)
        cred = credentials.Certificate(cred_dict)
    else:
        cred = None

if cred and not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

app = Flask(__name__)

@app.route("/")
def index():
    link = "<h1>歡迎進入黃彥璋的網頁</h1>"     
    link += "<a href='/mis'>課程</a><hr>" 
    link += "<a href='/today'>今天日期</a><hr>" 
    link += "<a href='/welcome?u=彥璋&dep=靜宜資管'>GET傳值</a><hr> "
    link += "<a href='/account'>POST傳值(帳號密碼)</a><hr> "
    link += "<a href='/math'>簡易計算機</a><hr> " 
    link += "<a href='/cup'>擲茭</a><hr>"
    link += "<a href='/read'>讀取Firestore資料 (排序取前3)</a><hr>"
    link += "<a href='/teacher_search'>查詢老師研究室</a><br>"
    return link

# --- 新增功能：線上查詢老師名字 (純字串回傳，不需 HTML 檔) ---
@app.route("/teacher_search", methods=["GET", "POST"])
def teacher_search():
    content = "<h2>師資研究室查詢系統</h2>"
    content += '<form method="POST">請輸入老師姓名關鍵字：<input type="text" name="kw"><input type="submit" value="開始查詢"></form>'
    
    if request.method == "POST":
        keyword = request.form.get("kw")
        db = firestore.client()
        docs = db.collection("靜宜資管").get()
        
        content += f"<hr><h4>查詢「{keyword}」的結果：</h4>"
        found = False
        for doc in docs:
            user = doc.to_dict()
            if keyword in user.get("name", ""):
                found = True
                # 新增一個外部連結
                link_url = f"https://www.google.com/search?q=靜宜大學+{user['name']}"
                content += f"● <b>{user['name']}</b> 老師的研究室在：{user['lab']} "
                content += f" <a href='{link_url}' target='_blank'>[點我 Google 搜尋]</a><br>"
        if not found:
            content += "抱歉，資料庫中找不到符合條件的老師。"
            
    content += "<br><hr><a href='/'>回到首頁</a>"
    return content

@app.route("/read")
def read():
    db = firestore.client()
    Temp = "<h3>資料庫前 3 筆資料：</h3>"
    collection_ref = db.collection("靜宜資管")
    docs = collection_ref.order_by("lab", direction=firestore.Query.DESCENDING).limit(3).get()
    for doc in docs:
        Temp += str(doc.to_dict()) + "<br>"
    return Temp + "<br><a href='/'>回首頁</a>"

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><br><a href='/'>回到網站首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    date_str = f"{now.year}年{now.month}月{now.day}日"
    return f"<h1>今天日期：{date_str}</h1><br><a href='/'>回到網站首頁</a>"

@app.route("/welcome", methods=["GET"])
def welcome():
    x = request.values.get("u")
    y = request.values.get("dep")
    return f"<h1>歡迎，{x}！</h1><p>部門：{y}</p><br><a href='/'>回首頁</a>"

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        return f"您輸入的帳號是：{user}; 密碼為：{pwd}<br><a href='/'>回首頁</a>"
    else:
        return """
            <form method='POST'>
                帳號：<input type='text' name='user'><br>
                密碼：<input type='password' name='pwd'><br>
                <input type='submit' value='登入'>
            </form>
        """

@app.route("/math", methods=["GET", "POST"])
def math():
    if request.method == "POST":
        x = int(request.form["x"])
        opt = request.form["opt"]
        y = int(request.form["y"])
        result = 0
        if opt == "/" and y == 0:
            result = "除數不能等於0"
        else:
            match opt:
                case "+": result = x + y
                case "-": result = x - y
                case "*": result = x * y
                case "/": result = x / y
        return f"計算結果：{x} {opt} {y} = {result}<br><a href='/math'>重新計算</a> | <a href='/'>回首頁</a>"
    else:
        return """
            <form method='POST'>
                數字1：<input type='number' name='x'><br>
                符號：<select name='opt'><option value='+'>+</option><option value='-'>-</option><option value='*'>*</option><option value='/'>/</option></select><br>
                數字2：<input type='number' name='y'><br>
                <input type='submit' value='計算'>
            </form>
        """

@app.route('/cup', methods=["GET"])
def cup():
    action = request.values.get("action")
    if action == 'toss':
        x1, x2 = random.randint(0, 1), random.randint(0, 1)
        if x1 != x2: msg = "聖筊：表示神明允許、同意。"
        elif x1 == 0: msg = "笑筊：表示神明不解，考慮中。"
        else: msg = "陰筊：表示神明否定。"
        return f"<h3>結果：{msg}</h3><br><a href='/cup?action=toss'>再擲一次</a> | <a href='/'>回首頁</a>"
    else:
        return "<h2>按下按鈕擲筊</h2><a href='/cup?action=toss'><button>擲筊</button></a><br><a href='/'>回首頁</a>"

if __name__ == "__main__":
    app.run()