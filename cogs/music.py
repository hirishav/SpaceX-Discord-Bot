# cogs/music.py
import discord
from discord.ext import commands
import yt_dlp
import asyncio

# Airtight operational streaming array matrices
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'extract_flat': False
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

    def play_next(self, ctx):
        queue = self.get_queue(ctx.guild.id)
        if len(queue) > 0:
            next_song = queue.pop(0)
            
            # Reconnect client verification logic
            if ctx.voice_client and ctx.voice_client.is_connected():
                audio_source = discord.FFmpegPCMAudio(next_song['url'], **FFMPEG_OPTIONS)
                ctx.voice_client.play(audio_source, after=lambda e: self.play_next(ctx))
                
                embed = discord.Embed(
                    title="🎶 Now Playing",
                    description=f"▶️ **[{next_song['title']}]({next_song['webpage_url']})**",
                    color=discord.Color.green()
                )
                coro = ctx.send(embed=embed)
                asyncio.run_coroutine_threadsafe(coro, self.bot.loop)

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx, *, search: str = None):
        """Voice Channel me gaana bajane ke liye."""
        if not search:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}play <Song Name / Link>`")

        if ctx.author.voice is None:
            return await ctx.send("❌ Bhai, pehle kisi Voice Channel me aao!")

        # Join or move configuration framework
        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect()
        elif ctx.voice_client.channel != ctx.author.voice.channel:
            await ctx.voice_client.move_to(ctx.author.voice.channel)

        async with ctx.typing():
            try:
                # Threadpool routing map parser loop execution
                loop = self.bot.loop or asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=False))
            except Exception as e:
                return await ctx.send(f"❌ Stream process load nahi ho paya: `{e}`")

            if 'entries' in data:
                video = data['entries'][0]
            else:
                video = data

            song_info = {
                'url': video['url'],
                'title': video['title'],
                'webpage_url': video['webpage_url']
            }

            queue = self.get_queue(ctx.guild.id)

            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                queue.append(song_info)
                embed = discord.Embed(
                    title="📝 Added to Queue",
                    description=f"✅ **[{song_info['title']}]({song_info['webpage_url']})** ko queue me laga diya hai!",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
            else:
                audio_source = discord.FFmpegPCMAudio(song_info['url'], **FFMPEG_OPTIONS)
                ctx.voice_client.play(audio_source, after=lambda e: self.play_next(ctx))
                
                embed = discord.Embed(
                    title="🎶 Now Playing",
                    description=f"▶️ **[{song_info['title']}]({song_info['webpage_url']})**",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)

    @commands.command(name="skip", aliases=["s"])
    async def skip(self, ctx):
        """Current chal rahe gaane ko skip karne ke liye."""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Gaana skip kar diya, agla track aa raha hai!")
        else:
            await ctx.send("❌ Abhi koi gaana chal hi nahi raha hai!")

    @commands.command(name="stop", aliases=["leave", "dc"])
    async def stop(self, ctx):
        """Music band karne aur channel leave karne ke liye."""
        if ctx.voice_client:
            if ctx.guild.id in self.queues:
                self.queues[ctx.guild.id].clear()
            await ctx.voice_client.disconnect()
            await ctx.send("🛑 Music stopped aur bot channel se leave kar gaya.")
        else:
            await ctx.send("❌ Main kisi voice channel me nahi hun bhai!")

    @commands.command(name="queue", aliases=["q"])
    async def queue(self, ctx):
        """Gaano ki dynamic queue dekhne ke liye."""
        queue = self.get_queue(ctx.guild.id)
        if not queue:
            return await ctx.send("🎵 Queue ekdum khali hai! `!!play` se gaane jodo.")

        embed = discord.Embed(title="📋 Upcoming Tracks Queue", color=discord.Color.orange())
        text = ""
        for idx, song in enumerate(queue[:10], start=1):
            text += f"`{idx}.` **[{song['title']}]({song['webpage_url']})**\n"
        
        if len(queue) > 10:
            text += f"\n*...aur {len(queue) - 10} gaane queue me hain!*"

        embed.description = text
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Music(bot))