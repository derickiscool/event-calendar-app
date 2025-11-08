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


@api_bp.route('/event/<event_id>', methods=['GET'])
def get_single_event(event_id):
    """
    Get a single event by ID.
    ID format: 'official_{mongodb_id}' or 'community_{mariadb_id}'
    """
    try:
        # Parse event ID
        if event_id.startswith('official_'):
            # Fetch from MongoDB
            mongo_id = event_id.replace('official_', '')
            
            client = get_mongo_client()
            if not client:
                return jsonify({'error': 'Database connection failed'}), 500
            
            db = client.get_database("event_calendar")
            events_collection = db.events
            
            event = events_collection.find_one({'_id': ObjectId(mongo_id)})
            client.close()
            
            if not event:
                return jsonify({'error': 'Event not found'}), 404
            
            # Transform to unified format
            unified_event = {
                'id': event_id,
                'title': event.get('title', 'Untitled Event'),
                'description': event.get('description', ''),
                'start_date': event.get('start_date', ''),
                'end_date': event.get('end_date', ''),
                'date': event.get('start_date', 'Date TBA'),
                'venue': event.get('venue_name', 'Venue TBA'),
                'location': event.get('address', ''),
                'image': event.get('image_url', ''),
                'category': _categorize_event(event.get('title', '') + ' ' + event.get('description', '')),
                'source': 'official',
                'source_label': 'Official Event',
                'registration_link': event.get('registration_link', ''),
                'external_source': event.get('source', '')
            }
            
            return jsonify({
                'status': 'success',
                'event': unified_event
            }), 200
            
        elif event_id.startswith('community_'):
            # Fetch from MariaDB
            from .models import db, Event, Venue, EventTag, Tag
            
            mariadb_id = int(event_id.replace('community_', ''))
            event = Event.query.get(mariadb_id)
            
            if not event:
                return jsonify({'error': 'Event not found'}), 404
            
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
                'id': event_id,
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
            
            return jsonify({
                'status': 'success',
                'event': unified_event
            }), 200
            
        else:
            return jsonify({'error': 'Invalid event ID format'}), 400
            
    except Exception as e:
        print(f"Error fetching event {event_id}: {e}")
        return jsonify({'error': 'Failed to fetch event'}), 500


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


@api_bp.route('/reviews', methods=['GET'])
def get_reviews():
    """
    Get reviews for an event.
    Query parameter: event_id (format: official_xxx or community_xxx)
    """
    try:
        from .models import db, Review, User
        
        event_id = request.args.get('event_id')
        if not event_id:
            return jsonify({'error': 'Event ID is required'}), 400
        
        # Query reviews by event_identifier for both official and community events
        reviews = Review.query.filter_by(event_identifier=event_id).order_by(Review.created_at.desc()).all()
        
        reviews_data = []
        for review in reviews:
            user = User.query.get(review.user_id) if review.user_id else None
            reviews_data.append({
                'id': review.id,
                'event_id': event_id,  # Return the full event_id format
                'user_id': review.user_id,
                'user_name': user.username if user else 'Anonymous',
                'rating': review.score,  # Map score to rating
                'title': review.title or '',  # Include review title
                'comment': review.body or '',  # Map body to comment
                'created_at': review.created_at.isoformat() if review.created_at else None
            })
        
        return jsonify(reviews_data), 200
        
    except Exception as e:
        print(f"Error fetching reviews: {e}")
        return jsonify({'error': 'Failed to fetch reviews'}), 500


