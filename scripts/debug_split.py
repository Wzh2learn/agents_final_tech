import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from tools.document_loader import load_document
from tools.text_splitter import split_text_by_markdown_structure

path = "assets/test_rule_document.md"
print(f"Loading: {path}")
doc = load_document.invoke({"file_path": path})
print(f"Type: {type(doc)}")
print(f"Len: {len(doc)}")
print(f"First 200 chars: {doc[:200]}")

print("\nSplitting...")
try:
    res = split_text_by_markdown_structure.invoke({"text": doc})
    print(f"Result len: {len(res)}")
    print(f"Result preview: {res[:500]}")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Error: {e}")
