import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from tools.document_loader import load_document

path = "assets/test_rule_document.md"
print("=== BEFORE LOAD ===", flush=True)
doc = load_document.invoke({"file_path": path})
print("=== AFTER LOAD ===", flush=True)
print(f"TYPE: {type(doc)}", flush=True)
print(f"REPR: {repr(doc)[:200]}", flush=True)
print(f"HAS page_content: {hasattr(doc, 'page_content')}", flush=True)
if hasattr(doc, 'page_content'):
    print(f"page_content type: {type(doc.page_content)}", flush=True)
    print(f"page_content len: {len(doc.page_content)}", flush=True)
else:
    print(f"IS STRING: {isinstance(doc, str)}", flush=True)
    print(f"STRING LEN: {len(doc)}", flush=True)
