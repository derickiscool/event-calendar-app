# project/models/bookmark.py
from . import db

class Bookmark(db.Model):
    __tablename__ = "bookmark"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    
    # Legacy support for internal events
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True)
    
    # Universal link to EventCache (supports both Official & Community)
    event_identifier = db.Column(db.String(255), db.ForeignKey("event_cache.event_identifier"), nullable=False)
    
    created_at = db.Column(db.DateTime, nullable=False , default=db.func.now())

    def as_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_id": self.event_id,
            "event_identifier": self.event_identifier,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }