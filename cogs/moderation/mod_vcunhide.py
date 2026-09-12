import discord
from discord.ext import commands

import sqlite3

class ModVCUnhide(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_name = "warnings.db"

    @commands.hybrid_command(name="vcunhide")
    @commands.has_permissions(manage_channels=True)
    async def vcunhide(self, ctx, channel: discord.VoiceChannel = None):
        """Voice channel ko instantly unhide karne ke liye (wapas sabko dikhne lagega)."""
        channel = channel or (ctx.author.voice.channel if ctx.author.voice else None)
        
        if not channel:
            return await ctx.send("❌ Bhai pehle kisi voice channel me join kar, ya fir command me channel mention/ID de (`!!vcunhide <channel_id>`)")

        overwrite = channel.overwrites_for(ctx.guild.default_role)
        
        if overwrite.view_channel is True or overwrite.view_channel is None:
            return await ctx.send(f"⚠️ `{channel.name}` pehle se hi sabko dikh raha hai!")

        original_view = None
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.execute('SELECT view_state FROM vc_states WHERE channel_id = ?', (str(channel.id),))
            row = cursor.fetchone()
            if row and row[0]:
                original_view = row[0]
            
            # Clear it out from db once unhidden
            conn.execute('UPDATE vc_states SET view_state = NULL WHERE channel_id = ?', (str(channel.id),))
            conn.commit()

        if original_view == "True":
            overwrite.view_channel = True
        elif original_view == "False":
            # This shouldn't logically happen because if it was False before hiding, it was already hidden
            # But just in case, we restore exactly what was there.
            overwrite.view_channel = False
        else:
            overwrite.view_channel = None

        if overwrite.is_empty():
            await channel.set_permissions(ctx.guild.default_role, overwrite=None, reason=f"VC Unhidden by {ctx.author}")
        else:
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"VC Unhidden by {ctx.author}")
        
        await ctx.send(f"👁️ **{channel.name}** successfully unhide kar diya gaya hai! Ab ye wapas sabko dikhega.")

async def setup(bot):
    await bot.add_cog(ModVCUnhide(bot))
