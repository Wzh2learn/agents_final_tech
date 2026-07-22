from __future__ import annotations

from scripts.prepare_tat_dqa_joint_v1 import (
    MAX_QUESTIONS,
    SEED,
    SPLIT_SIZES,
    TARGET_ANSWER_TYPES,
    build_manifest,
    validate_manifest,
)
from scripts.tat_dqa_data import PACKAGE_FILES, expected_package_bytes, package_plan


def fixture_payload(document_count: int = 120) -> list[dict]:
    return [
        {
            "doc_id": f"doc-{index:03d}",
            "questions": [
                {
                    "uid": f"q-{index:03d}-{answer_type}",
                    "answer_type": answer_type,
                    "page_number": 1,
                    "gold_inds": {f"block-{index:03d}-{answer_type}": "public fixture text"},
                }
                for answer_type in TARGET_ANSWER_TYPES
            ],
        }
        for index in range(document_count)
    ]


def test_package_plan_has_all_official_files_and_expected_size(tmp_path):
    plan = package_plan(tmp_path / "tat-dqa")
    assert len(PACKAGE_FILES) == 7
    assert plan["expected_archive_bytes"] == expected_package_bytes() == 1_514_773_595
    assert plan["license"] == "CC BY 4.0"


def test_joint_v1_is_reproducible_balanced_and_has_no_document_leakage():
    first_manifest, first_checks = build_manifest([fixture_payload()], SEED)
    second_manifest, second_checks = build_manifest([fixture_payload()], SEED)
    assert first_manifest == second_manifest
    assert first_checks == second_checks
    assert first_checks["documents_by_split"] == SPLIT_SIZES
    assert first_checks["question_count"] == MAX_QUESTIONS
    assert set(first_checks["questions_by_answer_type"]) >= set(TARGET_ANSWER_TYPES)
    assert first_checks["document_leakage"] is False
    validate_manifest(first_manifest)


def test_sampler_reserves_documents_for_rarest_answer_types():
    payload = fixture_payload()
    for document in payload[:100]:
        document["questions"] = [question for question in document["questions"] if question["answer_type"] != "counting"]
    manifest, checks = build_manifest([payload], SEED)
    assert checks["questions_by_answer_type"]["counting"] == 20
    assert len(manifest["documents"]) == 100


def test_document_split_assignment_keeps_each_document_in_one_split():
    manifest, _ = build_manifest([fixture_payload()], SEED)
    document_splits = {item["document_id"]: item["split"] for item in manifest["documents"]}
    question_splits = {(item["document_id"], item["split"]) for item in manifest["questions"]}
    assert all(document_splits[document_id] == split for document_id, split in question_splits)


def test_normalizes_official_nested_doc_shape_without_text():
    payload = [
        {
            "doc": {"uid": "official-doc", "page": 2, "source": "not-retained.pdf"},
            "questions": [
                {
                    "uid": "official-question",
                    "answer_type": "span",
                    "block_mapping": [{"public-block": [1, 2]}],
                    "question": "not-retained",
                    "answer": "not-retained",
                }
            ],
        }
    ]
    from scripts.prepare_tat_dqa_joint_v1 import normalize_documents

    document = normalize_documents([payload])[0]
    assert document["document_id"] == "official-doc"
    assert document["questions"][0] == {
        "question_id": "official-question",
        "answer_type": "span",
        "page_no": 2,
        "source_block_ids": ["public-block"],
    }


def test_official_answer_type_aliases_match_joint_v1_coverage_vocabulary():
    from scripts.prepare_tat_dqa_joint_v1 import canonical_answer_type

    assert canonical_answer_type({"answer_type": "multi-span"}) == "spans"
    assert canonical_answer_type({"answer_type": "count"}) == "counting"
    assert canonical_answer_type({"answer_type": "arithmetic", "req_comparison": True}) == "comparison"
