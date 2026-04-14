import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, render_template, request
from datetime import datetime
import random

# --- Firebase 初始化區塊 ---
if os.path.exists('serviceAccountKey.json'):
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

app = Flask(__name__)

@app.route("/")
def index():
    # 在首頁加入查詢老師的超連結
    link = "<h1>歡迎進入黃彥璋的網頁</h1>"     
    link += "<a href='/teacher_search'>🔍 線上查詢老師研究室</a><hr>" 
    link += "<a href=/mis>課程</a><hr>" 
    link += "<a href=/today>今天日期</a><hr>" 
    link += "<a href=/about>關於彥璋</a><hr>"
    link += "<a href=/welcome?u=彥璋&dep=靜宜資管>GET傳</a><hr> "
    link += "<a href=/account>POST傳值(帳號密碼)</a><hr> "
    link += "<a href=/math>簡易計算機</a><hr> " 
    link += "<a href=/cup>擲茭</a><hr>"
    link += "<a href=/read>讀取Firestore資料(根據lab遞減排序,取前4)</a><br>"
    return link

# --- 新增：純字串查詢路由 ---
@app.route("/teacher_search", methods=["GET", "POST"])
def teacher_search():
    # 建立一個簡單的 HTML 表單字串
    content = """
    <h2>老師研究室查詢系統</h2>
    <form method="POST">
        請輸入老師姓名關鍵字：<input type="text" name="keyword">
        <input type="submit" value="開始查詢">
    </form>
    <br><a href="/">回到首頁</a><hr>
    """
    
    if request.method == "POST":
        keyword = request.form.get("keyword")
        db = firestore.client()
        collection_ref = db.collection("靜宜資管")
        docs = collection_ref.get()
        
        content += f"<h3>查詢「{keyword}」的結果：</h3>"
        found = False
        for doc in docs:
            user = doc.to_dict()
            # 判斷關鍵字是否在老師名字內
            if keyword in user.get("name", ""):
                found = True
                # 同時加上一個導向 Google 搜尋的 Link
                google_link = f"https://www.google.com/search?q=靜宜大學+{user['name']}"
                content += f"● <b>{user['name']}</b> 老師的研究室在：{user['lab']} "
                content += f" <a href='{google_link}' target='_blank'>[查看老師簡介]</a><br>"
        
        if not found:
            content += "抱歉，找不到這位老師的資料。"
            
    return content

# 原有路由保持不變
@app.route("/read")
def read():
    db = firestore.client()
    Temp = ""
    collection_ref = db.collection("靜宜資管")
    docs = collection_ref.order_by("lab", direction=firestore.Query.DESCENDING).limit(3).get()
    for doc in docs:
        Temp += str(doc.to_dict()) + "<br>"
    return Temp + "<br><a href='/'>回首頁</a>"

if __name__ == "__main__":
    app.run()