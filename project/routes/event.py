# routes/event.py
from flask import Blueprint, request, jsonify, current_app
from project.models import db, Event, Venue
from werkzeug.utils import secure_filename
from datetime import datetime
import os

event_bp = Blueprint("event", __name__)

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_image_size(file):
    """Check if file size is within limit"""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)  # Reset file pointer
    return size <= MAX_FILE_SIZE

def save_event_image(file, event_id):
    """Save event image and return the URL"""
    if not file or file.filename == '':
        return None
    
    if not allowed_file(file.filename):
        raise ValueError("Invalid file type. Allowed: JPEG, PNG, WebP")
    
    if not validate_image_size(file):
        raise ValueError("File size exceeds 5MB limit")
    
    # Get file extension
    ext = file.filename.rsplit('.', 1)[1].lower()
    
    # Create filename
    filename = f"event_{event_id}.{ext}"
    
    # Ensure upload directory exists
    upload_dir = os.path.join(current_app.static_folder, 'assets', 'images', 'events')
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    
    # Return URL path
    return f"/static/assets/images/events/{filename}"

def delete_event_image(image_url):
    """Delete event image file"""
    if not image_url:
        return
    
    try:
        # Extract filename from URL
        filename = image_url.split('/')[-1]
        filepath = os.path.join(current_app.static_folder, 'assets', 'images', 'events', filename)
        
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"Error deleting image: {e}")

def find_or_create_venue(name, address, postal_code):
    """Find existing venue by name or create new one"""
    # Try to find existing venue by name
    venue = Venue.query.filter_by(name=name).first()
    
    if venue:
        # Update address and postal code if provided
        venue.address = address
        venue.postal_code = postal_code
    else:
        # Create new venue
        venue = Venue(
            name=name,
            address=address,
            postal_code=postal_code
        )
        db.session.add(venue)
    
    db.session.commit()
    return venue

# GET all events
@event_bp.route("/events", methods=["GET"])
def get_events():
    events = Event.query.all()
    return jsonify([e.as_dict() for e in events])

# GET user's own events
@event_bp.route("/events/my-events", methods=["GET"])
def get_my_events():
    from flask import session
    
    # Check authentication
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    # Get events created by this user, ordered by start date descending
    events = Event.query.filter_by(user_id=session["user_id"]).order_by(Event.start_datetime.desc()).all()
    return jsonify([e.as_dict() for e in events])

# GET single event
@event_bp.route("/events/<int:event_id>", methods=["GET"])
def get_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    return jsonify(event.as_dict())

# POST create event
@event_bp.route("/events", methods=["POST"])
def create_event():
    from flask import session
    
    # Check authentication
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    # Get form data
    title = request.form.get("title")
    description = request.form.get("description")
    start_datetime = request.form.get("start_datetime")
    end_datetime = request.form.get("end_datetime")
    location = request.form.get("location")
    venue_name = request.form.get("venue_name")
    venue_address = request.form.get("venue_address")
    venue_postal = request.form.get("venue_postal")
    
    # Validate required fields
    if not title:
        return jsonify({"error": "Event title is required"}), 400
    if not start_datetime:
        return jsonify({"error": "Start date/time is required"}), 400
    if not end_datetime:
        return jsonify({"error": "End date/time is required"}), 400
    if not venue_name:
        return jsonify({"error": "Venue name is required"}), 400
    if not venue_address:
        return jsonify({"error": "Venue address is required"}), 400
    if not venue_postal:
        return jsonify({"error": "Venue postal code is required"}), 400
    
    # Validate postal code format
    if not venue_postal.isdigit() or len(venue_postal) != 6:
        return jsonify({"error": "Postal code must be exactly 6 digits"}), 400
    
    try:
        # Convert ISO datetime strings to Python datetime objects
        # Handle both formats: '2025-11-07T22:30:00.000Z' and '2025-11-07T22:30:00Z'
        start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
        
        # Find or create venue
        venue = find_or_create_venue(venue_name, venue_address, venue_postal)
        
        # Create event (without image first to get ID)
        event = Event(
            user_id=session["user_id"],
            title=title,
            description=description if description else None,
            start_datetime=start_dt,
            end_datetime=end_dt,
            location=location if location else None,
            image_url=None,  # Will update after saving image
            venue_id=venue.id
        )
        db.session.add(event)
        db.session.flush()  # Get event ID without committing
        
        # Handle image upload if provided
        image_url = None
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename:
                try:
                    image_url = save_event_image(image_file, event.id)
                    event.image_url = image_url
                except ValueError as e:
                    return jsonify({"error": str(e)}), 400
        
        db.session.commit()
        return jsonify(event.as_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating event: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to create event: {str(e)}"}), 500

# PUT update event
@event_bp.route("/events/<int:event_id>", methods=["PUT"])
def update_event(event_id):
    from flask import session
    
    # Check authentication
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    
    # Check ownership
    if event.user_id != session["user_id"]:
        return jsonify({"error": "You don't have permission to edit this event"}), 403
    
    # Get form data
    title = request.form.get("title")
    description = request.form.get("description")
    start_datetime = request.form.get("start_datetime")
    end_datetime = request.form.get("end_datetime")
    location = request.form.get("location")
    venue_name = request.form.get("venue_name")
    venue_address = request.form.get("venue_address")
    venue_postal = request.form.get("venue_postal")
    
    # Validate postal code if provided
    if venue_postal and (not venue_postal.isdigit() or len(venue_postal) != 6):
        return jsonify({"error": "Postal code must be exactly 6 digits"}), 400
    
    try:
        # Update basic fields
        if title:
            event.title = title
        if description is not None:
            event.description = description if description else None
        if start_datetime:
            event.start_datetime = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
        if end_datetime:
            event.end_datetime = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
        if location is not None:
            event.location = location if location else None
        
        # Update venue if provided
        if venue_name and venue_address and venue_postal:
            venue = find_or_create_venue(venue_name, venue_address, venue_postal)
            event.venue_id = venue.id
        
        # Handle image upload if provided
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename:
                # Delete old image if exists
                if event.image_url:
                    delete_event_image(event.image_url)
                
                try:
                    image_url = save_event_image(image_file, event.id)
                    event.image_url = image_url
                except ValueError as e:
                    return jsonify({"error": str(e)}), 400
        
        db.session.commit()
        return jsonify(event.as_dict())
        
    except Exception as e:
        db.session.rollback()
        print(f"Error updating event: {e}")
        return jsonify({"error": "Failed to update event"}), 500

# DELETE event
@event_bp.route("/events/<int:event_id>", methods=["DELETE"])
def delete_event(event_id):
    from flask import session
    
    # Check authentication
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    
    # Check ownership
    if event.user_id != session["user_id"]:
        return jsonify({"error": "You don't have permission to delete this event"}), 403
    
    # Delete associated image if exists
    if event.image_url:
        delete_event_image(event.image_url)
    
    db.session.delete(event)
    db.session.commit()
    return jsonify({"message": "Event deleted successfully"})
    return jsonify({"message": "Event and all related data deleted"})
