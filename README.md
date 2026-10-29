# The Price of Everything — Shorts Engine

Separate Railway service for the faceless YouTube channel. This first deployment provides a health endpoint and authenticated draft API only. **No uploads, publishing, or monetization are enabled.**

Set SHORTS_ADMIN_TOKEN as a secret in Railway before using /api/drafts. /health is public. Draft storage uses temporary SQLite at /tmp and is **not durable** across restarts; attach a persistent database before production use.

YouTube OAuth, licensed assets, factual review, video rendering, rate limits and human publishing approval must be added before production publishing.
