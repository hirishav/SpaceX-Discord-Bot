# cogs/music_play.py
import discord
from discord.ext import commands
from cogs.music_core import YTDLSource

class MusicPlay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx, *, search: str = None):
        """Voice channel me gaana bajane ke liye."""
        if not search:
            return await ctx.send("❌ Bhai gaane ka naam ya link toh do!")

        if not ctx.author.voice:
            return await ctx.send("❌ Pehle kisi Voice Channel me connect ho jao!")

        # Voice channel se connect karo agar bot pehle se nahi hai
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()
        elif ctx.voice_client.channel != ctx.author.voice.channel:
            return await ctx.send("❌ Main pehle se kisi aur voice channel me hu!")

        await ctx.send(f"🔍 **Searching:** `{search}`... thoda sa sabr rakho bhai...")

        async with ctx.typing():
            try:
                # Agar pehle se kuch chal raha hai toh stop karo (abhi simple bina queue ke setup hai)
                if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                    ctx.voice_client.stop()

                player = await YTDLSource.from_url(search, loop=self.bot.loop)
                ctx.voice_client.play(player)
                
                embed = discord.Embed(
                    description=f"🎵 **Now Playing:** `{player.title}`",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
            except Exception as e:
                print(f"Play Error: {e}")
                await ctx.send("❌ Gaana dhoondhne me dikkat aayi. Naam thoda clear likho!")

async def setup(bot):
    await bot.add_cog(MusicPlay(bot))