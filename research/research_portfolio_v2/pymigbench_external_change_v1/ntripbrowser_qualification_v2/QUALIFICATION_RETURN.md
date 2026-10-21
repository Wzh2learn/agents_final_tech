# NtripBrowser Behavioral Task Qualification

Date: 2026-10-21, Asia/Shanghai

Status: `QUALIFIED_BEHAVIORAL_TASK_V4`

## Result

The PyMigBench `chardet -> cchardet` migration for
`emlid/ntripbrowser` now has a deterministic behavioral oracle:

| Snapshot | Environment | Result |
|---|---|---:|
| parent `ed5f52b2...` | parent packages | 7/7 pass |
| gold `9161c194...` | gold packages | 7/7 pass |
| parent | gold packages | collection blocked by missing `chardet` |
| gold | parent packages | collection blocked by missing `cchardet` |

The seven selected tests are local or mocked. Seven live-network tests were
excluded before execution. The task is eligible for a bounded behavioral model
probe; it is not evidence of general migration ability.

## Environment Contract

- Python `3.9.25`
- `PYCURL_CURL_CONFIG=/home/testuser/miniconda3/bin/curl-config`
- `PYCURL_SSL_LIBRARY=openssl`
- `LD_LIBRARY_PATH=/home/testuser/miniconda3/lib`
- parent detector: `chardet==3.0.4`
- gold detector: `cchardet==2.1.7`
- exact transitive package locks are in `evidence/run_v4/logs/*_packages.txt`

## Preserved Failures

- Revision 1 stopped before tests because `curl-config` was missing.
- Revision 2 installed dependencies but pycurl loaded mismatched libcurl
  versions during collection.
- Revision 3 fixed library selection but exposed an SSL-backend mismatch.
- Revision 4 set the official pycurl SSL build variable and passed.

All failed environments are preserved under `evidence/`. There were no
post-failure retries within a revision and no model calls.

## Oracle Boundary

- Actor-visible: parent module and a migration request.
- Oracle-only: gold module, seven selected tests, target dependency contract.
- Behavioral score: all seven hidden tests must pass in the gold environment.
- Structural score: candidate must import/use `cchardet`, not `chardet`.
- A candidate cannot pass by matching text alone.
