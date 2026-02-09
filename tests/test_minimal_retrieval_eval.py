from __future__ import annotations

import math
import re


DOCS = [
    ("doc_policy_2024", "Policy 2024 installment rule: interest accrues daily after 90 days."),
    ("doc_policy_2023", "Policy 2023 installment rule: interest accrues weekly after 60 days."),
    ("doc_fraud_checklist", "Fraud risk review checklist includes identity verification, income proof, credit score threshold 680."),
    ("doc_support_escalation", "Support escalation steps: tier1 triage, tier2 investigation, compliance review."),
]

QUERIES = [
    ("q_policy_2024", "What does the 2024 installment policy say about interest accrual", {"doc_policy_2024"}),
    ("q_policy_2023", "installment policy 2023 interest schedule", {"doc_policy_2023"}),
    ("q_fraud_threshold", "credit score threshold for fraud risk review", {"doc_fraud_checklist"}),
    ("q_escalation", "support escalation steps tier2 compliance review", {"doc_support_escalation"}),
]


def tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if t]


def build_corpus():
    corpus_tokens = []
    for doc_id, text in DOCS:
        tokens = tokenize(text)
        corpus_tokens.append((doc_id, tokens))
    return corpus_tokens


def bm25_rank(query: str, corpus_tokens: list[tuple[str, list[str]]], k1: float = 1.2, b: float = 0.75):
    query_tokens = tokenize(query)
    if not query_tokens:
        return [doc_id for doc_id, _ in corpus_tokens]

    doc_lengths = [len(tokens) for _, tokens in corpus_tokens]
    avgdl = sum(doc_lengths) / max(len(doc_lengths), 1)

    df = {}
    for _, tokens in corpus_tokens:
        seen = set(tokens)
        for t in seen:
            df[t] = df.get(t, 0) + 1

    scores = []
    for doc_id, tokens in corpus_tokens:
        tf = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        score = 0.0
        for t in query_tokens:
            if t not in df:
                continue
            idf = math.log(1 + (len(corpus_tokens) - df[t] + 0.5) / (df[t] + 0.5))
            freq = tf.get(t, 0)
            if freq == 0:
                continue
            denom = freq + k1 * (1 - b + b * (len(tokens) / (avgdl or 1.0)))
            score += idf * (freq * (k1 + 1)) / denom
        scores.append((doc_id, score))

    scores.sort(key=lambda x: (-x[1], x[0]))
    return [doc_id for doc_id, _ in scores]


def recall_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 1.0
    return 1.0 if set(ranked[:k]) & relevant else 0.0


def mrr_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    for idx, doc_id in enumerate(ranked[:k], start=1):
        if doc_id in relevant:
            return 1.0 / idx
    return 0.0


def test_minimal_retrieval_eval():
    corpus_tokens = build_corpus()
    k = 3
    recalls = []
    mrrs = []

    for _, query, relevant in QUERIES:
        ranked = bm25_rank(query, corpus_tokens)
        recalls.append(recall_at_k(ranked, relevant, k))
        mrrs.append(mrr_at_k(ranked, relevant, k))

    avg_recall = sum(recalls) / len(recalls)
    avg_mrr = sum(mrrs) / len(mrrs)

    assert avg_recall >= 0.9, f"Recall@{k} too low: {avg_recall:.3f}"
    assert avg_mrr >= 0.8, f"MRR@{k} too low: {avg_mrr:.3f}"
