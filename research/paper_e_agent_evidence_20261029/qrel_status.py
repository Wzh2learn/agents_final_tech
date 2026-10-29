"""Three-way qrels status: positive, explicitly nonpositive, or unjudged."""
import csv

def load_qrels(path):
    result = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            result.setdefault(row["query-id"], {})[row["corpus-id"]] = int(row["score"])
    return result

def status(judgments, qid, docid):
    row = judgments.get(qid, {})
    if docid not in row:
        return "UNJUDGED"
    return "QRELS_POSITIVE" if row[docid] > 0 else "QRELS_NONPOSITIVE"
