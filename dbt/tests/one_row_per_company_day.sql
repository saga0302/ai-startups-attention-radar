-- Fails if any company has more than one row for the same day.
SELECT entity_id, day_utc, COUNT(*) AS n
FROM {{ ref('pageviews_silver_daily') }}
GROUP BY entity_id, day_utc
HAVING COUNT(*) > 1
