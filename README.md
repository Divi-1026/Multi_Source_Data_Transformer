# Multi-Source Candidate Data Transformer

Turns messy candidate data from several sources into **one clean, canonical
profile per person** — normalized formats, deduplicated, with a record of where
every value came from (`provenance`) and how confident we are (`confidence`).

Built for the Eightfold Engineering Intern assignment. Pure Python standard
library — **no external dependencies, no network needed**.

## Sources handled

| Source | Group | Notes |
|---|---|---|
| Recruiter CSV (`samples/recruiter.csv`) | structured | name, email, phone, company, title, location, skills |
| ATS JSON (`samples/ats.json`) | structured | uses its own field names → remapped to canonical |
| Recruiter notes (`samples/notes.txt`) | unstructured | free text → regex / keyword extraction |

(Assignment needs ≥1 structured + ≥1 unstructured; this ships all three so the
merge + conflict resolution is actually visible.)

## How to run

Requires Python 3.8+. No install step.

```bash
# Default canonical schema, all three sources
python cli.py --csv samples/recruiter.csv --ats samples/ats.json --notes samples/notes.txt

# Custom output via a runtime config (the "twist")
python cli.py --csv samples/recruiter.csv --ats samples/ats.json --notes samples/notes.txt \
              --config configs/compact.json

# Write to a file instead of stdout
python cli.py --csv samples/recruiter.csv --out out.json
```

Any subset of `--csv / --ats / --notes` works. A missing or malformed source
prints a `[warn]` and is skipped — the run never crashes.

## Run the tests

```bash
python tests/test_pipeline.py        # or:  python -m pytest -q
```

## Produced output (committed)

- `samples/output_default.json` — full canonical profiles
- `samples/output_compact.json` — projected via `configs/compact.json`

## Design in one breath

```
parse → normalize → merge (+ provenance + confidence) → project (config) → validate
```

- **Canonical record vs projection are kept separate.** We always build the full
  internal record first; the config is applied as a *view* on top. One engine,
  many output shapes, no code changes.
- **Conflict resolution.** Sources are ranked by reliability
  (`ats_json` > `recruiter_csv` > `recruiter_notes`). For single-value fields the
  highest-reliability non-empty value wins; agreement between sources raises
  confidence. List fields (emails, phones, skills) are unioned and deduped.
- **Confidence.** Per field = winning source's reliability, bumped when sources
  agree. `overall_confidence` is the mean of resolved-field confidences.
- **Never invent.** Unknown / unparseable values become `null`, never a guess —
  honestly-empty beats wrong-but-confident.

## Config (the twist)

A runtime config reshapes the output without touching code. It can select a
subset of fields, rename/remap from a canonical path (`from`), normalize per
field, toggle confidence/provenance, and choose missing-value behaviour
(`null` / `omit` / `error`). Path syntax supports `emails[0]`, `location.city`,
`skills[].name`. See `configs/compact.json`.

## Assumptions & descoped

- Identity match key = primary email, falling back to lowercased name. (Real
  systems would add fuzzy name matching / phone matching.)
- Phone normalization is India-centric (`+91` default for 10-digit numbers).
- Resume (PDF/DOCX) and LinkedIn/GitHub live-API sources were **descoped** under
  time pressure; the parser layer is pluggable, so adding one is a new file in
  `transformer/parsers.py` plus a line in `pipeline._PARSERS`.
- `education` is in the schema but not populated by the current sample sources.

## Layout

```
transformer/
  schema.py      canonical shape + empty record
  normalize.py   phone (E.164), date (YYYY-MM), country (ISO-2), skill (canonical)
  parsers.py     csv / ats-json / notes parsers -> raw SourceRecords
  merge.py       normalize + group-by-identity + merge + confidence + provenance
  project.py     config-driven projection + path resolver
  validate.py    light type/shape checks for canonical + projected output
  pipeline.py    orchestrates the stages
cli.py           command-line surface
configs/         example custom-output config
samples/         sample inputs + produced outputs
tests/           pytest-style tests incl. a garbage-source edge case
```
