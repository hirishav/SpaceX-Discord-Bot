# cogs/music_stop.py
import discord
from discord.ext import commands

class MusicStop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="stop", aliases=["leave", "dc"])
    async def stop(self, ctx):
        """Bot ko voice channel se nikalne ke liye."""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Chalta hu bhai, baki kaam baad me!")
        else:
            await ctx.send("❌ Main kisi voice channel me nahi hu.")

async def setup(bot):
    await bot.add_cog(MusicStop(bot))