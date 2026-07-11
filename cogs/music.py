"""Music commands and per-guild playback management."""

from __future__ import annotations

import asyncio
import logging
import os
import random
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Deque, Optional
from urllib.parse import urlparse

import discord
import yt_dlp
from discord.ext import commands


log = logging.getLogger(__name__)

YTDL_BASE_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "nocheckcertificate": True,
    "quiet": True,
    "no_warnings": True,
    "source_address": "0.0.0.0",
}

FFMPEG_OPTIONS = {
    "before_options": "-nostdin -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


class TrackLookupError(RuntimeError):
    """A user-safe error raised when no provider can find a playable track."""


class YTDLPLogger:
    """Keep expected provider rejections out of the process error stream."""

    def debug(self, message: str) -> None:
        log.debug("yt-dlp: %s", message)

    def warning(self, message: str) -> None:
        log.debug("yt-dlp warning: %s", message)

    def error(self, message: str) -> None:
        log.debug("yt-dlp error: %s", message)


def configured_ytdl_options() -> dict:
    """Create extractor options and optionally load a deployed cookies file."""

    import tempfile
    options = {**YTDL_BASE_OPTIONS, "logger": YTDLPLogger()}
    
    # Support for passing raw cookie text via environment variable (Ideal for Render)
    cookie_content = os.getenv("YTDLP_COOKIES")
    if cookie_content:
        try:
            # Securely write to a temporary file (avoids PermissionError & file locking issues)
            temp_cookie = tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8", suffix=".txt")
            temp_cookie.write(cookie_content)
            temp_cookie.close()
            options["cookiefile"] = temp_cookie.name
            log.info("yt-dlp cookie authentication is enabled via YTDLP_COOKIES env variable.")
            return options
        except Exception as e:
            log.error("Failed to write YTDLP_COOKIES to a temporary file: %s", e)

    cookie_file = os.getenv("YTDLP_COOKIES_FILE")
    if cookie_file:
        cookie_path = Path(cookie_file).expanduser()
        if cookie_path.is_file():
            # Cookie files are credentials. Do not log their location or contents.
            options["cookiefile"] = str(cookie_path)
            log.info("yt-dlp cookie authentication is enabled.")
            return options
        log.warning("YTDLP_COOKIES_FILE is set, but no readable cookie file was found.")

    browser = os.getenv("YTDLP_COOKIES_FROM_BROWSER", "").strip().lower()
    if browser:
        options["cookiesfrombrowser"] = (browser,)
        log.info("yt-dlp will read cookies from the configured local browser.")
    return options


@dataclass(slots=True)
class Track:
    """The stable metadata needed to re-resolve a stream just before playback."""

    webpage_url: str
    title: str
    requester: discord.abc.User
    duration: Optional[int | float] = None
    uploader: Optional[str] = None
    thumbnail: Optional[str] = None

    @classmethod
    def from_info(cls, data: dict, requester: discord.abc.User) -> "Track":
        webpage_url = data.get("webpage_url") or data.get("original_url") or data.get("url")
        if not webpage_url:
            raise RuntimeError("The source did not provide a playable URL.")

        return cls(
            webpage_url=webpage_url,
            title=data.get("title") or "Unknown title",
            requester=requester,
            duration=data.get("duration"),
            uploader=data.get("uploader") or data.get("channel"),
            thumbnail=data.get("thumbnail"),
        )


@dataclass
class GuildPlayer:
    """Playback state for one Discord guild."""

    queue: Deque[Track] = field(default_factory=deque)
    history: Deque[Track] = field(default_factory=lambda: deque(maxlen=25))
    current: Optional[Track] = None
    volume: float = 0.5
    muted: bool = False
    looping: bool = False
    autoplay: bool = False
    starting: bool = False
    ignore_loop_once: bool = False
    generation: int = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class PlayerControls(discord.ui.View):
    """Full, short-lived controls attached to each now-playing message."""

    def __init__(self, cog: "Music", guild_id: int):
        super().__init__(timeout=1800)
        self.cog = cog
        self.guild_id = guild_id

    async def _voice_client_for(self, interaction: discord.Interaction) -> Optional[discord.VoiceClient]:
        guild = interaction.guild
        if guild is None or guild.id != self.guild_id:
            await interaction.response.send_message("These controls are no longer active.", ephemeral=True)
            return None

        voice_client = guild.voice_client
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        member_channel = member.voice.channel if member and member.voice else None
        if voice_client is None or member_channel != voice_client.channel:
            await interaction.response.send_message(
                "Join my voice channel before using the player controls.", ephemeral=True
            )
            return None
        return voice_client

    @discord.ui.button(label="Pause", emoji="⏯️", style=discord.ButtonStyle.success, row=0)
    async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        voice_client = await self._voice_client_for(interaction)
        if voice_client is None:
            return

        if voice_client.is_playing():
            voice_client.pause()
            button.emoji = "▶️"
            button.label = "Resume"
            await interaction.response.edit_message(view=self)
        elif voice_client.is_paused():
            voice_client.resume()
            button.emoji = "⏸️"
            button.label = "Pause"
            await interaction.response.edit_message(view=self)
        else:
            await interaction.response.send_message("Nothing is playing right now.", ephemeral=True)

    @discord.ui.button(label="Previous", emoji="⏮️", style=discord.ButtonStyle.secondary, row=0)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        voice_client = await self._voice_client_for(interaction)
        if voice_client is None:
            return
        if not (voice_client.is_playing() or voice_client.is_paused()):
            await interaction.response.send_message("Nothing is playing right now.", ephemeral=True)
            return
        if not await self.cog.play_previous(self.guild_id):
            await interaction.response.send_message("There is no previous track in this session.", ephemeral=True)
            return

        voice_client.stop()
        await interaction.response.send_message("Playing the previous track.", ephemeral=True)

    @discord.ui.button(label="Skip", emoji="⏭️", style=discord.ButtonStyle.primary, row=0)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        voice_client = await self._voice_client_for(interaction)
        if voice_client is None:
            return
        if not (voice_client.is_playing() or voice_client.is_paused()):
            await interaction.response.send_message("Nothing is playing right now.", ephemeral=True)
            return

        await self.cog.skip_current(self.guild_id)
        voice_client.stop()
        await interaction.response.send_message("Skipped the current track.", ephemeral=True)

    @discord.ui.button(label="Stop", emoji="⏹️", style=discord.ButtonStyle.danger, row=0)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        voice_client = await self._voice_client_for(interaction)
        if voice_client is None:
            return

        await self.cog.stop_player(self.guild_id, disconnect=True)
        await interaction.response.send_message("Stopped playback, cleared the queue, and disconnected.", ephemeral=True)

    @discord.ui.button(label="Queue", emoji="📜", style=discord.ButtonStyle.secondary, row=1)
    async def queue(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        voice_client = await self._voice_client_for(interaction)
        if voice_client is None:
            return
        await interaction.response.send_message(
            embed=self.cog.queue_embed(interaction.guild), ephemeral=True
        )

    @discord.ui.button(label="Loop", emoji="🔁", style=discord.ButtonStyle.secondary, row=1)
    async def loop(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        voice_client = await self._voice_client_for(interaction)
        if voice_client is None:
            return

        enabled = await self.cog.set_loop(self.guild_id)
        button.label = "Loop On" if enabled else "Loop"
        button.style = discord.ButtonStyle.success if enabled else discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Shuffle", emoji="🔀", style=discord.ButtonStyle.secondary, row=1)
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        voice_client = await self._voice_client_for(interaction)
        if voice_client is None:
            return

        count = await self.cog.shuffle_queue(self.guild_id)
        message = "Shuffled the queue." if count >= 2 else "Add at least two queued tracks to shuffle them."
        await interaction.response.send_message(message, ephemeral=True)

    @discord.ui.button(label="Autoplay", emoji="♾️", style=discord.ButtonStyle.secondary, row=1)
    async def autoplay(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        voice_client = await self._voice_client_for(interaction)
        if voice_client is None:
            return

        enabled = await self.cog.set_autoplay(self.guild_id)
        button.label = "Autoplay On" if enabled else "Autoplay"
        button.style = discord.ButtonStyle.success if enabled else discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Mute", emoji="🔇", style=discord.ButtonStyle.secondary, row=1)
    async def mute(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        voice_client = await self._voice_client_for(interaction)
        if voice_client is None:
            return

        muted = await self.cog.toggle_mute(self.guild_id, voice_client)
        button.label = "Unmute" if muted else "Mute"
        button.emoji = "🔊" if muted else "🔇"
        await interaction.response.edit_message(view=self)


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players: dict[int, GuildPlayer] = {}
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.ytdl_options = configured_ytdl_options()

    async def cog_load(self) -> None:
        # ``after`` callbacks are invoked on Discord's audio thread, so retain the
        # running loop for safely scheduling the next track back on the bot loop.
        self.loop = asyncio.get_running_loop()

    def get_player(self, guild_id: int) -> GuildPlayer:
        return self.players.setdefault(guild_id, GuildPlayer())

    @staticmethod
    def effective_volume(player: GuildPlayer) -> float:
        return 0.0 if player.muted else player.volume

    @staticmethod
    def format_duration(seconds: Optional[int | float]) -> str:
        if seconds is None:
            return "Live stream"

        try:
            total_seconds = max(0, int(seconds))
        except (TypeError, ValueError, OverflowError):
            return "Unknown"

        minutes, seconds = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"

    @staticmethod
    def _entry_from_result(data: object) -> dict:
        if not isinstance(data, dict):
            raise RuntimeError("The source returned an invalid result.")
        entries = data.get("entries")
        if entries is not None:
            data = next((entry for entry in entries if entry), None)
        if not isinstance(data, dict):
            raise RuntimeError("No playable result was found.")
        return data

    @staticmethod
    def _is_url(value: str) -> bool:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)

    @staticmethod
    def _youtube_auth_required(errors: list[Exception]) -> bool:
        return any("not a bot" in str(error).lower() for error in errors)

    async def extract_info(self, input_value: str) -> dict:
        def extract() -> dict:
            with yt_dlp.YoutubeDL(dict(self.ytdl_options)) as extractor:
                return self._entry_from_result(extractor.extract_info(input_value, download=False))

        return await asyncio.to_thread(extract)

    async def extract_track(self, query: str, requester: discord.abc.User) -> Track:
        """Resolve a URL or try YouTube then SoundCloud for a plain search."""

        candidates = [query] if self._is_url(query) else [f"ytsearch1:{query}", f"scsearch1:{query}"]
        errors: list[Exception] = []
        for candidate in candidates:
            try:
                return Track.from_info(await self.extract_info(candidate), requester)
            except Exception as error:
                errors.append(error)
                log.debug("Provider lookup failed for %s: %s", candidate.split(":", 1)[0], error)

        if self._youtube_auth_required(errors):
            raise TrackLookupError(
                "YouTube requires authentication for this server. Configure YTDLP_COOKIES_FILE or try a SoundCloud URL."
            )
        raise TrackLookupError("I could not find a playable result for that search or URL.")

    async def create_audio_source(self, track: Track, volume: float) -> discord.PCMVolumeTransformer:
        """Fetch a fresh stream URL, because provider stream URLs expire quickly."""

        def extract() -> dict:
            with yt_dlp.YoutubeDL(dict(self.ytdl_options)) as extractor:
                return self._entry_from_result(extractor.extract_info(track.webpage_url, download=False))

        data = await asyncio.to_thread(extract)
        stream_url = data.get("url")
        if not stream_url:
            raise RuntimeError("The source did not provide an audio stream.")

        track.title = data.get("title") or track.title
        track.duration = data.get("duration") or track.duration
        track.uploader = data.get("uploader") or data.get("channel") or track.uploader
        track.thumbnail = data.get("thumbnail") or track.thumbnail
        audio = discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS)
        return discord.PCMVolumeTransformer(audio, volume=volume)

    async def ensure_voice(self, ctx: commands.Context) -> Optional[discord.VoiceClient]:
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("Join a voice channel first.")
            return None

        requested_channel = ctx.author.voice.channel
        voice_client = ctx.guild.voice_client
        if voice_client is None:
            return await requested_channel.connect(self_deaf=True)
        if voice_client.channel != requested_channel:
            if voice_client.is_playing() or voice_client.is_paused():
                await ctx.send("I am already playing in another voice channel.")
                return None
            await voice_client.move_to(requested_channel)
        return voice_client

    async def enqueue(
        self, guild_id: int, track: Track, channel: discord.abc.Messageable, *, front: bool = False
    ) -> int:
        """Queue a track and start the worker if this guild is idle.

        The returned position is zero when the track is about to start.
        """

        player = self.get_player(guild_id)
        async with player.lock:
            # Count the current/loading item as position one for later requests.
            busy = player.current is not None or player.starting
            position = 1 if front and busy else len(player.queue) + (1 if busy else 0)
            if front:
                player.queue.appendleft(track)
            else:
                player.queue.append(track)
            should_start = player.current is None and not player.starting

        if should_start:
            await self.start_next(guild_id, channel)
        return position

    async def set_loop(self, guild_id: int, enabled: Optional[bool] = None) -> bool:
        player = self.get_player(guild_id)
        async with player.lock:
            player.looping = not player.looping if enabled is None else enabled
            return player.looping

    async def set_autoplay(self, guild_id: int, enabled: Optional[bool] = None) -> bool:
        player = self.get_player(guild_id)
        async with player.lock:
            player.autoplay = not player.autoplay if enabled is None else enabled
            return player.autoplay

    async def shuffle_queue(self, guild_id: int) -> int:
        player = self.get_player(guild_id)
        async with player.lock:
            count = len(player.queue)
            if count >= 2:
                tracks = list(player.queue)
                random.shuffle(tracks)
                player.queue = deque(tracks)
            return count

    async def toggle_mute(self, guild_id: int, voice_client: discord.VoiceClient) -> bool:
        player = self.get_player(guild_id)
        async with player.lock:
            player.muted = not player.muted
            muted = player.muted
            volume = self.effective_volume(player)

        if isinstance(voice_client.source, discord.PCMVolumeTransformer):
            voice_client.source.volume = volume
        return muted

    async def skip_current(self, guild_id: int) -> bool:
        player = self.get_player(guild_id)
        async with player.lock:
            if player.current is None:
                return False
            # A manual skip should never be converted into a repeat-one action.
            player.ignore_loop_once = True
            return True

    async def play_previous(self, guild_id: int) -> bool:
        player = self.get_player(guild_id)
        async with player.lock:
            if player.current is None or len(player.history) < 2:
                return False

            previous = list(player.history)[-2]
            # Resume the interrupted track after the previous one, and suppress
            # repeat-one for this intentional transition.
            player.queue.appendleft(player.current)
            player.queue.appendleft(previous)
            player.ignore_loop_once = True
            return True

    async def find_autoplay_track(self, previous: Track, player: GuildPlayer) -> Optional[Track]:
        """Find a related-style track when the manual queue has run out."""

        requester = self.bot.user or previous.requester
        played_urls = {track.webpage_url for track in player.history}
        queries = [
            f"{previous.uploader} radio" if previous.uploader else f"{previous.title} radio",
            f"{previous.title} similar music",
        ]
        for query in queries:
            try:
                track = await self.extract_track(query, requester)
            except TrackLookupError:
                continue
            except Exception:
                log.exception("Autoplay lookup failed in guild player")
                continue
            if track.webpage_url not in played_urls:
                return track
        return None

    async def start_next(self, guild_id: int, channel: discord.abc.Messageable) -> None:
        player = self.get_player(guild_id)
        async with player.lock:
            guild = self.bot.get_guild(guild_id)
            voice_client = guild.voice_client if guild else None
            if (
                player.current is not None
                or player.starting
                or not player.queue
                or voice_client is None
                or not voice_client.is_connected()
            ):
                return

            player.starting = True
            generation = player.generation
            track = player.queue.popleft()
            volume = self.effective_volume(player)

        try:
            source = await self.create_audio_source(track, volume)

            async with player.lock:
                guild = self.bot.get_guild(guild_id)
                voice_client = guild.voice_client if guild else None
                cancelled = generation != player.generation
                busy = voice_client is None or not voice_client.is_connected() or voice_client.is_playing()
                player.starting = False
                if cancelled or busy:
                    source.cleanup()
                    if not cancelled:
                        player.queue.appendleft(track)
                    return

                player.current = track
                player.history.append(track)
                voice_client.play(
                    source,
                    after=lambda error: self._schedule_advance(guild_id, channel.id, error),
                )

            await channel.send(embed=self.now_playing_embed(track), view=PlayerControls(self, guild_id))
        except Exception as error:
            log.warning("Could not play %r in guild %s: %s", track.title, guild_id, error)
            async with player.lock:
                player.starting = False
                player.current = None
            await channel.send(f"I could not play **{discord.utils.escape_markdown(track.title)}**. Trying the next track.")
            await self.start_next(guild_id, channel)

    def _schedule_advance(self, guild_id: int, channel_id: int, error: Optional[Exception]) -> None:
        if error:
            log.warning("Audio player error in guild %s: %s", guild_id, error)
        if self.loop is None or self.loop.is_closed():
            return
        future = asyncio.run_coroutine_threadsafe(self.advance(guild_id, channel_id), self.loop)
        future.add_done_callback(self._report_background_error)

    @staticmethod
    def _report_background_error(future: "asyncio.Future[None]") -> None:
        try:
            future.result()
        except Exception:
            log.exception("Unable to advance the music queue")

    async def advance(self, guild_id: int, channel_id: int) -> None:
        player = self.get_player(guild_id)
        should_autoplay = False
        generation = 0
        async with player.lock:
            previous = player.current
            player.current = None
            if previous is not None and player.looping and not player.ignore_loop_once:
                player.queue.appendleft(previous)
            elif previous is not None and player.autoplay and not player.queue:
                # Reserve the player while a recommendation is looked up so that
                # a manual request arriving in the meantime still takes priority.
                player.starting = True
                generation = player.generation
                should_autoplay = True
            player.ignore_loop_once = False

        channel = self.bot.get_channel(channel_id)
        if channel is None:
            return

        if should_autoplay and previous is not None:
            autoplay_track = await self.find_autoplay_track(previous, player)
            async with player.lock:
                still_current = player.current is None and player.generation == generation
                player.starting = False
                if still_current and autoplay_track is not None:
                    # Appending means tracks manually added during the lookup play first.
                    player.queue.append(autoplay_track)
                    log.info("Autoplay queued %r in guild %s", autoplay_track.title, guild_id)

        await self.start_next(guild_id, channel)

    async def stop_player(self, guild_id: int, *, disconnect: bool) -> None:
        player = self.get_player(guild_id)
        async with player.lock:
            player.generation += 1
            player.queue.clear()
            player.current = None
            player.starting = False
            player.looping = False
            player.autoplay = False
            player.ignore_loop_once = False
            player.history.clear()

        guild = self.bot.get_guild(guild_id)
        voice_client = guild.voice_client if guild else None
        if voice_client is None:
            return
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
        if disconnect and voice_client.is_connected():
            await voice_client.disconnect()

    def now_playing_embed(self, track: Track) -> discord.Embed:
        safe_title = discord.utils.escape_markdown(track.title)
        embed = discord.Embed(
            title="Now playing",
            description=f"**[{safe_title}]({track.webpage_url})**",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Duration", value=self.format_duration(track.duration))
        embed.add_field(name="Requested by", value=track.requester.mention)
        if track.uploader:
            embed.add_field(name="Channel", value=discord.utils.escape_markdown(track.uploader), inline=False)
        if track.thumbnail:
            embed.set_thumbnail(url=track.thumbnail)
        return embed

    def queue_embed(self, guild: discord.Guild) -> discord.Embed:
        player = self.get_player(guild.id)
        lines: list[str] = []
        if player.current:
            lines.append(f"**Now:** {discord.utils.escape_markdown(player.current.title)}")
        for index, track in enumerate(list(player.queue)[:10], start=1):
            lines.append(f"`{index}.` {discord.utils.escape_markdown(track.title)}")
        if len(player.queue) > 10:
            lines.append(f"*…and {len(player.queue) - 10} more.*")

        embed = discord.Embed(
            title=f"Queue for {guild.name}",
            description="\n".join(lines) if lines else "The queue is empty.",
            color=discord.Color.blurple(),
        )
        state = "on" if player.autoplay else "off"
        repeat = "on" if player.looping else "off"
        volume = 0 if player.muted else round(player.volume * 100)
        embed.set_footer(text=f"Autoplay: {state} • Repeat: {repeat} • Volume: {volume}%")
        return embed

    def history_embed(self, guild: discord.Guild) -> discord.Embed:
        player = self.get_player(guild.id)
        tracks = list(player.history)[-10:]
        description = "\n".join(
            f"`{index}.` {discord.utils.escape_markdown(track.title)}"
            for index, track in enumerate(reversed(tracks), start=1)
        )
        return discord.Embed(
            title=f"Recently played in {guild.name}",
            description=description or "No tracks have played in this session yet.",
            color=discord.Color.blurple(),
        )

    def requester_is_with_bot(self, ctx: commands.Context) -> bool:
        voice_client = ctx.guild.voice_client
        return bool(ctx.author.voice and voice_client and ctx.author.voice.channel == voice_client.channel)

    @commands.command(help="Join your voice channel.")
    @commands.guild_only()
    async def join(self, ctx: commands.Context) -> None:
        voice_client = await self.ensure_voice(ctx)
        if voice_client:
            await ctx.send(f"Connected to **{voice_client.channel.name}**.")

    @commands.command(aliases=["p"], help="Play a URL or search for a song.")
    @commands.guild_only()
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        await self.queue_query(ctx, query)

    @commands.command(aliases=["pn"], help="Add a URL or search result as the next track.")
    @commands.guild_only()
    async def playnext(self, ctx: commands.Context, *, query: str) -> None:
        await self.queue_query(ctx, query, front=True)

    async def queue_query(self, ctx: commands.Context, query: str, *, front: bool = False) -> None:
        voice_client = await self.ensure_voice(ctx)
        if voice_client is None:
            return

        searching = await ctx.send("🔎 Searching…")
        try:
            track = await self.extract_track(query, ctx.author)
            position = await self.enqueue(ctx.guild.id, track, ctx.channel, front=front)
        except TrackLookupError as error:
            log.info("Search failed: %s", error)
            await searching.edit(content=str(error))
            return
        except Exception:
            log.exception("Unexpected error while searching for a track")
            await searching.edit(content="I could not find a playable result for that search or URL.")
            return

        if position == 0:
            await searching.delete()
        else:
            placement = "next" if front else f"#{position}"
            await searching.edit(
                content=f"✅ Added **{discord.utils.escape_markdown(track.title)}** to the queue ({placement})."
            )

    @commands.command(help="Pause the current track.")
    @commands.guild_only()
    async def pause(self, ctx: commands.Context) -> None:
        if not self.requester_is_with_bot(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        voice_client = ctx.guild.voice_client
        if voice_client.is_playing():
            voice_client.pause()
            await ctx.send("Paused.")
        else:
            await ctx.send("Nothing is playing right now.")

    @commands.command(help="Resume the paused track.")
    @commands.guild_only()
    async def resume(self, ctx: commands.Context) -> None:
        if not self.requester_is_with_bot(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        voice_client = ctx.guild.voice_client
        if voice_client.is_paused():
            voice_client.resume()
            await ctx.send("Resumed.")
        else:
            await ctx.send("The player is not paused.")

    @commands.command(help="Skip the current track.")
    @commands.guild_only()
    async def skip(self, ctx: commands.Context) -> None:
        if not self.requester_is_with_bot(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        voice_client = ctx.guild.voice_client
        if voice_client.is_playing() or voice_client.is_paused():
            await self.skip_current(ctx.guild.id)
            voice_client.stop()
            await ctx.send("Skipped.")
        else:
            await ctx.send("Nothing is playing right now.")

    @commands.command(aliases=["prev"], help="Return to the previous track in this session.")
    @commands.guild_only()
    async def previous(self, ctx: commands.Context) -> None:
        if not self.requester_is_with_bot(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        voice_client = ctx.guild.voice_client
        if not (voice_client.is_playing() or voice_client.is_paused()):
            await ctx.send("Nothing is playing right now.")
            return
        if not await self.play_previous(ctx.guild.id):
            await ctx.send("There is no previous track in this session.")
            return
        voice_client.stop()
        await ctx.send("Playing the previous track.")

    @commands.command(help="Stop playback, clear the queue, and disconnect.")
    @commands.guild_only()
    async def stop(self, ctx: commands.Context) -> None:
        if not self.requester_is_with_bot(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        await self.stop_player(ctx.guild.id, disconnect=True)
        await ctx.send("Stopped playback and cleared the queue.")

    @commands.command(aliases=["disconnect", "dc"], help="Disconnect and clear playback.")
    @commands.guild_only()
    async def leave(self, ctx: commands.Context) -> None:
        if not self.requester_is_with_bot(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        await self.stop_player(ctx.guild.id, disconnect=True)
        await ctx.send("Disconnected and cleared the queue.")

    @commands.command(aliases=["q"], help="Show the current queue.")
    @commands.guild_only()
    async def queue(self, ctx: commands.Context) -> None:
        await ctx.send(embed=self.queue_embed(ctx.guild))

    @commands.command(aliases=["np"], help="Show the current track.")
    @commands.guild_only()
    async def nowplaying(self, ctx: commands.Context) -> None:
        track = self.get_player(ctx.guild.id).current
        if track is None:
            await ctx.send("Nothing is playing right now.")
            return
        await ctx.send(embed=self.now_playing_embed(track))

    @commands.command(help="Set the player volume from 0 to 200.")
    @commands.guild_only()
    async def volume(self, ctx: commands.Context, percent: Optional[int] = None) -> None:
        player = self.get_player(ctx.guild.id)
        if percent is None:
            await ctx.send(f"Volume is {round(player.volume * 100)}%.")
            return
        if not 0 <= percent <= 200:
            await ctx.send("Volume must be between 0 and 200.")
            return
        if not self.requester_is_with_bot(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return

        player.volume = percent / 100
        player.muted = percent == 0
        voice_client = ctx.guild.voice_client
        if isinstance(voice_client.source, discord.PCMVolumeTransformer):
            voice_client.source.volume = self.effective_volume(player)
        await ctx.send(f"Volume set to {percent}%.")

    @commands.command(name="vmute", aliases=["audiomute"], help="Toggle mute without changing the saved volume.")
    @commands.guild_only()
    async def vmute(self, ctx: commands.Context) -> None:
        if not self.requester_is_with_bot(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        muted = await self.toggle_mute(ctx.guild.id, ctx.guild.voice_client)
        await ctx.send("Muted." if muted else f"Unmuted ({round(self.get_player(ctx.guild.id).volume * 100)}%).")

    @commands.command(aliases=["ap"], help="Toggle autoplay, or use on/off to set it explicitly.")
    @commands.guild_only()
    async def autoplay(self, ctx: commands.Context, state: Optional[str] = None) -> None:
        if not self.requester_is_with_bot(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return

        if state is None:
            enabled = await self.set_autoplay(ctx.guild.id)
        elif state.lower() in {"on", "enable", "enabled"}:
            enabled = await self.set_autoplay(ctx.guild.id, True)
        elif state.lower() in {"off", "disable", "disabled"}:
            enabled = await self.set_autoplay(ctx.guild.id, False)
        else:
            await ctx.send("Use `on` or `off`, for example `!autoplay on`.")
            return
        await ctx.send(f"Autoplay is now **{'on' if enabled else 'off'}**.")

    @commands.command(help="Toggle repeating the current track.")
    @commands.guild_only()
    async def loop(self, ctx: commands.Context) -> None:
        if not self.requester_is_with_bot(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        enabled = await self.set_loop(ctx.guild.id)
        await ctx.send(f"Track repeat is now **{'on' if enabled else 'off'}**.")

    @commands.command(help="Shuffle the upcoming queue.")
    @commands.guild_only()
    async def shuffle(self, ctx: commands.Context) -> None:
        if not self.requester_is_with_bot(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        count = await self.shuffle_queue(ctx.guild.id)
        if count < 2:
            await ctx.send("Add at least two queued tracks to shuffle them.")
            return
        await ctx.send("Shuffled the queue.")

    @commands.command(help="Remove all upcoming tracks.")
    @commands.guild_only()
    async def clear(self, ctx: commands.Context) -> None:
        if not self.requester_is_with_bot(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        player = self.get_player(ctx.guild.id)
        count = len(player.queue)
        player.queue.clear()
        await ctx.send(f"Removed {count} queued track{'s' if count != 1 else ''}.")

    @commands.command(aliases=["rm"], help="Remove a queued track by its queue position.")
    @commands.guild_only()
    async def remove(self, ctx: commands.Context, position: int) -> None:
        if not self.requester_is_with_bot(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        player = self.get_player(ctx.guild.id)
        if not 1 <= position <= len(player.queue):
            await ctx.send("That queue position does not exist.")
            return
        tracks = list(player.queue)
        removed = tracks.pop(position - 1)
        player.queue = deque(tracks)
        await ctx.send(f"Removed **{discord.utils.escape_markdown(removed.title)}** from the queue.")

    @commands.command(help="Move a queued track to another queue position.")
    @commands.guild_only()
    async def move(self, ctx: commands.Context, from_position: int, to_position: int) -> None:
        if not self.requester_is_with_bot(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        player = self.get_player(ctx.guild.id)
        if not 1 <= from_position <= len(player.queue) or not 1 <= to_position <= len(player.queue):
            await ctx.send("Both queue positions must exist.")
            return
        tracks = list(player.queue)
        track = tracks.pop(from_position - 1)
        tracks.insert(to_position - 1, track)
        player.queue = deque(tracks)
        await ctx.send(f"Moved **{discord.utils.escape_markdown(track.title)}** to #{to_position}.")

    @commands.command(help="Show recently played tracks in this session.")
    @commands.guild_only()
    async def history(self, ctx: commands.Context) -> None:
        await ctx.send(embed=self.history_embed(ctx.guild))

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing an argument. Try `{ctx.prefix}help {ctx.command.qualified_name}`.")
            return
        if isinstance(error, commands.BadArgument):
            await ctx.send(f"That argument is not valid. Try `{ctx.prefix}help {ctx.command.qualified_name}`.")
            return
        if isinstance(error, commands.NoPrivateMessage):
            await ctx.send("Music commands can only be used in a server.")
            return
        log.error("Music command failed", exc_info=error)
        await ctx.send("Something went wrong while handling that command.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Music(bot))
