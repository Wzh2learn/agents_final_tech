# PyMigBench External Change V1

This bounded curation package uses the pinned PyMigBench commit
`d8ffb982d23e1bda2a844bd4a6f7b451e192bd5b` and public repository commits.
It fetches each exact gold commit and parent into the GB10 protected cache,
discovers a repository-local pytest command, and runs that command once at
each revision. Only actual JUnit outcomes create fail-to-pass and
pass-to-pass labels.

`TASKS.json` separates actor-visible parent context and equal-information
change facts from oracle-only target APIs, line maps, gold diffs, and tests.
The three future probe conditions are `BASE`, `PROSE_CHANGE_FACTS`, and
`STRUCTURED_CHANGE_FACTS`; the latter two contain the same non-answer facts.

`patch_protocol.py` validates repository-relative unified diffs, rejects
binary/creation/deletion/rename patches, and applies patches with `git apply`.
`test_curation.py` covers safe YAML loading and patch/fact boundaries.
