# Discord Screenshot Bot

Silently captures specific Windows application windows and posts screenshots to Discord on a schedule. Supports on-demand `/screenshot` slash command.

**Requirements:** Windows 10/11, Python 3.11+

---

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create a Discord Webhook: Channel Settings → Integrations → Webhooks → New Webhook → Copy URL

3. *(Optional)* Create a bot at https://discord.com/developers/applications for the `/screenshot` command

4. Fill in `config.json`:

   | Field | Description |
   |---|---|
   | `window_titles` | List of window title substrings to capture |
   | `discord_webhook_url` | Webhook URL |
   | `discord_bot_token` | Bot token (optional, enables `/screenshot`) |
   | `schedule_interval_minutes` | How often to auto-capture |
   | `screenshot_quality` | JPEG quality 1–100 |
   | `command_guild_id` | Server ID for instant slash command sync (`null` = global, up to 1hr) |

5. **Run:** double-click `start_silent.vbs`  
   **Stop:** double-click `stop.bat`  
   **Logs:** `bot.log`

---

## Auto-start on boot

Press `Win+R` → `shell:startup` → copy `start_silent.vbs` into that folder.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Window not found | Make sure the app is open; title match is partial and case-insensitive |
| Black screenshot | Run both the target app and this bot as Administrator |
| `/screenshot` not showing | Set `command_guild_id` to your server ID for instant sync |
| Webhook fails | Check the URL in `config.json`; webhook may have been deleted |
