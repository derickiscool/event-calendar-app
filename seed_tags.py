from project import app
from project.models import db, Tag, UserPreference, EventTag
from sqlalchemy import text

def seed_tags():
    print("--- Starting Tag Cleanup & Seeding ---")
    
    with app.app_context():
        try:
            # 1. DELETE EXISTING DATA (Order matters due to Foreign Keys!)
            # We must delete references to tags before deleting the tags themselves.
            print("Cleaning up old data...")
            
            # Remove preferences linking to tags
            deleted_prefs = db.session.query(UserPreference).delete()
            print(f"- Removed {deleted_prefs} user preferences")
            
            # Remove event tags linking to tags
            deleted_event_tags = db.session.query(EventTag).delete()
            print(f"- Removed {deleted_event_tags} event tag links")
            
            # Finally, delete the tags
            deleted_tags = db.session.query(Tag).delete()
            print(f"- Removed {deleted_tags} old tags")
            
            # Optional: Reset ID counter (Auto Increment) back to 1
            # Note: Syntax depends on MariaDB/MySQL
            db.session.execute(text("ALTER TABLE tag AUTO_INCREMENT = 1"))
            
            db.session.commit()

            # 2. INSERT OFFICIAL CONTROLLED VOCABULARY
            print("Seeding new tags...")
            
            # This list covers your mapped categories + common community interests
            official_tags = [
    "Music", "Theatre", "Comedy", "Film", "Visual Arts", "Workshops",
    "Dance", "Literature", "Tech", "Food & Drink", 
    "Nightlife", "Family Friendly", "Free", "Outdoor",
    "Festival", "Photography", "Crafts", "Wellness",
    "Other"  # <--- ADD THIS
            ]
            
            for tag_name in official_tags:
                new_tag = Tag(tag_name=tag_name)
                db.session.add(new_tag)
            
            db.session.commit()
            print(f"Success! Added {len(official_tags)} clean tags.")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding tags: {e}")

if __name__ == "__main__":
    seed_tags()