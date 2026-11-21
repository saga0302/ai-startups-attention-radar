-- One row per company per UTC day, for every day in the data.
-- hours_observed counts the hours the whole dataset has for that day, not just
-- the hours this company had views, so a quiet company is not marked incomplete.
-- Days with no views for a company get views = 0.
WITH bronze AS (
  SELECT * FROM {{ source('bronze', 'pageviews_bronze') }}
),
hours_per_day AS (
  SELECT to_date(substring(hour_utc, 1, 10)) AS day_utc,
         COUNT(DISTINCT hour_utc) AS hours_observed
  FROM bronze
  GROUP BY 1
),
companies AS (
  SELECT entity_id, any_value(en_wikipedia_title) AS en_wikipedia_title
  FROM bronze
  GROUP BY entity_id
),
actual AS (
  SELECT entity_id,
         to_date(substring(hour_utc, 1, 10)) AS day_utc,
         SUM(views) AS views
  FROM bronze
  GROUP BY 1, 2
)
SELECT c.entity_id,
       c.en_wikipedia_title,
       h.day_utc,
       COALESCE(a.views, 0) AS views,
       h.hours_observed
FROM companies c
CROSS JOIN hours_per_day h
LEFT JOIN actual a
  ON a.entity_id = c.entity_id AND a.day_utc = h.day_utc
