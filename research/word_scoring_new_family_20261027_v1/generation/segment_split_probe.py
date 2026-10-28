import json, collections, sys
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("/home/testuser/wzh/models/hf/Qwen3-4B", local_files_only=True)
path="research/word_scoring_new_family_20261027_v1/generation/results/RAW_RESPONSES.jsonl"
import os
os.chdir("/home/testuser/wzh/paper_e_c_review_20261028")
rows=[json.loads(l) for l in open(path,encoding="utf-8") if l.strip()]
out=[]
agg=collections.defaultdict(lambda: {"n":0,"reason":0,"answer":0,"unclosed":0,"sum_out":0})
for r in rows:
    t=r["response_text"]; arm=r["arm"]; ot=r["usage"]["output_tokens"]
    if "</think>" in t:
        head,rest=t.split("</think>",1)
        head=head+"</think>"
        nr=len(tok(head,add_special_tokens=False)["input_ids"])
        na=len(tok(rest,add_special_tokens=False)["input_ids"])
    else:
        nr=len(tok(t,add_special_tokens=False)["input_ids"]); na=0
    a=agg[arm]; a["n"]+=1; a["reason"]+=nr; a["answer"]+=na; a["sum_out"]+=ot
    if "</think>" not in t: a["unclosed"]+=1
    out.append({"arm":arm,"uid":r["question_uid"],"out_tokens":ot,"reason_tok":nr,"answer_tok":na,
                "closed":"</think>" in t})
for arm in ("D","T","M"):
    a=agg[arm]
    print(arm, "n",a["n"], "unclosed",a["unclosed"],
          "reason_tok_mean", round(a["reason"]/a["n"],1),
          "answer_tok_mean", round(a["answer"]/a["n"],1),
          "persisted_out_mean", round(a["sum_out"]/a["n"],1))
json.dump(out, open("/tmp/seg_split.json","w"), indent=1)
print("rows", len(out))
