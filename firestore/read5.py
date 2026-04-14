import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

# 避免重複初始化 Firebase App
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

# 設定集合名稱為「靜宜資管」
collection_ref = db.collection("靜宜資管")
docs = collection_ref.get()

# 修正變數拼字：keywoed -> keyword
keyword = input("您要查詢老師的名字? ")

for doc in docs:
    user = doc.to_dict()
    # 修正語法：加上冒號，並確保 "name" 鍵值存在於字典中
    if "name" in user and keyword in user["name"]:
        # 修正 f-string 內的引號衝突
        print(f"{user['name']}老師的研究室在{user['lab']}")