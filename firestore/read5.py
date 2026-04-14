import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

# 初始化 Firebase（避免重複）
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

collection_ref = db.collection("靜宜資管")

# 使用者輸入
keyword = input("請輸入老師名字：")

# 🔥 Firestore 查詢
docs = collection_ref\
    .where(filter=FieldFilter("name", ">=", keyword))\
    .where(filter=FieldFilter("name", "<=", keyword + "\uf8ff"))\
    .get()

found = False

for doc in docs:
    user = doc.to_dict()
    print(f"{user['name']}老師的研究室在 {user['lab']}")
    found = True

if not found:
    print("查無資料")