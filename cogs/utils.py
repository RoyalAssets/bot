
import discord
from discord.ext import commands


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_config = {}
        self.voice_owners = {}

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
        if not 0 <= seconds <= 21600:
            return await ctx.send("Slowmode must be between 0 and 21600 seconds.")

        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"Set slowmode to {seconds} seconds.")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def lock(self, ctx):
        await ctx.channel.set_permissions(
            ctx.guild.default_role,
            send_messages=False
        )
        await ctx.send("Channel locked.")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def unlock(self, ctx):
        await ctx.channel.set_permissions(
            ctx.guild.default_role,
            send_messages=True
        )
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

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def createchannel(self, ctx, *, name):
        await ctx.guild.create_text_channel(name)
        await ctx.send(f"Channel {name} created.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def setupvoice(self, ctx):
        guild = ctx.guild

        category = await guild.create_category(
            "Temporary Voice Channels"
        )

        join_channel = await guild.create_voice_channel(
            "➕ Join to Create",
            category=category
        )

        controls = await guild.create_text_channel(
            "🎛️・voice-controls",
            category=category
        )

        self.voice_config[guild.id] = {
            "join": join_channel.id,
            "controls": controls.id
        }

        await controls.send(
            "**TEMPORARY VOICE CHANNEL CONTROLS**\n\n"
            "`!vlock` - Lock your voice channel\n"
            "`!vunlock` - Unlock your voice channel\n"
            "`!limit <number>` - Set user limit\n"
            "`!rename <name>` - Rename your voice channel\n"
            "`!vckick @user` - Kick someone from your voice channel"
        )

        await ctx.send("Voice system successfully created!")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        guild = member.guild
        config = self.voice_config.get(guild.id)

        if not config:
            return

        if after.channel and after.channel.id == config["join"]:
            category = after.channel.category

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=True,
                    connect=True
                ),
                member: discord.PermissionOverwrite(
                    view_channel=True,
                    connect=True,
                    manage_channels=True,
                    move_members=True
                )
            }

            channel = await guild.create_voice_channel(
                f"{member.display_name}'s Channel",
                category=category,
                overwrites=overwrites
            )

            self.voice_owners[channel.id] = member.id
            await member.move_to(channel)

        if before.channel and before.channel.id in self.voice_owners:
            if len(before.channel.members) == 0:
                self.voice_owners.pop(before.channel.id, None)
                await before.channel.delete()

    async def get_voice_channel(self, ctx):
        config = self.voice_config.get(ctx.guild.id)

        if not config:
            return None

        if ctx.channel.id != config["controls"]:
            return None

        if not ctx.author.voice:
            return None

        channel = ctx.author.voice.channel

        if self.voice_owners.get(channel.id) != ctx.author.id:
            return None

        return channel

    @commands.command()
    async def vlock(self, ctx):
        channel = await self.get_voice_channel(ctx)

        if not channel:
            return await ctx.send("You don't own a temporary voice channel.")

        await channel.set_permissions(
            ctx.guild.default_role,
            connect=False
        )

        await ctx.send("Voice channel locked.")

    @commands.command()
    async def vunlock(self, ctx):
        channel = await self.get_voice_channel(ctx)

        if not channel:
            return await ctx.send("You don't own a temporary voice channel.")

        await channel.set_permissions(
            ctx.guild.default_role,
            overwrite=None
        )

        await ctx.send("Voice channel unlocked.")

    @commands.command()
    async def limit(self, ctx, amount: int):
        channel = await self.get_voice_channel(ctx)

        if not channel:
            return await ctx.send("You don't own a temporary voice channel.")

        if not 0 <= amount <= 99:
            return await ctx.send("Limit must be between 0 and 99.")

        await channel.edit(user_limit=amount)
        await ctx.send(f"Voice channel limit set to {amount}.")

    @commands.command()
    async def rename(self, ctx, *, name):
        channel = await self.get_voice_channel(ctx)

        if not channel:
            return await ctx.send("You don't own a temporary voice channel.")

        await channel.edit(name=name)
        await ctx.send(f"Voice channel renamed to {name}.")

    @commands.command()
    async def vckick(self, ctx, member: discord.Member):
        channel = await self.get_voice_channel(ctx)

        if not channel:
            return await ctx.send("You don't own a temporary voice channel.")

        if member not in channel.members:
            return await ctx.send("That member isn't in your voice channel.")

        if member.id == ctx.author.id:
            return await ctx.send("You can't kick yourself.")

        await member.move_to(None)
        await ctx.send(f"Kicked {member.display_name} from your voice channel.")


async def setup(bot):
    await bot.add_cog(Utils(bot))
