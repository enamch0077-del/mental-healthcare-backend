# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from datetime import datetime
import random
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Allows Flutter (mobile/web) to connect

# MySQL Config from .env
db_config = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DB', 'wellness_chat'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'autocommit': True
}

# Create database and table if not exists
def init_db():
    try:
        # Connect without specifying database first to create it
        conn = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password'],
            port=db_config['port']
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_config['database']}")
        cursor.close()
        conn.close()

        # Now connect to the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                is_user TINYINT(1) NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME NOT NULL
            )
        ''')
        print("MySQL Database & table ready!")
        cursor.close()
        conn.close()
    except Exception as e:
        print("Database init error:", e)

# Run once at startup
init_db()

# Empathetic wellness responses
WELLNESS_RESPONSES = [
    "I'm really glad you shared that with me. It's okay to feel this way.",
    "You're not alone in feeling like this. Would you like to tell me more?",
    "That sounds really tough. Thank you for trusting me with how you feel.",
    "I'm here with you. Take a deep breath. You're doing great by reaching out.",
    "Your feelings are valid. How can I support you right now?",
    "I'm listening. Whenever you're ready, I'm here.",
    "It's brave of you to open up. I'm proud of you for doing this."
]

def generate_ai_response(user_message: str) -> str:
    msg = user_message.lower()
    if any(word in msg for word in ["sad", "depressed", "down", "lonely", "cry", "hurt"]):
        return "I'm so sorry you're feeling this way. You're not alone — I'm right here with you. Would you like to talk about what's been hurting?"
    elif any(word in msg for word in ["anxious", "worry", "stress", "panic", "nervous"]):
        return "Anxiety can feel so heavy. Let's breathe together: inhale slowly... hold... now exhale gently. You're safe here with me."
    elif any(word in msg for word in ["happy", "good", "better", "great", "joy"]):
        return "This makes my heart so warm! You deserve every bit of this happiness. Tell me more about what’s lighting you up!"
    elif "help" in msg or "support" in msg:
        return "I'm here to help you, always. You're important, and your feelings matter. What’s one thing on your mind right now?"
    else:
        return random.choice(WELLNESS_RESPONSES)


@app.route('/api/messages', methods=['GET'])
def get_messages():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT is_user, message, timestamp FROM messages ORDER BY id")
        rows = cursor.fetchall()
        messages = []
        for row in rows:
            messages.append({
                "isUser": bool(row['is_user']),
                "message": row['message'],
                "time": row['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            })
        cursor.close()
        conn.close()
        return jsonify(messages)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/send', methods=['POST'])
def send_message():
    data = request.get_json()
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    timestamp = datetime.now()

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Save user message
        cursor.execute(
            "INSERT INTO messages (is_user, message, timestamp) VALUES (%s, %s, %s)",
            (1, user_message, timestamp)
        )

        # Generate AI response
        ai_response = generate_ai_response(user_message)

        # Save AI response
        cursor.execute(
            "INSERT INTO messages (is_user, message, timestamp) VALUES (%s, %s, %s)",
            (0, ai_response, timestamp)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "userMessage": {
                "isUser": True,
                "message": user_message,
                "time": timestamp.strftime("%Y-%m-%d %H:%M:%S")
            },
            "aiMessage": {
                "isUser": False,
                "message": ai_response,
                "time": timestamp.strftime("%Y-%m-%d %H:%M:%S")
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("Wellness AI Backend Running on http://127.0.0.1:5000")
    print("Make sure MySQL is running and credentials are correct!")
    app.run(debug=True, host='0.0.0.0', port=5000)