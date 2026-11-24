import logging, discord
from discord.ext import commands
log=logging.getLogger(__name__)
class Utils(commands.Cog):
 def __init__(self,bot): self.bot=bot; self.db=bot.db; self.cfg={}; self.creating=set(); self.restored=False
 @commands.Cog.listener()
 async def on_ready(self):
  if self.restored:return
  for r in self.db.configs():
   g=self.bot.get_guild(int(r["guild"]))
   if g:
    cat=g.get_channel(int(r["category"])); j=g.get_channel(int(r["join_channel"])); ctl=g.get_channel(int(r["controls"]))
    if isinstance(cat,discord.CategoryChannel) and isinstance(j,discord.VoiceChannel) and isinstance(ctl,discord.TextChannel): self.cfg[g.id]={"category":cat.id,"join":j.id,"controls":ctl.id}
  for r in self.db.owners():
   g=self.bot.get_guild(int(r["guild"])); ch=g.get_channel(int(r["channel"])) if g else None
   if not isinstance(ch,discord.VoiceChannel):self.db.delete_owner(r["channel"])
   elif not ch.members:
    try:await ch.delete(reason="Stale temporary voice channel")
    except discord.HTTPException:log.exception("Cleanup failed")
    else:self.db.delete_owner(ch.id)
  self.restored=True
 @commands.command()
 @commands.guild_only()
 @commands.has_permissions(manage_messages=True)
 async def clear(self,ctx,n:int):
  if not 1<=n<=100:return await ctx.send("Choose 1–100.")
  await ctx.channel.purge(limit=n+1)
 @commands.command()
 @commands.guild_only()
 @commands.has_permissions(manage_nicknames=True)
 async def changenick(self,ctx,m:discord.Member,*,nickname):
  await m.edit(nick=nickname);await ctx.send("Nickname updated.")
 @commands.command()
 @commands.guild_only()
 @commands.has_permissions(manage_nicknames=True)
 async def resetnick(self,ctx,m:discord.Member):
  await m.edit(nick=None);await ctx.send("Nickname reset.")
 @commands.command()
 @commands.guild_only()
 @commands.has_permissions(manage_channels=True)
 async def createchannel(self,ctx,*,name):
  c=await ctx.guild.create_text_channel(name);await ctx.send(f"Created {c.mention}.")
 @commands.command()
 @commands.guild_only()
 @commands.has_permissions(manage_channels=True)
 async def renamechannel(self,ctx,*,name):
  await ctx.channel.edit(name=name);await ctx.send("Channel renamed.")
 @commands.command()
 @commands.guild_only()
 @commands.has_permissions(manage_channels=True)
 async def deletechannel(self,ctx,confirm:str=None):
  if confirm!="confirm":return await ctx.send("Run .deletechannel confirm to delete this channel.")
  await ctx.channel.delete()
 @commands.command()
 @commands.guild_only()
 @commands.has_permissions(manage_guild=True)
 async def setupvoice(self,ctx):
  old=self.cfg.get(ctx.guild.id)
  if old and all(ctx.guild.get_channel(old[k]) for k in ("category","join","controls")):return await ctx.send("Voice system already configured.")
  cat=await ctx.guild.create_category("Temporary Voice Channels")
  try:
   j=await ctx.guild.create_voice_channel("➕ Join to Create",category=cat);ctl=await ctx.guild.create_text_channel("🎛️・voice-controls",category=cat)
  except discord.HTTPException:
   await cat.delete(reason="Setup rollback");raise
  self.cfg[ctx.guild.id]={"category":cat.id,"join":j.id,"controls":ctl.id};self.db.save_config(ctx.guild.id,cat.id,j.id,ctl.id)
  p=ctx.clean_prefix;await ctl.send(f"Voice controls: {p}vlock / {p}vunlock / {p}limit 5 / {p}rename Name / {p}vckick @user / {p}vtransfer @user")
  await ctx.send("Voice system created.")
 @commands.Cog.listener()
 async def on_voice_state_update(self,m,b,a):
  cfg=self.cfg.get(m.guild.id)
  if not cfg:return
  if a.channel and a.channel.id==cfg["join"] and m.id not in self.creating:
   self.creating.add(m.id);ch=None
   try:
    cat=m.guild.get_channel(cfg["category"])
    if not cat:return
    ow={m.guild.default_role:discord.PermissionOverwrite(view_channel=True,connect=True),m:discord.PermissionOverwrite(view_channel=True,connect=True,manage_channels=True,move_members=True)}
    ch=await m.guild.create_voice_channel(f"{m.display_name}'s Channel",category=cat,overwrites=ow);self.db.set_owner(ch.id,m.guild.id,m.id);await m.move_to(ch)
   except discord.HTTPException:
    log.exception("Voice channel creation failed")
    if ch:
     self.db.delete_owner(ch.id)
     try:await ch.delete(reason="Setup failed")
     except discord.HTTPException:log.exception("Cleanup failed")
   finally:self.creating.discard(m.id)
  if b.channel:
   owner=self.db.owner(b.channel.id)
   if owner is None:return
   remaining=list(b.channel.members)
   if not remaining:
    try:await b.channel.delete(reason="Temporary channel empty")
    except discord.NotFound:pass
    except discord.HTTPException:log.exception("Delete failed");return
    self.db.delete_owner(b.channel.id)
   elif owner==m.id:
    new=remaining[0];self.db.set_owner(b.channel.id,m.guild.id,new.id)
    try:await b.channel.set_permissions(new,view_channel=True,connect=True,manage_channels=True,move_members=True);await b.channel.send(f"{new.mention} is now the owner.")
    except discord.HTTPException:log.exception("Transfer failed")
 async def owned(self,ctx):
  c=self.cfg.get(ctx.guild.id)
  if not c or ctx.channel.id!=c["controls"] or not ctx.author.voice:return None
  ch=ctx.author.voice.channel
  return ch if self.db.owner(ch.id)==ctx.author.id else None
 @commands.command()
 @commands.guild_only()
 async def vlock(self,ctx):
  c=await self.owned(ctx)
  if not c:return await ctx.send("Use controls while in your own temporary channel.")
  o=c.overwrites_for(ctx.guild.default_role);o.connect=False;await c.set_permissions(ctx.guild.default_role,overwrite=o);await ctx.send("Locked.")
 @commands.command()
 @commands.guild_only()
 async def vunlock(self,ctx):
  c=await self.owned(ctx)
  if not c:return await ctx.send("Use controls while in your own temporary channel.")
  o=c.overwrites_for(ctx.guild.default_role);o.connect=None;await c.set_permissions(ctx.guild.default_role,overwrite=o);await ctx.send("Unlocked.")
 @commands.command()
 @commands.guild_only()
 async def limit(self,ctx,n:int):
  c=await self.owned(ctx)
  if not c:return await ctx.send("You do not own this channel.")
  if not 0<=n<=99:return await ctx.send("Limit must be 0–99.")
  await c.edit(user_limit=n);await ctx.send(f"Limit set to {n}.")
 @commands.command()
 @commands.guild_only()
 async def rename(self,ctx,*,name):
  c=await self.owned(ctx)
  if not c:return await ctx.send("You do not own this channel.")
  await c.edit(name=name[:100]);await ctx.send("Renamed.")
 @commands.command()
 @commands.guild_only()
 async def vckick(self,ctx,m:discord.Member):
  c=await self.owned(ctx)
  if not c:return await ctx.send("You do not own this channel.")
  if m not in c.members or m.id==ctx.author.id:return await ctx.send("Choose another member in your channel.")
  await m.move_to(None);await ctx.send("Member disconnected.")
 @commands.command()
 @commands.guild_only()
 async def vtransfer(self,ctx,m:discord.Member):
  c=await self.owned(ctx)
  if not c:return await ctx.send("You do not own this channel.")
  if m not in c.members or m.id==ctx.author.id:return await ctx.send("Choose another member in your channel.")
  self.db.set_owner(c.id,ctx.guild.id,m.id);await c.set_permissions(m,view_channel=True,connect=True,manage_channels=True,move_members=True);await c.send(f"{m.mention} is now the owner.")
async def setup(bot):await bot.add_cog(Utils(bot))
