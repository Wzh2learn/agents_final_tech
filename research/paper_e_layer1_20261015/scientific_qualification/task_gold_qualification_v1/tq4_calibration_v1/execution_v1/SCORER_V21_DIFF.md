# TQ-4 Scorer v2.1 Diff Record (N-1 hardening)

> Authorized by OWNER_DELEGATED_AUTHORIZATION_20261016_v1.md (S1: N-1 bool-as-int hardening allowed;
> scoring semantics / references / tolerances unchanged; frozen scorer_v2 kept, patch written as a NEW file).

- v2 sha256: `929139588790aa4f23311e0526efe89ef3a1ca49f3f12a719c260129cdd2f4ff`
- v2.1 sha256: `6068e1dcb51913de9f1ed5b228a2f73b6c9b3478a7c838d8d1d3067726e558ab`
- Change: `check_evidence_legality` rejects bool for table_row/table_col (`cell_not_integer`), since Python bool is an int subclass; ordering: non-integer check precedes bounds check.

```diff
--- scorer_v2/tq4_scoring_entry.py
+++ execution_v1/tq4_scoring_entry_v21.py
@@ -1,5 +1,5 @@
 # -*- coding: utf-8 -*-

-'''TQ-4 scoring entry v2 (fixed semantics, per adjudication 2026-10-16).

+'''TQ-4 scoring entry v2.1 (v2 semantics + N-1 hardening, authorized 2026-10-16).\nv2.1 change: check_evidence_legality requires cell coordinates to be true ints (bool rejected,\n'cell_not_integer'); scoring semantics, references and tolerances are unchanged from v2.



 Fixes vs tq3_scoring_entry v1:

 - percent conversion is driven ONLY by explicit unit markers; numeric magnitude

@@ -92,7 +92,9 @@
         if kind == 'cell':

             r0 = e.get('table_row')

             c0 = e.get('table_col')

-            if not isinstance(r0, int) or not isinstance(c0, int) or r0 < 0 or c0 < 0 or r0 >= len(table) or c0 >= len(table[r0]):

+            if type(r0) is not int or type(c0) is not int:

+                issues.append({'index': i, 'issue': 'cell_not_integer', 'table_row': r0, 'table_col': c0})

+            elif r0 < 0 or c0 < 0 or r0 >= len(table) or c0 >= len(table[r0]):

                 issues.append({'index': i, 'issue': 'cell_out_of_bounds', 'table_row': r0, 'table_col': c0})

         elif kind == 'paragraph':

             uid = e.get('paragraph_uid')

```
