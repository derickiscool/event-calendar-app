# project/__init__.py

from flask import Flask, jsonify
from dotenv import load_dotenv
from models import db  # SQLAlchemy (MariaDB) instance
from project.db import get_mongo_status, get_mariadb_status  # Import database status check functions

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")  # Load configuration

    # Initialize SQLAlchemy (MariaDB)
    db.init_app(app)

    # Register MongoDB routes (Keep these separate for MongoDB)
    from project.api import api_bp  # Import MongoDB routes
    app.register_blueprint(api_bp)  # MongoDB API blueprint

    # Register MariaDB routes (user, tag, event, etc.)
    from routes.user import user_bp
    from routes.tag import tag_bp
    from routes.event import event_bp
    from routes.user_profile import user_profile_bp
    from routes.venue import venue_bp
    from routes.event_tag import event_tag_bp
    from routes.registered_event import registered_event_bp
    from routes.review import review_bp

    app.register_blueprint(user_bp, url_prefix="/api")
    app.register_blueprint(tag_bp, url_prefix="/api")
    app.register_blueprint(event_bp, url_prefix="/api")
    app.register_blueprint(user_profile_bp, url_prefix="/api")
    app.register_blueprint(venue_bp, url_prefix="/api")
    app.register_blueprint(event_tag_bp, url_prefix="/api")
    app.register_blueprint(registered_event_bp, url_prefix="/api")
    app.register_blueprint(review_bp, url_prefix="/api")

    # Health Check Endpoint
    @app.route("/health")
    def health_check():
        """Health check endpoint that checks database connections."""
        mongo_status = get_mongo_status()
        mariadb_status = get_mariadb_status()

        # If both databases are connected
        if mongo_status == "connected" and mariadb_status == "connected":
            status_code = 200  # Success status
        else:
            status_code = 500  # Error status

        # Return the status of both databases
        return jsonify({
            "mongodb_status": mongo_status,
            "mariadb_status": mariadb_status
        }), status_code

    return app

