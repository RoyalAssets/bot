import sqlite3
from pathlib import Path
class Database:
 def __init__(self,path="data/bot.sqlite3"):
  self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
  with self.connect() as c:
   c.execute("PRAGMA journal_mode=WAL")
   c.executescript("""CREATE TABLE IF NOT EXISTS warnings(id INTEGER PRIMARY KEY,guild TEXT,user TEXT,reason TEXT,moderator TEXT,moderator_name TEXT,created TEXT); CREATE INDEX IF NOT EXISTS warning_lookup ON warnings(guild,user,id); CREATE TABLE IF NOT EXISTS voice_config(guild TEXT PRIMARY KEY,category TEXT,join_channel TEXT,controls TEXT); CREATE TABLE IF NOT EXISTS voice_owner(channel TEXT PRIMARY KEY,guild TEXT,owner TEXT);""")
 def connect(self):
  c=sqlite3.connect(self.path,timeout=10); c.row_factory=sqlite3.Row; return c
 def add_warning(self,g,u,r,m,mn,t):
  with self.connect() as c: c.execute("INSERT INTO warnings(guild,user,reason,moderator,moderator_name,created) VALUES(?,?,?,?,?,?)",(str(g),str(u),r,str(m),mn,t))
 def warnings(self,g,u):
  with self.connect() as c: return [dict(x) for x in c.execute("SELECT * FROM warnings WHERE guild=? AND user=? ORDER BY id",(str(g),str(u)))]
 def clear_warnings(self,g,u):
  with self.connect() as c: return c.execute("DELETE FROM warnings WHERE guild=? AND user=?",(str(g),str(u))).rowcount
 def save_config(self,g,cat,j,ctl):
  with self.connect() as c: c.execute("INSERT INTO voice_config VALUES(?,?,?,?) ON CONFLICT(guild) DO UPDATE SET category=excluded.category,join_channel=excluded.join_channel,controls=excluded.controls",(str(g),str(cat),str(j),str(ctl)))
 def configs(self):
  with self.connect() as c: return [dict(x) for x in c.execute("SELECT * FROM voice_config")]
 def owners(self):
  with self.connect() as c: return [dict(x) for x in c.execute("SELECT * FROM voice_owner")]
 def owner(self,ch):
  with self.connect() as c:
   x=c.execute("SELECT owner FROM voice_owner WHERE channel=?",(str(ch),)).fetchone()
   return int(x["owner"]) if x else None
 def set_owner(self,ch,g,o):
  with self.connect() as c: c.execute("INSERT INTO voice_owner VALUES(?,?,?) ON CONFLICT(channel) DO UPDATE SET owner=excluded.owner,guild=excluded.guild",(str(ch),str(g),str(o)))
 def delete_owner(self,ch):
  with self.connect() as c: c.execute("DELETE FROM voice_owner WHERE channel=?",(str(ch),))
 def close(self): pass
