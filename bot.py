#!/usr/bin/env python3
"""Telegram polling relay for the site-side PHP bot backend.

This process only receives Telegram updates and forwards them to
`telegram-webhook.php` on the site. All bot logic stays inside `api.php`,
so the website and the bot always use the same linking, subscription,
premium, referral, and broadcast rules.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import urllib.error
import urllib.request


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_php_config() -> dict[str, str]:
    config_path = os.path.join(ROOT_DIR, "api.secrets.php")
    if not os.path.exists(config_path):
        return {}

    try:
        with open(config_path, "r", encoding="utf-8") as fh:
            content = fh.read()
    except OSError:
        return {}

    values: dict[str, str] = {}
    for key in ("telegramBotToken", "telegramWebhookSecret"):
        match = re.search(rf"'{re.escape(key)}'\s*=>\s*'([^']*)'", content)
        if match:
            values[key] = match.group(1).strip()
    return values


PHP_CONFIG = load_php_config()


BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN",
    PHP_CONFIG.get("telegramBotToken", ""),
).strip()
SITE_URL = os.getenv(
    "SITE_URL",
    "https://xn----mtbcsi1d7aq.xn--p1ai",
).rstrip("/")
WEBHOOK_SECRET = os.getenv(
    "TELEGRAM_WEBHOOK_SECRET",
    PHP_CONFIG.get("telegramWebhookSecret", ""),
).strip()
RELAY_URL = os.getenv(
    "TELEGRAM_RELAY_URL",
    f"{SITE_URL}/telegram-webhook.php",
).strip()
POLL_TIMEOUT = max(10, int(os.getenv("TELEGRAM_POLL_TIMEOUT", "25")))
RETRY_DELAY = max(1.0, float(os.getenv("TELEGRAM_RETRY_DELAY", "3")))

TELEGRAM_API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"


def post_json(url: str, payload: dict, headers: dict[str, str] | None = None, timeout: int = 30) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            **(headers or {}),
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read()
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def telegram_api(method: str, payload: dict | None = None, timeout: int = 30):
    response = post_json(f"{TELEGRAM_API_BASE}/{method}", payload or {}, timeout=timeout)
    if not isinstance(response, dict) or not response.get("ok"):
        description = ""
        if isinstance(response, dict):
            description = str(response.get("description") or "").strip()
        raise RuntimeError(description or f"Telegram API call failed: {method}")
    return response.get("result")


def forward_update(update: dict) -> None:
    post_json(
        RELAY_URL,
        update,
        headers={"X-Telegram-Bot-Api-Secret-Token": WEBHOOK_SECRET},
        timeout=POLL_TIMEOUT + 15,
    )


def bootstrap() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is empty.")
    if not RELAY_URL:
        raise RuntimeError("TELEGRAM_RELAY_URL is empty.")
    telegram_api("deleteWebhook", {"drop_pending_updates": False}, timeout=20)
    me = telegram_api("getMe", timeout=20)
    username = ""
    if isinstance(me, dict):
        username = str(me.get("username") or "").strip()
    logging.info("Telegram relay started for @%s -> %s", username or "unknown_bot", RELAY_URL)


def poll_forever() -> None:
    offset = None
    while True:
        try:
            payload: dict[str, object] = {
                "timeout": POLL_TIMEOUT,
                "allowed_updates": ["message", "callback_query"],
            }
            if offset is not None:
                payload["offset"] = offset
            updates = telegram_api("getUpdates", payload, timeout=POLL_TIMEOUT + 20)
            if not isinstance(updates, list):
                continue
            for update in updates:
                if not isinstance(update, dict):
                    continue
                forward_update(update)
                update_id = int(update.get("update_id", 0))
                if update_id > 0:
                    offset = update_id + 1
        except KeyboardInterrupt:
            logging.info("Relay stopped by user.")
            return
        except urllib.error.HTTPError as error:
            body = ""
            try:
                body = error.read().decode("utf-8", errors="replace")
            except Exception:
                body = ""
            logging.error("HTTP error %s while relaying updates: %s", error.code, body or error.reason)
            time.sleep(RETRY_DELAY)
        except urllib.error.URLError as error:
            logging.error("Network error while relaying updates: %s", error)
            time.sleep(RETRY_DELAY)
        except Exception:
            logging.exception("Unexpected relay failure")
            time.sleep(RETRY_DELAY)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    bootstrap()
    poll_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
