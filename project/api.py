# project/api.py

from flask import Blueprint, jsonify
from .db import get_mongo_client

api_bp = Blueprint('api', __name__, url_prefix='/api')

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