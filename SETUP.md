# Ticket Monitor — Setup Guide

## 1. Create a Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather).
2. Send `/newbot`, choose a name and username.
3. Copy the **bot token** from BotFather's reply.
4. Send any message to your new bot (this initializes the chat).
5. Open `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates` in a browser.
6. Find `"chat":{"id": ...}` in the response — that number is your **chat ID**.

## 2. Get an Apify API Token

1. Sign up at [apify.com](https://apify.com).
2. Subscribe to the **Starter plan** ($29/mo) for sufficient compute units.
3. Go to **Settings → Integrations** and copy your API token.

## 3. Find Event URLs

- **StubHub**: Search for "FIFA World Cup Final 2026" on [stubhub.com](https://www.stubhub.com) and copy the event page URL.
- **Gametime**: Search for "FIFA World Cup Final" on [gametime.co](https://gametime.co) and copy the event page URL.

## 4. Deploy to Railway

1. Sign up at [railway.app](https://railway.app).
2. **New Project → Deploy from GitHub repo** — connect your fork of this repository.
3. Add environment variables in the Railway service settings:

   | Variable | Description |
   |----------|-------------|
   | `APIFY_TOKEN` | Apify API token |
   | `TELEGRAM_BOT_TOKEN` | Telegram bot token from step 1 |
   | `TELEGRAM_CHAT_ID` | Chat ID from step 1 |
   | `PRICE_THRESHOLD` | Max price per ticket in USD (default: 6000) |
   | `MIN_QUANTITY` | Minimum tickets available (default: 2) |
   | `STUBHUB_EVENT_URL` | StubHub event URL from step 3 |
   | `GAMETIME_EVENT_URL` | Gametime event URL from step 3 |

4. Set the **cron schedule** in the Railway service settings: `*/15 * * * *` (every 15 minutes).
5. Railway will build the Dockerfile automatically. No additional config needed.

## 5. Verify

- Check Railway deployment logs for the first successful run.
- You should see: `Cycle complete: X listings fetched ... Y alerts sent`
- If any listings match your criteria, you'll receive a Telegram alert.

## Notes

- **SQLite persistence**: The database lives in the container's filesystem. Data resets on each redeploy. For persistent storage, consider Railway's volume mounts or migrate to Postgres in the future.
- **Cron behavior**: Railway starts the container on schedule, runs the command, and expects the process to exit. The monitor exits after each cycle — this is by design.
- **Local testing**: `cp .env.example .env`, fill in real values, then run `uv run python -m ticket_monitor.main`.
