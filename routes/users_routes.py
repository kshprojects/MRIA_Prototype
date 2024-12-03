import os
import re
from flask import Flask, request, jsonify, Blueprint
from flask_bcrypt import Bcrypt
from datetime import datetime
from users import create_user, get_all_users, get_user_by_email_or_phone, get_user_by_id, update_user, delete_user

users_db = Blueprint('app', __name__)
bcrypt = Bcrypt()

def validate_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email)

def validate_password(password):
    password_regex = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$'
    return bool(re.match(password_regex, password))

def validate_phone_number(phone_number):
    phone_number_pattern = r'^[0-9]{10,15}$'
    return re.match(phone_number_pattern, str(phone_number))

@users_db.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    name = str(data.get('user_name'))
    email = str(data.get('email'))
    password = str(data.get('password'))
    phone_number = str(data.get('phone_number'))

    if not all([name, email, password, phone_number]):
        return jsonify({'msg': 'All fields are required.'}), 400

    if not validate_email(email):
        return jsonify({'msg': 'Invalid email format'}), 400
    if not validate_password(password):
        return jsonify({'msg': 'Invalid password format'}), 400
    if not validate_phone_number(phone_number):
        return jsonify({'msg': 'Invalid phone number format'}), 400

    email_exists = get_user_by_email_or_phone(email=email)
    phone_exists = get_user_by_email_or_phone(phone_number=phone_number)

    if email_exists or phone_exists:
        return jsonify({'msg': 'User with this email or phone already exists'}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user_id = create_user(name, email, hashed_password, phone_number)
    return jsonify({'user_id': user_id}), 201

@users_db.route('/api/users/<user_id>', methods=['GET', 'PUT', 'DELETE'])
def manage_user(user_id):
    if request.method == 'GET':
        user = get_user_by_id(user_id)
        if user:
            return jsonify(user), 200
        return jsonify({'msg': 'User not found'}), 404

    elif request.method == 'PUT':
        data = request.get_json()
        if 'email' in data and not validate_email(data['email']):
            return jsonify({'msg': 'Invalid email format'}), 400
        if 'password' in data:
            if not validate_password(data['password']):
                return jsonify({'msg': 'Invalid password format'}), 400
            data['password'] = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        if 'phone_number' in data and not validate_phone_number(data['phone_number']):
            return jsonify({'msg': 'Invalid phone number format'}), 400
        update_user(user_id, data)
        return jsonify({'msg': 'User updated successfully'}), 200

    elif request.method == 'DELETE':
        delete_user(user_id)
        return jsonify({'msg': 'User deleted successfully'}), 200

@users_db.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    identifier = data.get('identifier')
    password = data.get('password')

    email = identifier if '@' in identifier else None
    phone_number = identifier if email is None else None
    
    # Get the user by email or phone number
    user = get_user_by_email_or_phone(email=email, phone_number=phone_number)
    print("User fetched:", user)  # Debugging line
    
    if user and bcrypt.check_password_hash(user['password'], password):
        user_id = user.get('_id')  
  # The user ID should be included in the 'user' dictionary from Firestore
        login_time = datetime.utcnow()
        
        # Update the last login time in the user document
        update_user(user_id, {'last_login': login_time})
        
        # Return user info and login time
        return jsonify({'user_id': user_id, 'login_time': login_time}), 200

    # If login fails, return an error
    return jsonify({'msg': 'Invalid identifier or password'}), 401


@users_db.route('/api/users', methods=['GET'])
def list_users():
    users = get_all_users()
    return jsonify({'users': users}), 200
