import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import asyncio
from biz.rag_service import get_rag_service_sync

rag = get_rag_service_sync()

workspace_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
assets_dir = os.path.join(workspace_path, "assets")

for root, dirs, files in os.walk(assets_dir):
    for file in files:
        if file.endswith('.md') or file.endswith('.docx'):
            path = os.path.join(root, file)
            print(f"Processing: {path}")
            try:
                res = asyncio.get_event_loop().run_until_complete(rag.ingest_file(path))
                print(f"  Result: {res}")
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"  Error: {e}")
