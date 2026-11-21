# Attention Radar: AI Startup Visibility from Wikipedia Pageviews

Attention Radar measures how much public attention AI startups receive on English
Wikipedia, hour by hour, and flags the moments when a company's traffic is unusually
high compared with its own recent history.

A startup can use it to see whether a launch, funding round, or announcement changed
how many people looked it up, and how that compares with its peers. Large AI labs are
tracked as reference labs, to show what high attention looks like on the same measure.

## The problem

AI startups compete for public attention, and that attention often follows specific
events: a product launch, a funding round, a leadership change, a partnership, or a
controversy. Wikipedia pageviews are a public, consistent proxy for interest. The
question this project answers is: **when did a company's attention rise above its own
normal level, and does that spike line up with something it did?**

## Who it is for

- **AI startups**, to check whether they are getting noticed and how they compare with
  peers.
- **Analysts and researchers**, tracking public attention on AI companies over time.
- **Communications teams**, watching for unusual visibility.

## Scope

**Main panel: US AI startups.** English Wikipedia articles for US-headquartered AI
startups. A company joins the panel only if it:

1. Works on AI as a core product or research focus.
2. Has an English Wikipedia article, with the exact title recorded in the seed file.
3. Is headquartered in the United States. This is checked against Wikipedia's category
   "Artificial intelligence industry in the United States." Companies outside that
   category are verified separately before they join.

The panel is not capped at a fixed size. It grows as companies meet the rule.

**Reference labs: large AI companies.** Anthropic, OpenAI, xAI, Google DeepMind, Meta AI,
and Microsoft AI. Reference labs are reported separately and are never ranked against
startups.

**Time range:** at least 12 months of history, so that rolling windows and seasonal
patterns have enough data to test against.

The company list lives in `seeds/ai_companies.csv`, which is versioned so every change
is auditable.

## Data source

Wikimedia publishes a file for every hour, listing how many times each English
Wikipedia article was viewed in that hour. Each file covers all of Wikipedia, so the
pipeline keeps only the rows for panel companies.

Example file address:
`https://dumps.wikimedia.org/other/pageviews/2026/2026-11/pageviews-20261102-140000.gz`

Each run processes one hour, three hours behind the schedule, because Wikimedia
publishes each file a short while after the hour ends.

## How data is stored

| Layer | What it holds | Status |
|---|---|---|
| Bronze | Raw hourly rows for panel companies, unchanged from the source | Local files written; Databricks load next |
| Silver | Cleaned, typed, de-duplicated hourly counts per company | Planned |
| Gold | Daily baselines, z-scores, and anomaly flags, built with dbt | Planned |

Bronze files are compressed CSV, one per hour. Writes are atomic, and running the same
hour twice produces the same file.

## How an anomaly is defined

- **Baseline:** each company's average and spread over the previous 30 days. Today is
  never part of its own baseline.
- **Minimum history:** at least 14 days of data, otherwise no score is given.
- **Transform:** the log version of the counts is used by default, because page view
  counts are highly uneven.
- **Flag:** a day is flagged when its z-score is above 3.
- **No score** is given when the baseline has no spread, rather than dividing by zero.

## Architecture

```
Wikimedia hourly files (internet)
        │
        ▼
Airflow on AWS EC2 ──── schedules, retries, backfills
        │   (keeps only panel companies)
        ▼
Databricks: BRONZE → SILVER → GOLD (dbt)
   raw rows       clean rows     baselines, z-scores, flags
                                        │
                                        ▼
                    Dashboard (planned)

GitHub ── stores the code
```

## Tech stack

- **Apache Airflow 3.3.2** (Docker Compose on AWS EC2, us-east-2): scheduling, retries,
  and backfills
- **AWS EC2**: an always-on Ubuntu server, so the pipeline runs when no laptop is open
- **Databricks** (free edition, Delta tables): storage and processing
- **dbt** (on Databricks): gold-layer models and tests (planned)
- **Python**: parsing, filtering, and the anomaly calculation
- **GitHub**: source control

## Repository layout

```
dags/                       Airflow DAG (hourly schedule)
src/pageviews_anomaly/      Core logic: parsing, filtering, z-score, seed loading
tests/                      Automated tests (21)
seeds/ai_companies.csv      Company panel and reference lab list
infra/airflow/              Notes on running Airflow on EC2
pyproject.toml              Project settings and test configuration
```

## Running the tests

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pytest
pytest -q
```

Expected result: `21 passed`. The tests use small made-up examples. They don't
download data or connect to Airflow or Databricks.

## Status

| Phase | Scope | Status |
|---|---|---|
| 1 | Seed file, parser, z-score logic, ingest and staging, tests | Done |
| 2 | Hourly Airflow DAG on EC2, tested with one real hour | In progress |
| 3 | Load bronze into Databricks | Not started |
| 4 | Silver and gold layers with dbt, backfill over 12 months | Not started |
| 5 | Dashboard | Not started |

## Before the first backfill

1. Confirm every title in `seeds/ai_companies.csv` on Wikipedia, and set its
   `title_status` once checked.
2. Confirm the headquarters of each startup marked `not in category, verify HQ`.
3. Set the minimum-volume threshold below which articles are reported but not flagged.
4. Confirm that the EC2 server can download a Wikimedia file.

## Known limitations

- **Automated traffic:** the hourly files don't separate people from bots and crawlers,
  so some spikes may come from automated traffic.
- **Attention is not approval:** a spike can come from good or bad news. The pipeline
  measures attention, not sentiment.
- **Attribution is manual:** the pipeline flags spikes but does not explain them.
- **Flat history:** a company whose views have been exactly flat receives no score, so
  a jump from a flat baseline is not flagged yet.
- **Thin coverage:** many startups have few or no Wikipedia views, so their scores are
  noisy until a minimum-volume rule is in place.
- **Titles and redirects:** renamed articles split their traffic. Titles are pinned in
  the seed file, and changes are recorded there.

  
