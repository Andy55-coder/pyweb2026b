import requests
from bs4 import BeautifulSoup

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from flask import Flask, render_template, request
from datetime import datetime
import random

# 判斷是在 Vercel 還是本地
if os.path.exists('serviceAccountKey.json'):
    # 本地環境：讀取檔案
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 雲端環境：從環境變數讀取 JSON 字串
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)

app = Flask(__name__)

@app.route("/")
def index():
    link = "<h1>歡迎進入黃彥璋的網頁</h1>"     
    link += "<a href=/mis>課程</a><hr>" 
    link += "<a href=/today>今天日期</a><hr>" 
    link += "<a href=/about>關於彥璋</a><hr>"
    link += "<a href=/welcome?u=彥璋&dep=靜宜資管>GET傳值</a><hr> "
    link += "<a href=/account>POST傳值(帳號密碼)</a><hr> "
    link += "<a href=/math>簡易計算機</a><hr> " 
    link += "<a href=/cup>擲茭</a><hr>"
    link += "<a href=/read>讀取Firestore資料(根據lab遞減排序,取前3)</a><hr>"
    link += "<a href=/search>查詢老師研究室</a><hr>"
    link += "<a href=/>"
    return link

@app.route("/sp1")
def sp1():
    R = ""
    url = "https://pyweb2026b-haz9.vercel.app/about"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    #print(Data.text)
    sp = BeautifulSoup(Data.text, "html.parser")
    result=sp.select("td a")

    for item in result:
        R += item.text + "<br>" +item.get("href") + "<br><br>"
    return R






@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        keyword = request.form["keyword"]

        db = firestore.client()
        # 請確認你的集合名稱是 "靜宜資管" 還是 "靜宜資管2026a"
        collection_ref = db.collection("靜宜資管")

        docs = collection_ref.get()
        result = ""

        for doc in docs:
            user = doc.to_dict()
            # 模糊搜尋：檢查關鍵字是否在老師姓名中
            if keyword in user.get("name", ""):
                result += f"{user['name']}老師的研究室在 {user.get('lab', '未提供')}<br>"

        if result == "":
            result = "查無資料"

        return result + "<br><a href=/search>返回搜尋</a> | <a href=/>回首頁</a>"

    return """
    <h2>查詢老師研究室</h2>
    <form method="post">
        請輸入老師姓名：
        <input type="text" name="keyword">
        <input type="submit" value="查詢">
    </form>
    <a href="/">回首頁</a>
    """

@app.route("/read")
def read():
    db = firestore.client()
    Temp = "<h3>前3名實驗室資料：</h3>"
    collection_ref = db.collection("靜宜資管")
    # 根據 lab 遞減排序，取前 3 名
    docs = collection_ref.order_by("lab", direction=firestore.Query.DESCENDING).limit(3).get()

    for doc in docs:
        Temp += str(doc.to_dict()) + "<br>"

    return Temp + "<br><a href=/>回首頁</a>"

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>回到網站首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    now_str = f"{now.year}年{now.month}月{now.day}日"
    return render_template("today.html", datetime = now_str)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/welcome", methods=["GET"])
def welcome():
    x = request.values.get("u")
    y = request.values.get("dep")
    return render_template("welcome.html", name = x, dep = y) 

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        return f"您輸入的帳號是：{user}; 密碼為：{pwd} <br><a href=/>回首頁</a>"
    return render_template("account.html")
        
@app.route("/math", methods=["GET", "POST"])
def math():
    if request.method == "POST":
        try:
            x = int(request.form["x"])
            opt = request.form["opt"]
            y = int(request.form["y"])
            
            if opt == "/" and y == 0:
                result = "除數不能等於0"
            else:
                match opt:
                    case "+": result = x + y
                    case "-": result = x - y
                    case "*": result = x * y
                    case "/": result = x / y
                    case _: result = "無效的運算"
            return render_template("math.html", x=x, opt=opt, y=y, result=result)
        except ValueError:
            return "請輸入正確的數字！<br><a href=/math>返回</a>"
    return render_template("math.html")

@app.route('/cup', methods=["GET"])
def cup():
    action = request.values.get("action")
    result = None
    
    if action == 'toss':
        x1 = random.randint(0, 1)
        x2 = random.randint(0, 1)
        
        if x1 != x2:
            msg = "聖筊：表示神明允許、同意，或行事會順利。"
        elif x1 == 0:
            msg = "笑筊：表示神明一笑、不解，或者考慮中，行事狀況不明。"
        else:
            msg = "陰筊：表示神明否定、憤怒，或者不宜行事。"
            
        result = {
            "cup1": "/static/" + str(x1) + ".jpg",
            "cup2": "/static/" + str(x2) + ".jpg",
            "message": msg
        }
        
    return render_template('cup.html', result=result)

if __name__ == "__main__":
    app.run(debug=True)