# Decisions log

Each entry: date, decision, reason. Newest first.

## 2026-11-03: Panel is US AI startups, plus two labelled benchmark labs

- Startups are the main panel, so companies can compare visibility with peers.
- Anthropic and OpenAI stay as `role = benchmark` to show what high attention looks like.
- xAI (US, large) added as a benchmark.
- Google DeepMind, Meta AI, and Microsoft AI added as benchmarks.
- Startup headquarters checked against Wikipedia's category "Artificial intelligence industry in the United States". 19 startups are in the category; 22 are not and need checking.
- CoreWeave not in the panel. Its status as a large AI company is still undecided.
- Startup panel expanded to all high- and medium-confidence candidates from the Wikipedia AI company list. Medium-confidence headquarters still need verifying.
- Panel size is no longer capped at 15 to 25. The problem statement PDF still says 15 to 25 and needs updating in the source document.
- Non-US labs were removed. Full rule and limits in `docs/scope_change_2026-11-03.md`.
- Titles are unverified; every entry stays `verify_before_backfill` until checked on Wikipedia.

## 2026-11-02: Baseline excludes the current value; zero-variance windows give a null z

- The baseline is the trailing 30 observations strictly before the evaluation
  day. This follows the problem statement, which says the baseline never
  includes the current value.
- If the baseline std is 0, the z-score is null, not infinite. Flat history
  would otherwise flag any change.

## 2026-11-02: log1p transform by default

- Pageview counts are right-skewed. A log1p transform before computing mean and
  std keeps one large spike from inflating the baseline for weeks.
- The transform is a parameter (`use_log`). Raw-count results can be compared
  side by side to test whether the choice changes which days get flagged.
- This is a provisional default. Confirm it on real data before relying on it.

## 2026-11-02: Minimum 14 non-null prior observations

- Matches the problem statement. Below that, the z-score is null and the day
  is never flagged, to avoid false flags early in the backfill.

## 2026-11-02: Titles matched exactly after normalization; redirects not resolved

- Normalization is percent-decoding plus underscores for spaces.
- Redirect resolution is not done. A renamed article splits its traffic across
  the old and new titles until the seed is updated. The problem statement
  requires recording title changes in the seed, so that is where this is
  handled.

## 2026-11-02: Pure-Python anomaly logic, separate from Spark

- The z-score function is plain Python so it can be unit-tested without a
  cluster. The Spark or dbt version must produce the same numbers. Phase 4 will
  check that by running both on the same fixture.
