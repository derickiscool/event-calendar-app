# models/registered_event.py
from . import db

class RegisteredEvent(db.Model):
    __tablename__ = "registered_event"
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), primary_key=True)
    registered_at = db.Column(db.DateTime, nullable=False)

    def as_dict(self):
        return {
            "user_id": self.user_id,
            "event_id": self.event_id,
            "registered_at": self.registered_at.isoformat() if self.registered_at else None
        }
