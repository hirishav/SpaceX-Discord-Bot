# cogs/music_pause.py
import discord
from discord.ext import commands

class MusicPause(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="pause")
    async def pause(self, ctx):
        """Chal rahe gaane ko temporary pause karne ke liye."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Gaana pause kar diya hai bhai! Wapas shuru karne ke liye `!!resume` chalao.")
        else:
            await ctx.send("❌ Abhi koi gaana chal hi nahi raha hai jise pause karun!")

async def setup(bot):
    await bot.add_cog(MusicPause(bot))