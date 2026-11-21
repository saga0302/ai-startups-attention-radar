-- Fails if a day is flagged as both a spike and a drop.
SELECT entity_id, day_utc
FROM {{ ref('pageviews_zscore') }}
WHERE spike_flag AND drop_flag
