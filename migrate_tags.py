from project import app, db
from project.models import Event, EventCache, EventTag
from sqlalchemy import text

def migrate_tags():
    print("--- Starting Tag Migration ---")
    
    with app.app_context():
        # 1. BACKUP EXISTING DATA
        print("1. Backing up existing tags...")
        try:
            # Check if table exists first
            result = db.session.execute(text("SELECT id, tag_id, event_id FROM event_tag"))
            old_tags = [{'id': r[0], 'tag_id': r[1], 'event_id': r[2]} for r in result]
            print(f"   > Found {len(old_tags)} tags to migrate.")
        except Exception as e:
            print("   > No existing table or error reading tags. Skipping backup (New setup?).")
            old_tags = []

        # 2. DROP AND RECREATE TABLE
        print("2. Recreating EventTag table with new schema...")
        try:
            # We must drop the table to add the new Foreign Key column 'event_identifier'
            db.session.execute(text("DROP TABLE IF EXISTS event_tag"))
            db.session.commit()
            
            # Recreate it using the new Model definition from project/models/event_tag.py
            db.create_all() 
            print("   > Table recreated successfully.")
        except Exception as e:
            print(f"   > Error recreating table: {e}")
            return

        # 3. RESTORE DATA & POPULATE CACHE
        print("3. Restoring tags and updating EventCache...")
        restored_count = 0
        skipped_count = 0
        
        # We need to process unique events to batch cache creation efficiently
        # But for simplicity and safety, we'll do it row by row
        
        for item in old_tags:
            tag_id = item['tag_id']
            event_id = item['event_id']
            
            # Legacy tags were ONLY for community events (which have numeric IDs)
            if event_id:
                identifier = f"community_{event_id}"
                
                # A. Ensure Cache Entry Exists (The "Bridge")
                # We need this because the new EventTag table has a Foreign Key to EventCache
                cache_entry = EventCache.query.get(identifier)
                
                if not cache_entry:
                    # Fetch original event data to fill the cache title
                    original_event = Event.query.get(event_id)
                    
                    if original_event:
                        title = original_event.title
                        
                        new_cache = EventCache(
                            event_identifier=identifier,
                            source='community',
                            original_id=str(event_id),
                            title=title
                        )
                        db.session.add(new_cache)
                        # Commit immediately so the Foreign Key constraint is satisfied for the Tag
                        db.session.commit()
                    else:
                        print(f"   ! Warning: Event ID {event_id} not found in Event table. Skipping tag.")
                        skipped_count += 1
                        continue

                # B. Insert the migrated Tag
                # We explicitly set both ID links for maximum compatibility
                new_tag = EventTag(
                    tag_id=tag_id,
                    event_id=event_id,
                    event_identifier=identifier
                )
                db.session.add(new_tag)
                restored_count += 1

        db.session.commit()
        print(f"--- Migration Complete ---")
        print(f"   > Restored: {restored_count}")
        print(f"   > Skipped:  {skipped_count}")

if __name__ == "__main__":
    migrate_tags()