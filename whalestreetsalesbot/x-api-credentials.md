# X API Credentials, Explained

The X developer portal shows six credentials. **The bot uses four:** two that identify the **app** and two
that identify the **account that posts**. Mixing those up is the most common setup mistake. We made it too:
our first token posted as KernelsTools, not @WhaleStreetBuy.

## Each credential

| Name in the X portal | Also called | Belongs to | Used by our bot? | Goes in `.env` as |
|---|---|---|---|---|
| **API Key** | Consumer Key | The **app** (KernelsTools's app) | ✅ Yes | `X_API_KEY` |
| **API Key Secret** | Consumer Secret | The **app** | ✅ Yes | `X_API_SECRET` |
| **Access Token** | OAuth 1.0a user token | The **account that posts** (@WhaleStreetBuy) | ✅ Yes | `X_ACCESS_TOKEN` |
| **Access Token Secret** | | The **account that posts** | ✅ Yes | `X_ACCESS_TOKEN_SECRET` |
| Bearer Token | App-only token | The app | ❌ No | — |
| Client ID / Client Secret | OAuth 2.0 keys | The app | ❌ No | — |

- **API Key + Secret identify the app.** X calls them "the username and password for your X App".
  Every request the bot makes is signed with them. Whoever owns the app (KernelsTools) is billed for API usage.
- **Access Token + Secret identify the account that posts.** Posts appear on whichever account these
  tokens belong to, regardless of who owns the app.
- **Bearer Token** only reads public data. It can't post, so we don't use it.
- **Client ID / Client Secret** belong to OAuth 2.0, a separate login system. Our bot uses OAuth 1.0a, so these aren't needed.

## The catch: the portal's Access Token belongs to the app owner

The **"Keys and tokens" page only generates an Access Token for the account that owns the app.** Our app is owned
by KernelsTools, so that token posts as KernelsTools.

To post as a **different** account, that account has to authorize the app. In X's words: *"To make requests on behalf
of another user, generate a separate set of Access Tokens for that user using the 3-legged OAuth flow."*

```
KernelsTools (developer account)            @WhaleStreetBuy (bot account)
  └─ owns the X app                            └─ authorizes the app (PIN login)
       ├─ API Key         ─┐                        ├─ Access Token        ─┐
       └─ API Key Secret  ─┴── X_API_KEY/SECRET     └─ Access Token Secret ─┴── X_ACCESS_TOKEN/SECRET
                                   │                                                  │
                                   └───────────── bot signs every request with all 4 ─┘
                                                  → posts appear on @WhaleStreetBuy
```

## Getting the bot account's token (PIN login)

`authorize.py` runs X's PIN-based ("out-of-band") version of that 3-legged flow. It suits a command-line tool:
no website or redirect is needed.

1. Put **only** `X_API_KEY` and `X_API_SECRET` in `.env`, and save the file.
2. `docker compose run --rm -v "$PWD:/work" -w /work bot python authorize.py`
   prints an `api.x.com/oauth/authorize?...` link.
3. Open it in a browser **logged in as the bot account** (a private window avoids the wrong account) and click **Authorize app**.
4. X shows a 7-digit PIN. Run `... python authorize.py <PIN>`.
5. The script writes the bot account's Access Token and Secret into `.env` and prints which account it's for.
   It never prints the secrets themselves.
6. Check with `docker compose run --rm bot python bot.py --check`. It should say `X: authenticated as @WhaleStreetBuy`.

## Gotchas we hit or the docs warn about

- **Read and write first, then the token.** A token generated while the app was read-only stays read-only.
  Posting then fails with **403**. Fix: set **App permissions → Read and write**, then generate a new token.
- **A Callback URL must be set even for the PIN login.** Any URL works (e.g. `http://localhost`). It's under the
  app's *User authentication settings*.
- **PINs are single-use and expire in minutes.** If one fails, run step 2 again for a new link.
- **Wrong account in the browser = wrong token.** `authorize.py` prints the account name. If it isn't the bot account, redo it.
- **API Key/Secret are shown once.** If they're lost, regenerate them on the "Keys and tokens" tab. Any copies in
  `.env` files then need updating.
- **Never paste keys into chat, tickets or git.** Store all four in the team password manager.

## Sources
- [X authentication overview](https://docs.x.com/fundamentals/authentication/overview)
- [API Key and Secret](https://docs.x.com/fundamentals/authentication/oauth-1-0a/api-key-and-secret)
- [Obtaining user access tokens (3-legged OAuth)](https://docs.x.com/fundamentals/authentication/oauth-1-0a/obtaining-user-access-tokens)
- [PIN-based OAuth](https://docs.x.com/fundamentals/authentication/oauth-1-0a/pin-based-oauth)
