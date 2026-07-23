from __future__ import annotations

import json
import zipfile

from scripts.run_tat_dqa_m2_upper_bound import (
    answer_exact_match,
    load_upper_bound_data,
)


def test_answer_exact_match_normalizes_financial_values():
    assert answer_exact_match("$1,250.00", "1250.00")
    assert answer_exact_match(["B", "A"], ["a", "b"])
    assert not answer_exact_match("14.2", "14.3")


def test_loader_keeps_only_manifest_ids_and_parsed_blocks(tmp_path):
    document_ids = [f"doc-{index:02d}" for index in range(20)]
    question_ids = [f"q-{index:03d}" for index in range(100)]
    manifest = {
        "documents": [
            {
                "document_id": document_id,
                "source_split": "dev",
                "split": "validation",
            }
            for document_id in document_ids
        ],
        "questions": [
            {
                "question_id": question_id,
                "source_split": "dev",
                "split": "validation",
            }
            for question_id in question_ids
        ],
    }
    qa = []
    archive_path = tmp_path / "docs.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        for doc_index, document_id in enumerate(document_ids):
            questions = []
            for offset in range(5):
                question_id = question_ids[doc_index * 5 + offset]
                questions.append(
                    {
                        "uid": question_id,
                        "question": "private question",
                        "answer": "private answer",
                        "answer_type": "span",
                        "scale": "",
                        "block_mapping": [{"block-1": [0, 1]}],
                    }
                )
            qa.append(
                {
                    "doc": {"uid": document_id, "source": f"{document_id}.pdf"},
                    "questions": questions,
                }
            )
            archive.writestr(
                f"dev/{document_id}.json",
                json.dumps(
                    {
                        "pages": [
                            {
                                "blocks": [
                                    {
                                        "uuid": "block-1",
                                        "text": "private block",
                                        "bbox": [0, 0, 1, 1],
                                        "order": 1,
                                    }
                                ]
                            }
                        ]
                    }
                ),
            )

    manifest_path = tmp_path / "manifest.json"
    qa_path = tmp_path / "qa.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    qa_path.write_text(json.dumps(qa), encoding="utf-8")
    documents, cases = load_upper_bound_data(
        manifest_path,
        qa_path,
        archive_path,
        "validation",
    )
    assert len(documents) == 20
    assert len(cases) == 100
    assert documents[0]["blocks"][0]["block_id"] == "block-1"
    assert cases[0]["expected_block_ids"] == ["block-1"]
