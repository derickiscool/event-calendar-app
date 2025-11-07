# routes/user_profile.py
from flask import Blueprint, request, jsonify
from project.models import db, UserProfile
import os
import re
from werkzeug.utils import secure_filename
from PIL import Image
import io

user_profile_bp = Blueprint("user_profile", __name__)

# Configuration
UPLOAD_FOLDER = 'project/static/assets/images/avatars'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_SIZE = 3 * 1024 * 1024  # 3MB
MIN_DIMENSION = 268
RECOMMENDED_DIMENSION = 400

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_image(file_stream):
    """Validate image dimensions and format."""
    try:
        img = Image.open(file_stream)
        width, height = img.size
        
        if width < MIN_DIMENSION or height < MIN_DIMENSION:
            return f"Image dimensions must be at least {MIN_DIMENSION}×{MIN_DIMENSION}px (current: {width}×{height}px)"
        
        return None
    except Exception as e:
        return f"Invalid image file: {str(e)}"

def save_avatar(file, user_id):
    """Save avatar file and return the URL."""
    try:
        # Create upload folder if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Generate secure filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"user_{user_id}.{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save file
        file.save(filepath)
        
        # Return URL path (relative to static folder)
        return f"/static/assets/images/avatars/{filename}"
    except Exception as e:
        raise Exception(f"Failed to save avatar: {str(e)}")

def delete_avatar(user_id):
    """Delete user's avatar file if it exists."""
    try:
        for ext in ALLOWED_EXTENSIONS:
            filename = f"user_{user_id}.{ext}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
    except Exception as e:
        print(f"Error deleting avatar: {str(e)}")

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

# GET current user's profile
@user_profile_bp.route("/profile/me", methods=["GET"])
def get_my_profile():
    """Get the logged-in user's profile."""
    from flask import session
    from project.models import User
    
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    user = User.query.get(session["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Get profile (create if doesn't exist)
    profile = UserProfile.query.get(user.id)
    if not profile:
        profile = UserProfile(user_id=user.id, fname="", lname="")
        db.session.add(profile)
        db.session.commit()
    
    return jsonify({
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email
        },
        "profile": profile.as_dict()
    })

# PUT update current user's profile
@user_profile_bp.route("/profile/me", methods=["PUT"])
def update_my_profile():
    """Update the logged-in user's profile with file upload support."""
    from flask import session
    import re
    
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    profile = UserProfile.query.get(session["user_id"])
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
    
    # Get form data (multipart/form-data instead of JSON)
    fname = request.form.get('fname', '').strip()
    lname = request.form.get('lname', '').strip()
    phone = request.form.get('phone', '').strip()
    postal_code = request.form.get('postal_code', '').strip()
    remove_avatar = request.form.get('remove_avatar', '').lower() == 'true'
    
    # Validate first name (required)
    if not fname:
        return jsonify({"error": "First name is required"}), 400
    if len(fname) > 45:
        return jsonify({"error": "First name must be less than 45 characters"}), 400
    if not re.match(r'^[a-zA-Z\s\'-]+$', fname):
        return jsonify({"error": "First name can only contain letters, spaces, hyphens, and apostrophes"}), 400
    
    # Validate last name (optional)
    if lname and len(lname) > 45:
        return jsonify({"error": "Last name must be less than 45 characters"}), 400
    if lname and not re.match(r'^[a-zA-Z\s\'-]+$', lname):
        return jsonify({"error": "Last name can only contain letters, spaces, hyphens, and apostrophes"}), 400
    
    # Validate phone (optional) - Singapore format: 8 digits only
    if phone and len(phone) != 8:
        return jsonify({"error": "Phone number must be exactly 8 digits"}), 400
    if phone and not re.match(r'^\d{8}$', phone):
        return jsonify({"error": "Phone number must be 8 digits only (no spaces or symbols)"}), 400
    
    # Validate postal code (optional)
    if postal_code and len(postal_code) != 6:
        return jsonify({"error": "Postal code must be exactly 6 digits"}), 400
    if postal_code and not re.match(r'^\d{6}$', postal_code):
        return jsonify({"error": "Postal code must be 6 digits"}), 400
    
    # Handle avatar upload
    if remove_avatar:
        # Remove avatar
        delete_avatar(session["user_id"])
        profile.avatar_url = None
    elif 'avatar' in request.files:
        file = request.files['avatar']
        if file and file.filename:
            # Validate file
            if not allowed_file(file.filename):
                return jsonify({"error": "Only JPEG, PNG, and WebP images are allowed"}), 400
            
            # Check file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > MAX_FILE_SIZE:
                return jsonify({"error": f"File size must be less than 3MB (current: {file_size / 1024 / 1024:.2f}MB)"}), 400
            
            # Validate image dimensions
            file_copy = io.BytesIO(file.read())
            file.seek(0)  # Reset for saving later
            
            dimension_error = validate_image(file_copy)
            if dimension_error:
                return jsonify({"error": dimension_error}), 400
            
            # Save avatar
            try:
                avatar_url = save_avatar(file, session["user_id"])
                profile.avatar_url = avatar_url
            except Exception as e:
                return jsonify({"error": str(e)}), 500
    
    # Update profile fields
    profile.fname = fname
    profile.lname = lname if lname else None
    profile.phone = phone if phone else None
    profile.postal_code = postal_code if postal_code else None
    
    db.session.commit()
    return jsonify({
        "message": "Profile updated successfully",
        "profile": profile.as_dict()
    })
