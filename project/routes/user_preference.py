# routes/user_preference.py
from flask import Blueprint, request, jsonify
from project.models import db, UserPreference

user_preference_bp = Blueprint("user_preference", __name__)

# GET all preferences
@user_preference_bp.route("/user-preferences", methods=["GET"])
def get_preferences():
    prefs = UserPreference.query.all()
    return jsonify([p.as_dict() for p in prefs])

# GET preferences of a user
@user_preference_bp.route("/user-preferences/user/<int:user_id>", methods=["GET"])
def get_user_preferences(user_id):
    prefs = UserPreference.query.filter_by(user_id=user_id).all()
    return jsonify([p.as_dict() for p in prefs])

# POST add a user preference
@user_preference_bp.route("/user-preferences", methods=["POST"])
def add_preference():
    data = request.get_json()

    # Duplicate check
    existing = UserPreference.query.filter_by(
        user_id=data.get("user_id"),
        tag_id=data.get("tag_id")
    ).first()
    if existing:
        return jsonify({"message": "Preference already exists"}), 400

    pref = UserPreference(
        user_id=data.get("user_id"),
        tag_id=data.get("tag_id")
    )
    db.session.add(pref)
    db.session.commit()
    return jsonify(pref.as_dict()), 201


# DELETE user preference
@user_preference_bp.route("/user-preferences/user/<int:user_id>/tag/<int:tag_id>", methods=["DELETE"])
def delete_preference(user_id, tag_id):
    pref = UserPreference.query.filter_by(user_id=user_id, tag_id=tag_id).first()
    if not pref:
        return jsonify({"error": "Preference not found"}), 404
    db.session.delete(pref)
    db.session.commit()
    return jsonify({"message": "Preference deleted"})
