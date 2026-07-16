import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from storage.database.db import get_engine
from sqlalchemy import text

e = get_engine()
with e.connect() as c:
    r = c.execute(text('SELECT COUNT(*) FROM langchain_pg_embedding'))
    count = r.scalar()
    print(f'Embedding count: {count}')
    r2 = c.execute(text('SELECT COUNT(DISTINCT collection_id) FROM langchain_pg_embedding'))
    cols = r2.scalar()
    print(f'Collections: {cols}')
    r3 = c.execute(text("SELECT name FROM langchain_pg_collection"))
    for row in r3:
        print(f'Collection: {row[0]}')
    r4 = c.execute(text("SELECT cmetadata->>'source' as src, COUNT(*) FROM langchain_pg_embedding GROUP BY src"))
    for row in r4:
        print(f'  Source: {row[0]} -> {row[1]} docs')
