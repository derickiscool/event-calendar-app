from flask import Blueprint, request, jsonify, current_app, session
from project.models import db, Event, Venue, Tag
from project.db import get_mongo_client
from bson import ObjectId
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload
from datetime import datetime
import os

from project.db import get_mongo_status, get_mariadb_status


event_bp = Blueprint("event", __name__)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def allowed_file(filename):
    """Check if file extension is allowed"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_image_size(file):
    """Check if file size is within limit"""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)  # Reset file pointer
    return size <= MAX_FILE_SIZE


def save_event_image(file, event_id):
    """Save event image and return the URL"""
    if not file or file.filename == "":
        return None

    if not allowed_file(file.filename):
        raise ValueError("Invalid file type. Allowed: JPEG, PNG, WebP")

    if not validate_image_size(file):
        raise ValueError("File size exceeds 5MB limit")

    # Get file extension
    ext = file.filename.rsplit(".", 1)[1].lower()

    # Create filename
    filename = f"event_{event_id}.{ext}"

    # Ensure upload directory exists
    upload_dir = os.path.join(current_app.static_folder, "assets", "images", "events")
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
        filename = image_url.split("/")[-1]
        filepath = os.path.join(
            current_app.static_folder, "assets", "images", "events", filename
        )

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
        venue = Venue(name=name, address=address, postal_code=postal_code)
        db.session.add(venue)

    db.session.commit()
    return venue


def _categorize_event(text):
    text_lower = text.lower()
    categories = {
        "music": ["music", "concert", "band", "orchestra"],
        "theatre": ["theatre", "theater", "play", "drama", "musical"],
        "comedy": ["comedy", "stand-up", "funny"],
        "film": ["film", "movie", "cinema"],
        "visual-arts": ["art", "exhibition", "gallery", "painting"],
        "workshops": ["workshop", "class", "course"],
    }
    for category, keywords in categories.items():
        if any(keyword in text_lower for keyword in keywords):
            return category
    return "other"


def _map_tag_to_category(tag_name):
    mapping = {
        "music": "music",
        "theatre": "theatre",
        "art": "visual-arts",
        "workshop": "workshops",
    }
    return mapping.get(tag_name.lower(), "other")


@event_bp.route("/all-events", methods=["GET"])
def get_all_events():
    """Unified endpoint for MongoDB + MySQL Events"""
    category = request.args.get("category", "all")
    source_filter = request.args.get("source", "all")
    search_query = request.args.get("q", "").lower()

    all_events = []

    # 1. Fetch Mongo
    try:
        client = get_mongo_client()
        if client:
            db_mongo = client.get_database("event_calendar")
            for e in db_mongo.events.find({}):
                cat = _categorize_event(
                    e.get("title", "") + " " + e.get("description", "")
                )
                all_events.append(
                    {
                        "id": f"official_{str(e['_id'])}",
                        "title": e.get("title"),
                        "description": e.get("description"),
                        "date": e.get("start_date", "TBA"),
                        "venue": e.get("venue_name"),
                        "location": e.get("address"),
                        "image": e.get("image_url"),
                        "category": cat,
                        "source": "official",
                        "start_date": e.get("start_date"),
                        "tags": [cat],
                    }
                )
            client.close()
    except Exception as e:
        print(f"Mongo Error: {e}")

    # 2. Fetch MySQL
    try:
        community_events = Event.query.options(
            joinedload(Event.tags), joinedload(Event.creator)
        ).all()
        for e in community_events:
            venue = Venue.query.get(e.venue_id) if e.venue_id else None
            tags = [t.tag.tag_name for t in e.tags] if e.tags else []
            cat = _map_tag_to_category(tags[0]) if tags else "other"

            all_events.append(
                {
                    "id": f"community_{e.id}",
                    "title": e.title,
                    "description": e.description,
                    "date": (
                        e.start_datetime.strftime("%Y-%m-%d %H:%M")
                        if e.start_datetime
                        else "TBA"
                    ),
                    "venue": venue.name if venue else "TBA",
                    "location": venue.address if venue else "",
                    "image": e.image_url,
                    "category": cat,
                    "source": "community",
                    "start_date": (
                        e.start_datetime.isoformat() if e.start_datetime else ""
                    ),
                    "tags": tags,
                    "creator_id": e.user_id,
                }
            )
    except Exception as e:
        print(f"MySQL Error: {e}")

    # 3. Filter & Sort
    if source_filter != "all":
        all_events = [e for e in all_events if e["source"] == source_filter]
    if category != "all":
        all_events = [e for e in all_events if e["category"] == category]
    if search_query:
        all_events = [e for e in all_events if search_query in str(e).lower()]

    all_events.sort(key=lambda x: x.get("start_date") or "9999", reverse=False)
    official_count = sum(1 for e in all_events if e["source"] == "official")
    community_count = sum(1 for e in all_events if e["source"] == "community")
    
    return jsonify(
        {
            "status": "success",
            "total": len(all_events),
            "official_count": official_count,
            "community_count": community_count,
            "events": all_events,
        }
    )


@event_bp.route("/event/<event_id>", methods=["GET"])
def get_unified_event(event_id):
    """Get Single Event (Unified)"""
    try:
        if event_id.startswith("official_"):
            client = get_mongo_client()
            if not client:
                return jsonify({"error": "DB Error"}), 500

            event = client.get_database("event_calendar").events.find_one(
                {"_id": ObjectId(event_id.replace("official_", ""))}
            )
            client.close()
            if not event:
                return jsonify({"error": "Not Found"}), 404

            return jsonify(
                {
                    "status": "success",
                    "event": {
                        "id": event_id,
                        "title": event.get("title"),
                        "description": event.get("description"),
                        "start_date": event.get("start_date"),
                        "venue": event.get("venue_name"),
                        "image": event.get("image_url"),
                        "source": "official",
                    },
                }
            )

        elif event_id.startswith("community_"):
            e = Event.query.get(int(event_id.replace("community_", "")))
            if not e:
                return jsonify({"error": "Not Found"}), 404
            return jsonify({"status": "success", "event": e.as_dict()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# GET user's own events
@event_bp.route("/events/my-events", methods=["GET"])
def get_my_events():
    from flask import session

    # Check authentication
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    # Get events created by this user, ordered by start date descending
    events = (
        Event.query.filter_by(user_id=session["user_id"])
        .order_by(Event.start_datetime.desc())
        .all()
    )
    return jsonify([e.as_dict() for e in events])


# GET single event
@event_bp.route("/events/<int:event_id>", methods=["GET"])
def get_event(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404
    return jsonify(event.as_dict())


# GET event for editing (requires authentication and ownership)
@event_bp.route("/events/edit/<int:event_id>", methods=["GET"])
def get_event_for_edit(event_id):
    from flask import session

    # Check authentication
    if "user_id" not in session:
        return jsonify({"error": "Not authenticated"}), 401

    event = Event.query.get(event_id)
    if not event:
        return jsonify({"error": "Event not found"}), 404

    # Check ownership - only event creator can load it for editing
    if event.user_id != session["user_id"]:
        return jsonify({"error": "You don't have permission to edit this event"}), 403

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
        start_dt = datetime.fromisoformat(start_datetime.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_datetime.replace("Z", "+00:00"))

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
            venue_id=venue.id,
        )
        db.session.add(event)
        db.session.flush()  # Get event ID without committing

        # Handle image upload if provided
        image_url = None
        if "image" in request.files:
            image_file = request.files["image"]
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
            event.start_datetime = datetime.fromisoformat(
                start_datetime.replace("Z", "+00:00")
            )
        if end_datetime:
            event.end_datetime = datetime.fromisoformat(
                end_datetime.replace("Z", "+00:00")
            )
        if location is not None:
            event.location = location if location else None

        # Update venue if provided
        if venue_name and venue_address and venue_postal:
            venue = find_or_create_venue(venue_name, venue_address, venue_postal)
            event.venue_id = venue.id

        # Handle image upload if provided
        if "image" in request.files:
            image_file = request.files["image"]
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


@event_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint required by frontend"""
    mongo_status = get_mongo_status()
    mariadb_status = get_mariadb_status()

    # Return 200 if both are okay, or if at least one works (partial degradation)
    if mongo_status == "connected" or mariadb_status == "connected":
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Backend is running",
                    "mongodb": mongo_status,
                    "mariadb": mariadb_status,
                }
            ),
            200,
        )
    else:
        return (
            jsonify(
                {"status": "error", "mongodb": mongo_status, "mariadb": mariadb_status}
            ),
            500,
        )
