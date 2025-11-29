# routes/event_tag.py
from flask import Blueprint, request, jsonify
from project.models import db, EventTag, EventCache, Event
from project.db import get_mongo_client
from bson import ObjectId


event_tag_bp = Blueprint("event_tag", __name__)

# GET event-tags (optionally filtered by event_id or event_identifier)
@event_tag_bp.route("/event-tags", methods=["GET"])
def get_event_tags():
    event_id = request.args.get("event_id")
    event_identifier = request.args.get("event_identifier")
    
    # Build query with filters if provided
    query = EventTag.query
    
    if event_id:
        query = query.filter_by(event_id=int(event_id))
    
    if event_identifier:
        query = query.filter_by(event_identifier=event_identifier)
    
    tags = query.all()
    return jsonify([t.as_dict() for t in tags])

# POST create event-tag
@event_tag_bp.route("/event-tags", methods=["POST"])
def create_event_tag():
    """
    Apply a tag to ANY event (SQL or Mongo).
    Automatically caches the event if it doesn't exist in SQL yet.
    """
    data = request.get_json()
    tag_id = data.get("tag_id")
    event_identifier = data.get("event_identifier")
    
    # Fallback: construct identifier if only numeric ID provided
    if not event_identifier and data.get("event_id"):
        event_identifier = f"community_{data.get('event_id')}"

    if not tag_id or not event_identifier:
        return jsonify({"error": "tag_id and event_identifier are required"}), 400

    # --- 1. AUTO-CACHE LOGIC (The "Bridge") ---
    # Ensure the event exists in the cache table before tagging it
    cached_event = EventCache.query.get(event_identifier)
    
    if not cached_event:
        # Determine source
        if event_identifier.startswith('official_'):
            source_type = 'official'
            original_id = event_identifier.replace('official_', '')
            event_title = "Official Event"
            
            # Fetch title from MongoDB for cache
            try:
                client = get_mongo_client()
                if client:
                    mongo_doc = client.get_database("event_calendar").events.find_one({'_id': ObjectId(original_id)})
                    if mongo_doc:
                        event_title = mongo_doc.get('title', event_title)
                    client.close()
            except Exception as e:
                print(f"Mongo Fetch Error: {e}")

        elif event_identifier.startswith('community_'):
            source_type = 'community'
            original_id = event_identifier.replace('community_', '')
            event_title = "Community Event"
            
            # Fetch title from SQL for cache
            sql_event = Event.query.get(int(original_id))
            if sql_event:
                event_title = sql_event.title
        else:
            return jsonify({"error": "Invalid event identifier format"}), 400

        # Create Cache Entry
        new_cache = EventCache(
            event_identifier=event_identifier,
            source=source_type,
            original_id=original_id,
            title=event_title[:255]
        )
        try:
            db.session.add(new_cache)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to cache event: {str(e)}"}), 500

    # --- 2. DUPLICATE CHECK ---
    existing = EventTag.query.filter_by(
        tag_id=tag_id, 
        event_identifier=event_identifier
    ).first()
    
    if existing:
        return jsonify({"message": "Tag already applied"}), 200

    # --- 3. SAVE TAG ---
    numeric_id = None
    if event_identifier.startswith('community_'):
        try:
            numeric_id = int(event_identifier.replace('community_', ''))
        except:
            pass

    new_tag = EventTag(
        tag_id=tag_id,
        event_identifier=event_identifier,
        event_id=numeric_id # Optional legacy field
    )
    
    db.session.add(new_tag)
    db.session.commit()
    
    return jsonify(new_tag.as_dict()), 201

# DELETE event-tag
@event_tag_bp.route("/event-tags/event/<int:event_id>/tag/<int:tag_id>", methods=["DELETE"])
def delete_event_tag(event_id, tag_id):
    et = EventTag.query.filter_by(event_id=event_id, tag_id=tag_id).first()
    if not et:
        return jsonify({"error": "EventTag not found"}), 404
    db.session.delete(et)
    db.session.commit()
    return jsonify({"message": "EventTag deleted"})
