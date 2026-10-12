# deploy/selfhost: run UniWay on your own Windows computer

Everything needed to run the whole system (website, database, private file store, HTTPS, backups) on one Windows 10/11 computer,
without Render or Supabase. **The step-by-step guide is [`docs/self-host-windows-guide.md`](../../docs/self-host-windows-guide.md)** (Traditional Chinese). Read it first.

## What is here

| Path | What it is |
|---|---|
| `docker-compose.yml` | the five services: `db` (PostgreSQL 17 + pgvector), `rest` (PostgREST), `storage` (private file store), `gateway` (internal HTTPS front door to those two), `app` (the website). Images are pinned to the same versions `scripts/validate_supabase_runtime.py` validates the migrations against |
| `../../Dockerfile`, `docker-entrypoint.sh` | the website image; the entrypoint makes it trust the internal gateway's certificate |
| `gateway/Caddyfile` | the internal gateway (`https://gateway`), reachable only inside Docker |
| `caddy/Caddyfile.template` | the public front door (Caddy installed on Windows itself): HTTPS, compression, writes the visitor's real IP into `X-Client-IP`, 30-day access log |
| `env.template` | every setting, without values. The real file `.env` is generated on the server and is never committed |
| `tools/` | small Python checks that run inside the `app` container: bucket creation, the end-to-end smoke test, the disaster-recovery rehearsal helper |
| `scripts/` | the PowerShell steps below (plain ASCII, Windows PowerShell 5.1) |

## The steps, in order

| Script | Needs admin | What it does |
|---|---|---|
| `00-check.ps1` | no | read-only readiness check of the computer |
| `01-prepare-windows.ps1` | yes | folders, never sleep, firewall (80/443 for Caddy only), upload cap |
| `02-generate-secrets.ps1` | no | writes `.env` with random secrets (`-AskGoogle`, `-UseExistingKeys` available) |
| `03-start.ps1` | no | build, start, set database role passwords, apply migrations, create the private bucket |
| `04-apply-migrations.ps1` | no | called by 03; converts line endings to LF; skips what is already applied |
| `05-install-caddy.ps1` | yes (not with `-SkipService`) | download Caddy (checksum verified), write its config, start it at every boot |
| `06-migrate-from-cloud.ps1` | no | copy the data from the Supabase cloud project (`-Rehearsal` only counts) |
| `07-setup-backup.ps1` | yes | daily backup and 5-minute health check as scheduled tasks |
| `08-restore-backup.ps1` | no | put a backup back (new computer, or roll back to an earlier day) |
| `verify.ps1` | no | end-to-end checks, inside and (with a real domain) from the outside |
| `backup.ps1`, `restore-test.ps1`, `healthcheck.ps1`, `update.ps1` | no | day-to-day: backup, prove a backup restores, keep the site up, update / roll back |

Run each as `powershell -ExecutionPolicy Bypass -File .\NAME.ps1`.

## Rules of this folder

- No secret is ever written into a file that is committed. `deploy/selfhost/.env` is in `.gitignore`.
- Scripts are plain ASCII (Windows PowerShell 5.1 reads BOM-less files in the system code page). Chinese text lives in the guide.
- Only Caddy faces the internet (80 and 443). The website listens on `127.0.0.1:8000`; the database, REST door, storage and gateway are not published at all.
- Clone with `git clone -c core.autocrlf=false`; `.gitattributes` pins `*.sql` and shell scripts to LF because migrations compare function text.
