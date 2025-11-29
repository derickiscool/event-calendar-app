from flask import Blueprint, request, jsonify, session
from project.models import db, Review, User
from datetime import datetime

review_bp = Blueprint("review", __name__)

# GET reviews (FIXED: Filters by event_id)
@review_bp.route("/reviews", methods=["GET"])
def get_reviews():
    # 1. Get the event_id from the URL (e.g., ?event_id=community_5)
    event_id = request.args.get('event_id')
    
    if not event_id:
        return jsonify([]) # Return empty list if no ID provided
        
    # 2. Filter reviews by this specific ID
    # We use event_identifier because it stores both "official_..." and "community_..."
    reviews = Review.query.filter_by(event_identifier=event_id).order_by(Review.created_at.desc()).all()
    
    # 3. Join with User data manually (to show username/avatar)
    results = []
    for r in reviews:
        user = User.query.get(r.user_id)
        results.append({
            **r.as_dict(),
            "username": user.username if user else "Anonymous",
            "user_avatar": user.profile.avatar_url if user and user.profile else None
        })
        
    return jsonify(results)

# GET single review (Keep this for editing)
@review_bp.route("/reviews/<int:review_id>", methods=["GET"])
def get_review(review_id):
    review = Review.query.get(review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404
    return jsonify(review.as_dict())

# POST create review (FIXED: Uses Session for Security)
@review_bp.route("/reviews", methods=["POST"])
def create_review():
    if "user_id" not in session:
        return jsonify({"error": "You must be logged in to review"}), 401

    data = request.get_json()
    event_identifier = data.get("event_id") # Frontend sends ID as "event_id"

    if not event_identifier:
        return jsonify({"error": "Event ID is required"}), 400

    # 1. Check for existing review
    existing = Review.query.filter_by(
        user_id=session["user_id"],
        event_identifier=event_identifier
    ).first()

    if existing:
        return jsonify({"error": "You have already reviewed this event"}), 400

    # 2. [AUTO-CACHE] Ensure event exists in Cache Table
    from project.models.event_cache import EventCache
    
    cached_event = EventCache.query.get(event_identifier)
    
    if not cached_event:
        # It's missing! We must cache it now to satisfy the Foreign Key.
        source_type = 'community' if event_identifier.startswith('community_') else 'official'
        original_id = event_identifier.replace(f'{source_type}_', '')
        
        # Try to fetch title for "Official" events (nice to have)
        event_title = "Cached Event"
        if source_type == 'official':
            try:
                from project.db import get_mongo_client
                from bson import ObjectId
                client = get_mongo_client()
                if client:
                    mongo_event = client.get_database("event_calendar").events.find_one({'_id': ObjectId(original_id)})
                    if mongo_event:
                        event_title = mongo_event.get('title', 'Official Event')
                    client.close()
            except Exception:
                pass # If Mongo fails, we just use default title
        
        # Create the Cache Entry
        new_cache = EventCache(
            event_identifier=event_identifier,
            source=source_type,
            original_id=original_id,
            title=event_title
        )
        try:
            db.session.add(new_cache)
            db.session.commit() # Commit cache FIRST
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Failed to cache event: {str(e)}"}), 500

    # 3. Determine numeric ID (Legacy support for community events)
    numeric_id = None
    if event_identifier.startswith("community_"):
        try:
            numeric_id = int(event_identifier.replace("community_", ""))
        except:
            pass

    # 4. Create the Review
    review = Review(
        user_id=session["user_id"],
        event_identifier=event_identifier, # Stores "official_xyz" or "community_1"
        score=int(data.get("rating", 5)),
        title=data.get("title", ""),
        body=data.get("comment", ""),
        created_at=datetime.now()
    )
    
    try:
        db.session.add(review)
        db.session.commit()
        
        # Return with user info for immediate display
        user = User.query.get(session["user_id"])
        response_data = review.as_dict()
        response_data["username"] = user.username
        response_data["user_avatar"] = user.profile.avatar_url if user.profile else None
        
        return jsonify({"message": "Review submitted!", "review": response_data}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
# PUT update review
@review_bp.route("/reviews/<int:review_id>", methods=["PUT"])
def update_review(review_id):
    if "user_id" not in session: return jsonify({"error": "Auth required"}), 401
    
    review = Review.query.get(review_id)
    if not review: return jsonify({"error": "Review not found"}), 404
    
    if review.user_id != session["user_id"]: return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    if "score" in data: review.score = int(data["score"])
    if "title" in data: review.title = data["title"]
    if "body" in data: review.body = data["body"] #Frontend sends "body" or "comment"? Adjusted to model.
    if "comment" in data: review.body = data["comment"] # Handle both just in case

    db.session.commit()
    return jsonify(review.as_dict())

# DELETE review
@review_bp.route("/reviews/<int:review_id>", methods=["DELETE"])
def delete_review(review_id):
    if "user_id" not in session: return jsonify({"error": "Auth required"}), 401
        
    review = Review.query.get(review_id)
    if not review: return jsonify({"error": "Review not found"}), 404
        
    if review.user_id != session["user_id"]: return jsonify({"error": "Unauthorized"}), 403
        
    db.session.delete(review)
    db.session.commit()
    return jsonify({"message": "Review deleted"})