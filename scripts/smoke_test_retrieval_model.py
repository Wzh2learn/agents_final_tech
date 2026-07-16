"""Smoke-test a local embedding or reranker model without starting a service."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DOCUMENTS = [
    "个人信用贷款申请人年龄应为22至60周岁。",
    "企业流动资金贷款的资产负债率原则上不高于70%。",
    "知识库文档需要保留章节和页码等来源信息。",
]
QUERY = "个人信用贷款的申请年龄要求是什么？"


def parse_args() -> argparse.Namespace:
    """Parse the local model path and the inference mode."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--kind", choices=("embedding", "reranker"), required=True)
    parser.add_argument("--device", default="cuda", help="Sentence Transformers device, e.g. cuda or cpu.")
    return parser.parse_args()


def run_embedding(model_path: Path, device: str) -> dict[str, Any]:
    """Encode a query and three documents, then return a ranked similarity list."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(str(model_path), trust_remote_code=True, device=device)
    document_embeddings = model.encode(DOCUMENTS, normalize_embeddings=True)
    query_embedding = model.encode([QUERY], normalize_embeddings=True)[0]
    scores = document_embeddings @ query_embedding
    ranking = sorted(
        ({"document": document, "score": round(float(score), 6)} for document, score in zip(DOCUMENTS, scores)),
        key=lambda item: item["score"],
        reverse=True,
    )
    return {"kind": "embedding", "dimension": int(document_embeddings.shape[1]), "ranking": ranking}


def run_reranker(model_path: Path, device: str) -> dict[str, Any]:
    """Score the same query-document pairs with a cross-encoder reranker."""
    from sentence_transformers import CrossEncoder

    model = CrossEncoder(str(model_path), trust_remote_code=True, device=device)
    scores = model.predict([(QUERY, document) for document in DOCUMENTS])
    ranking = sorted(
        ({"document": document, "score": round(float(score), 6)} for document, score in zip(DOCUMENTS, scores)),
        key=lambda item: item["score"],
        reverse=True,
    )
    return {"kind": "reranker", "ranking": ranking}


def main() -> None:
    """Load the requested model and print a compact JSON result."""
    args = parse_args()
    if not args.model_path.is_dir():
        raise SystemExit(f"Model directory does not exist: {args.model_path}")

    if args.kind == "embedding":
        result = run_embedding(args.model_path, args.device)
    else:
        result = run_reranker(args.model_path, args.device)

    result["model_path"] = str(args.model_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
