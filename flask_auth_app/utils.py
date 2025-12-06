import mysql.connector
import smtplib
from email.mime.text import MIMEText
import jwt
import datetime

# Your email credentials
EMAIL = "zehcalmtech@gmail.com"
PASSWORD = "zcwx ejxv bpjv womb"

# Secret key for JWT encoding/decoding
SECRET_KEY = "your_secret_key"  # Change this to a more secure secret key

def get_db_connection():
    """Establish a connection to the MySQL database and return the connection object."""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="1234",
        database="zehmn"
    )

def send_otp(to_email, otp):
    """Send OTP to the user via email."""
    subject = "Your OTP Code"
    body = f"Your OTP code is: {otp}"
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL
    msg['To'] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com",465) as server:
            server.login(EMAIL, PASSWORD)
            server.sendmail(EMAIL, to_email, msg.as_string())
        print(f"[SUCCESS] OTP sent to {to_email}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send OTP email: {e}")
        return False

def generate_token(payload):
    """Generate a JWT token with user data."""
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=1)  # Token expiration set to 1 hour
    payload["exp"] = expiration_time

    # Encode the payload to create a token
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

def decode_token(token):
    """Decode the JWT token and return the payload."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")
