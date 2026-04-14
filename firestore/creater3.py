import firebase_admin
from firebase_admin import credentials, firestore

# Initialize the SDK
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

# Define the data
doc = {
  "name": "黃彥璋",
  "mail": "jimmy0937505327@gmail.com",
  "lab": 549
}

# Fix: Ensure the variable names match
# Using 'collection_ref' to make it clear we are pointing to the collection
collection_ref = db.collection("靜宜資管2026a")
collection_ref.add(doc)

print("Document added successfully!")
