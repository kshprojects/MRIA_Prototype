import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("credentials.json")
firebase_admin.initialize_app(cred)

db = firestore.client()
conversations_collection = db.collection('conversations')
users_collection = db.collection('users')
queries_collection = db.collection('queries') 
responses_collection = db.collection('responses')