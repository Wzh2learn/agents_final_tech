# PyMigBench External Change Curation Report

- PyMigBench commit: `d8ffb982d23e1bda2a844bd4a6f7b451e192bd5b`
- Retained tasks: `0`
- Candidate attempts: `36`
- Model calls: `0`
- Failed-environment retries: `0`
- Observed fail-to-pass labels: `0`
- Observed pass-to-pass labels: `0`

## Batches

| Batch | Attempted | Retained | Status | Finding |
|---|---:|---:|---|---|
| `batch_01` | 12 | 0 | `SUPERSEDED_HARNESS_TEST_SELECTION_DEFECT` | Non-Python fixtures under tests/ were passed to pytest; the failed environments were not retried. |
| `batch_02` | 12 | 0 | `SUPERSEDED_MISSING_PYTEST` | GB10 /usr/bin/python3 lacked pytest, so no candidate reached collection; these environments were not retried. |
| `batch_03` | 12 | 0 | `COMPLETE` | Fresh records only; prior record paths and pairs excluded. |

## Retained Tasks

| Task | Repo | Source -> target | Parent | Gold | F2P | P2P |
|---|---|---|---|---|---:|---:|

## Rejected Candidates

| Repo | Commit | Status | Reason |
|---|---|---|---|
| `sk-415/harukabot` | `0611d16a4cdc` | `REJECTED` | `FETCH_FAILED` |
| `openstack/ironic` | `cbf214b5130e` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `rapid-design-of-systems-laboratory/beluga` | `078e3e56fe5b` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `romanz/trezor-agent` | `e1bbdb4bccb9` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `princetonuniversity/psyneulink` | `5253a55c46d5` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `testdrivenio/flask-react-aws` | `d4119a0f609b` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `openshot/openshot-qt` | `4349753e0eec` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `hxlstandard/libhxl-python` | `0babff28e04c` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `obsidianforensics/hindsight` | `973b3d327860` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `paratoolsinc/taucmdr` | `2a2c28aeee46` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `camptocamp/c2cgeoportal` | `14388c3d85ab` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `milvus-io/bootcamp` | `e5073e4c0c3e` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `celery/celery` | `9b39fc41998c` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `haoxizhong/pytorch-worker` | `fa8de771a86d` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `oddluck/limnoria-plugins` | `33c7a3fc0878` | `REJECTED` | `FETCH_FAILED` |
| `city-of-helsinki/respa` | `4fecb9770836` | `REJECTED` | `NO_DISCOVERED_TESTS` |
| `openstack/aodh` | `7587ab9bf362` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `slackapi/python-slack-sdk` | `5f4d92a80488` | `REJECTED` | `NO_DISCOVERED_TESTS` |
| `pimoroni/inky` | `cba36514eb8c` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `whynothugo/django-afip` | `827dd9f05a0a` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `nlesc/xtas` | `0dbf3884e1a6` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `adithyabsk/keep2roam` | `d340eea2fded` | `REJECTED` | `NO_DISCOVERED_TESTS` |
| `ceph/teuthology` | `fb3210538573` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `augerai/a2ml` | `13ea499e413b` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `twiliodeved/sms2fa-flask` | `22eedfcd1ef7` | `REJECTED` | `NO_DISCOVERED_TESTS` |
| `cfpb/cfgov-refresh` | `326261015566` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `whoopinc/mkwheelhouse` | `54806ffc8edd` | `REJECTED` | `NO_DISCOVERED_TESTS` |
| `cqmoe/python-cqhttp` | `f9f083ec6b1d` | `REJECTED` | `NO_DISCOVERED_TESTS` |
| `emlid/ntripbrowser` | `9161c1943a86` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `kittenparry/meituri-downloader` | `422d73beace3` | `REJECTED` | `FETCH_FAILED` |
| `danielyule/hearthbreaker` | `d018edff306b` | `REJECTED` | `NO_DISCOVERED_TESTS` |
| `ctlearn-project/ctlearn` | `2375af87fa36` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `ckan/ckanext-datapackager` | `a6a3fb3aaa48` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `thombashi/datetimerange` | `936761f779c4` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `bcgov/theorgbook` | `728f86e941df` | `REJECTED` | `GOLD_NOT_REPRODUCIBLE_OR_NO_BEHAVIORAL_LABEL` |
| `aio-libs/aioftp` | `ba6ef08fb7eb` | `REJECTED` | `NO_DISCOVERED_TESTS` |

## Conditions

- `BASE`: actor-visible pre-migration context only.
- `PROSE_CHANGE_FACTS`: the shared non-answer facts rendered as prose.
- `STRUCTURED_CHANGE_FACTS`: the same facts as structured fields.
- Target APIs, target line maps, gold diffs, and tests are oracle-only.

## Execution Boundary

Each retained task was fetched at the exact gold commit and parent, and its discovered pytest command ran once at each revision. Only actual JUnit outcomes produced fail-to-pass/pass-to-pass labels. No model call, judge, training run, or retry of a failed environment was used.
