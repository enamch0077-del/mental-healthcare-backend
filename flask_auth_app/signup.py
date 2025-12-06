from flask import Flask, Blueprint, request, jsonify
from datetime import datetime, timedelta
import random
from werkzeug.security import generate_password_hash
import jwt
from utils import get_db_connection, send_otp  # Ensure this import is correct

app = Flask(__name__)
app.secret_key = '1234567'

signup_route = Blueprint('signup_route', __name__)
otp_route = Blueprint('otp_route', __name__)

# Secret key for encoding JWT
JWT_SECRET = 'your_jwt_secret_key'
JWT_ALGORITHM = 'HS256'

# Helper function to generate JWT token with all user data
def generate_signup_token(user_data, otp):
    expiration_time = timedelta(minutes=30)  # Token expiration time
    otp_created_at = datetime.now()
    
    # Create payload with all user information and OTP
    payload = {
        'email': user_data['email'].lower(),
        'full_name': user_data['full_name'],
        'gender': user_data['gender'],
        'age': user_data['age'],
        'trustee_number': user_data['trustee_number'],
        'password': user_data['password'],  # Will be hashed before saving to DB
        'otp': otp,
        'otp_created_at': otp_created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'exp': datetime.utcnow() + expiration_time  # Set expiration time
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

@signup_route.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['email', 'full_name', 'gender', 'age', 'trustee_number', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Normalize email
    email = data['email'].lower()
    
    # Check if the user already exists in the database
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({'error': 'User already exists'}), 400
    cursor.close()
    conn.close()
    
    # Generate OTP
    otp = str(random.randint(1000, 9999))
    
    # Generate token with all user data and OTP
    token = generate_signup_token(data, otp)
    
    # Send OTP to user's email
    if send_otp(email, otp):
        return jsonify({
            'message': 'OTP sent successfully. Please verify to complete registration.',
            'token': token
        }), 200
    else:
        return jsonify({'error': 'Failed to send OTP'}), 500

@otp_route.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    otp_input = data.get('otp')
    token = data.get('token')
    email = data.get('email')

    if not otp_input or not token or not email:
        return jsonify({'error': 'OTP, token, and email are required'}), 400

    try:
        # Decode the token
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        # Verify email matches token
        if decoded_token['email'].lower() != email.lower():
            return jsonify({'valid': False, 'message': 'Email does not match token'}), 400

        # Extract values from token
        stored_otp = decoded_token['otp']
        otp_created_at = datetime.strptime(decoded_token['otp_created_at'], '%Y-%m-%d %H:%M:%S')

        # Check if OTP is expired (5 minutes)
        current_time = datetime.now()
        time_difference = (current_time - otp_created_at).total_seconds()
        if time_difference > 300:
            return jsonify({'valid': False, 'message': 'OTP expired. Please request a new OTP.'}), 400

        # Verify OTP
        if otp_input != stored_otp:
            return jsonify({'valid': False, 'message': 'Invalid OTP'}), 400

        # Hash the password before saving
        hashed_password = generate_password_hash(decoded_token['password'])

        # Insert user data into database
        conn = get_db_connection()
        cursor = conn.cursor()

        insert_query = """
            INSERT INTO users (email, full_name, gender, age, trustee_number, password)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            decoded_token['email'],
            decoded_token['full_name'],
            decoded_token['gender'],
            decoded_token['age'],
            decoded_token['trustee_number'],
            hashed_password
        ))
        conn.commit()
        cursor.close()
        conn.close()

        # Prepare response
        user_data = {
            'email': decoded_token['email'],
            'full_name': decoded_token['full_name'],
            'gender': decoded_token['gender'],
            'age': decoded_token['age'],
            'trustee_number': decoded_token['trustee_number']
        }

        return jsonify({
            'valid': True,
            'message': 'OTP verified and user registered successfully',
            'user_data': user_data
        }), 200

    except jwt.ExpiredSignatureError:
        return jsonify({'valid': False, 'message': 'Token has expired. Please register again.'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'valid': False, 'message': 'Invalid token. Please register again.'}), 401
    except Exception as e:
        return jsonify({'valid': False, 'message': str(e)}), 500

# Register blueprints
app.register_blueprint(signup_route)
app.register_blueprint(otp_route)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)