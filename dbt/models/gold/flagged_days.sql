-- Gold table: only the days a company was flagged, with a direction label.
-- This is the table the dashboard reads.
SELECT
  entity_id,
  en_wikipedia_title,
  day_utc,
  views,
  z,
  CASE WHEN spike_flag THEN 'spike' WHEN drop_flag THEN 'drop' END AS direction
FROM {{ ref('pageviews_zscore') }}
WHERE spike_flag OR drop_flag
