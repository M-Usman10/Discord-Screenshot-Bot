# Discord Screenshot Bot

Silently captures specific application windows and posts screenshots to a Discord channel on a fixed schedule. Also supports an on-demand `/screenshot` slash command from Discord.

---

## Requirements

- **Windows 10 or 11** (uses Windows-only APIs)
- **Python 3.11 or newer** — download from https://www.python.org/downloads/
  - During install, check **"Add Python to PATH"**

---

## Setup (step-by-step)

### 1 — Install dependencies

Open **Command Prompt** (search "cmd" in the Start menu) and run:

```
cd path\to\Discord-Screenshot-Bot
pip install -r requirements.txt
```

If `pip` is not found, try `python -m pip install -r requirements.txt`.

---

### 2 — Create a Discord Webhook

A webhook lets the bot post screenshots to a channel without a full bot account.

1. Open Discord and go to the channel where you want screenshots posted.
2. Click the **gear icon** (Edit Channel) → **Integrations** → **Webhooks** → **New Webhook**.
3. Give it a name (e.g. "Screenshot Bot"), then click **Copy Webhook URL**.
4. Paste that URL into `config.json` as `discord_webhook_url`.

---

### 3 — (Optional) Create a Discord Bot for the `/screenshot` command

Skip this if you only want scheduled screenshots and don't need the slash command.

1. Go to https://discord.com/developers/applications and click **New Application**.
2. Name it (e.g. "Screenshot Bot"), then go to the **Bot** tab.
3. Click **Reset Token**, copy the token, and paste it into `config.json` as `discord_bot_token`.
4. Under **Privileged Gateway Intents**, no extra intents are needed — leave them off.
5. Go to **OAuth2 → URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: (none required)
   - Copy the generated URL and open it in your browser to invite the bot to your server.

---

### 4 — Edit config.json

Open `config.json` in Notepad and fill in your values:

```json
{
  "window_titles": ["DeepCharts", "Bookmap"],
  "discord_webhook_url": "https://discord.com/api/webhooks/...",
  "discord_bot_token": "YOUR_BOT_TOKEN_HERE",
  "schedule_interval_minutes": 5,
  "screenshot_quality": 95,
  "include_timestamp": true,
  "command_guild_id": null
}
```

| Field | Description |
|---|---|
| `window_titles` | List of window title substrings to capture (case-insensitive partial match) |
| `discord_webhook_url` | Webhook URL from Step 2 |
| `discord_bot_token` | Bot token from Step 3 (leave placeholder to disable slash command) |
| `schedule_interval_minutes` | How often to auto-capture, in minutes |
| `screenshot_quality` | JPEG quality 1–100 (95 is a good balance) |
| `include_timestamp` | Add a timestamp to each Discord message |
| `command_guild_id` | Your Discord server ID for instant slash command registration (right-click server icon → Copy Server ID). Leave `null` to register globally (takes up to 1 hour). |

---

### 5 — Run the bot

Double-click `start.bat`, or run in Command Prompt:

```
python main.py
```

The bot will:
- Run an immediate capture on startup
- Post screenshots on the configured schedule
- Respond to `/screenshot` in Discord (if bot token is set)
- Write a `bot.log` file for troubleshooting

---

## Running silently on Windows startup (no window)

### Option A — Task Scheduler (recommended)

1. Search for **Task Scheduler** in the Start menu.
2. Click **Create Basic Task** → give it a name → **Next**.
3. Trigger: **When the computer starts** → **Next**.
4. Action: **Start a program** → **Next**.
5. Program: `pythonw.exe` (use full path, e.g. `C:\Python311\pythonw.exe`)
6. Arguments: `"C:\path\to\Discord-Screenshot-Bot\main.py"`
7. Finish, then right-click the task → **Properties** → **Run whether user is logged on or not**.

Using `pythonw.exe` instead of `python.exe` suppresses the console window entirely.

### Option B — Startup folder shortcut

1. Press `Win + R`, type `shell:startup`, press Enter.
2. Copy `start_silent.vbs` from the bot folder into that startup folder.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "Window not found: DeepCharts" | Make sure the application is open. The title match is partial and case-insensitive — check the exact window title in the taskbar. |
| Screenshot is black / blank | Some DX12/OpenGL apps block GDI capture. Try running the target app as Administrator, or run this script as Administrator. |
| Minimized window not captured | The script auto-restores minimized windows briefly, then re-minimizes them. If this causes issues, keep the windows open on-screen. |
| Webhook posts fail | Double-check the webhook URL in config.json. Make sure the Discord channel still has the webhook (it can be deleted from Discord). |
| `/screenshot` command not appearing | If `command_guild_id` is null, global sync takes up to 1 hour. Set it to your server ID for instant registration. |
| Bot token invalid | Re-generate the token in the Discord Developer Portal (Bot tab → Reset Token). |

Check `bot.log` in the bot folder for detailed error messages.

---

## File overview

```
Discord-Screenshot-Bot/
├── bot/
│   ├── __init__.py      — package exports
│   ├── capture.py       — win32 window finding + PrintWindow capture
│   ├── webhook.py       — Discord webhook posting + capture orchestration
│   ├── scheduler.py     — fixed-interval schedule thread
│   └── discord_bot.py   — ScreenshotBot class + /screenshot slash command
├── main.py              — entry point (config, wiring, startup)
├── config.json          — all user-editable settings (not committed to git)
├── requirements.txt     — Python package dependencies
├── start.bat            — run with visible console (for testing)
├── start_silent.vbs     — run silently via pythonw.exe (for production)
├── README.md            — this file
└── bot.log              — created at runtime, contains logs
```
