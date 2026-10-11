# Whale Street Sales Bot: Deployment & Operations

Posts every sale of Whales of WhaleStreet (Robinhood Chain) to **@WhaleStreetBuy** on X.
This doc covers the current state and how to run it.

> Values in `<ANGLE_BRACKETS>` (Google account, project, billing account, server IP) are kept out of this
> public repo. Find them in the team password manager, or in `deployment.local.md` (gitignored) on the deploying laptop. Each change is recorded in
[`deployment-log.md`](deployment-log.md); how the bot itself works is in [`README.md`](README.md).

---

## 1. Status

| | |
|---|---|
| **State** | 🟢 **LIVE** since 2026-10-11 20:28 UTC |
| Posts as | @WhaleStreetBuy (X developer app owned by KernelsTools) |
| Server | `whale-bot`: Google Cloud e2-micro (always free), us-central1-a, IP <SERVER_IP> |
| Google account | <GCP_ACCOUNT>, project `<GCP_PROJECT>` |
| Hosting cost | $0 (free tier). $1/month budget alert on billing account `<BILLING_ACCOUNT>` |
| X API cost | ~$0.015 per post (≈ $10/month at ~20 sales/day) |
| Last change | 2026-10-11 20:41: hourly heartbeat log (see the deployment log) |

### Open items
- [ ] **First live sale posted correctly**: image, price, and ENS names look right
- [ ] Delete the #2863 test post (https://x.com/i/status/2109321027708703005)
- [ ] Confirm the X API spending limit is set (developer.x.com)
- [ ] Name an owner for the weekly check and X credit top-ups: ___
- [ ] If billing is on the free trial: **activate the full account before day 90**, or Google stops the server
- [ ] Week-1 billing check: hosting still $0
- [ ] Later: "Automated by" label on @WhaleStreetBuy (Settings → Your account → Account information → Automation)
- [ ] Later: put this folder in our own git repo (the server copy was deployed with `scp`)

---

## 2. How it fits together

```
Robinhood Chain RPC ──(every 15 s: new NFT transfers + OpenSea/Seaport orders)──┐
Coinbase (ETH→USD) ─────────────────────────────────────────────────────────────┤
Ethereum RPC (ENS names) ───────────────────────────────────────────────────────┼─► bot container ─► X API ─► @WhaleStreetBuy
IPFS gateway (NFT image) ───────────────────────────────────────────────────────┘        │
                                                                        /data/state.json (Docker volume `bot-data`)
```

- The bot only makes **outbound** connections. No ports are open, apart from SSH for us.
- **`state.json`** records the last block scanned and recent sale IDs. A restart resumes from there:
  sales aren't missed or posted twice. It lives in the Docker volume `whale-bot_bot-data`.
- The bot waits for **20 confirmations** (~2 s), so a post goes out a few seconds to ~30 s after the sale.

---

## 3. Accounts & credentials

Never paste keys into chat, tickets or git. Keep them in the team password manager.
For what each X key is and why we need the PIN login, see [`x-api-credentials.md`](x-api-credentials.md).

| What | Where it lives | Notes |
|---|---|---|
| Google Cloud | <GCP_ACCOUNT> | Owns the project, billing, and server |
| X developer app | KernelsTools developer account | Pays for the API credits; holds the API Key/Secret |
| X posting account | @WhaleStreetBuy | Authorized the KernelsTools app via PIN login |
| `X_API_KEY`, `X_API_SECRET` | `.env` on the server + password manager | The **app's** keys (also called Consumer Key/Secret) |
| `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET` | `.env` on the server + password manager | **@WhaleStreetBuy's** keys, from `authorize.py`. Not the ones on the portal's "Keys and tokens" page; those belong to KernelsTools |

