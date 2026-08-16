# CURBO Operations Runbook

## Production prerequisites

Do not expose CURBO directly to the internet. Put the frontend and API behind an HTTPS identity-aware gateway. Production startup deliberately fails unless authentication, a strong API key, an explicit HTTPS CORS origin, trusted hosts, and a required database are configured.

Apply database migrations before starting a new application version:

```bash
cd backend
DATABASE_URL="postgresql+psycopg2://..." .venv/bin/alembic upgrade head
```

The application verifies the expected migration revision during production startup. Test upgrades and downgrades against a copy of production data before deployment.

## Required platform controls

- Terminate TLS at a managed ingress or load balancer.
- Replace the shared API-key foundation with the organization's OIDC provider before multi-user launch.
- Store secrets in the hosting platform's secret manager; never in Git or a browser bundle.
- Restrict PostgreSQL to private networking and require encrypted connections.
- Send JSON request logs to immutable centralized storage with retention and alerting.
- Monitor readiness failures, HTTP 5xx/429 rates, latency, database saturation, disk usage, and report growth.
- Configure resource limits, autoscaling, a CDN for immutable frontend assets, and an edge request-size limit of 1 MB.

## Backup and restore

Run `scripts/backup_postgres.sh` on a schedule using a restricted database account. Copy each dump and checksum to encrypted, versioned storage in a separate failure domain. A local dump on the application host is not a backup.

Test `scripts/restore_postgres.sh` at least quarterly in an isolated environment. Record recovery time, verify annotation counts and reports, run smoke tests, and never point the restore command at production without an approved incident/change record.

Recommended minimum targets before launch:

- point-in-time database recovery with at least 30 days of retention;
- daily independent restore verification;
- documented recovery point and recovery time objectives;
- object-storage versioning and lifecycle policy for generated reports.

## Deployment and rollback

1. Run CI and security/dependency checks.
2. Back up the database and test the migration on a restored copy.
3. Build one immutable image per commit and scan/sign it in the deployment platform.
4. Apply migrations, deploy to staging, and run authenticated smoke tests.
5. Promote the same image using a canary or rolling deployment.
6. Watch error, latency, readiness, and saturation signals.
7. Roll back the application image when a release fails. Only downgrade a database migration after its downgrade has been proven safe on copied data.

## Incident basics

If writes may be corrupt or unauthorized, block mutation traffic first, preserve logs and database snapshots, rotate credentials, and do not delete evidence. If readiness fails, keep the instance out of rotation; liveness should remain healthy unless the process itself is stuck. Record all manual recovery actions and verify user-visible data before reopening traffic.
