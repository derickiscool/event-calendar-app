# models/user_preference.py
from . import db

class UserPreference(db.Model):
    __tablename__ = "user_preference"
    tag_id = db.Column(db.Integer, db.ForeignKey("tag.id"), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)

    def as_dict(self):
        return {
            "tag_id": self.tag_id,
            "user_id": self.user_id
        }
