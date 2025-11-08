# models/registered_event.py
from . import db

class RegisteredEvent(db.Model):
    __tablename__ = "registered_event"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)
    event_identifier = db.Column(db.String(45), nullable=True)
    registered_at = db.Column(db.DateTime, nullable=False)

    def as_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_id": self.event_id,
            "event_identifier": self.event_identifier,
            "registered_at": self.registered_at.isoformat() if self.registered_at else None
        }
