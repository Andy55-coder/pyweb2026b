import os
import json
import random
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, render_template, request, make_response, jsonify
from google import genai
from google.genai import types

# ================== Firebase 初始化 ==================
# 判斷是在 Vercel 還是本地環境
if not firebase_admin._apps:
    if os.path.exists('serviceAccountKey.json'):
        cred = credentials.Certificate('serviceAccountKey.json')
    else:
        firebase_config = os.getenv('FIREBASE_CONFIG')
        cred_dict = json.loads(firebase_config)
        cred = credentials.Certificate(cred_dict)

    firebase_admin.initialize_app(cred)

app = Flask(__name__)
client = genai.Client()



@app.route("/")
def index():
    # 修正首頁歡迎名稱，並維持原本的超連結架構
    link = "<h1>歡迎進入網頁首頁</h1>"
    link += "<a href=/mis>課程</a><hr>"
    link += "<a href=/today>今天日期</a><hr>"
    link += "<a href=/about>關於我</a><hr>"
    link += "<a href=/welcome?u=彥璋&dep=靜宜資管>GET傳值</a><hr>"   
    link += "<a href=/account>POST傳值(帳號密碼)</a><hr>" 
    link += "<a href=/math>數學運算</a><hr>" 
    link += "<a href=/math2>次方與根號計算</a><hr>" 
    link += "<a href=/cup>擲茭</a><hr>"
    link += "<a href=/read>讀取Firestore資料</a><hr>"
    link += "<a href=/search>查詢老師研究室</a><hr>"
    link += "<a href=/movies2>即將上映電影</a><hr>"
    link += "<a href=/movie2>寫入電影資料</a><hr>"
    link += "<a href=/movie3>查詢電影</a><hr>"
    link += "<a href=/road>十大肇事路口</a><hr>"
    link += "<a href=/weather>天氣預報</a><hr>"
    link += "<a href=/rate>電影分級</a><hr>"
    link += "<a href=/demo>聊天機器人</a><hr>"
    link += "<a href=/AI>Gemini</a><hr>"
    link += "<a href=/ask>問答</a><hr>"
    return link

@app.route('/ask', methods=['GET', 'POST']) 
def ask():
    if request.method == "POST":
        user_prompt = request.form.get('prompt', '')
        if not user_prompt:
            return "請輸入內容", 400
        try:
            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=user_prompt,
            )
            return response.text
        except Exception as e:
            return f"發生錯誤: {str(e)}", 500

    else:    
        # 當使用者直接打開網頁 (GET) 時，顯示輸入框畫面
        return render_template("ask.html")


@app.route("/AI")
def AI():
    # 每次使用者拜訪該路徑時，直接使用全域的 client 呼叫模型
    response = client.models.generate_content(
        model='gemini-3.5-flash',
        contents='我想查詢靜宜大學資管系的評價？',
    )
    return response.text

@app.route("/demo")
def demo():
    return render_template("demo.html")


def mis():
    # 補上原本缺少的課程資訊路由
    return "<h2>資訊管理導論（MIS）相關課程資訊頁面</h2><br><a href='/'>回首頁</a>"


@app.route("/search")
def search():
    # 補上原本缺少的查詢老師研究室路由
    return "<h2>查詢老師研究室頁面（開發中）</h2><br><a href='/'>回首頁</a>"


@app.route("/read")
def read():
    # 補上原本首頁有連結但程式碼缺少的簡單讀取範例
    try:
        db = firestore.client()
        docs = db.collection("電影").limit(5).get()
        R = "<h2>Firestore 電影資料庫抽樣讀取測試</h2>"
        for doc in docs:
            R += f"ID: {doc.id} => {doc.to_dict().get('title')}<br>"
        if not docs:
            R += "目前資料庫無資料"
        return R + "<br><a href='/'>回首頁</a>"
    except Exception as e:
        return f"讀取失敗：{str(e)}<br><a href='/'>回首頁</a>"


