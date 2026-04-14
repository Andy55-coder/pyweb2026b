import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

doc = {
  "name": "黃彥璋",
  "mail": "jimmy0937505327@gmail.com",
  "lab": 549
}

doc_ref = db.collection("靜宜資管2026a").document("Yan Zhang")
doc_ref.set(doc)
