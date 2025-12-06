from flask import Blueprint, request, jsonify
from flask_mail import Mail, Message
import random
import mysql.connector
from datetime import datetime, timedelta
import jwt
from werkzeug.security import generate_password_hash
from utils import get_db_connection, send_otp  # Make sure this is working
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

forge_route = Blueprint('forge_route', __name__)
mail = Mail()

# Secret key for JWT
JWT_SECRET = 'your_jwt_secret_key'
JWT_ALGORITHM = 'HS256'

# Check if email exists
def is_email_in_database(email):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result is not None
    except Exception as e:
        logger.error(f"Error checking email in database: {str(e)}")
        return False

# Generate OTP
def generate_otp():
    return str(random.randint(1000, 9999))

# Helper function to generate JWT token with OTP
def generate_otp_token(email, otp):
    expiration_time = timedelta(minutes=5)
    payload = {
        'email': email,
        'otp': otp,
        'exp': datetime.utcnow() + expiration_time
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

# Forgot Password - Send OTP
@forge_route.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')

    if not email:
        logger.warning("Email not provided in forgot-password request")
        return jsonify({"error": "Email is required"}), 400

    if not is_email_in_database(email):
        logger.warning(f"Email not found: {email}")
        return jsonify({"error": "Email not found"}), 404

    otp = generate_otp()
    now = datetime.now()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET otp = %s, otp_created_at = %s, otp_attempts = 0 WHERE email = %s",
            (otp, now, email)
        )
        conn.commit()
        cursor.close()
        conn.close()

        token = generate_otp_token(email, otp)
        logger.info(f"Generated OTP: {otp} and token for email: {email}")

        msg = Message("Your OTP Code", sender="your_email@gmail.com", recipients=[email])
        msg.body = f"Your OTP is: {otp}"
        mail.send(msg)
        logger.info(f"OTP email sent to: {email}")

        return jsonify({
            "message": "OTP sent to email",
            "token": token
        }), 200

    except Exception as e:
        logger.error(f"Failed to send email for {email}: {str(e)}")
        return jsonify({"error": "Failed to send email", "details": str(e)}), 500
    
@forge_route.route('/check-otp', methods=['POST'])
def check_otp():
    data = request.get_json()
    user_otp = data.get('otp')
    email = data.get('email')
    token = data.get('token')

    logger.info(f"Received check-otp request: email={email}, otp={user_otp}, token={token}")

    if not user_otp or not email or not token:
        logger.warning("Missing required fields in check-otp request")
        return jsonify({"error": "Email, OTP, and Token are required"}), 400

    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        logger.info(f"Decoded token: {decoded_token}")

        if decoded_token['email'].lower() != email.lower():
            logger.warning(f"Email mismatch: token email={decoded_token['email']}, provided email={email}")
            return jsonify({"error": "Email does not match token"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT otp, otp_created_at, otp_attempts FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        logger.info(f"Database user data: {user}")

        if not user:
            cursor.close()
            conn.close()
            logger.warning(f"User not found in database: {email}")
            return jsonify({"error": "User not found"}), 404

        max_attempts = 3
        otp_attempts = int(user['otp_attempts'] or 0)

        if otp_attempts >= max_attempts:
            # Clear OTP after 3 failed attempts
            cursor.execute(
                "UPDATE users SET otp = NULL, otp_created_at = NULL, otp_attempts = 0 WHERE email = %s",
                (email,)
            )
            conn.commit()
            cursor.close()
            conn.close()
            logger.warning(f"Too many OTP attempts for {email}")
            return jsonify({"error": "Too many failed attempts. OTP has been removed. Please request a new one."}), 429

        otp_created_at = user['otp_created_at']
        if otp_created_at:
            time_difference = (datetime.now() - otp_created_at).total_seconds()
            if time_difference > 300:
                cursor.close()
                conn.close()
                logger.warning(f"OTP expired for {email}")
                return jsonify({"error": "OTP has expired, please request a new OTP"}), 400
        else:
            cursor.close()
            conn.close()
            logger.warning(f"No OTP found in database for {email}")
            return jsonify({"error": "No OTP found in database, please request a new OTP"}), 400

        stored_otp = decoded_token.get('otp')
        db_otp = user.get('otp')

        if not stored_otp or not db_otp:
            cursor.close()
            conn.close()
            logger.warning(f"OTP missing: token OTP={stored_otp}, database OTP={db_otp}")
            return jsonify({"error": "OTP data missing, please request a new OTP"}), 400

        if user_otp == stored_otp and user_otp == db_otp:
            cursor.execute(
                "UPDATE users SET otp = NULL, otp_created_at = NULL, otp_attempts = 0 WHERE email = %s",
                (email,)
            )
            conn.commit()
            cursor.close()
            conn.close()
            logger.info(f"OTP verified successfully for {email}")
            return jsonify({"message": "OTP verified successfully"}), 200
        else:
            # Increment attempts, but only clear OTP if it's the third wrong try
            new_attempts = otp_attempts + 1
            if new_attempts >= max_attempts:
                cursor.execute(
                    "UPDATE users SET otp = NULL, otp_created_at = NULL, otp_attempts = 0 WHERE email = %s",
                    (email,)
                )
                conn.commit()
                cursor.close()
                conn.close()
                logger.warning(f"OTP removed after {new_attempts} failed attempts for {email}")
                return jsonify({"error": "Invalid OTP. Maximum attempts reached. OTP has been removed."}), 400
            else:
                cursor.execute("UPDATE users SET otp_attempts = %s WHERE email = %s", (new_attempts, email))
                conn.commit()
                cursor.close()
                conn.close()
                logger.warning(f"Incorrect OTP attempt {new_attempts} for {email}")
                return jsonify({"error": "Invalid OTP"}), 400

    except jwt.ExpiredSignatureError:
        logger.warning(f"OTP token expired for {email}")
        return jsonify({"error": "OTP token has expired, please request a new OTP"}), 400
    except jwt.InvalidTokenError:
        logger.warning(f"Invalid OTP token for {email}")
        return jsonify({"error": "Invalid OTP token, please request a new OTP"}), 400
    except Exception as e:
        logger.error(f"Error in check-otp for {email}: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

# Reset Password
@forge_route.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    email = data.get('email')
    new_password = data.get('new_password')

    logger.info(f"Received reset-password request for email: {email}")

    if not email or not new_password:
        logger.warning("Missing email or new password in reset-password request")
        return jsonify({"error": "Email and new password are required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, otp FROM users WHERE LOWER(email) = LOWER(%s)", (email,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            logger.warning(f"User not found for reset-password: {email}")
            return jsonify({"error": "User not found"}), 404

        if user.get('otp') is not None:
            cursor.close()
            conn.close()
            logger.warning(f"OTP not verified for {email}")
            return jsonify({"error": "Please verify your OTP before resetting your password"}), 400

        hashed_password = generate_password_hash(new_password)
        user_id = user['id']

        cursor.execute("UPDATE users SET password = %s WHERE id = %s", (hashed_password, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Password reset successful for {email}")

        return jsonify({"message": "Password reset successful"}), 200

    except Exception as e:
        logger.error(f"Error in reset-password for {email}: {str(e)}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500