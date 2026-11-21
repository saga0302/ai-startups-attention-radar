-- One row per company per UTC day: total views and how many hours we saw.
SELECT
  entity_id,
  any_value(en_wikipedia_title) AS en_wikipedia_title,
  to_date(substring(hour_utc, 1, 10)) AS day_utc,
  SUM(views) AS views,
  COUNT(DISTINCT hour_utc) AS hours_observed
FROM {{ source('bronze', 'pageviews_bronze') }}
GROUP BY entity_id, to_date(substring(hour_utc, 1, 10))