@api_bp.route('/reviews', methods=['POST'])
def create_review():
    """
    Create a new review for an event (official or community).
    Requires: event_id, rating, title, comment in JSON body
    """
    try:
        from .models import db, Review
        from flask import session
        from datetime import datetime
        
        data = request.get_json()
        
        # Validate required fields
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        event_id = data.get('event_id')
        rating = data.get('rating')
        title = data.get('title')
        comment = data.get('comment')
        
        if not event_id:
            return jsonify({'error': 'Event ID is required'}), 400
        
        # Validate event_id format
        if not (event_id.startswith('official_') or event_id.startswith('community_')):
            return jsonify({'error': 'Invalid event ID format'}), 400
        
        if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
        
        if not title or not title.strip():
            return jsonify({'error': 'Review title is required'}), 400
        
        if not comment or not comment.strip():
            return jsonify({'error': 'Comment is required'}), 400
        
        # Get user_id from session (if logged in)
        user_id = session.get('user_id')
        
        # Require login for reviews
        if not user_id:
            return jsonify({'error': 'You must be logged in to submit a review'}), 401
        
        # For community events, extract numeric ID for the foreign key
        numeric_event_id = None
        if event_id.startswith('community_'):
            numeric_event_id = int(event_id.replace('community_', ''))
        
        # Create new review
        new_review = Review(
            event_id=numeric_event_id,  # NULL for official events, numeric ID for community events
            event_identifier=event_id,  # Store full event_id (official_xxx or community_xxx)
            user_id=user_id,
            score=rating,  # Map rating to score
            title=title.strip(),  # Add review title
            body=comment.strip(),  # Map comment to body
            created_at=datetime.now()
        )
        
        db.session.add(new_review)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Review submitted successfully',
            'review_id': new_review.id
        }), 201
        
    except Exception as e:
        print(f"Error creating review: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to submit review'}), 500


# ===== BOOKMARK/REGISTRATION ENDPOINTS =====

@api_bp.route('/registered-events', methods=['GET'])
def get_registered_events():
    """
    Get all events bookmarked by the current user.
    Returns list of event_identifiers.
    """
    try:
        from .models import db, RegisteredEvent
        from flask import session
        
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'You must be logged in'}), 401
        
        registered = RegisteredEvent.query.filter_by(user_id=user_id).all()
        
        event_ids = [reg.event_identifier for reg in registered if reg.event_identifier]
        
        return jsonify({
            'status': 'success',
            'event_ids': event_ids,
            'count': len(event_ids)
        }), 200
        
    except Exception as e:
        print(f"Error fetching registered events: {e}")
        return jsonify({'error': 'Failed to fetch registered events'}), 500


@api_bp.route('/registered-events/check', methods=['GET'])
def check_event_registration():
    """
    Check if a specific event is bookmarked by the current user.
    Query parameter: event_id (format: official_xxx or community_xxx)
    """
    try:
        from .models import db, RegisteredEvent
        from flask import session
        
        event_id = request.args.get('event_id')
        user_id = session.get('user_id')
        
        if not event_id:
            return jsonify({'error': 'Event ID is required'}), 400
        
        if not user_id:
            return jsonify({'is_registered': False}), 200
        
        registration = RegisteredEvent.query.filter_by(
            user_id=user_id,
            event_identifier=event_id
        ).first()
        
        return jsonify({
            'is_registered': registration is not None
        }), 200
        
    except Exception as e:
        print(f"Error checking registration: {e}")
        return jsonify({'error': 'Failed to check registration'}), 500


@api_bp.route('/registered-events', methods=['POST'])
def register_event():
    """
    Bookmark an event for the current user.
    Requires: event_id in JSON body (format: official_xxx or community_xxx)
    """
    try:
        from .models import db, RegisteredEvent
        from flask import session
        from datetime import datetime
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        event_id = data.get('event_id')
        
        if not event_id:
            return jsonify({'error': 'Event ID is required'}), 400
        
        # Validate event_id format
        if not (event_id.startswith('official_') or event_id.startswith('community_')):
            return jsonify({'error': 'Invalid event ID format'}), 400
        
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'You must be logged in to bookmark events'}), 401
        
        # Check if already bookmarked
        existing = RegisteredEvent.query.filter_by(
            user_id=user_id,
            event_identifier=event_id
        ).first()
        
        if existing:
            return jsonify({'error': 'Already bookmarked this event'}), 400
        
        # For community events, extract numeric ID for foreign key
        numeric_event_id = None
        if event_id.startswith('community_'):
            numeric_event_id = int(event_id.replace('community_', ''))
        
        # Create bookmark
        registration = RegisteredEvent(
            user_id=user_id,
            event_id=numeric_event_id,
            event_identifier=event_id,
            registered_at=datetime.now()
        )
        
        db.session.add(registration)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Event bookmarked successfully'
        }), 201
        
    except Exception as e:
        print(f"Error bookmarking event: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to bookmark event'}), 500


@api_bp.route('/registered-events/<event_id>', methods=['DELETE'])
def unregister_event(event_id):
    """
    Remove bookmark for an event.
    URL parameter: event_id (format: official_xxx or community_xxx)
    """
    try:
        from .models import db, RegisteredEvent
        from flask import session
        
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'You must be logged in'}), 401
        
        registration = RegisteredEvent.query.filter_by(
            user_id=user_id,
            event_identifier=event_id
        ).first()
        
        if not registration:
            return jsonify({'error': 'Event not bookmarked'}), 404
        
        db.session.delete(registration)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Bookmark removed successfully'
        }), 200
        
    except Exception as e:
        print(f"Error removing bookmark: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to remove bookmark'}), 500

