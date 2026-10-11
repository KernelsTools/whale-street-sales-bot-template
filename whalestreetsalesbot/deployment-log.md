# Deployment Log: Whale Street Sales Bot

A dated record of every change to the production bot. Newest first. Times are UTC.
Add an entry whenever you change the server, the settings, the code, or the accounts.

Entry format: **what changed**, **why**, **how it was verified**.

---

## 2026-10-11

### Repo prepared for the public KernelsTools GitHub repo
- **What:** added a top-level `.gitignore` (secrets, runtime files, Python and OS clutter, `*.local.md`) and removed `__pycache__`.
  Replaced the Google account, project, billing account and server IP in these docs with placeholders. The real
  values are in the gitignored `deployment.local.md` and the team password manager.
- **Why:** `KernelsTools/whale-street-sales-bot-template` is public.
- **Verified:** scan of the files to be committed: no keys and no private IDs. `.env` and `deployment.local.md` are ignored. Tests pass.

### 20:55: Docs: X credentials explainer
- **What:** added `x-api-credentials.md` (which X key belongs to the app vs. the posting account, the PIN login,
  gotchas), linked from README and `deployment-plan.md`. Docs only, no server change.

### 20:41: Hourly heartbeat log added and deployed
- **What:** `bot.py` writes `Heartbeat: scanned up to block N, M sales handled since start` once an hour.
  Copied only `bot.py` to the server and rebuilt; the server's `.env` was untouched (`DRY_RUN=false` kept).
- **Why:** with no sales, the log was silent for hours, so a healthy bot looked the same as a stuck one.
- **Verified:** unit tests pass (11 OK). A local dry run with a 1 s interval printed heartbeats with an
  advancing block number. After the restart the server resumed from block 86120930, so no blocks were skipped.

### 20:28: Went live
- **What:** server `.env` set to `DRY_RUN=false`, container recreated. Watching from block 86112943.
- **Why:** the test post was approved, so the team chose to go live without the full 24–48 h dry run.
- **Verified:** startup log has no "DRY RUN" suffix. Dry-run logs from 16:16 to 20:28: 0 sales, 0 errors or warnings.
- **Note:** the server hasn't processed a real sale yet. Watch the first live post.

### 16:31: Test post to @WhaleStreetBuy
- **What:** one-off live run from the laptop of past sale #2863
  (tx `0x215505a6...ebbb`): https://x.com/i/status/2109321027708703005
- **Why:** check posting, the image upload, and the format on the real account.
- **Verified:** posted with the image. The team approved the format.
- **To do:** delete this post. It's an old sale, and followers will read it as a new one.

### 16:16: Deployed to Google Cloud in dry run
- **What:**
  - Project `<GCP_PROJECT>` created under <GCP_ACCOUNT> and linked to billing account `<BILLING_ACCOUNT>`.
  - $1/month budget alert added (50% / 100%; counts the always-free credit only, so trial credits can't hide spend).
  - Server `whale-bot` created: e2-micro, us-central1-a, Debian 12, 30 GB pd-standard, IP <SERVER_IP>.
  - Docker 29.9.0 + Compose v5.6.0 installed, 1 GB swap added.
  - Bot files and `.env` copied to `~/whale-bot`, started with `docker compose up -d`.
- **Verified:** `--check` on the server: RPC chain 4663, contract WhaleStreet, `X: authenticated as @WhaleStreetBuy`, DRY RUN.
- **Note:** the first gcloud login used the wrong Google account (its billing account was closed). We switched
  to `<GCP_ACCOUNT>` and revoked the other account from gcloud on the laptop.

### Before 16:16 (exact time not recorded): X access token for @WhaleStreetBuy
- **What:** added `authorize.py` (X PIN login). The app is owned by KernelsTools, and the portal's Access Token
  belongs to the app owner, so @WhaleStreetBuy authorized the app and its token was written to `.env`.
- **Verified:** `--check` gives `X: authenticated as @WhaleStreetBuy`.

### ~15:35: Repo prepared for launch
- **What:**
  - Added `.env.example` (it was referenced in the README but missing), `.gitignore`, and Docker log rotation (3 × 10 MB).
  - Wrote `deployment-plan.md`.
- **Verified:** image builds; 11 unit tests pass. `--tx` on sale #2863 renders
  `🐳 Whale Street #2863 Bought / 💰 0.003849 ETH ($9.66) / 🛒 OpenSea / 👤 0xea0e...d9b1 → hotmagenta.eth` with the image.
