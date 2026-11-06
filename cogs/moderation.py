
import discord
from discord.ext import commands
from datetime import timedelta
import json
import os


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings_file = "warnings.json"
        self.warnings = self.load_warnings()

    def load_warnings(self):
        if not os.path.exists(self.warnings_file):
            return {}

        try:
            with open(self.warnings_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError):
            return {}

    def save_warnings(self):
        with open(self.warnings_file, "w", encoding="utf-8") as file:
            json.dump(self.warnings, file, indent=4)

    def embed(self, title, description, color=discord.Color.blurple()):
        return discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=discord.utils.utcnow()
        )

    async def check_hierarchy(self, ctx, member):
        if member.id == ctx.author.id:
            await ctx.send("You cannot moderate yourself.")
            return False

        if member.id == ctx.guild.owner_id:
            await ctx.send("You cannot moderate the server owner.")
            return False

        if ctx.author.id != ctx.guild.owner_id:
            if member.top_role >= ctx.author.top_role:
                await ctx.send("You cannot moderate someone with an equal or higher role.")
                return False

        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send("My highest role must be above the target's highest role.")
            return False

        return True

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        if not await self.check_hierarchy(ctx, member):
            return

        await member.kick(reason=f"{ctx.author}: {reason}")

        embed = self.embed(
            "Member Kicked",
            f"**Member:** {member.mention}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
            discord.Color.orange()
        )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        if not await self.check_hierarchy(ctx, member):
            return

        await member.ban(reason=f"{ctx.author}: {reason}")

        embed = self.embed(
            "Member Banned",
            f"**Member:** {member}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
            discord.Color.red()
        )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def softban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        if not await self.check_hierarchy(ctx, member):
            return

        await member.ban(reason=f"Softban by {ctx.author}: {reason}", delete_message_days=1)
        await ctx.guild.unban(member, reason=f"Softban by {ctx.author}: {reason}")

        await ctx.send(embed=self.embed(
            "Member Softbanned",
            f"**Member:** {member}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
            discord.Color.orange()
        ))

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user: discord.User, *, reason="No reason provided"):
        await ctx.guild.unban(user, reason=f"{ctx.author}: {reason}")

        await ctx.send(embed=self.embed(
            "Member Unbanned",
            f"**User:** {user}\n**Moderator:** {ctx.author.mention}\n**Reason:** {reason}",
            discord.Color.green()
        ))

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, minutes: int, *, reason="No reason provided"):
        if not 1 <= minutes <= 40320:
            return await ctx.send("Timeout must be between 1 and 40320 minutes.")

        if not await self.check_hierarchy(ctx, member):
            return

        await member.timeout(
            timedelta(minutes=minutes),
            reason=f"{ctx.author}: {reason}"
        )

        await ctx.send(embed=self.embed(
            "Member Timed Out",
            f"**Member:** {member.mention}\n**Duration:** {minutes} minutes\n**Reason:** {reason}",
            discord.Color.orange()
        ))

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member, *, reason="No reason provided"):
        if not await self.check_hierarchy(ctx, member):
            return

        await member.timeout(None, reason=f"{ctx.author}: {reason}")

        await ctx.send(embed=self.embed(
            "Timeout Removed",
            f"**Member:** {member.mention}\n**Reason:** {reason}",
            discord.Color.green()
        ))

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def r(self, ctx, member: discord.Member, role: discord.Role):
        if not await self.check_hierarchy(ctx, member):
            return

        if role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("You cannot assign a role equal to or higher than your highest role.")

        if role >= ctx.guild.me.top_role:
            return await ctx.send("My highest role must be above that role.")

        await member.add_roles(role, reason=f"Role added by {ctx.author}")

        await ctx.send(embed=self.embed(
            "Role Added",
            f"**Role:** {role.mention}\n**Member:** {member.mention}",
            discord.Color.green()
        ))

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    async def rr(self, ctx, member: discord.Member, role: discord.Role):
        if not await self.check_hierarchy(ctx, member):
            return

        if role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("You cannot remove a role equal to or higher than your highest role.")

        if role >= ctx.guild.me.top_role:
            return await ctx.send("My highest role must be below your target role.")

        await member.remove_roles(role, reason=f"Role removed by {ctx.author}")

        await ctx.send(embed=self.embed(
            "Role Removed",
            f"**Role:** {role.mention}\n**Member:** {member.mention}",
            discord.Color.orange()
        ))

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        if not 1 <= amount <= 100:
            return await ctx.send("Choose an amount between 1 and 100.")

        deleted = await ctx.channel.purge(limit=amount + 1)

        msg = await ctx.send(f"Deleted **{len(deleted) - 1}** messages.")
        await msg.delete(delay=4)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_nicknames=True)
    async def nick(self, ctx, member: discord.Member, *, nickname=None):
        if not await self.check_hierarchy(ctx, member):
            return

        await member.edit(nick=nickname, reason=f"Nickname changed by {ctx.author}")

        await ctx.send(embed=self.embed(
            "Nickname Updated",
            f"**Member:** {member.mention}\n**Nickname:** {nickname or 'Reset'}",
            discord.Color.green()
        ))

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def slowmode(self, ctx, seconds: int):
        if not 0 <= seconds <= 21600:
            return await ctx.send("Slowmode must be between 0 and 21600 seconds.")

        await ctx.channel.edit(slowmode_delay=seconds)

        await ctx.send(embed=self.embed(
            "Slowmode Updated",
            f"Slowmode set to **{seconds} seconds**.",
            discord.Color.green()
        ))

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        await ctx.channel.set_permissions(
            ctx.guild.default_role,
            send_messages=False,
            reason=f"Locked by {ctx.author}"
        )

        await ctx.send(embed=self.embed(
            "Channel Locked",
            f"Locked by {ctx.author.mention}.",
            discord.Color.red()
        ))

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        await ctx.channel.set_permissions(
            ctx.guild.default_role,
            send_messages=None,
            reason=f"Unlocked by {ctx.author}"
        )

        await ctx.send(embed=self.embed(
            "Channel Unlocked",
            f"Unlocked by {ctx.author.mention}.",
            discord.Color.green()
        ))

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason="No reason provided"):
        if not await self.check_hierarchy(ctx, member):
            return

        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        self.warnings.setdefault(guild_id, {})
        self.warnings[guild_id].setdefault(user_id, [])

        self.warnings[guild_id][user_id].append({
            "reason": reason,
            "moderator": str(ctx.author),
            "timestamp": discord.utils.utcnow().isoformat()
        })

        self.save_warnings()

        await ctx.send(embed=self.embed(
            "Member Warned",
            f"**Member:** {member.mention}\n**Reason:** {reason}\n**Total Warnings:** {len(self.warnings[guild_id][user_id])}",
            discord.Color.orange()
        ))

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def warnings(self, ctx, member: discord.Member):
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        user_warnings = self.warnings.get(guild_id, {}).get(user_id, [])

        if not user_warnings:
            return await ctx.send(f"{member} has no warnings.")

        description = "\n\n".join(
            f"**{i}.** {warning['reason']}\n"
            f"Moderator: {warning['moderator']}"
            for i, warning in enumerate(user_warnings, 1)
        )

        embed = self.embed(
            f"Warnings for {member}",
            description,
            discord.Color.orange()
        )

        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def clearwarnings(self, ctx, member: discord.Member):
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)

        self.warnings.get(guild_id, {}).pop(user_id, None)
        self.save_warnings()

        await ctx.send(embed=self.embed(
            "Warnings Cleared",
            f"Cleared all warnings for {member.mention}.",
            discord.Color.green()
        ))

    @commands.command()
    @commands.guild_only()
    async def userinfo(self, ctx, member: discord.Member = None):
        member = member or ctx.author

        embed = discord.Embed(
            title=f"User Information - {member}",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Account Created", value=discord.utils.format_dt(member.created_at, "R"), inline=True)
        embed.add_field(name="Joined Server", value=discord.utils.format_dt(member.joined_at, "R") if member.joined_at else "Unknown", inline=True)
        embed.add_field(name="Top Role", value=member.top_role.mention, inline=True)
        embed.add_field(name="Bot", value="Yes" if member.bot else "No", inline=True)

        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def roleinfo(self, ctx, role: discord.Role):
        embed = self.embed(
            f"Role Information - {role.name}",
            f"**ID:** {role.id}\n"
            f"**Color:** {role.color}\n"
            f"**Members:** {len(role.members)}\n"
            f"**Position:** {role.position}\n"
            f"**Mentionable:** {role.mentionable}\n"
            f"**Hoisted:** {role.hoist}",
            role.color if role.color.value else discord.Color.blurple()
        )

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.MissingPermissions):
            return await ctx.send("You don't have permission to use this command.")

        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(f"Missing argument: `{error.param.name}`.")

        if isinstance(error, commands.BadArgument):
            return await ctx.send("Invalid argument. Check the command usage.")

        if isinstance(error, commands.NoPrivateMessage):
            return await ctx.send("This command can only be used in a server.")

        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(f"Try again in {error.retry_after:.1f} seconds.")

        if isinstance(error, discord.Forbidden):
            return await ctx.send("I don't have permission to perform that action.")

        if isinstance(error, discord.NotFound):
            return await ctx.send("The requested user or resource was not found.")

        if isinstance(error, commands.CommandInvokeError):
            original = error.original

            if isinstance(original, discord.Forbidden):
                return await ctx.send("I don't have permission to perform that action.")

            if isinstance(original, discord.NotFound):
                return await ctx.send("The requested user or resource was not found.")

        raise error


async def setup(bot):
    await bot.add_cog(Moderation(bot))
