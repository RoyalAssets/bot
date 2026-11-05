
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

PREFIX = "."
TOKEN = os.getenv("Token")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix=PREFIX,
    intents=intents
)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


async def main():
    async with bot:
        await bot.load_extension("cogs.moderation")
        await bot.load_extension("cogs.utils")
        await bot.start(TOKEN)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
