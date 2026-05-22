# cogs/music_resume.py
import discord
from discord.ext import commands

class MusicResume(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="resume")
    async def resume(self, ctx):
        """Paused gaane ko wapas chalu karne ke liye."""
        if not ctx.voice_client or not ctx.voice_client.is_paused():
            return await ctx.send("❌ Koi gaana pause nahi hai bhai!")
        
        ctx.voice_client.resume()
        await ctx.send("▶️ Gaana wapas chalu ho gaya hai!")

async def setup(bot):
    await bot.add_cog(MusicResume(bot))