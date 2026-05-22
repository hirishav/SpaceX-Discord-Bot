# cogs/music_pause.py
import discord
from discord.ext import commands

class MusicPause(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="pause")
    async def pause(self, ctx):
        """Chalu gaane ko pause karne ke liye."""
        if not ctx.voice_client or not ctx.voice_client.is_playing():
            return await ctx.send("❌ Abhi koi gaana chal hi nahi raha hai jise pause karu!")
        
        ctx.voice_client.pause()
        await ctx.send("⏸️ Gaana pause kar diya hai! Chalu karne ke liye `!!resume` likho.")

async def setup(bot):
    await bot.add_cog(MusicPause(bot))