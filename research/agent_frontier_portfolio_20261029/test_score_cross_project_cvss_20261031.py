import csv
import json

from score_cross_project_cvss_20261031 import FIELDS, evaluate, metadata_audit, reference


def record(cve, nvd=None, ghsa=None):
    scores = {}
    if nvd is not None:
        scores["nvd"] = {"V3Score": nvd}
    if ghsa is not None:
        scores["ghsa"] = {"V3Score": ghsa}
    return {"PkgName": "demo", "InstalledVersion": "1", "VulnerabilityID": cve,
            "Severity": "HIGH", "CVSS": scores}


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def test_priority_and_strict_threshold(tmp_path):
    report = {"Results": [{"Vulnerabilities": [record("CVE-1", 6.5, 9.8),
                                                  record("CVE-2", 8.0),
                                                  record("CVE-3", None, 8.1)]}]}
    assert list(reference(report)) == [("demo", "1", "CVE-3", "HIGH")]
    output = tmp_path / "security_audit.csv"
    base = dict(zip(FIELDS, ("demo", "1", "CVE-3", "HIGH", "8.1", "N/A", "t", "u")))
    write_csv(output, [base])
    assert evaluate(output, report)["identity_and_score_exact"]
    base["CVSS_Score"] = "9.8"
    write_csv(output, [base])
    assert not evaluate(output, report)["identity_and_score_exact"]
    write_csv(output, [base, base])
    assert not evaluate(output, report)["identity_exact"]


def test_empty_result_and_missing_output(tmp_path):
    report = {"Results": [{"Vulnerabilities": [record("CVE-1", 7.0)]}]}
    output = tmp_path / "security_audit.csv"
    assert evaluate(output, report)["status"] == "MISSING_OUTPUT"
    write_csv(output, [])
    assert evaluate(output, report)["identity_and_score_exact"]


def test_metadata_difference_is_reported(tmp_path):
    original = {"Version": 2, "UpdatedAt": "2026", "DownloadedAt": "2026", "NextUpdate": "2026"}
    path = tmp_path / "cache" / "metadata.json"
    path.parent.mkdir()
    path.write_text(json.dumps({**original, "NextUpdate": "2099"}), encoding="utf-8")
    result = metadata_audit(tmp_path, original)
    assert result["changed_copies"] == 1


def test_unreadable_database_metadata_is_not_treated_as_unchanged(tmp_path):
    path = tmp_path / "trivy-cache" / "db" / "metadata.json"
    path.parent.mkdir(parents=True)
    path.write_text("{invalid", encoding="utf-8")
    result = metadata_audit(tmp_path, {})
    assert result["original_location_present"]
    assert result["changed_copies"] == 0
    assert result["unresolved_copies"] == 1
