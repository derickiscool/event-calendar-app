# routes/user_profile.py
from flask import Blueprint, request, jsonify
from project.models import db, UserProfile

user_profile_bp = Blueprint("user_profile", __name__)

# GET all profiles
@user_profile_bp.route("/user-profiles", methods=["GET"])
def get_profiles():
    profiles = UserProfile.query.all()
    return jsonify([p.as_dict() for p in profiles])

# GET single profile
@user_profile_bp.route("/user-profiles/<int:user_id>", methods=["GET"])
def get_profile(user_id):
    profile = UserProfile.query.get(user_id)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    return jsonify(profile.as_dict())

# PUT update profile
@user_profile_bp.route("/user-profiles/<int:user_id>", methods=["PUT"])
def update_profile(user_id):
    profile = UserProfile.query.get(user_id)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    data = request.get_json()

    for field in ["fname", "lname", "avatar_url", "phone", "postal_code"]:
        if field in data:
            setattr(profile, field, data[field])

    db.session.commit()
    return jsonify(profile.as_dict())
