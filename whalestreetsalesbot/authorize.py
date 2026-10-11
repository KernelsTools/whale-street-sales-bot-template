"""Gets an X Access Token for the bot account (e.g. @WhaleStreetBuy) when the developer app
belongs to a different account. Uses X's PIN login and writes the token into .env.

    python authorize.py          step 1: prints a link; open it logged in as the bot account
    python authorize.py 1234567  step 2: the PIN X showed you; saves the token to .env

Needs X_API_KEY and X_API_SECRET (the app's keys) in .env already.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from requests_oauthlib import OAuth1Session

from config import load_settings

ENV_FILE = Path(".env")
PENDING_FILE = Path(".x_auth_pending")  # the half-finished login between step 1 and step 2
API = "https://api.x.com"


def set_env(values: dict) -> None:
    text = ENV_FILE.read_text()
    for key, value in values.items():
        line = f"{key}={value}"
        if re.search(rf"^{key}=.*$", text, flags=re.M):
            text = re.sub(rf"^{key}=.*$", lambda _: line, text, flags=re.M)
        else:
            text += f"\n{line}\n"
    ENV_FILE.write_text(text)


def start(key: str, secret: str) -> None:
    session = OAuth1Session(key, client_secret=secret, callback_uri="oob")
    token = session.fetch_request_token(f"{API}/oauth/request_token")
    PENDING_FILE.write_text(json.dumps(token))
    PENDING_FILE.chmod(0o600)
    print("1. Open this link in a browser logged in as the BOT account (e.g. @WhaleStreetBuy):")
    print(f"   {API}/oauth/authorize?oauth_token={token['oauth_token']}")
    print("2. Click Authorize app, then run:  python authorize.py <PIN>")


def finish(key: str, secret: str, pin: str) -> None:
    if not PENDING_FILE.exists():
        raise SystemExit("No login in progress: run `python authorize.py` first.")
    pending = json.loads(PENDING_FILE.read_text())
    session = OAuth1Session(key, client_secret=secret, resource_owner_key=pending["oauth_token"],
                            resource_owner_secret=pending["oauth_token_secret"], verifier=pin)
    token = session.fetch_access_token(f"{API}/oauth/access_token")
    PENDING_FILE.unlink()
    set_env({"X_ACCESS_TOKEN": token["oauth_token"], "X_ACCESS_TOKEN_SECRET": token["oauth_token_secret"]})
    print(f"Saved the access token for @{token.get('screen_name', '?')} to .env")


def main() -> None:
    s = load_settings()
    if not (s.x_api_key and s.x_api_secret):
        raise SystemExit("Set X_API_KEY and X_API_SECRET in .env first (and save the file).")
    if len(sys.argv) > 1:
        finish(s.x_api_key, s.x_api_secret, sys.argv[1].strip())
    else:
        start(s.x_api_key, s.x_api_secret)


if __name__ == "__main__":
    main()
