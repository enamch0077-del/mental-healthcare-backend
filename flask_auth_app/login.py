# backend/login.py  ← FINAL CLEAN VERSION
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from datetime import timedelta
from werkzeug.security import check_password_hash
from utils import get_db_connection

login_route = Blueprint('login_route', __name__)

# ← YE DONO LINES PURI TARAH HATA DI GAYI HAIN (kyunki app yahan defined nahi hai)
# from flask_cors import CORS
# CORS(app)   ← YE GALAT THI

@login_route.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required!"}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email.lower(),))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user:
        return jsonify({"error": "User not found"}), 404

    if not check_password_hash(user['password'], password):
        return jsonify({"error": "Invalid credentials"}), 401

    # Token 30 din tak valid rahega
    token = create_access_token(identity=str(user['id']), expires_delta=timedelta(days=30))

    return jsonify({
        "message": "Loginnnnnnnn successful",
        "token": token,
        "user": {
            "id": user['id'],                              # ← Diary ke liye zaroori hai
            "full_name": user['full_name'] or "User",
            "email": user['email'],
            "gender": user.get('gender', ''),
            "age": user.get('age', 0),
            "trustee_number": user.get('trustee_number', '')
        }
    }), 200