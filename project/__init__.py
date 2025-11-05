from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

# 1. Load environment variables
load_dotenv()

# --- 2. Create the Flask App Instance ---
app = Flask(__name__)

# --- 3.Enable CORS for frontend integration ---
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:*", "http://127.0.0.1:*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# --- 4. Configure Flask-SQLAlchemy for MariaDB ---
MARIADB_URI = (
    f"mysql+mysqlconnector://{os.getenv('MARIADB_USER')}:"
    f"{os.getenv('MARIADB_PASSWORD')}@"
    f"{os.getenv('MARIADB_HOST')}:"
    f"{os.getenv('MARIADB_PORT')}/"
    f"{os.getenv('MARIADB_DATABASE')}"
    f"?ssl_ca={os.getenv('SSL_CA_PATH', 'ca.pem')}"
)

app.config["SQLALCHEMY_DATABASE_URI"] = MARIADB_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False 

# --- 5. Initialize SQLAlchemy and Import Models ---
from .models import db 
db.init_app(app)

# --- 6. Register Blueprints and Core Routes ---

# CRITICAL: This one line is all that's needed to activate routes.py
from project import routes 
from project import core_routes

# Import all new RESTful API blueprints
from .api import api_bp
from .routes.user import user_bp
from .routes.user_profile import user_profile_bp
from .routes.user_preference import user_preference_bp
from .routes.event import event_bp
from .routes.venue import venue_bp
from .routes.tag import tag_bp
from .routes.review import review_bp
from .routes.registered_event import registered_event_bp
from .routes.event_tag import event_tag_bp
from .core_routes import main_bp

# Register Blueprints
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(main_bp)
app.register_blueprint(user_bp)
app.register_blueprint(user_profile_bp)
app.register_blueprint(user_preference_bp)
app.register_blueprint(event_bp)
app.register_blueprint(venue_bp)
app.register_blueprint(tag_bp)
app.register_blueprint(review_bp)
app.register_blueprint(registered_event_bp)
app.register_blueprint(event_tag_bp)