# RoyalAssets Discord bot

Requires Python 3.10+ and discord.py 2.x.

1. Install: `python -m pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and set `Token`.
3. Enable Message Content, Server Members and Voice States intents in the Discord Developer Portal.
4. Run `python main.py`.

SQLite is created in `data/bot.sqlite3`; back it up regularly. Prefix defaults to `.` and is configurable with `BOT_PREFIX`.

Voice: `.setupvoice`, `.vlock`, `.vunlock`, `.limit`, `.rename`, `.vckick`, `.vtransfer`.
Moderation: `.kick`, `.ban`, `.softban`, `.unban`, `.timeout`, `.untimeout`, `.r`, `.rr`, `.purge`, `.nick`, `.slowmode`, `.lock`, `.unlock`, `.warn`, `.warnings`, `.clearwarnings`.

Never commit `.env`; reset any exposed token. Grant only required Discord permissions and keep the bot role above managed roles.
