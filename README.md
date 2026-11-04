# AI Company Pageviews Anomaly Pipeline

Ingests hourly Wikimedia pageview dumps for ~15–25 AI company articles on
English Wikipedia, establishes each article's own rolling baseline, and flags
statistically unusual traffic (default: |z| > 3 against a 30-day trailing window).

See `docs/problem_statement.md` for the scope and questions this answers,
and `docs/decisions.md` for choices made while building.

## Status

| Phase | Scope | State |
|---|---|---|
| 1 | Seed file, dump parser, URL builder, z-score baseline, unit tests | Done (local, 15 tests pass) |
| 2 | Airflow DAG: hourly ingest + sensor + backfill + retries | Not started |
| 3 | Databricks bronze/silver (Delta, Unity Catalog) | Not started |
| 4 | dbt gold: rolling state, z-score mart, tests, docs | Not started |
| 5 | Lakeview dashboard (later: HF Space or Databricks App) | Not started |

Real-data validation is **not yet done**. It needs access to
`dumps.wikimedia.org`, which the build sandbox could not reach.

## Layout

```
seeds/ai_companies.csv          versioned entity -> en.wikipedia title map
src/pageviews_anomaly/parse.py  dump line parsing, title filtering, dump URL builder
src/pageviews_anomaly/anomaly.py rolling-baseline z-score (pure Python, no Spark)
tests/                          unit tests for the above
docs/                           problem statement, decisions log, scope change
```

## Running the tests

```bash
pip install pytest
PYTHONPATH=src pytest -q
```

## Before the first backfill

1. Verify every `en_wikipedia_title` in `seeds/ai_companies.csv` against the
   live article. Titles are marked `verify_before_backfill`. Change
   `title_status` to `verified` once checked, and record any rename in the
   seed with a new `title_pinned_on` date.
2. Expand the startup panel toward 15–25 companies using the inclusion rule in
   `docs/scope_change_2026-11-03.md`. The seed's startup and benchmark counts are
   listed in `seeds/ai_companies.csv`.
3. Decide whether the per-agent (user-traffic) dump variant is available, and
   compare it against the all-agents series (see Known limitations in the
   problem statement).
