import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request
from datetime import datetime
import random

# --- Firebase 初始化優化版 ---
def init_firebase():
    if not firebase_admin._apps:
        try:
            if os.path.exists('serviceAccountKey.json'):
                # 本地開發環境
                cred = credentials.Certificate('serviceAccountKey.json')
                firebase_admin.initialize_app(cred)
            else:
                # Vercel 雲端環境
                firebase_config = os.getenv('FIREBASE_CONFIG')
                if firebase_config:
                    # 確保環境變數能被正確解析為 JSON
                    cred_dict = json.loads(firebase_config)
                    cred = credentials.Certificate(cred_dict)
                    firebase_admin.initialize_app(cred)
                else:
                    return "找不到 FIREBASE_CONFIG 環境變數"
        except Exception as e:
            return f"Firebase 初始化失敗: {str(e)}"
    return None

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

@app.route("/teacher_search", methods=["GET", "POST"])
def teacher_search():
    # 確保連線正常
    err = init_firebase()
    if err: return err

    content = "<h2>師資研究室查詢系統</h2>"
    content += '<form method="POST">請輸入老師姓名關鍵字：<input type="text" name="kw"><input type="submit" value="開始查詢"></form>'
    
    if request.method == "POST":
        keyword = request.form.get("kw")
        try:
            db = firestore.client()
            docs = db.collection("靜宜資管").get()
            
            content += f"<hr><h4>查詢「{keyword}」的結果：</h4>"
            found = False
            for doc in docs:
                user = doc.to_dict()
                if keyword in user.get("name", ""):
                    found = True
                    link_url = f"https://www.google.com/search?q=靜宜大學+{user['name']}"
                    content += f"● <b>{user['name']}</b> 老師的研究室在：{user['lab']} "
                    content += f" <a href='{link_url}' target='_blank'>[Google 搜尋]</a><br>"
            if not found:
                content += "找不到相關老師資料。"
        except Exception as e:
            content += f"<p style='color:red;'>查詢出錯：{str(e)}</p>"
            
    content += "<br><hr><a href='/'>回到首頁</a>"
    return content

@app.route("/read")
def read():
    err = init_firebase()
    if err: return err

    try:
        db = firestore.client()
        Temp = "<h3>最新 3 筆老師資料：</h3>"
        collection_ref = db.collection("靜宜資管")
        docs = collection_ref.order_by("lab", direction=firestore.Query.DESCENDING).limit(3).get()
        for doc in docs:
            Temp += str(doc.to_dict()) + "<br>"
        return Temp + "<br><a href='/'>回首頁</a>"
    except Exception as e:
        return f"讀取失敗: {str(e)} <br><a href='/'>回首頁</a>"

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><br><a href='/'>回到首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    return f"<h1>今天日期：{now.year}年{now.month}月{now.day}日</h1><br><a href='/'>回到首頁</a>"

@app.route("/welcome", methods=["GET"])
def welcome():
    x = request.values.get("u")
    y = request.values.get("dep")
    return f"<h1>歡迎，{x}！</h1><p>部門：{y}</p><br><a href='/'>回首頁</a>"

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form.get("user")
        pwd = request.form.get("pwd")
        return f"您輸入的帳號是：{user}; 密碼為：{pwd}<br><a href='/'>回首頁</a>"
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
        try:
            x = int(request.form["x"])
            opt = request.form["opt"]
            y = int(request.form["y"])
            if opt == "/" and y == 0: result = "除數不能等於0"
            else:
                if opt == "+": result = x + y
                elif opt == "-": result = x - y
                elif opt == "*": result = x * y
                elif opt == "/": result = x / y
            return f"結果：{result}<br><a href='/math'>回計算機</a> | <a href='/'>回首頁</a>"
        except: return "輸入錯誤<br><a href='/math'>重試</a>"
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
        msg = "聖筊" if x1 != x2 else ("笑筊" if x1 == 0 else "陰筊")
        return f"<h3>結果：{msg}</h3><br><a href='/cup?action=toss'>再擲一次</a> | <a href='/'>回首頁</a>"
    return "<a href='/cup?action=toss'><button>按此擲筊</button></a>"

# Vercel 部署不需要 app.run()