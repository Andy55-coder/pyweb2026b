import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request

# 1. 初始化
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

app = Flask(__name__)

@app.route("/api_query")
def api_query():
    # 透過網址傳值查詢，例如：/api_query?name=張
    keyword = request.args.get("name")
    if not keyword:
        return "請在網址後方輸入查詢參數，例如：?name=老師名字"

    db = firestore.client()
    docs = db.collection("靜宜資管").get()
    
    output = f"正在為您查詢包含「{keyword}」的老師...<br><br>"
    results_count = 0
    
    for doc in docs:
        user = doc.to_dict()
        if keyword in user.get("name", ""):
            results_count += 1
            output += f"【第 {results_count} 筆】<br>"
            output += f"教師姓名：{user['name']}<br>"
            output += f"研究室位置：{user['lab']}<br>"
            output += "-" * 30 + "<br>"

    if results_count == 0:
        return f"找不到關於「{keyword}」的老師。"
    
    return output

if __name__ == "__main__":
    # 本地測試使用
    app.run(port=8000)