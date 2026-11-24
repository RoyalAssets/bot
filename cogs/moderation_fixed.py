import discord
from discord.ext import commands
from datetime import timedelta
class Moderation(commands.Cog):
 def __init__(self,bot):self.db=bot.db
 def emb(self,t,d,c=None):return discord.Embed(title=t,description=d,color=c or discord.Color.blurple(),timestamp=discord.utils.utcnow())
 async def hierarchy(self,ctx,m):
  if m.id in (ctx.author.id,ctx.guild.owner_id):await ctx.send("Cannot moderate that member.");return False
  if ctx.author.id!=ctx.guild.owner_id and m.top_role>=ctx.author.top_role:await ctx.send("Target role is equal to or above yours.");return False
  if not ctx.guild.me or m.top_role>=ctx.guild.me.top_role:await ctx.send("My highest role must be above target.");return False
  return True
 @commands.command()
 @commands.guild_only()
 @commands.has_permissions(kick_members=True)
 async def kick(self,ctx,m:discord.Member,*,reason="No reason provided"):
  if not await self.hierarchy(ctx,m):return
  await m.kick(reason=f"{ctx.author}: {reason}");await ctx.send(embed=self.emb("Kicked",f"{m} — {reason}"))
 @commands.command()
 @commands.guild_only()
 @commands.has_permissions(ban_members=True)
 async def ban(self,ctx,m:discord.Member,*,reason="No reason provided"):
  if not await self.hierarchy(ctx,m):return
  await m.ban(reason=f"{ctx.author}: {reason}");await ctx.send(embed=self.emb("Banned",f"{m} — {reason}",discord.Color.red()))
 @commands.command()
 @commands.guild_only()
 @commands.has_permissions(ban_members=True)
 async def softban(self,ctx,m:discord.Member,*,reason="No reason provided"):
  if not await self.hierarchy(ctx,m):return
  await m.ban(reason=f"Softban by {ctx.author}: {reason}",delete_message_seconds=86400);await ctx.guild.unban(m,reason=f"Softban by {ctx.author}: {reason}");await ctx.send("Softban completed.")
 @commands.command()
 @commands.guild_only()
 @commands.has_permissions(ban_members=True)
 async def unban(self,ctx,u:discord.User,*,reason="No reason provided"):
  try:await ctx.guild.unban(u,reason=f"{ctx.author}: {reason}")
  except discord.NotFound:return await ctx.send("User is not banned.")
  await ctx.send(f"Unbanned {u}.")
 @commands.command()
 @commands.guild_only()
 @commands.has_permissions(moderate_members=True)
 async def timeout(self,ctx,m:discord.Member,n:int,*,reason="No reason provided"):
  if not 1<=n<=40320:return await ctx.send("Duration must be 1–40320 minutes.")
  if not await self.hierarchy(ctx,m):return
  await m.timeout(timedelta(minutes=n),reason=f"{ctx.author}: {reason}");await ctx.send(f"Timed out {m} for {n} minutes.")
 @commands.command()
 @commands.guild_only()
 @commands.has_permissions(moderate_members=True)
 async def untimeout(self,ctx,m:discord.Member):
  if not await self.hierarchy(ctx,m):return
  await m.timeout(None,reason=f"By {ctx.author}");await ctx.send("Timeout removed.")
 @commands.command()
 @commands.guild_only()
 @commands.has_permissions(manage_roles=True)
 async def r(self,ctx,m:discord.Member,r:discord.Role):
  if not await self.hierarchy(ctx,m):return
  if r>=ctx.guild.me.top_role or (ctx.author.id!=ctx.guild.owner_id and r>=ctx.author.top_role):return await ctx.send("Role hierarchy prevents this.")
  await m.add_roles(r,reason=f"By {ctx.author}");await ctx.send(f"Added {r.mention}.")
 @commands.command()
 @commands.guild_only()
 @commands.has_permissions(manage_roles=True)
 async def rr(self,ctx,m:discord.Member,r:discord.Role):
  if not await self.hierarchy(ctx,m):return
  if r>=ctx.guild.me.top_role or (ctx.author.id!=ctx.guild.owner_id and r>=ctx.author.top_role):return await ctx.send("Role hierarchy prevents this.")
  await m.remove_roles(r,reason=f"By {ctx.author}");await ctx.send(f"Removed {r.mention}.")
 @commands.command()
 @commands.guild_only()
 @commands.has_permissions(manage_messages=True)
 async def purge(self,ctx,n:int):
  if not 1<=n<=100:return await ctx.send("Choose 1–100.")
  await ctx.channel.purge(limit=n+1)
 @commands.command()
 @commands.guild_only()
 @commands.has_permissions(manage_nicknames=True)
 async def nick(self,ctx,m:discord.Member,*,nickname=None):
  if not await self.hierarchy(ctx,m):return
  await m.edit(nick=nickname,reason=f"By {ctx.author}");await ctx.send("Nickname updated.")
 @commands.command()
 @commands.guild_only()
 @commands.has_permissions(manage_messages=True)
 async def slowmode(self,ctx,n:int):
  if not 0<=n<=21600:return await ctx.send("Slowmode must be 0–21600.")
  await ctx.channel.edit(slowmode_delay=n);await ctx.send(f"Slowmode {n}s.")
 @commands.command()
 @commands.guild_only()
 @commands.has_permissions(manage_channels=True)
 async def lock(self,ctx):
  o=ctx.channel.overwrites_for(ctx.guild.default_role);o.send_messages=False;await ctx.channel.set_permissions(ctx.guild.default_role,overwrite=o);await ctx.send("Locked.")
 @commands.command()
 @commands.guild_only()
 @commands.has_permissions(manage_channels=True)
 async def unlock(self,ctx):
  o=ctx.channel.overwrites_for(ctx.guild.default_role);o.send_messages=None;await ctx.channel.set_permissions(ctx.guild.default_role,overwrite=o);await ctx.send("Unlocked.")
 @commands.command()
 @commands.guild_only()
 @commands.has_permissions(manage_messages=True)
 async def warn(self,ctx,m:discord.Member,*,reason="No reason provided"):
  if not await self.hierarchy(ctx,m):return
  self.db.add_warning(ctx.guild.id,m.id,reason,ctx.author.id,str(ctx.author),discord.utils.utcnow().isoformat());await ctx.send(f"Warned {m}. Total: {len(self.db.warnings(ctx.guild.id,m.id))}.")
 @commands.command()
 @commands.guild_only()
 @commands.has_permissions(manage_messages=True)
 async def warnings(self,ctx,m:discord.Member):
  rows=self.db.warnings(ctx.guild.id,m.id)
  if not rows:return await ctx.send("No warnings.")
  batch=[];pages=[];size=0
  for i,w in enumerate(rows,1):
   line=f"**{i}.** {discord.utils.escape_markdown(w['reason'])}\nModerator: {discord.utils.escape_markdown(w['moderator_name'])}"
   if batch and size+len(line)>3800:pages.append("\n\n".join(batch));batch=[];size=0
   batch.append(line);size+=len(line)+2
  if batch:pages.append("\n\n".join(batch))
  for i,p in enumerate(pages,1):await ctx.send(embed=self.emb(f"Warnings for {m} ({i}/{len(pages)})",p,discord.Color.orange()))
 @commands.command()
 @commands.guild_only()
 @commands.has_permissions(manage_messages=True)
 async def clearwarnings(self,ctx,m:discord.Member,confirm:str=None):
  if confirm!="confirm":return await ctx.send(f"Confirm with {ctx.clean_prefix}clearwarnings {m.id} confirm.")
  n=self.db.clear_warnings(ctx.guild.id,m.id);await ctx.send(f"Removed {n} warning(s).")
 @commands.command()
 @commands.guild_only()
 async def userinfo(self,ctx,m:discord.Member=None):
  m=m or ctx.author;e=self.emb(f"User — {m}",f"ID: {m.id}\nCreated: {discord.utils.format_dt(m.created_at,'R')}\nJoined: {discord.utils.format_dt(m.joined_at,'R') if m.joined_at else 'Unknown'}\nTop role: {m.top_role.mention}\nBot: {m.bot}");e.set_thumbnail(url=m.display_avatar.url);await ctx.send(embed=e)
 @commands.command()
 @commands.guild_only()
 async def roleinfo(self,ctx,r:discord.Role):
  await ctx.send(embed=self.emb(f"Role — {r.name}",f"ID: {r.id}\nMembers: {len(r.members)}\nPosition: {r.position}\nMentionable: {r.mentionable}"))
async def setup(bot):await bot.add_cog(Moderation(bot))