# ================== Webhook (Dialogflow) ==================@app.route("/webhook", methods=["POST"])
def webhook():
    req = request.get_json(force=True)
    
    # 💡 優化 2：安全地取得 action，若結構不符則預設為空字串
    query_result = req.get("queryResult", {})
    action = query_result.get("action", "")
    
    # 預設回傳訊息，防止 action 都不匹配時報錯
    info = "抱歉，我聽不懂你在說什麼。" 
    
    # 1. 處理電影分級查詢
    if action == "rateChoice":
        parameters = query_result.get("parameters", {})
        rate = parameters.get("rate")
        
        if not rate:
            info = "請告訴我您想查詢的電影分級（例如：普遍級、輔12級）。"
        else:
            info = f"我是黃彥璋設計的電影聊天機器人，您選擇的分級是：{rate}，相關電影：\n\n"
            
            # 集合名稱改為 "本週新片含分級"
            collection_ref = db.collection("本週新片含分級")
            
            # 使用精確查詢
            docs = collection_ref.where("rate", "==", rate).get()
            
            result = ""
            for doc in docs:
                movie_data = doc.to_dict()
                title = movie_data.get("title", "未知片名")
                picture = movie_data.get("picture", "#")
                
                result += f"🎬 片名：{title}\n"
                result += f"🔗 圖片/連結：{picture}\n\n"
            
            if not result:
                result = f"找不到符合 {rate} 的電影，請確認分級輸入是否正確（例如：輔12級）。"
                
            info += result

    # 2. 當 Dialogflow 聽不懂時，交給 Gemini 自由發揮
    elif action == "input.unknown":
        user_query = query_result.get("queryText", "")
        
        # 設定希望限制的最大 Token 數
        ai_config = genai.types.GenerateContentConfig(
            max_output_tokens=500
        )

        try:
            # 💡 優化 3：加入 try-except，避免 Gemini API 呼叫失敗導致整個 Webhook 崩潰
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=user_query,
                config=ai_config
            )
            
            # 確保有拿到文字回應
            if response.text:
                info = response.text
            else:
                info = "我現在稍微有點混亂，請換個方式問我試試看！"
        except Exception as e:
            print(f"Gemini API 發生錯誤: {e}")
            info = "真抱歉，我的大腦暫時連不上線，請稍後再試。"
    
    # 3. 其他未定義的 Action
    else:
        info = "Action 不匹配，無法處理此請求。"

    # 統一在最外層回傳給 Dialogflow
    return make_response(jsonify({"fulfillmentText": info}))
# ================== movie2 ==================
@app.route("/movie2")
def movie2():
    url = "http://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".filmListAllX li")
    lastUpdate = sp.find("div", class_="smaller09").text[5:]

    db = firestore.client()

    for item in result:
        picture = item.find("img").get("src").replace(" ", "")
        title = item.find("div", class_="filmtitle").text
        movie_id = item.find("div", class_="filmtitle").find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw" + item.find("div", class_="filmtitle").find("a").get("href")

        show = item.find("div", class_="runtime").text.replace("上映日期：", "")
        show = show.replace("片長：", "")
        show = show.replace("分", "")
        showDate = show[0:10]
        showLength = show[13:]

        doc = {
            "title": title,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": showLength,
            "lastUpdate": lastUpdate
        }

        db.collection("電影").document(movie_id).set(doc)

    return "近期上映電影已寫入Firestore，更新時間：" + lastUpdate


# ================== movie3 ==================
@app.route("/movie3", methods=["GET", "POST"])
def movie3():
    if request.method == "POST":
        keyword = request.form["keyword"]

        db = firestore.client()
        docs = db.collection("電影").get()

        result = "<h2>查詢結果</h2>"

        for doc in docs:
            movie = doc.to_dict()
            if keyword in movie["title"]:
                result += f"""
                <img src="{movie['picture']}" width="100"><br>
                片名：{movie['title']}<br>
                上映日：{movie['showDate']}<br>
                片長：{movie['showLength']}<br>
                <a href="{movie['hyperlink']}" target="_blank">詳細資訊</a>
                <hr>
                """

        if result == "<h2>查詢結果</h2>":
            result += "查無資料"

        return result + '<br><a href="/movie3">返回</a>'

    return """
    <h2>電影查詢</h2>
    <form method="post">
        關鍵字：
        <input type="text" name="keyword">
        <input type="submit" value="查詢">
    </form>
    <a href="/">回首頁</a>
    """


