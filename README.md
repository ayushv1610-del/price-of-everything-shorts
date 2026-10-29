# The Price of Everything — Production Studio

Isolated from JARVIS. Single-replica FastAPI application with a durable SQLite queue and asset directory on the existing Railway `/data` volume. No paid model, voice, music, footage or stock services are called.

## Working pipeline

Curated source evidence → unique topic queue → offline synthetic narration → original animated 720×1280 H.264/AAC video at 24fps → caption SRT, thumbnail, source-linked metadata → ffprobe validation and full video decode → authenticated review dashboard.

The worker selects one unused topic per UTC day. The initial catalog has **three verified evergreen topics**. When exhausted it stops; it does not invent facts or repeat existing topics. This is a bounded curated producer, not unlimited autonomous web research or an AI growth system. New topics currently require adding reviewed scripts and evidence in `catalog.py` and deploying them.

Queue transitions: `queued → rendering → ready`; a render gets at most three automatic attempts. Startup recovers interrupted renders. Failed jobs can be retried through the authenticated API. Drafts from the original schema remain intact. Audit events persist in SQLite. The service must run **one replica / one uvicorn worker**; scaling requires a shared transactional queue and object storage.

## Access and configuration

- `SHORTS_ADMIN_TOKEN`: strong secret; enter on the Studio login screen. Stored in an HttpOnly, Secure, SameSite cookie for 24 hours. Never put it in a URL.
- `SHORTS_DB_PATH`: persistent database file, on `/data` in production.
- `SHORTS_OUTPUT_DIR=/data/shorts-output`: persistent outputs and private Google credentials.
- `SHORTS_PUBLIC_URL`: exact HTTPS service URL.
- `SHORTS_WORKER_ENABLED=1`: production worker; set to 0 for API-only tests.
- `SHORTS_COOKIE_SECURE=0`: local HTTP development only.

Public `/health` and `/ready` expose no scripts or assets. All queue, assets, schedule and audit endpoints require admin authentication. Asset routes use an allowlist. Low storage fails health/readiness and rendering explicitly. There is no media library mounted publicly and no JARVIS code or credentials are referenced.

## Google authorization (not connected until completed)

Enable YouTube Data API v3 in a Google Cloud project, create a Web OAuth client, and configure this redirect URI:

`https://shorts-api-production-9483.up.railway.app/oauth/google/callback`

Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` as private Railway variables. Click **Connect Google** in Studio and authorize the intended channel. Tokens are written atomically with file mode 0600 outside the source repository. OAuth state is single-use and expires after ten minutes. Set `YOUTUBE_CHANNEL_ID` to the confirmed channel ID before any upload; the uploader checks the authorized channel matches.

A private upload requires `/api/jobs/{id}/approve-private` with the exact QA SHA-256 and then `/api/jobs/{id}/upload-private`. Uploads explicitly set `privacyStatus=private` and `notifySubscribers=false`. Completed uploads return their persisted YouTube ID on repeat requests. Interrupted/ambiguous uploads become `upload_unknown` and **are never retried automatically**, because a remote video may already exist. Reconcile in YouTube Studio before any further upload action.

**There is no public-publishing endpoint.** Public publishing requires a separate user decision and implementation. No automatic uploads run in the daily worker. Live OAuth and YouTube API behavior remain unverified until authorization.

## Local validation

```
python -m pip install -r requirements.txt
python -m pip install httpx
python -m unittest -v test_production test_system
```

Install ffmpeg with the `flite` audio filter and DejaVu fonts for the renderer (included in Docker). Use `renderer.render(catalog.plan_for(catalog.CATALOG[0]), output_folder)` for a real media integration test. Tests cover auth, CSRF-origin checks, unique topic selection, catalog exhaustion, render retry limits, crash recovery, upload gates, token-file denial and old draft compatibility. Synthetic narration is a basic offline voice; premium voice and richer media are separate quality upgrades requiring cost decisions where applicable.

The mounted volume is durable across redeploys, not an offsite backup. No external backup service or billing changes have been enabled.
