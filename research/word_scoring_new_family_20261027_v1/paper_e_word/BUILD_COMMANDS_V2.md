# Paper E revision — reproducible build commands

Date: 2026-10-28, Asia/Shanghai. Every command below was actually executed for
the frozen render recorded in `CONVERSION_MANIFEST_V2.json`.

The production source is `paper_e_revision_v2.md`. Nothing is edited by hand in
the DOCX or the PDF; both are derived.

## 0. Prerequisites (already verified in this environment)

| Tool | Version / location | Note |
|---|---|---|
| Pandoc | 3.2.1, `D:/pandocLatex2word/pandoc.exe` | local, no TeX engine needed |
| python-docx | isolated venv at `D:/aircommend_tmp/venv` | outside the repository, no system change |
| LibreOffice | 24.2.7.2, `/usr/bin/soffice` on GB10 | headless, fresh `UserInstallation` per render |
| pdftoppm / pdfinfo | `/usr/bin/…` on GB10 | PNG at 120 DPI |

## 1. Rebuild the production source from the frozen extraction

```bash
cd research/word_scoring_new_family_20261027_v1/paper_e_word
python build_revision_v2.py
```

Reads the raw blob of `paper_e_word.md` and of the canonical TeX
`research/adaptive_mechanism_20261027_v1/paper_e_formal_build/paper_e_sncs.tex`
directly from Git (immune to `core.autocrlf`), asserts both SHA-256 values,
applies every documented transformation with an occurrence assertion, and
writes `paper_e_revision_v2.md` plus `REVISION_V2_BUILD_LOG.json`.

Idempotence check — must print `CHECK OK`:

```bash
python build_revision_v2.py --check
```

## 2. Deterministic document lint

```bash
python verify_revision_v2.py --json-out ../validation/REVISION_V2_LINT.json
```

Exit code 0 and `"verdict": "PASS"` are required. The lint covers blank-line
structure around headings/lists/tables/images, caption numbering and resolution,
in-text table/figure/section cross-references, citation ordering and coverage,
LaTeX residue, placeholder count, and 28 arithmetic identities.

## 3. DOCX

```bash
D:/pandocLatex2word/pandoc.exe paper_e_revision_v2.md \
  --from=markdown+pipe_tables+tex_math_dollars \
  --resource-path=. \
  --reference-doc=reference_style.docx \
  --output=paper_e_revision_v2.docx

D:/aircommend_tmp/venv/Scripts/python.exe polish_docx_v2.py --docx paper_e_revision_v2.docx
```

`polish_docx_v2.py` applies the table grid/borders/widths/margins, marks the
header row to repeat and rows non-splittable, converts every `Table N.` /
`Figure N.` paragraph to the `Caption` style with a bold label and regular
body text, tightens the reference list to single spacing, and removes dangling
paragraph-style references that `reference_style.docx` does not define
(`Compact`, `FirstParagraph`, `CaptionedFigure`, `ImageCaption`,
`TableCaption`). Removing those is required: LibreOffice 24.2 discards the
whole paragraph-properties block when the referenced style is undefined, which
silently deleted the list numbering and the bullet glyphs.

## 4. PDF and page images (GB10)

```bash
scp paper_e_revision_v2.docx <ssh-user>@<gb10>:wzh/paper_e_rev_v2/
ssh <ssh-user>@<gb10>
cd ~/wzh/paper_e_rev_v2
rm -rf rendered_final && mkdir -p rendered_final
/usr/bin/soffice --headless \
  -env:UserInstallation=file:///tmp/lo_profile_paper_e_rev_v2 \
  --convert-to pdf --outdir rendered_final paper_e_revision_v2.docx
/usr/bin/pdftoppm -png -r 120 rendered_final/paper_e_revision_v2.pdf rendered_final/page
/usr/bin/pdfinfo rendered_final/paper_e_revision_v2.pdf
```

Expected: `Producer: LibreOffice 24.2`, `Creator: Writer`, `Pages: 14`.

## 5. Page hashes

```bash
cd rendered_v2
sha256sum page-*.png paper_e_revision_v2.pdf > ../D_PAGE_HASHES_V2.sha256
```

## 6. Integrity check of everything at once

```bash
python - <<'PY'
import hashlib, json, pathlib
m = json.loads(pathlib.Path('CONVERSION_MANIFEST_V2.json').read_text(encoding='utf-8'))
for rel, rec in list(m['outputs'].items()):
    if isinstance(rec, dict) and 'sha256' in rec:
        p = pathlib.Path(rel)
        if not p.exists():
            p = pathlib.Path('rendered_v2', rel)
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        print(rel, 'OK' if got == rec['sha256'] else 'MISMATCH')
PY
```
