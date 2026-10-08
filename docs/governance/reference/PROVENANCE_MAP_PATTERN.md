# Provenance Map

**Read this if** you have produced something substantial — a paper, a design, a system — and
six weeks later cannot reconstruct *why* a particular decision in it is the way it is.

A reading index answers "what did I read?" A provenance map answers the reverse and much harder
question: **"this claim in my output — what is it standing on?"** You need both, and only one of
them is usually written.

## The four-level chain

For each design decision or claim in the output, record the full chain:

```
claim in the output  →  your own notes on the source  →  the primary source  →  the code that implements it
   (§ and line)          (which section, which figure)     (paper / spec / data)     (file:function)
```

Any link you cannot fill is a real signal, not a formatting gap:

| Missing link | What it means |
|---|---|
| No notes | You absorbed it secondhand. The claim rests on someone's summary |
| No primary source | It is your own invention — fine, but label it as such rather than letting it inherit borrowed authority |
| No code | It is unimplemented. Either it is future work or the output overstates what exists |
| No claim (source with nothing pointing at it) | You read it and it changed nothing. Worth knowing before you cite it as an influence |

That table is the payoff. The map's value is less in the links that exist than in the ones that
turn out not to.

## Structure that survives contact with revision

1. **The core story in one paragraph** — the through-line. If the map does not open with it,
   readers reconstruct it from the table and get it wrong.
2. **The decision table** — one row per design decision: what it is, the mechanism, what changed
   in the last revision, and what is actually novel about it. The "what changed" column is what
   makes the map maintainable rather than a one-time artifact.
3. **The code cross-reference** — decision → implementing file and function.
4. **Open risks** — the claims you know are thin, listed before a reviewer finds them.

Head the document with a version, a last-updated date, a status, and **the exact revision of the
output it describes**. A provenance map pointing at a stale draft is worse than none: it will be
trusted and it will be wrong.

## Use it as a reading route, not an archive

The map's daily use is navigation: read the core story, then follow the decision table into your
notes, then into the code, then check the risk list. That is a route through your own material
that takes minutes instead of an afternoon of grep.

It is also the natural artifact to hand a reviewer, a new collaborator, or an agent picking up
the work — it is the only document that connects the output to its evidence in both directions.

## Cost, honestly

Maintaining this is real overhead, and it only pays off on work that (a) lives longer than your
memory of it and (b) will be defended to someone. For a two-week project, skip it. For anything
you will be asked to justify — a submission, a design that others will build on, a system whose
decisions need auditing — the map is cheaper than reconstructing the reasoning later, and much
cheaper than defending a claim whose basis you have forgotten.

## Related

- `templates/READING_NOTES_INDEX.md` — the forward direction (source → what it feeds)
- `templates/DESIGN_DOCUMENT.md` / `templates/ADR.md` — where individual decisions get recorded
- `SUPERSEDE_CHAIN.md` — how to keep the map honest when decisions get replaced
- `PAPER_WRITING_PIPELINE.md` — the workflow this indexes
