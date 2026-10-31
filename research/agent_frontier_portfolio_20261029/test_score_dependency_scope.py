import csv

from research.agent_frontier_portfolio_20261029.score_dependency_scope_20261031 import HEADERS, evaluate


def test_distinct_cves_for_same_package_are_not_collapsed(tmp_path):
    report = {"Results": [{"Vulnerabilities": [
        {"PkgName": "p", "InstalledVersion": "1", "VulnerabilityID": "CVE-1", "Severity": "HIGH"},
        {"PkgName": "p", "InstalledVersion": "1", "VulnerabilityID": "CVE-2", "Severity": "HIGH"},
    ]}]}
    path = tmp_path / "out.csv"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerow({"Package": "p", "Version": "1", "CVE_ID": "CVE-2", "Severity": "HIGH"})
    result = evaluate(path, report, "high")
    assert result["expected_records"] == 2
    assert result["missing"] == [["p", "1", "CVE-1", "HIGH"]]
    assert not result["exact_identity_and_scope"]


def test_cvss_threshold_uses_strict_numeric_boundary(tmp_path):
    report = {"Results": [{"Vulnerabilities": [
        {"PkgName": "p", "InstalledVersion": "1", "VulnerabilityID": "CVE-1", "Severity": "LOW",
         "CVSS": {"nvd": {"V3Score": 9.8}}},
    ]}]}
    path = tmp_path / "out.csv"
    for value, accepted in (("9.8", True), ("8.0", False), ("inf", False)):
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=HEADERS)
            writer.writeheader()
            writer.writerow({"Package": "p", "Version": "1", "CVE_ID": "CVE-1",
                             "Severity": "LOW", "CVSS_Score": value})
        assert evaluate(path, report, "cvss_gt_8")["exact_identity_and_scope"] is accepted
