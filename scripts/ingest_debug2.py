import sys, os, asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from biz.rag_service import get_rag_service_sync

rag = get_rag_service_sync()

for root, dirs, files in os.walk("assets"):
    for file in files:
        if file.endswith('.md') or file.endswith('.docx'):
            path = os.path.join(root, file)
            print(f"\nProcessing: {path}")
            try:
                res = asyncio.get_event_loop().run_until_complete(rag.ingest_file(path))
                print(f"  SUCCESS: chunks={res['chunks']}, collection={res['collection']}")
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"  FAILED: {e}")
