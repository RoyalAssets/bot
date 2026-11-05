
import discord
from discord.ext import commands


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        await member.kick(reason=reason)
        await ctx.send(f"{member} has been kicked. Reason: {reason}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        await member.ban(reason=reason)
        await ctx.send(f"{member} has been banned. Reason: {reason}")

    @commands.command()
    @commands.has_permissions(unban_members=True)
    async def unban(self, ctx, user: discord.User, *, reason="No reason provided"):
        await ctx.guild.unban(user, reason=reason)
        await ctx.send(f"{user} has been unbanned. Reason: {reason}")

    @commands.command()
    @commands.has_permissions(mute_members=True)
    async def mute(self, ctx, member: discord.Member, *, reason="No reason provided"):
        await member.edit(mute=True, reason=reason)
        await ctx.send(f"{member} has been muted. Reason: {reason}")

    @commands.command()
    @commands.has_permissions(unmute_members=True)
    async def unmute(self, ctx, member: discord.Member, *, reason="No reason provided"):
        await member.edit(mute=False, reason=reason)
        await ctx.send(f"{member} has been unmuted. Reason: {reason}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def addrole(self, ctx, member: discord.Member, role: discord.Role):
        await member.add_roles(role)
        await ctx.send(f"{role} has been added to {member}.")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def removerole(self, ctx, member: discord.Member, role: discord.Role):
        await member.remove_roles(role)
        await ctx.send(f"{role} has been removed from {member}.")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
