
import discord
from discord.ext import commands


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def changenick(self, ctx, member: discord.Member, *, nickname):
        await member.edit(nick=nickname)
        await ctx.send(f"Changed {member}'s nickname to {nickname}.")

    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def resetnick(self, ctx, member: discord.Member):
        await member.edit(nick=None)
        await ctx.send(f"Reset {member}'s nickname.")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def slowmode(self, ctx, seconds: int):
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"Set slowmode to {seconds} seconds.")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def lock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send("Channel locked.")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def unlock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send("Channel unlocked.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def renamechannel(self, ctx, *, new_name):
        await ctx.channel.edit(name=new_name)
        await ctx.send(f"Channel renamed to {new_name}.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def deletechannel(self, ctx):
        await ctx.channel.delete()
        await ctx.send("Channel deleted.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def createchannel(self, ctx, *, name):
        guild = ctx.guild
        await guild.create_text_channel(name)
        await ctx.send(f"Channel {name} created.")

async def setup(bot):
    await bot.add_cog(Utils(bot))
