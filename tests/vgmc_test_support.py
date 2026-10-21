"""Self-contained VGMC test corpora for isolated acceptance worktrees."""

import copy


def simple_corpus():
    uid = "synthetic-vgmc-uid"
    canonicals = ["Amount", "Alternate Amount"]
    entries = [
        {"uid": uid, "col": 0, "original": canonicals[0], "injected": canonicals[0]},
        {"uid": uid, "col": 1, "original": canonicals[1], "injected": canonicals[1]},
    ]
    rows = [canonicals, ["123", "456"], ["789", "012"]]
    return {
        uid: {
            "uid": uid,
            "rows": rows,
            "inj_header": canonicals.copy(),
            "orig_header": canonicals.copy(),
            "canonicals": canonicals.copy(),
            "entries": copy.deepcopy(entries),
        }
    }


def overlay_base_corpus(overlay):
    """Create the 95-table base needed by split_uids without ignored runtime data."""
    overlay_uids = list(overlay["tables"])
    filler_uids = [f"synthetic-vgmc-filler-{index:02d}" for index in range(95 - len(overlay_uids))]
    corpus = {}
    for index, uid in enumerate(overlay_uids + filler_uids):
        table_spec = overlay["tables"].get(uid)
        canonicals = []
        if table_spec:
            canonicals = list(dict.fromkeys(
                column["true_canonical"] for column in table_spec["cols"]
            ))
        canonicals.append("Alternate Canonical Field")
        corpus[uid] = {
            "uid": uid,
            "rows": [
                canonicals.copy(),
                [f"row-{index}-{row_index}" for row_index in range(len(canonicals))],
            ],
            "inj_header": canonicals.copy(),
            "orig_header": canonicals.copy(),
            "canonicals": canonicals.copy(),
            "entries": [
                {"uid": uid, "col": column_index, "original": canonical, "injected": canonical}
                for column_index, canonical in enumerate(canonicals)
            ],
        }
    if len(corpus) != 95:
        raise AssertionError(f"synthetic corpus must contain 95 tables, got {len(corpus)}")
    missing = set(overlay_uids).difference(corpus)
    if missing:
        raise AssertionError(f"synthetic corpus is missing overlay tables: {sorted(missing)}")
    return corpus
