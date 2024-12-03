from config.db_config import db
from config.db_config import firestore
from datetime import datetime

users_collection = db.collection('users')

def create_user(name, email, hashed_password, phone_number):
    user_data = {
        'name': name.lower(),
        'email': email,
        'password': hashed_password,
        'phone_number': phone_number,
        'created_at': datetime.utcnow()
    }

    # Add new document to 'users' collection
    result = users_collection.add(user_data)
       
    # Check for tuple order and handle both cases
    if isinstance(result[0], firestore.DocumentReference):
        document_ref = result[0]  # DocumentReference is the first element
    elif isinstance(result[1], firestore.DocumentReference):
        document_ref = result[1]  # DocumentReference is the second element
    else:
        raise TypeError("Unexpected result from Firestore add() method: {}".format(result))

    return document_ref.id  # Return the document ID


def get_all_users():
    users = []
    docs = users_collection.stream()
    for doc in docs:
        user = doc.to_dict()
        user['_id'] = doc.id  # Add the Firestore document ID
        user['name'] = user['name'].lower()  # Optional: Convert name to lowercase
        users.append(user)
    return users

def get_user_by_id(user_id):
    try:
        doc = users_collection.document(user_id).get()
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        raise ValueError("Invalid User ID")  # This exception will be raised if the document doesn't exist or on other errors

def update_user(user_id, update_data):
    try:
        users_collection.document(user_id).update(update_data)
    except Exception as e:
        raise ValueError("Invalid User ID")

def get_user_by_email_or_phone(email=None, phone_number=None):
    query = None
    if email and phone_number:
        query = users_collection.where('email', '==', email).where('phone_number', '==', phone_number)
    elif email:
        query = users_collection.where('email', '==', email)
    elif phone_number:
        query = users_collection.where('phone_number', '==', phone_number)
    
    if query:
        # Convert the stream to a list and fetch the first result
        results = [doc.to_dict() for doc in query.stream()]
        
        if results:
            user = results[0]
            # Get the document ID and add it to the user dictionary
            user['_id'] = list(query.stream())[0].id  # Correct way to get the document ID
            return user
        
    return None


def delete_user(user_id):
    try:
        users_collection.document(user_id).delete()
    except Exception as e:
        raise ValueError("Invalid User ID")
