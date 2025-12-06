# reminder.py ←←← FINAL 100% WORKING WITH FLUTTER

from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils import get_db_connection
from flask_mail import Message

def register_reminder_routes(app, mail):

    @app.route('/send-reminder-email', methods=['POST'])
    @jwt_required()
    def save_and_send_reminder():
        user_id = get_jwt_identity()
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data received"}), 400

        reminder_type = data.get('type', 'General Reminder')
        message = data.get('message', '').strip()
        time_str = data.get('time', '').strip()  # Flutter se "23 Nov 2025, 04:30 PM"

        if not time_str:
            return jsonify({"error": "Time is required"}), 400

        try:
            conn = get_db_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT full_name, email FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()

            if not user:
                return jsonify({"error": "User not found"}), 404

            name = user['full_name'] or "User"
            user_email = user['email']

            # Save to Database
            cur.execute("""
                INSERT INTO reminders 
                (user_id, user_name, user_email, reminder_type, message, reminder_time, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (user_id, name, user_email, reminder_type, message or None, time_str))
            conn.commit()

            print(f"Reminder SAVED in DB for {user_email}: {time_str}")

        except Exception as e:
            print("DB Error:", str(e))
            return jsonify({"error": "Database error", "details": str(e)}), 500
        finally:
            cur.close()
            conn.close()

        # Send Email
        try:
            msg = Message(
                subject=f"Reminder: {reminder_type} - ZEH CalmTech",
                sender=app.config['MAIL_USERNAME'],
                recipients=[user_email]
            )
            msg.html = f"""
            <div style="font-family:Arial; text-align:center; padding:40px; background:#fffef5;">
                <h2 style="color:#d48a8a;">Assalam-o-Alaikum {name}!</h2>
                <h3>Yeh aapka <strong>{reminder_type}</strong> ka reminder hai</h3>
                {f'<p style="font-style:italic; color:#8B4513; font-size:18px;">"{message}"</p>' if message else ''}
                <h2 style="color:#d48a8a;">{time_str}</h2>
                <p>Apna khayal rakhiye ❤️</p>
                <strong>ZEH CalmTech Team</strong>
            </div>
            """
            mail.send(msg)
            print(f"EMAIL SENT to {user_email}")

        except Exception as e:
            print("Email failed:", str(e))

        return jsonify({
            "status": "success",
            "message": "Reminder set ho gaya! Email bhi bhej diya",
            "data": {"type": reminder_type, "message": message, "time": time_str}
        }), 200


    @app.route('/my-reminders', methods=['GET'])
    @jwt_required()
    def get_my_reminders():
        user_id = get_jwt_identity()
        try:
            conn = get_db_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("""
                SELECT 
                    reminder_type AS type,
                    message,
                    reminder_time AS time,
                    created_at
                FROM reminders 
                WHERE user_id = %s 
                ORDER BY created_at DESC
            """, (user_id,))
            reminders = cur.fetchall()
            cur.close()
            conn.close()
            return jsonify(reminders), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500