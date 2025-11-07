# models/review.py
from . import db

class Review(db.Model):
    __tablename__ = "review"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)  # Made nullable for official events
    event_identifier = db.Column(db.String(255), nullable=True)  # New field for full event IDs (official_xxx or community_xxx)
    score = db.Column(db.SmallInteger, nullable=False)
    title = db.Column(db.String(255))
    body = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False)

    def as_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_id": self.event_id,
            "event_identifier": self.event_identifier,
            "score": self.score,
            "title": self.title,
            "body": self.body,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
