-- Z-score per company per day, against that company's previous 30 full days (log scale).
-- Only full days (24 hours) are used, both as the score and in the baseline.
-- A day needs at least 14 prior full days before it gets a score.
WITH base AS (
  SELECT entity_id, en_wikipedia_title, day_utc, views, hours_observed,
         CASE WHEN hours_observed = 24 THEN log1p(views) END AS y
  FROM {{ ref('pageviews_silver_daily') }}
),
stats AS (
  SELECT *,
         COUNT(y) OVER w AS n_history,
         AVG(y) OVER w AS baseline_mean,
         STDDEV_SAMP(y) OVER w AS baseline_std
  FROM base
  WINDOW w AS (PARTITION BY entity_id ORDER BY day_utc
               ROWS BETWEEN 30 PRECEDING AND 1 PRECEDING)
),
scored AS (
  SELECT *,
         CASE WHEN hours_observed = 24 AND n_history >= 14 AND baseline_std > 0
              THEN (y - baseline_mean) / baseline_std END AS z
  FROM stats
)
SELECT entity_id, en_wikipedia_title, day_utc, views, hours_observed, n_history,
       baseline_mean, baseline_std, z,
       z > 3 AS spike_flag,
       z < -3 AS drop_flag
FROM scored
