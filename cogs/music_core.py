# cogs/music_core.py
import discord
import asyncio
import yt_dlp

ytdl_format_options = {
    'format': 'bestaudio/best',
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
    async def from_url(cls, search, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        # Non-blocking tarike se data extract karne ke liye
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch:{search}" if not search.startswith('http') else search, download=False))
        
        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url']
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

# Khaali setup taaki main bot ise loading ke waqt crash na kare
async def setup(bot):
    pass