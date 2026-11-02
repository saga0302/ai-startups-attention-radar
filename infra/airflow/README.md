# Keeping Airflow running

Airflow in Docker stops when Docker stops. Three things have to be true for
it to keep running:

1. **Docker starts on login.** Docker Desktop → Settings → General →
   tick "Start Docker Desktop when you sign in to your computer".
2. **Containers restart with the daemon.** Apply `docker-compose.restart.yml`
   (see the comments in that file for the service names to match):

   ```bash
   docker compose -f docker-compose.yaml -f docker-compose.restart.yml up -d
   ```

   After this, `docker ps` shows `restart: unless-stopped` behavior
   on the Airflow containers, and they come back after a reboot.
3. **Missed runs are recovered, not lost.** This matters more than the
   restart policy. When the laptop sleeps or is off, hourly runs are missed.
   The planned DAG (Phase 2, not yet written) will use `catchup=True` so that
   when Airflow returns it re-runs the missed hours in order. The Databricks
   writes will use `MERGE` on `(entity_id, hour_utc)`, so re-running an hour
   never double counts.

## What this does not fix

- A laptop that is asleep or powered off still cannot run anything.
  Restarts only work while the machine is on.
- If you need the pipeline to run continuously, put Airflow on a machine
  that is always on: a small cloud VM (for example a free-tier instance on
  Oracle, GCP, or Azure) running the same compose file. The DAG code does not
  change; only where Airflow runs changes.

## Check that it worked

```bash
docker compose ps            # all services 'running' or 'healthy'
docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' $(docker compose ps -q airflow-scheduler)
# expected output: unless-stopped
```
