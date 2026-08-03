from storage.collaboration import get_collaboration_db
from sqlalchemy import inspect, text

def migrate():
    db = get_collaboration_db()
    engine = db.engine
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('collaboration_sessions')]
    
    with engine.connect() as conn:
        if 'type' not in columns:
            print("Adding column 'type' to collaboration_sessions")
            conn.execute(text("ALTER TABLE collaboration_sessions ADD COLUMN type VARCHAR(20) DEFAULT 'private'"))
        if 'role_key' not in columns:
            print("Adding column 'role_key' to collaboration_sessions")
            conn.execute(text("ALTER TABLE collaboration_sessions ADD COLUMN role_key VARCHAR(50) DEFAULT 'default_engineer'"))
        conn.commit()
    print("Migration completed or already up to date.")

if __name__ == "__main__":
    migrate()
