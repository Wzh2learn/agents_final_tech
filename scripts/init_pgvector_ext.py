import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from sqlalchemy import create_engine, text
engine = create_engine('postgresql+psycopg://postgres:postgres@localhost:15432/vector_db')
with engine.connect() as conn:
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    conn.commit()
    result = conn.execute(text("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"))
    exists = result.scalar()
    print(f"PGVector extension exists: {exists}")
print("Done")
