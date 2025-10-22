# models/user_profile.py
from . import db

class UserProfile(db.Model):
    __tablename__ = "user_profile"
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    fname = db.Column(db.String(45), nullable=False)
    lname = db.Column(db.String(45))
    avatar_url = db.Column(db.String(255))
    phone = db.Column(db.String(16))
    postal_code = db.Column(db.String(6))

    def as_dict(self):
        return {
            "user_id": self.user_id,
            "fname": self.fname,
            "lname": self.lname,
            "avatar_url": self.avatar_url,
            "phone": self.phone,
            "postal_code": self.postal_code
        }
