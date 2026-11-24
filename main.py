import asyncio, logging, os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from database import Database
load_dotenv()
TOKEN=os.getenv("Token")
if not TOKEN: raise RuntimeError("Set Token in your local .env file.")
logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO").upper(),format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log=logging.getLogger("bot")
intents=discord.Intents.default(); intents.message_content=True; intents.members=True; intents.voice_states=True
bot=commands.Bot(command_prefix=os.getenv("BOT_PREFIX","."),intents=intents)
bot.db=Database(os.getenv("DATABASE_PATH","data/bot.sqlite3"))
@bot.event
async def on_ready(): log.info("Logged in as %s (%s)",bot.user,bot.user.id)
@bot.event
async def on_command_error(ctx,error):
    if isinstance(error,commands.CommandNotFound): return
    if isinstance(error,commands.MissingPermissions): return await ctx.send("You do not have permission.")
    if isinstance(error,commands.BotMissingPermissions): return await ctx.send("The bot is missing a required permission.")
    if isinstance(error,commands.NoPrivateMessage): return await ctx.send("Server-only command.")
    if isinstance(error,commands.MissingRequiredArgument): return await ctx.send(f"Missing argument: {error.param.name}")
    if isinstance(error,commands.BadArgument): return await ctx.send("Invalid argument.")
    original=getattr(error,"original",error)
    if isinstance(original,discord.Forbidden): return await ctx.send("Discord denied this action; check permissions and role hierarchy.")
    if isinstance(original,discord.NotFound): return await ctx.send("That Discord resource no longer exists.")
    log.error("Command error in %s",ctx.command,exc_info=(type(error),error,error.__traceback__))
    await ctx.send("Unexpected error; it has been logged.")
async def main():
    try:
        async with bot:
            await bot.load_extension("cogs.moderation_fixed")
            await bot.load_extension("cogs.utils_fixed")
            await bot.start(TOKEN)
    finally: bot.db.close()
if __name__=="__main__": asyncio.run(main())
