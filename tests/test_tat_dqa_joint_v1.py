from __future__ import annotations

from scripts.prepare_tat_dqa_joint_v1 import (
    MAX_QUESTIONS,
    SEED,
    SPLIT_SIZES,
    SOURCE_TO_SPLIT,
    TARGET_ANSWER_TYPES,
    build_manifest,
    validate_manifest,
)
from scripts.tat_dqa_data import (
    PackageFile,
    PACKAGE_FILES,
    download_package,
    expected_package_bytes,
    package_plan,
)


def fixture_payload(prefix: str, document_count: int) -> list[dict]:
    return [
        {
            "doc_id": f"{prefix}-doc-{index:03d}",
            "questions": [
                {
                    "uid": f"{prefix}-q-{index:03d}-{answer_type}",
                    "answer_type": answer_type,
                    "page_number": 1,
                    "gold_inds": {f"{prefix}-block-{index:03d}-{answer_type}": "public fixture text"},
                }
                for answer_type in TARGET_ANSWER_TYPES
            ],
        }
        for index in range(document_count)
    ]


def fixture_splits() -> dict[str, list[list[dict]]]:
    return {
        "train": [fixture_payload("train", 80)],
        "dev": [fixture_payload("dev", 30)],
        "test_gold": [fixture_payload("test", 30)],
    }


def test_package_plan_has_all_official_files_and_expected_size(tmp_path):
    plan = package_plan(tmp_path / "tat-dqa")
    assert len(PACKAGE_FILES) == 7
    assert plan["expected_archive_bytes"] == expected_package_bytes() == 1_514_773_595
    assert plan["license"] == "CC BY 4.0"


def test_joint_v1_is_reproducible_balanced_and_has_no_document_leakage():
    first_manifest, first_checks = build_manifest(fixture_splits(), SEED)
    second_manifest, second_checks = build_manifest(fixture_splits(), SEED)
    assert first_manifest == second_manifest
    assert first_checks == second_checks
    assert first_checks["documents_by_split"] == SPLIT_SIZES
    assert first_checks["question_count"] == MAX_QUESTIONS
    assert set(first_checks["questions_by_answer_type"]) >= set(TARGET_ANSWER_TYPES)
    assert first_checks["document_leakage"] is False
    assert first_checks["official_split_leakage"] is False
    assert first_checks["documents_by_source_split"] == {"dev": 20, "test_gold": 20, "train": 60}
    validate_manifest(first_manifest)


def test_sampler_reserves_documents_for_rarest_answer_types():
    payloads = fixture_splits()
    for document in payloads["train"][0][:60]:
        document["questions"] = [question for question in document["questions"] if question["answer_type"] != "counting"]
    manifest, checks = build_manifest(payloads, SEED)
    assert checks["questions_by_answer_type"]["counting"] > 0
    assert len(manifest["documents"]) == 100


def test_document_split_assignment_keeps_each_document_in_one_split():
    manifest, _ = build_manifest(fixture_splits(), SEED)
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

    document = normalize_documents([payload], "train")[0]
    assert document["document_id"] == "official-doc"
    assert document["source_split"] == "train"
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


def test_official_source_splits_never_cross_training_boundaries():
    manifest, _ = build_manifest(fixture_splits(), SEED)
    for document in manifest["documents"]:
        assert document["split"] == SOURCE_TO_SPLIT[document["source_split"]]
        if document["source_split"] in {"dev", "test_gold"}:
            assert document["split"] != "train"


def test_split_mapping_order_does_not_change_manifest():
    payloads = fixture_splits()
    reversed_payloads = dict(reversed(list(payloads.items())))
    assert build_manifest(payloads, SEED) == build_manifest(reversed_payloads, SEED)


def test_manifest_excludes_question_answer_and_evidence_text():
    manifest, _ = build_manifest(fixture_splits(), SEED)
    forbidden_keys = {"question", "question_text", "answer", "evidence", "evidence_text"}

    def walk(value):
        if isinstance(value, dict):
            assert forbidden_keys.isdisjoint(value)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
        elif isinstance(value, str):
            assert value != "public fixture text"

    walk(manifest)


def test_downloader_resumes_a_partial_file(monkeypatch, tmp_path):
    import scripts.tat_dqa_data as data_module

    item = PackageFile("sample.zip", "drive-id", 6)
    partial = tmp_path / "raw" / "sample.zip.part"
    partial.parent.mkdir()
    partial.write_bytes(b"abc")

    class FakeResponse:
        status_code = 206
        headers = {
            "Content-Type": "application/zip",
            "Content-Range": "bytes 3-5/6",
        }

        def raise_for_status(self):
            return None

        def iter_content(self, chunk_size):
            yield b"def"

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def get(self, url, **kwargs):
            assert kwargs["headers"] == {"Range": "bytes=3-"}
            return FakeResponse()

    monkeypatch.setattr(data_module, "PACKAGE_FILES", (item,))
    monkeypatch.setattr(data_module.requests, "Session", FakeSession)
    result = download_package(tmp_path)
    assert (tmp_path / "raw" / "sample.zip").read_bytes() == b"abcdef"
    assert result["downloads"][0]["status"] == "resumed"
