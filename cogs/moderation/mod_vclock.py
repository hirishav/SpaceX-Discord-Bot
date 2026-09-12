import discord
from discord.ext import commands

import sqlite3

class ModVCLock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_name = "warnings.db"
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS vc_states (
                    channel_id TEXT PRIMARY KEY,
                    connect_state TEXT,
                    view_state TEXT
                )
            ''')
            conn.commit()

    @commands.hybrid_command(name="vclock")
    @commands.has_permissions(manage_channels=True)
    async def vclock(self, ctx, channel: discord.VoiceChannel = None):
        """Voice channel ko instantly lock karne ke liye (koi aur join nahi kar payega)."""
        channel = channel or (ctx.author.voice.channel if ctx.author.voice else None)
        
        if not channel:
            return await ctx.send("❌ Bhai pehle kisi voice channel me join kar, ya fir command me channel mention/ID de (`!!vclock <channel_id>`)")

        overwrite = channel.overwrites_for(ctx.guild.default_role)
        
        if overwrite.connect is False:
            return await ctx.send(f"⚠️ `{channel.name}` pehle se hi locked hai!")

        current_connect = str(overwrite.connect)
        with sqlite3.connect(self.db_name) as conn:
            conn.execute('''
                INSERT INTO vc_states (channel_id, connect_state)
                VALUES (?, ?)
                ON CONFLICT(channel_id) DO UPDATE SET connect_state = ?
            ''', (str(channel.id), current_connect, current_connect))
            conn.commit()

        overwrite.connect = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"VC Locked by {ctx.author}")
        
        await ctx.send(f"🔒 **{channel.name}** successfully lock kar diya gaya hai! Ab yahan aur koi join nahi kar payega.")

async def setup(bot):
    await bot.add_cog(ModVCLock(bot))
