import csv

from research.agent_frontier_portfolio_20261029.audit_dependency_cvss_sources_20261031 import check


def test_score_checked_against_corresponding_cve_not_other_package_row(tmp_path):
    report = {"Results": [{"Vulnerabilities": [
        {"PkgName": "p", "InstalledVersion": "1", "VulnerabilityID": "CVE-1", "Severity": "HIGH",
         "CVSS": {"nvd": {"V3Score": 8.1}, "redhat": {"V3Score": 9.8}}},
        {"PkgName": "p", "InstalledVersion": "1", "VulnerabilityID": "CVE-2", "Severity": "HIGH",
         "CVSS": {"nvd": {"V3Score": 8.2}}},
    ]}]}
    path = tmp_path / "out.csv"
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["Package", "Version", "CVE_ID", "Severity", "CVSS_Score"])
        writer.writeheader()
        writer.writerow({"Package": "p", "Version": "1", "CVE_ID": "CVE-1", "Severity": "HIGH", "CVSS_Score": "9.8"})
        writer.writerow({"Package": "p", "Version": "1", "CVE_ID": "CVE-2", "Severity": "HIGH", "CVSS_Score": "9.8"})
    rows = check(path, report)["rows"]
    assert rows[0]["matching_sources"] == ["redhat"]
    assert rows[1]["status"] == "NO_MATCH"
