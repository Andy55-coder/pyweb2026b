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

# --- Firebase 初始化 ---
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
    link += "<a href=/movie>即將上映電影</a><hr>" 
    link += "<a href=/movie2>讀取開眼電影即將上映影片，寫入Firestore</a><hr>"
    link += "<a href=/movie3>電影查詢</a><hr>"
    link += "<a href=/traffic>台中市交通事故查詢</a><hr>"
    link += "<a href=/weather>各縣市天氣查詢</a><hr>"
    link += "<a href=/rate>本週新片含分級</a><br>"
    return link


@app.route("/rate")
def rate():
    #本週新片
    url = "https://www.atmovies.com.tw/movie/new/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text[5:]
    print(lastUpdate)
    print()

    result=sp.select(".filmList")

    for x in result:
        title = x.find("a").text
        introduce = x.find("p").text

        movie_id = x.find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw/movie/" + movie_id
        picture = "https://www.atmovies.com.tw/photo101/" + movie_id + "/pm_" + movie_id + ".jpg"

        r = x.find(class_="runtime").find("img")
        rate = ""
        if r != None:
            rr = r.get("src").replace("/images/cer_", "").replace(".gif", "")
            if rr == "G":
                rate = "普遍級"
            elif rr == "P":
                rate = "保護級"
            elif rr == "F2":
                rate = "輔12級"
            elif rr == "F5":
                rate = "輔15級"
            else:
                rate = "限制級"

        t = x.find(class_="runtime").text

        t1 = t.find("片長")
        t2 = t.find("分")
        showLength = t[t1+3:t2]

        t1 = t.find("上映日期")
        t2 = t.find("上映廳數")
        showDate = t[t1+5:t2-8]

        doc = {
            "title": title,
            "introduce": introduce,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": int(showLength),
            "rate": rate,
            "lastUpdate": lastUpdate
        }

        db = firestore.client()
        doc_ref = db.collection("本週新片含分級").document(movie_id)
        doc_ref.set(doc)
    return "本週新片已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate


@app.route("/weather", methods=["GET", "POST"])
def weather():
    if request.method == "POST":
        city = request.form["city"]
        city = city.replace("台", "臺")  
        token = "rdec-key-123-45678-011121314" 
        url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={token}&format=JSON&locationName={city}"
        
        try:
            data = requests.get(url)
            json_data = json.loads(data.text)
            
            
            if json_data["records"]["location"]:
                location_data = json_data["records"]["location"][0]
                # 天氣現象 (例如：多雲時陰)
                weather_state = location_data["weatherElement"][0]["time"][0]["parameter"]["parameterName"]
                # 降雨機率
                rain_chance = location_data["weatherElement"][1]["time"][0]["parameter"]["parameterName"]
                
                result = f"<h2>{city} 的天氣預報</h2>"
                result += f"目前天氣狀況：{weather_state}<br>"
                result += f"降雨機率：{rain_chance}%<br>"
            else:
                result = f"<h2>抱歉，找不到 '{city}' 的氣象資料。</h2>"
                result += "請確認縣市名稱是否正確（例如：臺中市、臺北市）。"
                
        except Exception as e:
            result = f"查詢失敗，錯誤原因：{e}"

        result += "<br><br><a href='/weather'>重新查詢</a> | <a href='/'>回首頁</a>"
        return result

    return """
    <h2>各縣市天氣查詢</h2>
    <form method="post">
        請輸入欲查詢的縣市（例如：臺中市）：
        <input type="text" name="city" placeholder="臺中市">
        <input type="submit" value="查詢">
    </form>
    <a href="/">回首頁</a>
    """