**Regenerating the @WhaleStreetBuy token** (e.g. after a leak or revoked access): on a laptop with the bot folder
and the app keys in `.env`, run
```bash
docker compose run --rm -v "$PWD:/work" -w /work bot python authorize.py          # prints a link
#   open it while logged in as @WhaleStreetBuy, click Authorize, note the PIN
docker compose run --rm -v "$PWD:/work" -w /work bot python authorize.py <PIN>    # writes the token to .env
```
Then copy the two new values into the **server's** `.env` by hand (see §4) and restart.

---

## 4. Runbook

Every server command starts from an SSH session. You need gcloud on your laptop, logged in as <GCP_ACCOUNT>:
```bash
gcloud compute ssh whale-bot --zone=us-central1-a --project=<GCP_PROJECT>
cd ~/whale-bot
```

| Task | Command (on the server, in `~/whale-bot`) |
|---|---|
| Is it running? | `sudo docker compose ps` (should say `Up ...`) |
| Live logs | `sudo docker compose logs -f --tail 100` |
| Logs since a time | `sudo docker compose logs --since 24h` |
| Just the posts | `sudo docker compose logs \| grep Posted` |
| Just the problems | `sudo docker compose logs \| grep -E "ERROR\|WARNING"` |
| Health check | `sudo docker compose run --rm bot python bot.py --check` |
| Restart | `sudo docker compose restart` |
| **Emergency: stop posting** | `sed -i 's/^DRY_RUN=.*/DRY_RUN=true/' .env && sudo docker compose up -d` |
| Resume posting | `sed -i 's/^DRY_RUN=.*/DRY_RUN=false/' .env && sudo docker compose up -d` |
| Change a setting | `nano .env` → `sudo docker compose up -d` |
| Change the post text | `nano tweet_template.txt`. It applies from the next post, no restart |
| Re-post one missed sale | `sudo docker compose run --rm bot python bot.py --tx 0x<tx hash>` |

### Deploying a code change
From the laptop, in the bot folder. **Copy code files only; never copy `.env`.** The laptop's `.env` has
`DRY_RUN=true`, so copying it would quietly stop posting.
```bash
docker run --rm -v "$PWD:/app" -w /app python:3.12-slim sh -c "pip -q install -r requirements.txt && python -m unittest discover tests"
gcloud compute scp --zone=us-central1-a <changed files> whale-bot:~/whale-bot/
gcloud compute ssh whale-bot --zone=us-central1-a --command='cd ~/whale-bot && sudo docker compose up -d --build'
```
Then check the logs for a fresh `Watching ... from block N` line, and add an entry to `deployment-log.md`.

