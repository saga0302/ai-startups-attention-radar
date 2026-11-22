-- Gold table: days a company was flagged as a spike (z > 3).
-- Drops stay in pageviews_zscore but are not shown here. This is the table the dashboard reads.
SELECT
  entity_id,
  en_wikipedia_title,
  day_utc,
  views,
  z
FROM {{ ref('pageviews_zscore') }}
WHERE spike_flag
