# routes/review.py
from flask import Blueprint, request, jsonify
from project.models import db, Review

review_bp = Blueprint("review", __name__)

# GET all reviews
@review_bp.route("/reviews", methods=["GET"])
def get_reviews():
    reviews = Review.query.all()
    return jsonify([r.as_dict() for r in reviews])

# GET review by ID
@review_bp.route("/reviews/<int:review_id>", methods=["GET"])
def get_review(review_id):
    review = Review.query.get(review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404
    return jsonify(review.as_dict())

# POST create review
@review_bp.route("/reviews", methods=["POST"])
def create_review():
    data = request.get_json()

    # Duplicate check
    existing = Review.query.filter_by(
        user_id=data.get("user_id"),
        event_id=data.get("event_id")
    ).first()
    if existing:
        return jsonify({"message": "User has already reviewed this event"}), 400

    review = Review(
        user_id=data.get("user_id"),
        event_id=data.get("event_id"),
        score=data.get("score"),
        title=data.get("title"),
        body=data.get("body"),
        created_at=data.get("created_at")
    )
    db.session.add(review)
    db.session.commit()
    return jsonify(review.as_dict()), 201


# PUT update review
@review_bp.route("/reviews/<int:review_id>", methods=["PUT"])
def update_review(review_id):
    review = Review.query.get(review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404
    data = request.get_json()
    
    for field in ["score", "title", "body", "created_at"]:
        if field in data:
            setattr(review, field, data[field])
    
    db.session.commit()
    return jsonify(review.as_dict())

# DELETE review
@review_bp.route("/reviews/<int:review_id>", methods=["DELETE"])
def delete_review(review_id):
    review = Review.query.get(review_id)
    if not review:
        return jsonify({"error": "Review not found"}), 404
    db.session.delete(review)
    db.session.commit()
    return jsonify({"message": "Review deleted"})
