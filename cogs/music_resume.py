# cogs/music_resume.py
import discord
from discord.ext import commands

class MusicResume(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="resume")
    async def resume(self, ctx):
        """Paused gaane ko wapas shuru karne ke liye."""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Gaana wapas shuru ho gaya hai, enjoy karo!")
        else:
            await ctx.send("❌ Abhi koi gaana pause nahi hai bhai!")

async def setup(bot):
    await bot.add_cog(MusicResume(bot))