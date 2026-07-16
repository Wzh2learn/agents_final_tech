import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from tools.document_loader import load_document

for root, dirs, files in os.walk("assets"):
    for file in files:
        if file.endswith('.md'):
            path = os.path.join(root, file)
            print(f"Loading: {path}")
            doc = load_document.invoke({"file_path": path})
            print(f"  Type: {type(doc)}")
            print(f"  Has page_content: {hasattr(doc, 'page_content')}")
            if hasattr(doc, 'page_content'):
                print(f"  Content len: {len(doc.page_content)}")
                print(f"  Content preview: {doc.page_content[:100]}")
            else:
                print(f"  Value: {doc}")
            break
    break
