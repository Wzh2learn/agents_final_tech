from probe_trivy_fresh_cache_20261101 import vulnerability_rows


def test_compare_retains_identity_severity_and_cvss():
    first = {"PkgName": "p", "InstalledVersion": "1", "VulnerabilityID": "CVE-1",
             "Severity": "HIGH", "CVSS": {"nvd": {"V3Score": 9.0}}}
    second = {**first, "VulnerabilityID": "CVE-2"}
    a = {"Results": [{"Vulnerabilities": [first, second]}]}
    b = {"Results": [{"Vulnerabilities": [second, first]}]}
    assert vulnerability_rows(a) == vulnerability_rows(b)
    changed = {**first, "CVSS": {"nvd": {"V3Score": 8.0}}}
    c = {"Results": [{"Vulnerabilities": [changed, second]}]}
    assert vulnerability_rows(a) != vulnerability_rows(c)
