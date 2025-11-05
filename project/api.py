# project/api.py

from flask import Blueprint, jsonify
from .db import get_mongo_client
from datetime import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api')

# --- Health Check Endpoints for Frontend Integration ---
@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify backend is running.
    This is used by the frontend to confirm connection.
    """
    return jsonify({
        'status': 'success',
        'message': 'Event Calendar Backend is Running!',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }), 200


@api_bp.route('/status', methods=['GET'])
def status():
    """
    Detailed status endpoint including database connectivity.
    Checks both MariaDB (SQLAlchemy) and MongoDB connections.
    """
    status_info = {
        'status': 'success',
        'backend': 'running',
        'timestamp': datetime.now().isoformat()
    }

     # Check MariaDB connection
    try:
        from .models import db
        db.session.execute('SELECT 1')
        status_info['mariadb'] = 'connected'
    except Exception as e:
        status_info['mariadb'] = f'disconnected: {str(e)}'
    
    # Check MongoDB connection
    try:
        client = get_mongo_client()
        if client:
            # Try to ping MongoDB
            client.admin.command('ping')
            status_info['mongodb'] = 'connected'
            client.close()
        else:
            status_info['mongodb'] = 'connection failed'
    except Exception as e:
        status_info['mongodb'] = f'disconnected: {str(e)}'
    
    return jsonify(status_info), 200

# --- Existing Endpoints ---

@api_bp.route('/official-events')
def get_official_events():
    """
    API endpoint to fetch all events from the MongoDB 'events' collection.
    """
    client = get_mongo_client()
    if not client:
        return jsonify({"error": "Database connection failed"}), 500

    db = client.get_database("event_calendar")
    events_collection = db.events

   
    events_cursor = events_collection.find({})

    events_list = []
    for event in events_cursor:
       
        event['_id'] = str(event['_id'])
        events_list.append(event)
    
    client.close()

    return jsonify(events_list)