import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from langchain_text_splitters import MarkdownHeaderTextSplitter

text = "# 标题1\n\n内容1\n\n## 标题2\n\n内容2"
print(f"Input type: {type(text)}")
print(f"Input: {text!r}")

try:
    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[("#", "Header 1"), ("##", "Header 2")])
    chunks = splitter.split_text(text)
    print(f"Chunks: {len(chunks)}")
    for c in chunks:
        print(f"  - {type(c)}: {c.page_content[:50]}")
except Exception as e:
    import traceback
    traceback.print_exc()
