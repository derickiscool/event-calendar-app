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

# GET check if specific event is bookmarked
@bookmark_bp.route("/bookmarks/check", methods=["GET"])
def check_bookmark():
    if "user_id" not in session:
        return jsonify({"is_bookmarked": False}), 200
    
    event_id = request.args.get("event_id")
    if not event_id:
        return jsonify({"error": "Event ID required"}), 400
    
    bookmark = Bookmark.query.filter_by(
        user_id=session["user_id"],
        event_identifier=event_id
    ).first()
    
    return jsonify({"is_bookmarked": bookmark is not None}), 200

# POST Add Bookmark
@bookmark_bp.route("/bookmarks", methods=["POST"])
def add_bookmark():
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
        return jsonify({"status": "added", "message": "Already bookmarked"}), 200

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
        created_at=datetime.now()
    )

    try:
        db.session.add(new_bookmark)
        db.session.commit()
        return jsonify({"status": "added", "message": "Event saved"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# DELETE Remove Bookmark
@bookmark_bp.route("/bookmarks/<event_identifier>", methods=["DELETE"])
def remove_bookmark(event_identifier):
    if "user_id" not in session:
        return jsonify({"error": "You must be logged in"}), 401

    if not event_identifier:
        return jsonify({"error": "Event ID is required"}), 400

    # Find and delete the bookmark
    bookmark = Bookmark.query.filter_by(
        user_id=session["user_id"],
        event_identifier=event_identifier
    ).first()

    if not bookmark:
        return jsonify({"status": "removed", "message": "Bookmark not found"}), 200

    try:
        db.session.delete(bookmark)
        db.session.commit()
        return jsonify({"status": "removed", "message": "Bookmark removed"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500