# project/api.py

from flask import Blueprint, jsonify, request
from .db import get_mongo_client
from datetime import datetime
from bson import ObjectId

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


@api_bp.route('/all-events', methods=['GET'])
def get_all_events():
    """
    Unified endpoint that fetches both official events (MongoDB) 
    and community events (MariaDB) and returns them in a consistent format.
    Supports filtering by category, search query, and date range.
    """
    # Get query parameters
    category = request.args.get('category', 'all')
    search_query = request.args.get('q', '').lower()
    
    all_events = []
    
    # 1. Fetch Official Events from MongoDB
    try:
        client = get_mongo_client()
        if client:
            db = client.get_database("event_calendar")
            events_collection = db.events
            
            mongo_events = events_collection.find({})
            
            for event in mongo_events:
                try:
                    # Transform MongoDB event to unified format
                    unified_event = {
                        'id': f"official_{str(event['_id'])}",
                        'title': event.get('title', 'Untitled Event'),
                        'description': event.get('description', ''),
                        'start_date': event.get('start_date', ''),
                        'end_date': event.get('end_date', ''),
                        'date': event.get('start_date', 'Date TBA'),  # Display format
                        'venue': event.get('venue_name', 'Venue TBA'),
                        'location': event.get('address', ''),
                        'image': event.get('image_url', ''),
                        'category': _categorize_event(event.get('title', '') + ' ' + event.get('description', '')),
                        'source': 'official',
                        'source_label': 'Official Event',
                        'registration_link': event.get('registration_link', ''),
                        'external_source': event.get('source', '')
                    }
                    all_events.append(unified_event)
                except Exception as inner_e:
                    print(f"Error processing MongoDB event: {inner_e}")
            
            client.close()
    except Exception as e:
        print(f"Error fetching MongoDB events: {e}")
    
    # 2. Fetch Community Events from MariaDB
    try:
        from .models import db, Event, Venue, EventTag, Tag, User
        from sqlalchemy.orm import joinedload
        
        community_events = Event.query.options(
            joinedload(Event.tags),
            joinedload(Event.creator)
        ).all()
        
        for event in community_events:
            try:
                # Get venue details
                venue = Venue.query.get(event.venue_id) if event.venue_id else None
                venue_name = venue.name if venue else 'Venue TBA'
                venue_address = venue.address if venue else ''
                
                # Get tags/categories
                tags = []
                if event.tags:
                    for et in event.tags:
                        tag = Tag.query.get(et.tag_id)
                        if tag:
                            tags.append(tag.tag_name)
                
                event_category = tags[0] if tags else 'other'
                
                # Get creator info
                creator_name = event.creator.username if event.creator else 'Anonymous'
                
                unified_event = {
                    'id': f"community_{event.id}",
                    'title': event.title,
                    'description': event.description or '',
                    'start_date': event.start_datetime.isoformat() if event.start_datetime else '',
                    'end_date': event.end_datetime.isoformat() if event.end_datetime else '',
                    'date': event.start_datetime.strftime('%Y-%m-%d %H:%M') if event.start_datetime else 'Date TBA',
                    'venue': venue_name,
                    'location': venue_address or event.location or '',
                    'image': event.image_url or '',
                    'category': _map_tag_to_category(event_category),
                    'source': 'community',
                    'source_label': f'Community Event by {creator_name}',
                    'tags': tags,
                    'creator_id': event.user_id
                }
                all_events.append(unified_event)
            except Exception as inner_e:
                print(f"Error processing MariaDB event: {inner_e}")
            
    except Exception as e:
        print(f"Error fetching MariaDB events: {e}")
    
    # 3. Apply filters
    filtered_events = all_events
    
    # Filter by category
    if category != 'all':
        filtered_events = [e for e in filtered_events if e.get('category') == category]
    
    # Filter by search query
    if search_query:
        filtered_events = [
            e for e in filtered_events 
            if search_query in e.get('title', '').lower() 
            or search_query in e.get('description', '').lower()
            or search_query in e.get('venue', '').lower()
        ]
    
    # 4. Sort by date (newest first)
    filtered_events.sort(
        key=lambda x: x.get('start_date', '') or '9999-12-31', 
        reverse=False
    )
    
    return jsonify({
        'status': 'success',
        'total': len(filtered_events),
        'official_count': sum(1 for e in all_events if e['source'] == 'official'),
        'community_count': sum(1 for e in all_events if e['source'] == 'community'),
        'events': filtered_events
    }), 200


def _categorize_event(text):
    """
    Categorize event based on keywords in title/description.
    Returns category slug.
    """
    text_lower = text.lower()
    
    categories = {
        'music': ['music', 'concert', 'band', 'orchestra', 'jazz', 'classical', 'rock', 'pop', 'singer'],
        'theatre': ['theatre', 'theater', 'play', 'drama', 'musical', 'performance', 'stage'],
        'comedy': ['comedy', 'stand-up', 'standup', 'comedian', 'funny', 'humor'],
        'film': ['film', 'movie', 'cinema', 'screening', 'documentary'],
        'visual-arts': ['art', 'exhibition', 'gallery', 'painting', 'sculpture', 'photography', 'installation'],
        'workshops': ['workshop', 'class', 'course', 'lesson', 'tutorial', 'masterclass', 'training']
    }
    
    for category, keywords in categories.items():
        if any(keyword in text_lower for keyword in keywords):
            return category
    
    return 'other'


def _map_tag_to_category(tag_name):
    """
    Map database tag names to frontend category slugs.
    """
    tag_lower = tag_name.lower()
    
    mapping = {
        'music': 'music',
        'theatre': 'theatre',
        'theater': 'theatre',
        'comedy': 'comedy',
        'film': 'film',
        'movie': 'film',
        'art': 'visual-arts',
        'visual arts': 'visual-arts',
        'workshop': 'workshops',
        'class': 'workshops'
    }
    
    return mapping.get(tag_lower, 'other')
