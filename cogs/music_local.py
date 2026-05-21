# cogs/music_local.py
import discord
from discord.ext import commands
import asyncio
import yt_dlp

# YT-DLP Configuration
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, search, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{search}" if not search.startswith('http') else search, download=not stream))
        
        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class MusicLocal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}

    def check_queue(self, ctx, id):
        if id in self.queues and self.queues[id]:
            player = self.queues[id].pop(0)
            ctx.voice_client.play(player, after=lambda e: self.check_queue(ctx, id))
            asyncio.run_coroutine_threadsafe(ctx.send(f"🎵 **Now Playing:** `{player.title}`"), self.bot.loop)

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx, *, search: str = None):
        """Direct Bina Lavalink ke gaana bajane ke liye!"""
        if not search:
            return await ctx.send("❌ Gaane ka naam toh batao bhai!")

        if not ctx.author.voice:
            return await ctx.send("❌ Pehle kisi Voice Channel me aao!")

        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        await ctx.send(f"🔍 **Searching:** `{search}`... thoda sa sabr rakhein...")

        async with ctx.typing():
            try:
                player = await YTDLSource.from_url(search, loop=self.bot.loop, stream=True)
                guild_id = ctx.guild.id

                if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                    if guild_id not in self.queues:
                        self.queues[guild_id] = []
                    self.queues[guild_id].append(player)
                    await ctx.send(f"➕ **Queue me joda gaya:** `{player.title}`")
                else:
                    ctx.voice_client.play(player, after=lambda e: self.check_queue(ctx, guild_id))
                    await ctx.send(f"🎵 **Now Playing:** `{player.title}`")
            except Exception as e:
                await ctx.send("❌ Gaana dhoondhne me dikkat aayi, link change karke try karein!")

    @commands.command(name="skip", aliases=["s"])
    async def skip(self, ctx):
        """Gaana skip karne ke liye."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Gaana skip kar diya!")
        else:
            await ctx.send("❌ Abhi koi gaana chal hi nahi raha hai.")

    @commands.command(name="stop", aliases=["leave"])
    async def stop(self, ctx):
        """Bot ko voice channel se nikalne ke liye."""
        if ctx.voice_client:
            if ctx.guild.id in self.queues:
                self.queues[ctx.guild.id] = []
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Taa-taa, bye-bye! Voice channel saaf.")
        else:
            await ctx.send("❌ Main kisi voice channel me nahi hu bhai.")

async def setup(bot):
    await bot.add_cog(MusicLocal(bot))