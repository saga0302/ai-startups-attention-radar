"""Hourly ingest of Wikimedia pageviews for the AI company panel.

Each run processes one hour: LAG_HOURS before the run's logical time, because
Wikimedia publishes an hour's file some time after the hour ends.

Deploy: the package (pageviews_anomaly/) and the seed file (seeds/) must sit
next to this file in the Airflow dags folder.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from airflow.sdk import dag, task

sys.path.insert(0, str(Path(__file__).parent))

from pageviews_anomaly.ingest import stage_hour  # noqa: E402
from pageviews_anomaly.seed import load_seed, title_to_entity  # noqa: E402

LAG_HOURS = 3
SEED_PATH = Path(__file__).parent / "seeds" / "ai_companies.csv"
BRONZE_DIR = os.environ.get("PAGEVIEWS_BRONZE_DIR", "/opt/airflow/data/bronze")


@dag(
    dag_id="pageviews_hourly_ingest",
    schedule="@hourly",
    start_date=datetime(2026, 11, 2, tzinfo=timezone.utc),
    catchup=False,
    max_active_runs=2,
    default_args={"retries": 3, "retry_delay": timedelta(minutes=30)},
    tags=["pageviews", "bronze"],
)
def pageviews_hourly_ingest():
    @task
    def hour_to_process(logical_date: datetime) -> str:
        hour = logical_date.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
        hour -= timedelta(hours=LAG_HOURS)
        return hour.strftime("%Y-%m-%dT%H:%M:%SZ")

    @task
    def stage(hour_utc: str) -> str:
        seed_map = title_to_entity(load_seed(SEED_PATH))
        path = stage_hour(hour_utc, seed_map, BRONZE_DIR)
        return str(path)

    stage(hour_to_process())


pageviews_hourly_ingest()
