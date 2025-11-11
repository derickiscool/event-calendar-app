# routes/user_preference.py
from flask import Blueprint, request, jsonify, session
from project.models import db, UserPreference, Tag

user_preference_bp = Blueprint("user_preference", __name__)

# GET current user's preferences with tag details
@user_preference_bp.route("/preferences/me", methods=["GET"])
def get_my_preferences():
    """Get the logged-in user's tag preferences with full tag details."""
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    user_id = session["user_id"]
    
    # Get user's preference records
    prefs = UserPreference.query.filter_by(user_id=user_id).all()
    
    # Get full tag details for each preference
    tag_ids = [p.tag_id for p in prefs]
    tags = Tag.query.filter(Tag.id.in_(tag_ids)).all() if tag_ids else []
    
    return jsonify({
        "preferences": [{"tag_id": p.tag_id, "user_id": p.user_id} for p in prefs],
        "tags": [t.as_dict() for t in tags]
    })

# POST add preference for current user
@user_preference_bp.route("/preferences/me", methods=["POST"])
def add_my_preference():
    """Add a tag preference for the logged-in user."""
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    user_id = session["user_id"]
    data = request.get_json()
    tag_id = data.get("tag_id")
    
    if not tag_id:
        return jsonify({"error": "tag_id is required"}), 400
    
    # Check if tag exists
    tag = Tag.query.get(tag_id)
    if not tag:
        return jsonify({"error": "Tag not found"}), 404
    
    # Check if preference already exists
    existing = UserPreference.query.filter_by(
        user_id=user_id,
        tag_id=tag_id
    ).first()
    
    if existing:
        return jsonify({"message": "Preference already exists"}), 200
    
    # Create new preference
    pref = UserPreference(user_id=user_id, tag_id=tag_id)
    db.session.add(pref)
    db.session.commit()
    
    return jsonify({
        "message": "Preference added",
        "preference": pref.as_dict(),
        "tag": tag.as_dict()
    }), 201

# DELETE preference for current user
@user_preference_bp.route("/preferences/me/<int:tag_id>", methods=["DELETE"])
def delete_my_preference(tag_id):
    """Remove a tag preference for the logged-in user."""
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    user_id = session["user_id"]
    
    pref = UserPreference.query.filter_by(user_id=user_id, tag_id=tag_id).first()
    if not pref:
        return jsonify({"error": "Preference not found"}), 404
    
    db.session.delete(pref)
    db.session.commit()
    
    return jsonify({"message": "Preference removed"})
