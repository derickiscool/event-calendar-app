# routes/venue.py
from flask import Blueprint, request, jsonify
from models import db, Venue

venue_bp = Blueprint("venue", __name__)

# GET all venues
@venue_bp.route("/venues", methods=["GET"])
def get_venues():
    venues = Venue.query.all()
    return jsonify([v.as_dict() for v in venues])

# GET single venue
@venue_bp.route("/venues/<int:venue_id>", methods=["GET"])
def get_venue(venue_id):
    venue = Venue.query.get(venue_id)
    if not venue:
        return jsonify({"error": "Venue not found"}), 404
    return jsonify(venue.as_dict())

# POST create venue
@venue_bp.route("/venues", methods=["POST"])
def create_venue():
    data = request.get_json()

    # Duplicate check
    existing = Venue.query.filter_by(
        name=data.get("name"),
        address=data.get("address")
    ).first()
    if existing:
        return jsonify({"message": "Venue already exists"}), 400

    venue = Venue(
        name=data.get("name"),
        address=data.get("address"),
        postal_code=data.get("postal_code")
    )
    db.session.add(venue)
    db.session.commit()
    return jsonify(venue.as_dict()), 201

# PUT update venue
@venue_bp.route("/venues/<int:venue_id>", methods=["PUT"])
def update_venue(venue_id):
    venue = Venue.query.get(venue_id)
    if not venue:
        return jsonify({"error": "Venue not found"}), 404
    data = request.get_json()
    
    for field in ["name", "address", "postal_code"]:
        if field in data:
            setattr(venue, field, data[field])
    
    db.session.commit()
    return jsonify(venue.as_dict())

# DELETE venue
@venue_bp.route("/venues/<int:venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    venue = Venue.query.get(venue_id)
    if not venue:
        return jsonify({"error": "Venue not found"}), 404
    db.session.delete(venue)
    db.session.commit()
    return jsonify({"message": "Venue deleted"})
