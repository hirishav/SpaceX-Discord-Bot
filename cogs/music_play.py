# cogs/music_play.py
import discord
from discord.ext import commands
import yt_dlp
import asyncio
from cogs.music_core import GLOBAL_QUEUES, CURRENT_TRACK, FFMPEG_OPTIONS, get_bin_path

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

class MusicPlay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def play_next_track(self, ctx):
        g_id = ctx.guild.id
        if g_id not in GLOBAL_QUEUES or len(GLOBAL_QUEUES[g_id]) == 0:
            if g_id in CURRENT_TRACK: del CURRENT_TRACK[g_id]
            return

        next_song = GLOBAL_QUEUES[g_id].pop(0)
        CURRENT_TRACK[g_id] = next_song

        if ctx.voice_client and ctx.voice_client.is_connected():
            audio_source = discord.FFmpegPCMAudio(next_song['url'], executable_path=get_bin_path(), **FFMPEG_OPTIONS)
            ctx.voice_client.play(audio_source, after=lambda e: self.play_next_track(ctx))
            
            embed = discord.Embed(
                title="🎶 Now Playing",
                description=f"▶️ **[{next_song['title']}]({next_song['webpage_url']})**",
                color=discord.Color.green()
            )
            self.bot.loop.create_task(ctx.send(embed=embed))

    @commands.command(name="play", aliases=["p"])
    async def play(self, ctx, *, search: str = None):
        """Voice Channel me gaana stream karne ke liye."""
        if not search:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}play <Gaane ka naam ya Link>`")

        if ctx.author.voice is None:
            return await ctx.send("❌ Bhai, pehle kisi Voice Channel me aao!")

        if ctx.voice_client is None:
            try:
                await ctx.author.voice.channel.connect(timeout=20.0, reconnect=True)
            except Exception as e:
                return await ctx.send(f"❌ Voice channel connection deadlock: `{e}`")
        elif ctx.voice_client.channel != ctx.author.voice.channel:
            await ctx.voice_client.move_to(ctx.author.voice.channel)

        async with ctx.typing():
            try:
                with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ytdl:
                    data = await self.bot.loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=False))
                
                if 'entries' in data: video = data['entries'][0]
                else: video = data

                song_info = {
                    'url': video['url'],
                    'title': video['title'],
                    'webpage_url': video['webpage_url']
                }
            except Exception as e:
                return await ctx.send(f"❌ YouTube extraction failure: `{e}`")

            g_id = ctx.guild.id
            if g_id not in GLOBAL_QUEUES: GLOBAL_QUEUES[g_id] = []

            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                GLOBAL_QUEUES[g_id].append(song_info)
                embed = discord.Embed(
                    title="📝 Added to Queue",
                    description=f"✅ **[{song_info['title']}]({song_info['webpage_url']})** ko queue me laga diya hai!",
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
            else:
                CURRENT_TRACK[g_id] = song_info
                audio_source = discord.FFmpegPCMAudio(song_info['url'], executable_path=get_bin_path(), **FFMPEG_OPTIONS)
                ctx.voice_client.play(audio_source, after=lambda e: self.play_next_track(ctx))
                
                embed = discord.Embed(
                    title="🎶 Now Playing",
                    description=f"▶️ **[{song_info['title']}]({song_info['webpage_url']})**",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(MusicPlay(bot))