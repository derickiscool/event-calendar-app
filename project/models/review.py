from . import db

class Review(db.Model):
    __tablename__ = "review"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    
    # [FIX] Added db.ForeignKey("event.id") back so Event.reviews works
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=True) 
    
    # The real link to the Cache Table
    event_identifier = db.Column(db.String(255), db.ForeignKey("event_cache.event_identifier"), nullable=False)
    
    score = db.Column(db.SmallInteger, nullable=False)
    title = db.Column(db.String(255))
    body = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False)

    def as_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_identifier": self.event_identifier,
            "event_id": self.event_id,
            "score": self.score,
            "title": self.title,
            "body": self.body,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }