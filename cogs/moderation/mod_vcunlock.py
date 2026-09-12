import discord
from discord.ext import commands

import sqlite3

class ModVCUnlock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_name = "warnings.db"

    @commands.hybrid_command(name="vcunlock")
    @commands.has_permissions(manage_channels=True)
    async def vcunlock(self, ctx, channel: discord.VoiceChannel = None):
        """Voice channel ko instantly unlock karne ke liye (koi bhi wapas join kar payega)."""
        channel = channel or (ctx.author.voice.channel if ctx.author.voice else None)
        
        if not channel:
            return await ctx.send("❌ Bhai pehle kisi voice channel me join kar, ya fir command me channel mention/ID de (`!!vcunlock <channel_id>`)")

        overwrite = channel.overwrites_for(ctx.guild.default_role)
        
        if overwrite.connect is True or overwrite.connect is None:
            return await ctx.send(f"⚠️ `{channel.name}` pehle se hi unlocked hai!")

        original_connect = None
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.execute('SELECT connect_state FROM vc_states WHERE channel_id = ?', (str(channel.id),))
            row = cursor.fetchone()
            if row and row[0]:
                original_connect = row[0]
            
            # Clear it out from db once unlocked
            conn.execute('UPDATE vc_states SET connect_state = NULL WHERE channel_id = ?', (str(channel.id),))
            conn.commit()

        if original_connect == "True":
            overwrite.connect = True
        elif original_connect == "False":
            overwrite.connect = False
        else:
            overwrite.connect = None

        if overwrite.is_empty():
            await channel.set_permissions(ctx.guild.default_role, overwrite=None, reason=f"VC Unlocked by {ctx.author}")
        else:
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"VC Unlocked by {ctx.author}")
        
        await ctx.send(f"🔓 **{channel.name}** successfully unlock kar diya gaya hai! Ab sab join kar sakte hain.")

async def setup(bot):
    await bot.add_cog(ModVCUnlock(bot))
