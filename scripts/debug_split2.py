import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from tools.text_splitter import split_text_by_markdown_structure

text = "# 标题1\n\n内容1\n\n## 标题2\n\n内容2\n\n### 标题3\n\n内容3"
print(f"Input type: {type(text)}")
print(f"Input len: {len(text)}")
try:
    res = split_text_by_markdown_structure.invoke({"text": text})
    print(f"OK: {len(res)}")
except Exception as e:
    import traceback
    traceback.print_exc()
