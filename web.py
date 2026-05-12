import requests
from bs4 import BeautifulSoup
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, render_template, request, make_response, jsonify
from datetime import datetime
import random

# --- 1. Firebase 初始化 ---
if os.path.exists('serviceAccountKey.json'):
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 針對雲端環境 (如 Render/Heroku) 使用環境變數
    firebase_config = os.getenv('FIREBASE_CONFIG')
    if firebase_config:
        cred_dict = json.loads(firebase_config)
        cred = credentials.Certificate(cred_dict)
    else:
        raise ValueError("找不到 Firebase 設定檔或環境變數")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# 初始化 Firestore db (全域使用)
db = firestore.client()

app = Flask(__name__)

# --- 2. 首頁路由 ---
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
    link += "<a href=/read>讀取Firestore資料(靜宜資管)</a><hr>"
    link += "<a href=/search>查詢老師研究室</a><hr>"
    link += "<a href=/movie>即將上映電影(爬蟲展示)</a><hr>" 
    link += "<a href=/rate>本週新片爬蟲(寫入資料庫)</a><br>"
    return link

# --- 3. Dialogflow Webhook (電影查詢邏輯) ---
@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json(force=True)
    query_result = req.get("queryResult", {})
    action = query_result.get("action")
    
    info = ""
    
    if action == "rateChoice":
        parameters = query_result.get("parameters", {})
        rate = parameters.get("rate") # Dialogflow 抓到的分級參數
        
        if not rate:
            return make_response(jsonify({"fulfillmentText": "請告訴我您想看哪種分級的電影 (如：普遍級)。"}))

        info = f"我是黃彥璋開發的電影機器人，為您找到分級為【{rate}】的本週新片：\n\n"
        
        # 這裡必須對應爬蟲存入的集合名稱
        collection_ref = db.collection("本週新片含分級")
        docs = collection_ref.where("rate", "==", rate).stream()
        
        result_text = ""
        count = 0
        for doc in docs:
            m = doc.to_dict()
            result_text += f"🎬 {m.get('title')}\n🔗 介紹：{m.get('hyperlink')}\n\n"
            count += 1

        if count == 0:
            info = f"抱歉，目前資料庫中沒有【{rate}】的相關電影資訊。"
        else:
            info += result_text

    return make_response(jsonify({"fulfillmentText": info}))

# --- 4. 電影爬蟲路由 (寫入資料庫) ---
@app.route("/rate")
def rate():
    url = "https://www.atmovies.com.tw/movie/new/"
    data = requests.get(url)
    data.encoding = "utf-8"
    sp = BeautifulSoup(data.text, "html.parser")
    
    # 取得更新日期
    update_info = sp.find(class_="smaller09")
    lastUpdate = update_info.text[5:] if update_info else "未知"

    films = sp.select(".filmList")
    for x in films:
        title = x.find("a").text
        introduce = x.find("p").text
        movie_href = x.find("a").get("href")
        movie_id = movie_href.replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw" + movie_href
        picture = "https://www.atmovies.com.tw/photo101/" + movie_id + "/pm_" + movie_id + ".jpg"

        # 處理分級圖片轉文字
        r_img = x.find(class_="runtime").find("img")
        rate_str = "未列分級"
        if r_img:
            rr = r_img.get("src").replace("/images/cer_", "").replace(".gif", "")
            mapping = {"G": "普遍級", "P": "保護級", "F2": "輔12級", "F5": "輔15級", "R": "限制級"}
            rate_str = mapping.get(rr, "限制級")

        # 寫入 Firestore
        doc = {
            "title": title,
            "introduce": introduce,
            "picture": picture,
            "hyperlink": hyperlink,
            "rate": rate_str,
            "lastUpdate": lastUpdate
        }
        db.collection("本週新片含分級").document(movie_id).set(doc)
        
    return f"本週新片已爬取並存入資料庫！最近更新日期：{lastUpdate}"

# --- 5. 計算機 (安全版本) ---
@app.route("/math", methods=["GET", "POST"])
def math():
    if request.method == "POST":
        try:
            x = int(request.form["x"])
            y = int(request.form["y"])
            opt = request.form["opt"]
            if opt == "+": res = x + y
            elif opt == "-": res = x - y
            elif opt == "*": res = x * y
            elif opt == "/": res = x / y if y != 0 else "除數不可為0"
            return render_template("math.html", x=x, opt=opt, y=y, result=res)
        except:
            return "輸入格式錯誤"
    return render_template("math.html")

# --- 6. 其他基礎路由 ---
@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        keyword = request.form["keyword"]
        docs = db.collection("靜宜資管").get()
        result = ""
        for doc in docs:
            user = doc.to_dict()
            if keyword in user.get("name", ""):
                result += f"{user['name']}老師的研究室在 {user.get('lab')}<br>"
        return (result if result else "查無資料") + "<br><a href=/search>返回</a>"
    return """<h2>查詢老師</h2><form method="post">姓名關鍵字：<input type="text" name="keyword"><input type="submit"></form>"""

@app.route("/mis")
def course(): return "<h1>資訊管理導論</h1><a href=/>回到首頁</a>"

@app.route("/today")
def today():
    now_str = datetime.now().strftime("%Y年%m月%d日")
    return render_template("today.html", datetime=now_str)

@app.route("/about")
def about(): return render_template("about.html")

@app.route("/welcome")
def welcome():
    u = request.values.get("u")
    dep = request.values.get("dep")
    return render_template("welcome.html", name=u, dep=dep)

@app.route('/cup')
def cup():
    res = None
    if request.values.get("action") == 'toss':
        x1, x2 = random.randint(0,1), random.randint(0,1)
        msg = "聖筊" if x1 != x2 else ("笑筊" if x1==0 else "陰筊")
        res = {"cup1": f"/static/{x1}.jpg", "cup2": f"/static/{x2}.jpg", "message": msg}
    return render_template('cup.html', result=res)

if __name__ == "__main__":
    app.run(debug=True)