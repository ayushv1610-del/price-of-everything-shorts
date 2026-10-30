# The Price of Everything — Production Studio

Isolated from JARVIS. Single-replica FastAPI application with a durable SQLite queue and asset directory on the existing Railway `/data` volume. No paid model, voice, music, footage or stock services are called.

## Working pipeline

Curated source evidence → unique topic queue → offline synthetic narration → original animated 720×1280 H.264/AAC video at 24fps → caption SRT, thumbnail, source-linked metadata → ffprobe validation and full video decode → authenticated review dashboard.

In cartoon mode the worker selects one unused story per day after 09:00 Asia/Kolkata. The bank contains three English stories and two Hindi stories; the Hindi stories are held for language review. The three English entries have already been consumed in production. When exhausted it stops without repeating stories. This is a bounded curated producer, not unlimited autonomous script generation or a growth system. New stories require reviewed scripts in `cartoon_stories.py` and a deployment.

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

Install ffmpeg, DejaVu/Noto fonts and the voice requirements (included in Docker). Download verified models with `download_voice_models.py`. Use `renderer.render(cartoon_stories.plan_for_story(cartoon_stories.STORIES[0]), output_folder)` for a Hindi media integration test. Tests cover auth, CSRF, unique selection, exhaustion, retry limits, crash recovery, upload gates, language review holds and rejected voice fallback. Missing or unsupported voices fail before encoding; flite is not used.

The mounted volume is durable across redeploys, not an offsite backup. No external backup service or billing changes have been enabled.

## Cartoon automation (current implementation)

Set `SHORTS_CONTENT_MODE=cartoon` for the reviewed original story bank in `cartoon_stories.py`. The worker queues one unused story at or after 09:00 Asia/Kolkata each day. It stops when the bank is exhausted rather than repeating scripts. The initial bank contains three distinct stories. This does not include unlimited story generation or automatic analytics-driven revisions.

The Docker build installs `requirements-voice.txt`, downloads pinned Kokoro release assets, checks exact SHA-256 digests, and bundles them outside the persistent volume. Neural voice inference runs locally; it does not call a paid voice API. Rendering normalizes dialogue to stereo AAC at 48kHz and reports per-line voice validation. Mouth motion responds to speech energy, not phoneme-level alignment.

`SHORTS_AUTO_PUBLISH=1` enables the worker's public-upload step only for reviewed cartoon plans whose QA reports validated dialogue and whose current video hash matches the validated hash. Google authorization, the confirmed `YOUTUBE_CHANNEL_ID`, and correct per-plan audience settings are required. Old prototypes and the silent imported test do not qualify for this automatic worker. Ambiguous upload outcomes are held for reconciliation and never automatically uploaded again.

Run `python -m unittest -v test_dialogue test_production test_system` for automated coverage. A real local queue-render integration test produced a 15.592-second cartoon with all five Kokoro lines validated. Deployed behavior must be independently verified after each release.


### Hindi jungle episodes
The story bank now begins with two original Hindi scripts starring Golu (elephant),
Tara (monkey), and Mithu (parrot). They use Hindi Kokoro voices and the `hi`
phonemizer, plus Noto Sans Devanagari and RAQM shaping. They are deliberately
marked `language_review_required` and `publication_ready=False`: waveform and
codec tests cannot establish fluent, natural pronunciation. Neither the worker
nor the explicit public endpoint publishes these held episodes. This is a
quality hold, not a request for another routine publishing approval.

The renderer checks every encoded dialogue interval after muxing. Missing or
silent dialogue fails the render; no replacement voice or silent fallback is used.
Production status exposes remaining story count and publishable count, so a finite
reviewed bank is not mistaken for unlimited autonomous story creation.


## Unattended Hindi publishing

`SHORTS_FEED_ENABLED=1`, cartoon mode, worker, auto publishing and public publishing
must all be enabled. The cloud worker reserves one durable daily slot at 09:00
Asia/Kolkata (catches up after downtime), renders a new story, checks encoded audio
with independent multilingual Whisper, and uploads only matching audible dialogue.
The first upload after enabling the new feed catches up the current day's slot.
`story_feed.json` is a bounded Hindi story inbox, replenished by the separate recurring
ChatGPT task. The service refreshes it from this exact repository, validates schema,
caches the last valid copy, and rejects reused story IDs and identical scripts.
This is AI story authoring plus local neural synthesis/ASR, not an unlimited static bank.
Failed Hindi checks remain failed; the system never weakens QA to meet a schedule.
Ambiguous uploads without an ID require reconciliation; known IDs are checked read-only
and never uploaded twice. Media older than 14 days is pruned after publication;
SQLite records and script hashes remain. /health reports the last public upload and
schedule state without exposing credentials. No paid generation API is used.
