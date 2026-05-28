# cogs/music_nowplaying.py
import discord
from discord.ext import commands
from cogs.music_core import CURRENT_TRACK

class MusicNowPlaying(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="nowplaying", aliases=["np"])
    async def now_playing(self, ctx):
        """Abhi kaunsa gaana chal raha hai uski live info dekhne ke liye."""
        g_id = ctx.guild.id
        
        if ctx.voice_client and ctx.voice_client.is_playing() and g_id in CURRENT_TRACK:
            song = CURRENT_TRACK[g_id]
            embed = discord.Embed(
                title="🎶 Live Tracks Display",
                description=f"▶️ **Now Playing:** **[{song['title']}]({song['webpage_url']})**",
                color=discord.Color.purple()
            )
            embed.set_footer(text=f"Requested by {ctx.author.name}")
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Abhi voice space par koi active track play nahi ho raha hai!")

async def setup(bot):
    await bot.add_cog(MusicNowPlaying(bot))