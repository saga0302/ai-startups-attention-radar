# Airflow on EC2

Airflow runs on an AWS EC2 server, not on a laptop. It keeps running when the
computer is off.

## Server
- Region: us-east-2 (Ohio)
- OS: Ubuntu Server 24.04 LTS
- Instance: m7i-flex.large (2 vCPU, 8 GB RAM), 30 GB disk, 2 GB swap
- Airflow: 3.3.2, installed with Docker Compose in `~/airflow`

## What is on the server (not in this repo)
- `~/airflow/docker-compose.yaml`: Airflow's official Docker setup
- `~/airflow/docker-compose.restart.yml`: restart rules, so Airflow comes back after a reboot
- `~/airflow/.env`: secret keys. Never copy this into Git.
- `~/airflow/dags/`: the DAG and the code it uses. Copied from this repo.

## Access
- The web page is on port 8080. It only accepts connections from my current IP.
- SSH is on port 22, from my current IP only.
- Log in with the `airflow-key.pem` key. Keep it out of Git.

## Restart behavior
Each service has `restart: unless-stopped`. Airflow comes back on its own after
a reboot, and it stays stopped only if someone stops it on purpose.
This was tested with a server reboot.

## Useful commands (run on the server, in `~/airflow`)
```bash
docker compose ps                              # service status
docker compose logs airflow-scheduler --tail 50  # recent scheduler logs
docker compose restart                         # restart all services
```

## Cost
The server is billed while it runs. Stop it in the AWS console when you are
not using it. Stopping keeps the setup; terminating deletes it.