# project/routes/bookmark.py
from flask import Blueprint, request, jsonify, session
from project.models import db, Bookmark
from project.models.event_cache import EventCache
from datetime import datetime

bookmark_bp = Blueprint("bookmark", __name__)

# GET all bookmarks
@bookmark_bp.route("/bookmarks", methods=["GET"])
def get_bookmarks():
    if "user_id" not in session:
        return jsonify({"error": "Auth required"}), 401
        
    bookmarks = Bookmark.query.filter_by(user_id=session["user_id"]).all()
    
    return jsonify({
        "status": "success",
        "event_ids": [b.event_identifier for b in bookmarks],
        "bookmarks": [b.as_dict() for b in bookmarks]
    })

# POST Toggle Bookmark (Save/Unsave)
@bookmark_bp.route("/bookmarks", methods=["POST"])
def toggle_bookmark():
    if "user_id" not in session:
        return jsonify({"error": "You must be logged in to bookmark"}), 401

    data = request.get_json()
    event_identifier = data.get("event_id") # Frontend sends "event_id"

    if not event_identifier:
        return jsonify({"error": "Event ID is required"}), 400

    # 1. Check if already bookmarked
    existing = Bookmark.query.filter_by(
        user_id=session["user_id"],
        event_identifier=event_identifier
    ).first()

    if existing:
        # REMOVE (Toggle off)
        db.session.delete(existing)
        db.session.commit()
        return jsonify({"status": "removed", "message": "Bookmark removed"}), 200

    # 2. [AUTO-CACHE] Ensure event exists in Cache Table
    cached_event = EventCache.query.get(event_identifier)
    
    if not cached_event:
        source_type = 'community' if event_identifier.startswith('community_') else 'official'
        original_id = event_identifier.replace(f'{source_type}_', '')
        
        # Try fetch title
        title = "Saved Event"
        if source_type == 'official':
            try:
                from project.db import get_mongo_client
                from bson import ObjectId
                client = get_mongo_client()
                if client:
                    doc = client.get_database("event_calendar").events.find_one({'_id': ObjectId(original_id)})
                    if doc: title = doc.get('title', title)
                    client.close()
            except: pass
            
        new_cache = EventCache(
            event_identifier=event_identifier,
            source=source_type,
            original_id=original_id,
            title=title
        )
        try:
            db.session.add(new_cache)
            db.session.commit()
        except:
            db.session.rollback()

    # 3. Create Bookmark
    new_bookmark = Bookmark(
        user_id=session["user_id"],
        event_identifier=event_identifier,
        event_id=None, 
        created_at=datetime.now()
    )

    try:
        db.session.add(new_bookmark)
        db.session.commit()
        return jsonify({"status": "added", "message": "Event saved"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500