# ================== 電影列表 ==================
@app.route("/movies2")
def movies2():
    url = "https://www.atmovies.com.tw/movie/next/"
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    res.encoding = "utf-8"

    soup = BeautifulSoup(res.text, "html.parser")
    items = soup.select("ul.filmListAllX li a")

    R = "<h2>即將上映電影</h2>"
    R += '<a href="/">🏠 回首頁</a><hr>'

    for a in items:
        name = a.text.strip()
        link = "https://www.atmovies.com.tw" + a.get("href")
        R += f'<a href="{link}" target="_blank">{name}</a><br><br>'

    return R


# ================== 其他功能路由 ==================
@app.route("/today")
def today():
    now = datetime.now()
    return f"{now.year}年{now.month}月{now.day}日"


@app.route("/about")
def about():
    return render_template("mis2a.html")


@app.route("/welcome")
def welcome():
    x = request.values.get("u")
    y = request.values.get("dep")
    return render_template("welcome.html", name=x, dep=y)


@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        return f"您輸入的帳號是：{user}; 密碼為：{pwd}"
    return render_template("account.html")


@app.route("/math", methods=["GET", "POST"])
def math():
    if request.method == "POST":
        x = int(request.form["x"])
        opt = request.form["opt"]
        y = int(request.form["y"])

        if opt == "/" and y == 0:
            return "除數不能為0"

        match opt:
            case "+": r = x + y
            case "-": r = x - y
            case "*": r = x * y
            case "/": r = x / y

        return f"{x}{opt}{y}={r}<br><a href=/>返回首頁</a>"

    return render_template("math.html")


@app.route("/rate")
def rate():
    # 本週新片
    url = "https://www.atmovies.com.tw/movie/new/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text[5:]

    result = sp.select(".filmList")

    for x in result:
        title = x.find("a").text
        introduce = x.find("p").text

        movie_id = x.find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw/movie/" + movie_id
        picture = "https://www.atmovies.com.tw/photo101/" + movie_id + "/pm_" + movie_id + ".jpg"

        r = x.find(class_="runtime").find("img")
        rate = ""
        if r is not None:
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


@app.route("/math2", methods=["GET", "POST"])
def math2():
    result = None
    if request.method == "POST":
        x = int(request.form.get("x"))
        opt = request.form.get("opt")
        y = int(request.form.get("y"))

        match opt:
            case "∧":
                result = x ** y
            case "√":
                result = x ** (1/y) if y != 0 else "錯誤"

    return render_template("math2.html", result=result)


@app.route("/road")
def road():
    R = ""
    url = "https://newdatacenter.taichung.gov.tw/api/v1/no-auth/resource.download?rid=a1b899c0-511f-4e3d-b22b-814982a97e41"
    Data = requests.get(url)
    JsonData = json.loads(Data.text)

    for item in JsonData:
        R += item["路口名稱"] + "，總共發生" + str(item["總件數"]) + "件事故<br>"

    return R


@app.route("/weather", methods=["GET", "POST"])
def weather():
    result = ""

    if request.method == "POST":
        city = request.form["city"]
        city = city.replace("台", "臺")

        token = "rdec-key-123-45678-011121314"
        url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization=" + token + "&format=JSON&locationName=" + city

        Data = requests.get(url)
        data = Data.json()

        try:
            weather = data["records"]["location"][0]["weatherElement"][0]["time"][0]["parameter"]["parameterName"]
            rain = data["records"]["location"][0]["weatherElement"][1]["time"][0]["parameter"]["parameterName"]

            result = f"""
            <h2>{city} 天氣預報</h2>
            天氣：{weather}<br>
            降雨機率：{rain}%<br><hr>
            """

        except Exception:
            result = "查無資料，請確認縣市名稱"

    return result + """
    <form method="post">
        輸入縣市：
        <input type="text" name="city">
        <input type="submit" value="查詢">
    </form>
    <br><a href="/">回首頁</a>
    """


if __name__ == "__main__":
    app.run(debug=True)