### Things never to do
- `docker compose down -v`: the `-v` deletes the state volume. The bot restarts from "now" and misses everything in between.
- Change the server to another machine type, region, or disk type: it leaves the free tier.
- Commit `.env` (it's in `.gitignore`), or copy the laptop's `.env` over the server's.

---

## 5. Reading the logs

Every line has a timestamp and a level (`INFO`, `WARNING`, `ERROR`). Docker keeps the last ~30 MB (3 × 10 MB files).

| Log line | Meaning | Action |
|---|---|---|
| `Watching 0x01f3... from block N` | Bot started. If it ends with `(DRY RUN ...)`, it isn't posting | Make sure "DRY RUN" is only there when intended |
| `Heartbeat: scanned up to block N, M sales handled since start` | Hourly sign of life. N should go up every hour | None. **No heartbeat for 2+ hours means something's wrong** |
| `Posted #2863: https://x.com/i/status/...` | A sale went out | None |
| `Skipping #N at $X (under MIN_PRICE_USD)` | Sale below the minimum price setting | None |
| `X says #N was already posted; skipping` | X rejected a duplicate | None |
| `No image for #N: ...` | Couldn't load the NFT image from IPFS. The post goes out without it | If it's frequent, set `IPFS_GATEWAY` to a dedicated gateway |
| `Image upload failed, posting without the image` | X refused the image upload | If it repeats, check the X API status |
| `Couldn't fetch the ETH price ...; using the last known price` | Coinbase blip | None unless it persists |
| `RPC ... failed (...), retrying` | Robinhood Chain RPC blip, retried automatically | None unless it persists |
| `X rate limit hit, waiting Ns` | Too many X requests; waits and retries | None |
| `ERROR Error, will retry: ...` | Something failed mid-scan. Retries with backoff (up to ~5 min); **nothing is skipped** | If it repeats, read the message (below) |
| `ERROR ... X API error 401` | X keys invalid or revoked | Regenerate the token (§3) |
| `ERROR ... X API error ...` mentioning credits, payment or 402 | **Probably out of X API credits** (we haven't seen this error yet; update this row when we do). The bot pauses and posts the backlog once credits are topped up | Top up at developer.x.com |
| `ERROR ... X API error 403` | App lost "Read and write", or the token is read-only | Check the app permissions, then regenerate the token (§3) |

### When something's wrong
1. `sudo docker compose ps`: is it `Up`? If not, `sudo docker compose up -d`, then read the logs.
2. `sudo docker compose logs --since 3h | grep -E "ERROR|WARNING|Heartbeat"`: what's failing, and is the block number still going up?
3. `sudo docker compose run --rm bot python bot.py --check`: which of RPC, X, or price is broken?
4. A sale didn't post? Find its tx hash on the explorer or OpenSea, then
   `sudo docker compose run --rm bot python bot.py --tx 0x...` to post it by hand.
5. Record what happened and the fix in `deployment-log.md`.

### Weekly check (~5 min)
- [ ] Recent @WhaleStreetBuy posts match recent OpenSea sales
- [ ] `sudo docker compose logs --since 168h | grep -c ERROR` is low, and heartbeats are present
- [ ] X developer portal: credit balance OK
- [ ] Google Cloud billing (<GCP_ACCOUNT>): $0, no budget alert emails

---

## 6. Rebuilding from scratch

Use this if the server is lost, or to move the bot elsewhere. The steps for 2026-10-11 are in `deployment-log.md`.

**Why Google Cloud:** our Docker account (Docker Hub) only stores images and can't run them. Google Cloud's
always-free e2-micro runs 24/7 at $0. Alternatives were Oracle Cloud Always Free (backup option), Render/Railway/Fly.io
(no longer free for 24/7 workers), or a cheap VPS (~$5/month).

**Free-tier rules:** one e2-micro, in us-west1, us-central1 or us-east1, with a **Standard** disk (pd-standard)
≤ 30 GB. The console's default "Balanced" disk is billed. 1 GB/month outbound traffic is free.

```bash
# On the laptop (gcloud logged in as <GCP_ACCOUNT>)
gcloud config set project <GCP_PROJECT>
gcloud compute instances create whale-bot --zone=us-central1-a --machine-type=e2-micro \
  --image-family=debian-12 --image-project=debian-cloud --boot-disk-size=30GB --boot-disk-type=pd-standard

# On the server (gcloud compute ssh whale-bot --zone=us-central1-a)
curl -fsSL https://get.docker.com | sudo sh && sudo systemctl enable --now docker
sudo fallocate -l 1G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile \
  && sudo swapon /swapfile && echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
mkdir -p ~/whale-bot

# From the laptop: copy the code, then create the server .env from the password manager (DRY_RUN=true first)
gcloud compute scp --zone=us-central1-a *.py tweet_template.txt requirements.txt Dockerfile \
  docker-compose.yml .env.example whale-bot:~/whale-bot/

# On the server
cd ~/whale-bot && cp .env.example .env && nano .env && chmod 600 .env
sudo docker compose up -d --build
sudo docker compose run --rm bot python bot.py --check     # expect @WhaleStreetBuy
# check the logs, then set DRY_RUN=false and run `sudo docker compose up -d`
```
A new server starts watching from "now". To post sales missed while it was down, set `START_BLOCK` in `.env`
**before** the first start, to the block recorded in the last heartbeat line you have.
