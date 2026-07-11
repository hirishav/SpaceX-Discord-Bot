"""Lavalink-backed music commands selected with AUDIO_BACKEND=lavalink."""

from __future__ import annotations

import logging
from typing import Optional

import discord
import wavelink
from discord.ext import commands


log = logging.getLogger(__name__)


class LavalinkControls(discord.ui.View):
    """Interactive controls attached to each Lavalink now-playing message."""

    def __init__(self, cog: "LavalinkMusic", guild_id: int):
        super().__init__(timeout=1800)
        self.cog = cog
        self.guild_id = guild_id

    async def _player_for(self, interaction: discord.Interaction) -> Optional[wavelink.Player]:
        guild = interaction.guild
        if guild is None or guild.id != self.guild_id:
            await interaction.response.send_message("These controls are no longer active.", ephemeral=True)
            return None

        player = guild.voice_client
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        member_channel = member.voice.channel if member and member.voice else None
        if not isinstance(player, wavelink.Player) or member_channel != player.channel:
            await interaction.response.send_message(
                "Join my voice channel before using the player controls.", ephemeral=True
            )
            return None
        return player

    @discord.ui.button(label="Pause", emoji="⏯️", style=discord.ButtonStyle.success, row=0)
    async def play_pause(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        player = await self._player_for(interaction)
        if player is None:
            return
        if not player.playing:
            await interaction.response.send_message("Nothing is playing right now.", ephemeral=True)
            return

        await player.pause(not player.paused)
        button.label = "Resume" if player.paused else "Pause"
        button.emoji = "▶️" if player.paused else "⏸️"
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Previous", emoji="⏮️", style=discord.ButtonStyle.secondary, row=0)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        player = await self._player_for(interaction)
        if player is None:
            return
        if not await self.cog.play_previous(player):
            await interaction.response.send_message("There is no previous track in this session.", ephemeral=True)
            return
        await interaction.response.send_message("Playing the previous track.", ephemeral=True)

    @discord.ui.button(label="Skip", emoji="⏭️", style=discord.ButtonStyle.primary, row=0)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        player = await self._player_for(interaction)
        if player is None:
            return
        if not player.playing:
            await interaction.response.send_message("Nothing is playing right now.", ephemeral=True)
            return
        await player.skip(force=True)
        await interaction.response.send_message("Skipped the current track.", ephemeral=True)

    @discord.ui.button(label="Stop", emoji="⏹️", style=discord.ButtonStyle.danger, row=0)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        player = await self._player_for(interaction)
        if player is None:
            return
        await self.cog.stop_player(player, disconnect=True)
        await interaction.response.send_message("Stopped playback, cleared the queue, and disconnected.", ephemeral=True)

    @discord.ui.button(label="Queue", emoji="📜", style=discord.ButtonStyle.secondary, row=1)
    async def queue(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        player = await self._player_for(interaction)
        if player is None:
            return
        await interaction.response.send_message(embed=self.cog.queue_embed(interaction.guild, player), ephemeral=True)

    @discord.ui.button(label="Loop", emoji="🔁", style=discord.ButtonStyle.secondary, row=1)
    async def loop(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        player = await self._player_for(interaction)
        if player is None:
            return
        enabled = self.cog.toggle_loop(player)
        button.label = "Loop On" if enabled else "Loop"
        button.style = discord.ButtonStyle.success if enabled else discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Shuffle", emoji="🔀", style=discord.ButtonStyle.secondary, row=1)
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        player = await self._player_for(interaction)
        if player is None:
            return
        if len(player.queue) < 2:
            await interaction.response.send_message("Add at least two queued tracks to shuffle them.", ephemeral=True)
            return
        player.queue.shuffle()
        await interaction.response.send_message("Shuffled the queue.", ephemeral=True)

    @discord.ui.button(label="Autoplay", emoji="♾️", style=discord.ButtonStyle.secondary, row=1)
    async def autoplay(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        player = await self._player_for(interaction)
        if player is None:
            return
        enabled = self.cog.set_autoplay(player)
        button.label = "Autoplay On" if enabled else "Autoplay"
        button.style = discord.ButtonStyle.success if enabled else discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Mute", emoji="🔇", style=discord.ButtonStyle.secondary, row=1)
    async def mute(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        player = await self._player_for(interaction)
        if player is None:
            return
        muted = await self.cog.toggle_mute(player)
        button.label = "Unmute" if muted else "Mute"
        button.emoji = "🔊" if muted else "🔇"
        await interaction.response.edit_message(view=self)


class LavalinkMusic(commands.Cog):
    """Music commands that send audio through the configured Lavalink node."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.text_channels: dict[int, int] = {}
        self.saved_volumes: dict[int, int] = {}

    @staticmethod
    def format_duration(milliseconds: int) -> str:
        seconds = max(0, int(milliseconds // 1000))
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"

    @staticmethod
    def is_same_voice_channel(ctx: commands.Context) -> bool:
        player = ctx.guild.voice_client
        return bool(
            isinstance(player, wavelink.Player)
            and ctx.author.voice
            and ctx.author.voice.channel == player.channel
        )

    async def ensure_player(self, ctx: commands.Context) -> Optional[wavelink.Player]:
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("Join a voice channel first.")
            return None

        requested_channel = ctx.author.voice.channel
        voice_client = ctx.guild.voice_client
        if voice_client is None:
            player = await requested_channel.connect(cls=wavelink.Player, self_deaf=True)
            player.autoplay = wavelink.AutoPlayMode.partial
            await player.set_volume(self.saved_volumes.get(ctx.guild.id, 50))
            return player
        if not isinstance(voice_client, wavelink.Player):
            await ctx.send("Another audio backend is connected. Disconnect it before using Lavalink.")
            return None
        if voice_client.channel != requested_channel:
            if voice_client.playing:
                await ctx.send("I am already playing in another voice channel.")
                return None
            await voice_client.move_to(requested_channel, self_deaf=True)
        return voice_client

    async def search_track(self, query: str) -> Optional[wavelink.Playable]:
        tracks = await wavelink.Playable.search(query, source=wavelink.TrackSource.YouTubeMusic)
        if not tracks:
            tracks = await wavelink.Playable.search(query, source=wavelink.TrackSource.YouTube)
        return tracks[0] if tracks else None

    async def queue_query(self, ctx: commands.Context, query: str, *, front: bool = False) -> None:
        player = await self.ensure_player(ctx)
        if player is None:
            return

        searching = await ctx.send("🔎 Searching…")
        try:
            track = await self.search_track(query)
        except Exception:
            log.exception("Lavalink search failed")
            await searching.edit(content="I could not find a playable result for that search or URL.")
            return
        if track is None:
            await searching.edit(content="I could not find a playable result for that search or URL.")
            return

        track.extras = {"requester": ctx.author.mention, "channel_id": ctx.channel.id}
        self.text_channels[ctx.guild.id] = ctx.channel.id
        if front and player.playing:
            tracks = [track, *list(player.queue)]
            player.queue.clear()
            player.queue.put(tracks)
        else:
            player.queue.put(track)

        if not player.playing:
            await player.play(player.queue.get(), volume=self.saved_volumes.get(ctx.guild.id, 50))
            await searching.delete()
        else:
            placement = "next" if front else f"#{len(player.queue)}"
            await searching.edit(content=f"✅ Added **{discord.utils.escape_markdown(track.title)}** ({placement}).")

    def now_playing_embed(self, track: wavelink.Playable) -> discord.Embed:
        title = discord.utils.escape_markdown(track.title)
        
        # Determine track source for custom color/icon (Premium feel)
        source = track.source if hasattr(track, 'source') else 'unknown'
        color = discord.Color.blurple()
        icon_url = "https://cdn.discordapp.com/attachments/1105436691458920448/1105436737520775248/music.png"
        
        if "youtube" in str(source).lower():
            color = discord.Color.from_str("#FF0000")
            icon_url = "https://cdn.discordapp.com/attachments/1105436691458920448/1105436762397196328/youtube.png"
        elif "spotify" in str(source).lower():
            color = discord.Color.from_str("#1DB954")
            icon_url = "https://cdn.discordapp.com/attachments/1105436691458920448/1105436785004494918/spotify.png"
        elif "soundcloud" in str(source).lower():
            color = discord.Color.from_str("#FF5500")

        embed = discord.Embed(
            title=f"{title}",
            url=track.uri or "",
            color=color,
        )
        embed.set_author(name="🎵 Now Playing", icon_url=icon_url)
        
        # Robustly fetch requester from extras, fallback gracefully
        requester = "Autoplay"
        if hasattr(track, "extras") and track.extras:
            if hasattr(track.extras, "get"):
                requester = track.extras.get("requester", "Autoplay")
            else:
                requester = getattr(track.extras, "requester", "Autoplay")

        embed.add_field(name="👤 Requested by", value=requester, inline=True)
        embed.add_field(name="⏳ Duration", value=f"`{self.format_duration(track.length)}`", inline=True)
        embed.add_field(name="🎙️ Channel", value=f"`{discord.utils.escape_markdown(track.author or 'Unknown')}`", inline=True)
        
        if track.artwork:
            embed.set_thumbnail(url=track.artwork)
            
        embed.set_footer(text="Powered by Lavalink ✨")
        return embed

    def queue_embed(self, guild: discord.Guild, player: wavelink.Player) -> discord.Embed:
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
        autoplay = "on" if player.autoplay is wavelink.AutoPlayMode.enabled else "off"
        repeat = "on" if player.queue.mode is wavelink.QueueMode.loop else "off"
        embed.set_footer(text=f"Autoplay: {autoplay} • Repeat: {repeat} • Volume: {player.volume}%")
        return embed

    def history_embed(self, guild: discord.Guild, player: wavelink.Player) -> discord.Embed:
        history = list(player.queue.history or [])[-10:]
        description = "\n".join(
            f"`{index}.` {discord.utils.escape_markdown(track.title)}"
            for index, track in enumerate(reversed(history), start=1)
        )
        return discord.Embed(
            title=f"Recently played in {guild.name}",
            description=description or "No tracks have played in this session yet.",
            color=discord.Color.blurple(),
        )

    @staticmethod
    def toggle_loop(player: wavelink.Player) -> bool:
        enabled = player.queue.mode is not wavelink.QueueMode.loop
        player.queue.mode = wavelink.QueueMode.loop if enabled else wavelink.QueueMode.normal
        return enabled

    @staticmethod
    def set_autoplay(player: wavelink.Player, enabled: Optional[bool] = None) -> bool:
        currently_enabled = player.autoplay is wavelink.AutoPlayMode.enabled
        enabled = not currently_enabled if enabled is None else enabled
        # Partial mode progresses the manual queue without adding recommendations.
        player.autoplay = wavelink.AutoPlayMode.enabled if enabled else wavelink.AutoPlayMode.partial
        return enabled

    async def toggle_mute(self, player: wavelink.Player) -> bool:
        guild_id = player.guild.id
        if player.volume > 0:
            self.saved_volumes[guild_id] = player.volume
            await player.set_volume(0)
            return True
        await player.set_volume(self.saved_volumes.get(guild_id, 50))
        return False

    @staticmethod
    async def play_previous(player: wavelink.Player) -> bool:
        history = player.queue.history
        if history is None or len(history) < 2:
            return False
        await player.play(history[-2], volume=player.volume)
        return True

    async def stop_player(self, player: wavelink.Player, *, disconnect: bool) -> None:
        player.queue.clear()
        player.auto_queue.clear()
        player.autoplay = wavelink.AutoPlayMode.partial
        if player.playing:
            await player.skip(force=True)
        if disconnect:
            await player.disconnect()

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload) -> None:
        try:
            player = payload.player
            if player is None or player.guild is None:
                return
            
            track = payload.original or payload.track
            
            # Robustly resolve channel ID
            channel_id = self.text_channels.get(player.guild.id)
            if hasattr(track, "extras") and track.extras:
                if hasattr(track.extras, "get"):
                    channel_id = track.extras.get("channel_id", channel_id)
                else:
                    channel_id = getattr(track.extras, "channel_id", channel_id)

            channel = self.bot.get_channel(channel_id) if channel_id else None
            
            if channel is not None:
                await channel.send(embed=self.now_playing_embed(track), view=LavalinkControls(self, player.guild.id))
        except Exception as e:
            log.exception("Error in on_wavelink_track_start")
            # Emergency fallback to show error in Discord
            try:
                if channel is not None:
                    await channel.send(f"⚠️ **Debug Error in Player:** `{e}`")
            except:
                pass


    @commands.Cog.listener()
    async def on_wavelink_track_exception(self, payload: wavelink.TrackExceptionEventPayload) -> None:
        player = payload.player
        if player is None or player.guild is None:
            return
        channel_id = self.text_channels.get(player.guild.id)
        channel = self.bot.get_channel(channel_id) if channel_id else None
        if channel is not None:
            await channel.send("Lavalink could not play that track; moving on if another track is queued.")

    @commands.command(help="Join your voice channel.")
    @commands.guild_only()
    async def join(self, ctx: commands.Context) -> None:
        player = await self.ensure_player(ctx)
        if player:
            await ctx.send(f"Connected to **{player.channel.name}** through Lavalink.")

    @commands.command(aliases=["p"], help="Play a URL or search for a song.")
    @commands.guild_only()
    async def play(self, ctx: commands.Context, *, query: str) -> None:
        await self.queue_query(ctx, query)

    @commands.command(aliases=["pn"], help="Add a URL or search result as the next track.")
    @commands.guild_only()
    async def playnext(self, ctx: commands.Context, *, query: str) -> None:
        await self.queue_query(ctx, query, front=True)

    @commands.command(help="Pause the current track.")
    @commands.guild_only()
    async def pause(self, ctx: commands.Context) -> None:
        if not self.is_same_voice_channel(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        player = ctx.guild.voice_client
        if player.playing and not player.paused:
            await player.pause(True)
            await ctx.send("Paused.")
        else:
            await ctx.send("Nothing is playing right now.")

    @commands.command(help="Resume the paused track.")
    @commands.guild_only()
    async def resume(self, ctx: commands.Context) -> None:
        if not self.is_same_voice_channel(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        player = ctx.guild.voice_client
        if player.playing and player.paused:
            await player.pause(False)
            await ctx.send("Resumed.")
        else:
            await ctx.send("The player is not paused.")

    @commands.command(help="Skip the current track.")
    @commands.guild_only()
    async def skip(self, ctx: commands.Context) -> None:
        if not self.is_same_voice_channel(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        player = ctx.guild.voice_client
        if player.playing:
            await player.skip(force=True)
            await ctx.send("Skipped.")
        else:
            await ctx.send("Nothing is playing right now.")

    @commands.command(aliases=["prev"], help="Return to the previous track in this session.")
    @commands.guild_only()
    async def previous(self, ctx: commands.Context) -> None:
        if not self.is_same_voice_channel(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        player = ctx.guild.voice_client
        if not await self.play_previous(player):
            await ctx.send("There is no previous track in this session.")
            return
        await ctx.send("Playing the previous track.")

    @commands.command(help="Stop playback, clear the queue, and disconnect.")
    @commands.guild_only()
    async def stop(self, ctx: commands.Context) -> None:
        if not self.is_same_voice_channel(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        await self.stop_player(ctx.guild.voice_client, disconnect=True)
        await ctx.send("Stopped playback and cleared the queue.")

    @commands.command(aliases=["disconnect", "dc"], help="Disconnect and clear playback.")
    @commands.guild_only()
    async def leave(self, ctx: commands.Context) -> None:
        if not self.is_same_voice_channel(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        await self.stop_player(ctx.guild.voice_client, disconnect=True)
        await ctx.send("Disconnected and cleared the queue.")

    @commands.command(aliases=["q"], help="Show the current queue.")
    @commands.guild_only()
    async def queue(self, ctx: commands.Context) -> None:
        player = ctx.guild.voice_client
        if not isinstance(player, wavelink.Player):
            await ctx.send("The queue is empty.")
            return
        await ctx.send(embed=self.queue_embed(ctx.guild, player))

    @commands.command(aliases=["np"], help="Show the current track.")
    @commands.guild_only()
    async def nowplaying(self, ctx: commands.Context) -> None:
        player = ctx.guild.voice_client
        if not isinstance(player, wavelink.Player) or player.current is None:
            await ctx.send("Nothing is playing right now.")
            return
        await ctx.send(embed=self.now_playing_embed(player.current))

    @commands.command(help="Set the player volume from 0 to 200.")
    @commands.guild_only()
    async def volume(self, ctx: commands.Context, percent: Optional[int] = None) -> None:
        player = ctx.guild.voice_client
        if not isinstance(player, wavelink.Player):
            await ctx.send("I am not connected to a voice channel.")
            return
        if percent is None:
            await ctx.send(f"Volume is {player.volume}%.")
            return
        if not 0 <= percent <= 200:
            await ctx.send("Volume must be between 0 and 200.")
            return
        if not self.is_same_voice_channel(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        self.saved_volumes[ctx.guild.id] = percent
        await player.set_volume(percent)
        await ctx.send(f"Volume set to {percent}%.")

    @commands.command(name="vmute", aliases=["audiomute"], help="Toggle mute without changing the saved volume.")
    @commands.guild_only()
    async def vmute(self, ctx: commands.Context) -> None:
        if not self.is_same_voice_channel(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        muted = await self.toggle_mute(ctx.guild.voice_client)
        await ctx.send("Muted." if muted else "Unmuted.")

    @commands.command(aliases=["ap"], help="Toggle autoplay, or use on/off to set it explicitly.")
    @commands.guild_only()
    async def autoplay(self, ctx: commands.Context, state: Optional[str] = None) -> None:
        if not self.is_same_voice_channel(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        if state is None:
            enabled = self.set_autoplay(ctx.guild.voice_client)
        elif state.lower() in {"on", "enable", "enabled"}:
            enabled = self.set_autoplay(ctx.guild.voice_client, True)
        elif state.lower() in {"off", "disable", "disabled"}:
            enabled = self.set_autoplay(ctx.guild.voice_client, False)
        else:
            await ctx.send("Use `on` or `off`, for example `!autoplay on`.")
            return
        await ctx.send(f"Autoplay is now **{'on' if enabled else 'off'}**.")

    @commands.command(help="Toggle repeating the current track.")
    @commands.guild_only()
    async def loop(self, ctx: commands.Context) -> None:
        if not self.is_same_voice_channel(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        enabled = self.toggle_loop(ctx.guild.voice_client)
        await ctx.send(f"Track repeat is now **{'on' if enabled else 'off'}**.")

    @commands.command(help="Shuffle the upcoming queue.")
    @commands.guild_only()
    async def shuffle(self, ctx: commands.Context) -> None:
        if not self.is_same_voice_channel(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        player = ctx.guild.voice_client
        if len(player.queue) < 2:
            await ctx.send("Add at least two queued tracks to shuffle them.")
            return
        player.queue.shuffle()
        await ctx.send("Shuffled the queue.")

    @commands.command(help="Remove all upcoming tracks.")
    @commands.guild_only()
    async def clear(self, ctx: commands.Context) -> None:
        if not self.is_same_voice_channel(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        player = ctx.guild.voice_client
        count = len(player.queue)
        player.queue.clear()
        await ctx.send(f"Removed {count} queued track{'s' if count != 1 else ''}.")

    @commands.command(aliases=["rm"], help="Remove a queued track by its queue position.")
    @commands.guild_only()
    async def remove(self, ctx: commands.Context, position: int) -> None:
        if not self.is_same_voice_channel(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        player = ctx.guild.voice_client
        if not 1 <= position <= len(player.queue):
            await ctx.send("That queue position does not exist.")
            return
        track = player.queue[position - 1]
        del player.queue[position - 1]
        await ctx.send(f"Removed **{discord.utils.escape_markdown(track.title)}** from the queue.")

    @commands.command(help="Move a queued track to another queue position.")
    @commands.guild_only()
    async def move(self, ctx: commands.Context, from_position: int, to_position: int) -> None:
        if not self.is_same_voice_channel(ctx):
            await ctx.send("Join my voice channel before controlling playback.")
            return
        player = ctx.guild.voice_client
        if not 1 <= from_position <= len(player.queue) or not 1 <= to_position <= len(player.queue):
            await ctx.send("Both queue positions must exist.")
            return
        tracks = list(player.queue)
        track = tracks.pop(from_position - 1)
        tracks.insert(to_position - 1, track)
        player.queue.clear()
        player.queue.put(tracks)
        await ctx.send(f"Moved **{discord.utils.escape_markdown(track.title)}** to #{to_position}.")

    @commands.command(help="Show recently played tracks in this session.")
    @commands.guild_only()
    async def history(self, ctx: commands.Context) -> None:
        player = ctx.guild.voice_client
        if not isinstance(player, wavelink.Player):
            await ctx.send("No tracks have played in this session yet.")
            return
        await ctx.send(embed=self.history_embed(ctx.guild, player))

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
        log.error("Lavalink music command failed", exc_info=error)
        await ctx.send("Something went wrong while handling that command.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LavalinkMusic(bot))
