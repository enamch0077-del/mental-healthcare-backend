# app.py
from flask import Flask, request
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
from flask_session import Session
from utils import get_db_connection

app = Flask(__name__)

# -----------------------------------------
# CORS Configuration
# -----------------------------------------
CORS(app,
     resources={r"/*": {"origins": "*"}},
     supports_credentials=True,
     expose_headers=["Content-Type", "Authorization"],
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

# -----------------------------------------
# Preflight OPTIONS Fix
# -----------------------------------------
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        return ("", 200)

# -----------------------------------------
# Secret Keys
# -----------------------------------------
app.secret_key = '111222'
app.config['JWT_SECRET_KEY'] = '1122'

# -----------------------------------------
# Email Configuration (Gmail App Password)
# -----------------------------------------
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USE_TLS=False,
    MAIL_USERNAME="zehcalmtech@gmail.com",
    MAIL_PASSWORD="zcwx ejxv bpjv womb"
)

# -----------------------------------------
# Session Configuration
# -----------------------------------------
app.config['SESSION_TYPE'] = 'filesystem'

# -----------------------------------------
# Initialize Extensions
# -----------------------------------------
jwt = JWTManager(app)
mail = Mail(app)
Session(app)

# -----------------------------------------
# Register Blueprints
# -----------------------------------------
from login import login_route
from add_values import add_route
from signup import signup_route, otp_route
from forge import forge_route
from questionnaire import questionnaire_route
from diary import diary_bp
from reminder import register_reminder_routes

app.register_blueprint(login_route)
app.register_blueprint(add_route)
app.register_blueprint(signup_route)
app.register_blueprint(otp_route)
app.register_blueprint(forge_route)
app.register_blueprint(questionnaire_route)
app.register_blueprint(diary_bp)
register_reminder_routes(app, mail)

# -----------------------------------------
# Test Route
# -----------------------------------------
@app.route('/')
def home():
    return "<h1>ZEH CalmTech Backend is LIVE!</h1>"

# -----------------------------------------
# Run Server
# -----------------------------------------
if __name__ == "__main__":
    print("Server chal raha hai → http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)
