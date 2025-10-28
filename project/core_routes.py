from flask import Blueprint, jsonify
from project.db import get_mongo_status, get_mariadb_status 

# Define a Blueprint for the core routes
main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    """A simple root endpoint to show the server is running."""
    return "<h1>Event Calendar Backend is Running!</h1>"

@main_bp.route("/health")
def health_check():
    """Health check endpoint that checks database connections."""
    mongo_status = get_mongo_status()
    mariadb_status = get_mariadb_status()
    
    # Logic from your file
    if mongo_status == "connected" and mariadb_status == "connected":
        status_code = 200
    else:
        status_code = 500
        
    return jsonify({
        "mongodb_status": mongo_status,
        "mariadb_status": mariadb_status
    }), status_code