# --- 原有的路由 (保持不變) ---
@app.route("/traffic", methods=["GET", "POST"])
def traffic():
    if request.method == "POST":
        road_name = request.form["road"]
        url = "https://datacenter.taichung.gov.tw/swagger/OpenData/a1b899c0-511f-4e3d-b22b-814982a97e41"
        try:
            data = requests.get(url)
            json_data = json.loads(data.text)
            result_text = f"<h2>路名：{road_name} 的查詢結果</h2>"
            found = False
            for item in json_data:
                if road_name in item["路口名稱"]:
                    found = True
                    result_text += f"<b>{item['路口名稱']}</b>：發生 {item['總件數']} 件，主因是 {item['主要肇因']}<br><br>"
            if not found: result_text += "抱歉，查無相關資料！"
        except Exception as e: result_text = f"發生錯誤：{e}"
        return result_text + "<br><a href='/traffic'>重新查詢</a> | <a href='/'>回首頁</a>"
    return """<h2>台中市交通事故熱點查詢</h2><form method="post">路名：<input type="text" name="road"><input type="submit" value="查詢"></form><a href="/">回首頁</a>"""

@app.route("/movie3", methods=["GET", "POST"])
def movie3():
    if request.method == "POST":
        keyword = request.form["keyword"]
        url = "https://www.atmovies.com.tw/movie/next/"
        data = requests.get(url); data.encoding = "utf-8"
        sp = BeautifulSoup(data.text, "html.parser")
        result = sp.select(".filmListAllX li")
        output = f"<h2>搜尋結果：{keyword}</h2>"; found = False
        for item in result:
            title = item.find("img").get("alt")
            if keyword in title:
                found = True
                link = "https://www.atmovies.com.tw" + item.find("a").get("href")
                output += f"{title}<br><a href='{link}' target='_blank'>查看電影</a><br><br>"
        if not found: output += "查無相關電影 😢<br>"
        return output + "<a href='/movie3'>返回</a>"
    return """<h2>電影查詢</h2><form method="post"><input type="text" name="keyword"><input type="submit" value="搜尋"></form><a href="/">回首頁</a>"""

@app.route("/movie2")
def movie2():
    url = "http://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url); Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".filmListAllX li")
    lastUpdate = sp.find("div", class_="smaller09").text[5:]
    db = firestore.client()
    for item in result:
        title = item.find("div", class_="filmtitle").text
        movie_id = item.find("div", class_="filmtitle").find("a").get("href").replace("/", "").replace("movie", "")
        doc = {"title": title, "lastUpdate": lastUpdate} # 簡化示範
        db.collection("電影").document(movie_id).set(doc)
    return "近期上映電影已爬蟲及存檔完畢，日期：" + lastUpdate 

@app.route("/movie")
def movie():
    url = "https://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url); Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".filmListAllX li")
    output = "<h2>即將上映電影</h2>"
    for item in result:
        name = item.find("img").get("alt")
        output += f"<div>{name}</div>"
    return output + "<br><a href=/>回首頁</a>"

@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        keyword = request.form["keyword"]
        db = firestore.client()
        docs = db.collection("靜宜資管").get()
        result = ""
        for doc in docs:
            user = doc.to_dict()
            if keyword in user.get("name", ""):
                result += f"{user['name']}老師的研究室在 {user.get('lab')}<br>"
        return (result if result else "查無資料") + "<br><a href=/search>返回</a>"
    return """<h2>查詢老師</h2><form method="post"><input type="text" name="keyword"><input type="submit"></form>"""

@app.route("/read")
def read():
    db = firestore.client()
    docs = db.collection("靜宜資管").order_by("lab", direction=firestore.Query.DESCENDING).limit(3).get()
    temp = "<h3>前3名實驗室：</h3>"
    for doc in docs: temp += str(doc.to_dict()) + "<br>"
    return temp + "<br><a href=/>回首頁</a>"

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
    u = request.values.get("u"); dep = request.values.get("dep")
    return render_template("welcome.html", name=u, dep=dep)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        return f"帳號：{request.form['user']} <br><a href=/>回首頁</a>"
    return render_template("account.html")

@app.route("/math", methods=["GET", "POST"])
def math():
    if request.method == "POST":
        x = int(request.form["x"]); y = int(request.form["y"]); opt = request.form["opt"]
        res = eval(f"{x}{opt}{y}") # 簡易運算
        return render_template("math.html", x=x, opt=opt, y=y, result=res)
    return render_template("math.html")

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