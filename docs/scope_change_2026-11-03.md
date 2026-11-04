# Scope change: 2026-11-03

## Decision
The main panel is AI startups. Large AI companies are kept as labelled benchmarks.
The panel size is no longer capped at 15 to 25. The panel includes every startup that passes the inclusion rule.

- `role = startup`: the main panel. These companies are compared with each other.
- `role = benchmark`: large AI companies, used as a reference for what high attention looks like on Wikipedia. They are not ranked against startups.

## Current counts
See `seeds/ai_companies.csv`. At this date: 41 startups and 6 benchmarks.

## Benchmarks
Anthropic, OpenAI, xAI, Google DeepMind, Meta AI, Microsoft AI.

## Inclusion rule for startups
1. Works on AI as a core product or research focus.
2. Has an English Wikipedia article, with the exact title pinned in the seed.
3. Headquarters: checked against Wikipedia's category "Artificial intelligence industry in the United States".
   - `US (in category)`: confirmed by the category list.
   - `not in category, verify HQ`: not listed in the category. This does not prove the company is non-US. It means the headquarters still needs checking.
4. Non-US companies are not in the panel. Confirm this for each `verify HQ` entry before the first backfill.

Non-US labs from the original list were removed: Mistral AI (France), Cohere (Canada), Stability AI (UK), and Google DeepMind was kept only as a benchmark, since it is headquartered in London.

## Known limits
- Many startups have no English Wikipedia article, or very low daily views. Low counts make z-scores noisy, so a minimum-volume threshold is needed before flagging.
- The z-score compares each company only with its own history. Peer comparison needs a separate metric, such as share of views within the panel. Not built yet.
- Spikes show attention, not approval. Attribution remains a manual step.
- The category page lists "SpaceXAI" rather than xAI. Check whether the xAI title is still current.

## Open items
- Verify every title in the seed on Wikipedia before the first backfill.
- Verify headquarters for the `not in category` startups.
- Set a minimum-volume threshold.
- The problem statement PDF still says 15 to 25 companies. It has not been edited, since PDFs can't be edited here. Update it in the source document.
