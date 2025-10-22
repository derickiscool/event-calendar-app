# models/tag.py
from . import db

class Tag(db.Model):
    __tablename__ = "tag"
    id = db.Column(db.Integer, primary_key=True)
    tag_name = db.Column(db.String(45), unique=True, nullable=False)

    def as_dict(self):
        return {
            "id": self.id,
            "tag_name": self.tag_name
        }
