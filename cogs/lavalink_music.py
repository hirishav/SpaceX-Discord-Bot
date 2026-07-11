"""Lavalink-backed music commands selected with AUDIO_BACKEND=lavalink."""

from __future__ import annotations

import logging
import sqlite3
import asyncio
from typing import Optional

import discord
import wavelink
from discord.ext import commands

log = logging.getLogger(__name__)

# --- Helper Functions for DB ---
def get_dj_role(server_id: int) -> Optional[int]:
    try:
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        cursor.execute("SELECT role_id FROM dj_roles WHERE server_id = ?", (str(server_id),))
        res = cursor.fetchone()
        conn.close()
        if res:
            return int(res[0])
    except Exception:
        pass
    return None

def is_247_enabled(server_id: int) -> bool:
    try:
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        cursor.execute("SELECT enabled FROM twentyfour_seven WHERE server_id = ?", (str(server_id),))
        res = cursor.fetchone()
        conn.close()
        if res and res[0] == 1:
            return True
    except Exception:
        pass
    return False

def can_control(ctx: commands.Context) -> bool:
    """Check if user has DJ role, is Administrator, or is alone with the bot."""
    if ctx.author.guild_permissions.administrator:
        return True
    
    dj_role_id = get_dj_role(ctx.guild.id)
    if dj_role_id:
        role = ctx.guild.get_role(dj_role_id)
        if role and role in ctx.author.roles:
            return True

    vc = ctx.guild.voice_client
    if vc and getattr(vc, 'channel', None):
        # Allow if the user is the only non-bot listener
        members = [m for m in vc.channel.members if not m.bot]
        if len(members) <= 1 and ctx.author in members:
            return True
            
    # Default fail if DJ role exists but user doesn't have it (and isn't alone/admin)
    if dj_role_id:
        return False
        
    return True # If no DJ role is set, anyone can control

class LavalinkControls(discord.ui.View):
    """Interactive controls attached to each Lavalink now-playing message."""

    def __init__(self, cog: "LavalinkMusic", guild_id: int):
        super().__init__(timeout=1800)
        self.cog = cog
        self.guild_id = guild_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if getattr(interaction.user, 'guild_permissions', None) and interaction.user.guild_permissions.administrator:
            return True
            
        dj_role_id = get_dj_role(self.guild_id)
        if dj_role_id and interaction.guild:
            role = interaction.guild.get_role(dj_role_id)
            if role and role in getattr(interaction.user, 'roles', []):
                return True
                
        player = interaction.guild.voice_client if interaction.guild else None
        if player and getattr(player, 'channel', None):
            members = [m for m in player.channel.members if not m.bot]
            if len(members) <= 1 and interaction.user in members:
                return True
                
        if dj_role_id:
            await interaction.response.send_message("❌ You need the DJ role to use these controls.", ephemeral=True)
            return False
            
        return True

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
        if player is None: return
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
        if player is None: return
        if not await self.cog.play_previous(player):
            await interaction.response.send_message("There is no previous track in this session.", ephemeral=True)
            return
        await interaction.response.send_message("Playing the previous track.", ephemeral=True)

    @discord.ui.button(label="Skip", emoji="⏭️", style=discord.ButtonStyle.primary, row=0)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        player = await self._player_for(interaction)
        if player is None: return
        if not player.playing:
            await interaction.response.send_message("Nothing is playing right now.", ephemeral=True)
            return
        await player.skip(force=True)
        await interaction.response.send_message("Skipped the current track.", ephemeral=True)

    @discord.ui.button(label="Stop", emoji="⏹️", style=discord.ButtonStyle.danger, row=0)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        player = await self._player_for(interaction)
        if player is None: return
        await self.cog.stop_player(player, disconnect=not is_247_enabled(self.guild_id))
        await interaction.response.send_message("Stopped playback and cleared the queue.", ephemeral=True)

    @discord.ui.button(label="Queue", emoji="📜", style=discord.ButtonStyle.secondary, row=1)
    async def queue(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        player = await self._player_for(interaction)
        if player is None: return
        await interaction.response.send_message(embed=self.cog.queue_embed(interaction.guild, player), ephemeral=True)

    @discord.ui.button(label="Loop", emoji="🔁", style=discord.ButtonStyle.secondary, row=1)
    async def loop(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        player = await self._player_for(interaction)
        if player is None: return
        enabled = self.cog.toggle_loop(player)
        button.label = "Loop On" if enabled else "Loop"
        button.style = discord.ButtonStyle.success if enabled else discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Shuffle", emoji="🔀", style=discord.ButtonStyle.secondary, row=1)
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        player = await self._player_for(interaction)
        if player is None: return
        if len(player.queue) < 2:
            await interaction.response.send_message("Add at least two queued tracks to shuffle them.", ephemeral=True)
            return
        player.queue.shuffle()
        await interaction.response.send_message("Shuffled the queue.", ephemeral=True)

    @discord.ui.button(label="Autoplay", emoji="♾️", style=discord.ButtonStyle.secondary, row=1)
    async def autoplay(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        player = await self._player_for(interaction)
        if player is None: return
        enabled = self.cog.set_autoplay(player)
        button.label = "Autoplay On" if enabled else "Autoplay"
        button.style = discord.ButtonStyle.success if enabled else discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)


class LavalinkMusic(commands.Cog):
    """Ultimate Music commands with premium features."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.text_channels: dict[int, int] = {}
        self.saved_volumes: dict[int, int] = {}
        self.idle_timers: dict[int, asyncio.Task] = {}

    @staticmethod
    def format_duration(milliseconds: int) -> str:
        seconds = max(0, int(milliseconds // 1000))
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes}:{seconds:02d}"

    @staticmethod
    def create_progress_bar(current: int, total: int, length: int = 15) -> str:
        if total <= 0: return "🔘" + "▬" * (length - 1)
        progress = int(length * (current / total))
        progress = max(0, min(length - 1, progress))
        bar = ["▬"] * length
        bar[progress] = "🔘"
        return "".join(bar)

    @staticmethod
    def is_same_voice_channel(ctx: commands.Context) -> bool:
        player = ctx.guild.voice_client
        return bool(
            isinstance(player, wavelink.Player)
            and ctx.author.voice
            and ctx.author.voice.channel == player.channel
        )

    def cancel_idle(self, guild_id: int):
        if guild_id in self.idle_timers:
            self.idle_timers[guild_id].cancel()
            del self.idle_timers[guild_id]

    async def idle_timeout(self, guild_id: int, player: wavelink.Player):
        await asyncio.sleep(180)  # 3 minutes idle
        if not is_247_enabled(guild_id):
            if not player.playing:
                await player.disconnect()
                channel_id = self.text_channels.get(guild_id)
                if channel_id:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        await channel.send("💤 Left the voice channel due to inactivity. Enable 24/7 mode to prevent this!")
        self.cancel_idle(guild_id)

    async def ensure_player(self, ctx: commands.Context) -> Optional[wavelink.Player]:
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("Join a voice channel first.")
            return None

        requested_channel = ctx.author.voice.channel
        voice_client = ctx.guild.voice_client
        if voice_client is None:
            player = await requested_channel.connect(cls=wavelink.Player, self_deaf=True)
            player.autoplay = wavelink.AutoPlayMode.enabled # Default Autoplay ON
            await player.set_volume(self.saved_volumes.get(ctx.guild.id, 80)) # Default 80%
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
        if not tracks:
            tracks = await wavelink.Playable.search(query)
        return tracks[0] if tracks else None

    async def queue_query(self, ctx: commands.Context, query: str, *, front: bool = False) -> None:
        player = await self.ensure_player(ctx)
        if player is None: return

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
        
        self.cancel_idle(ctx.guild.id)
        
        if front and player.playing:
            tracks = [track, *list(player.queue)]
            player.queue.clear()
            player.queue.put(tracks)
        else:
            player.queue.put(track)

        if not player.playing:
            await player.play(player.queue.get(), volume=self.saved_volumes.get(ctx.guild.id, 80))
            await searching.delete()
        else:
            placement = "next" if front else f"#{len(player.queue)}"
            await searching.edit(content=f"✅ Added **{discord.utils.escape_markdown(track.title)}** ({placement}).")

    def now_playing_embed(self, track: wavelink.Playable, position: int = 0) -> discord.Embed:
        title = discord.utils.escape_markdown(track.title)
        
        source = track.source if hasattr(track, 'source') else 'unknown'
        color = discord.Color.from_str("#ff0077") # Premium pinkish-purple default
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
        
        requester = "Autoplay ♾️"
        if hasattr(track, "extras") and track.extras:
            if hasattr(track.extras, "get"):
                requester = track.extras.get("requester", "Autoplay ♾️")
            else:
                requester = getattr(track.extras, "requester", "Autoplay ♾️")

        bar = self.create_progress_bar(position, track.length)
        embed.description = f"`{self.format_duration(position)}` {bar} `{self.format_duration(track.length)}`\n\n👤 **Requested by:** {requester}\n🎙️ **Channel:** `{discord.utils.escape_markdown(track.author or 'Unknown')}`"
        
        if track.artwork:
            embed.set_thumbnail(url=track.artwork)
            
        embed.set_footer(text="Powered by Annieee ✨")
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
            color=discord.Color.from_str("#ff0077"),
        )
        autoplay = "ON" if player.autoplay is wavelink.AutoPlayMode.enabled else "OFF"
        repeat = "ON" if player.queue.mode is wavelink.QueueMode.loop else "OFF"
        t247 = "ON" if is_247_enabled(guild.id) else "OFF"
        embed.set_footer(text=f"Autoplay: {autoplay} | Repeat: {repeat} | 24/7: {t247} | Volume: {player.volume}%")
        return embed

    @staticmethod
    def toggle_loop(player: wavelink.Player) -> bool:
        enabled = player.queue.mode is not wavelink.QueueMode.loop
        player.queue.mode = wavelink.QueueMode.loop if enabled else wavelink.QueueMode.normal
        return enabled

    @staticmethod
    def set_autoplay(player: wavelink.Player, enabled: Optional[bool] = None) -> bool:
        currently_enabled = player.autoplay is wavelink.AutoPlayMode.enabled
        enabled = not currently_enabled if enabled is None else enabled
        player.autoplay = wavelink.AutoPlayMode.enabled if enabled else wavelink.AutoPlayMode.partial
        return enabled

    async def toggle_mute(self, player: wavelink.Player) -> bool:
        guild_id = player.guild.id
        if player.volume > 0:
            self.saved_volumes[guild_id] = player.volume
            await player.set_volume(0)
            return True
        await player.set_volume(self.saved_volumes.get(guild_id, 80))
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
            if player is None or player.guild is None: return
            
            self.cancel_idle(player.guild.id)
            track = payload.original or payload.track
            
            channel_id = self.text_channels.get(player.guild.id)
            if hasattr(track, "extras") and track.extras:
                if hasattr(track.extras, "get"):
                    channel_id = track.extras.get("channel_id", channel_id)
                else:
                    channel_id = getattr(track.extras, "channel_id", channel_id)

            channel = None
            if channel_id:
                channel = self.bot.get_channel(channel_id)
                if channel is None:
                    try: channel = await self.bot.fetch_channel(channel_id)
                    except: pass
            
            if channel is None and hasattr(player, 'channel') and player.channel:
                channel = player.channel

            if channel is not None:
                await channel.send(embed=self.now_playing_embed(track, 0), view=LavalinkControls(self, player.guild.id))
        except Exception as e:
            log.exception("Error in on_wavelink_track_start")
            # Try to send error to Discord
            try:
                if 'channel' in locals() and channel is not None:
                    await channel.send(f"⚠️ Debug Error in Player: `{e}`")
                elif hasattr(payload.player, 'channel') and payload.player.channel:
                    await payload.player.channel.send(f"⚠️ Debug Error in Player: `{e}`")
            except:
                pass

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload) -> None:
        player = payload.player
        if player is None or player.guild is None: return
        
        if not player.playing and len(player.queue) == 0:
            self.cancel_idle(player.guild.id)
            self.idle_timers[player.guild.id] = self.bot.loop.create_task(self.idle_timeout(player.guild.id, player))

    @commands.command(help="Set the DJ role for the server.")
    @commands.has_permissions(administrator=True)
    async def setdj(self, ctx: commands.Context, role: discord.Role) -> None:
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        cursor.execute("REPLACE INTO dj_roles (server_id, role_id) VALUES (?, ?)", (str(ctx.guild.id), str(role.id)))
        conn.commit()
        conn.close()
        await ctx.send(f"✅ DJ Role has been set to **{role.name}**.")

    @commands.command(name="247", aliases=["24/7"], help="Toggle 24/7 mode.")
    @commands.has_permissions(administrator=True)
    async def toggle_247(self, ctx: commands.Context) -> None:
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        enabled = is_247_enabled(ctx.guild.id)
        new_val = 0 if enabled else 1
        cursor.execute("REPLACE INTO twentyfour_seven (server_id, enabled) VALUES (?, ?)", (str(ctx.guild.id), new_val))
        conn.commit()
        conn.close()
        
        if new_val == 1:
            self.cancel_idle(ctx.guild.id)
            await ctx.send("✅ **24/7 Mode ENABLED**. I will no longer leave the voice channel when idle.")
        else:
            await ctx.send("❌ **24/7 Mode DISABLED**. I will leave the voice channel when inactive.")

    @commands.command(help="Join your voice channel.")
    @commands.guild_only()
    async def join(self, ctx: commands.Context) -> None:
        if not can_control(ctx):
            return await ctx.send("❌ You need the DJ role to use this command.")
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
        if not can_control(ctx):
            return await ctx.send("❌ You need the DJ role to use this command.")
        if not self.is_same_voice_channel(ctx):
            return await ctx.send("Join my voice channel before controlling playback.")
        
        player = ctx.guild.voice_client
        if player.playing and not player.paused:
            await player.pause(True)
            await ctx.send("⏸️ Paused.")
        else:
            await ctx.send("Nothing is playing right now.")

    @commands.command(help="Resume the paused track.")
    @commands.guild_only()
    async def resume(self, ctx: commands.Context) -> None:
        if not can_control(ctx):
            return await ctx.send("❌ You need the DJ role to use this command.")
        if not self.is_same_voice_channel(ctx):
            return await ctx.send("Join my voice channel before controlling playback.")
        
        player = ctx.guild.voice_client
        if player.playing and player.paused:
            await player.pause(False)
            await ctx.send("▶️ Resumed.")
        else:
            await ctx.send("The player is not paused.")

    @commands.command(aliases=["s"], help="Skip the current track.")
    @commands.guild_only()
    async def skip(self, ctx: commands.Context) -> None:
        if not can_control(ctx):
            return await ctx.send("❌ You need the DJ role to use this command.")
        if not self.is_same_voice_channel(ctx):
            return await ctx.send("Join my voice channel before controlling playback.")
            
        player = ctx.guild.voice_client
        if player.playing:
            await player.skip(force=True)
            await ctx.send("⏭️ Skipped.")
        else:
            await ctx.send("Nothing is playing right now.")
            
    @commands.command(aliases=["prev"], help="Return to the previous track in this session.")
    @commands.guild_only()
    async def previous(self, ctx: commands.Context) -> None:
        if not can_control(ctx):
            return await ctx.send("❌ You need the DJ role to use this command.")
        if not self.is_same_voice_channel(ctx):
            return await ctx.send("Join my voice channel before controlling playback.")
            
        player = ctx.guild.voice_client
        if not await self.play_previous(player):
            await ctx.send("There is no previous track in this session.")
            return
        await ctx.send("Playing the previous track.")

    @commands.command(help="Stop playback, clear the queue, and disconnect.")
    @commands.guild_only()
    async def stop(self, ctx: commands.Context) -> None:
        if not can_control(ctx):
            return await ctx.send("❌ You need the DJ role to use this command.")
        if not self.is_same_voice_channel(ctx):
            return await ctx.send("Join my voice channel before controlling playback.")
            
        await self.stop_player(ctx.guild.voice_client, disconnect=not is_247_enabled(ctx.guild.id))
        await ctx.send("⏹️ Stopped playback and cleared the queue.")

    @commands.command(aliases=["dc", "leave"], help="Disconnect and clear playback.")
    @commands.guild_only()
    async def disconnect(self, ctx: commands.Context) -> None:
        if not can_control(ctx):
            return await ctx.send("❌ You need the DJ role to use this command.")
        if not self.is_same_voice_channel(ctx):
            return await ctx.send("Join my voice channel before controlling playback.")
            
        await self.stop_player(ctx.guild.voice_client, disconnect=True)
        await ctx.send("👋 Disconnected and cleared the queue.")

    @commands.command(aliases=["q"], help="Show the current queue.")
    @commands.guild_only()
    async def queue(self, ctx: commands.Context) -> None:
        player = ctx.guild.voice_client
        if not isinstance(player, wavelink.Player):
            return await ctx.send("The queue is empty.")
        await ctx.send(embed=self.queue_embed(ctx.guild, player))

    @commands.command(aliases=["np", "now"], help="Show the current track.")
    @commands.guild_only()
    async def nowplaying(self, ctx: commands.Context) -> None:
        player = ctx.guild.voice_client
        if not isinstance(player, wavelink.Player) or player.current is None:
            return await ctx.send("Nothing is playing right now.")
        await ctx.send(embed=self.now_playing_embed(player.current, player.position))

    @commands.command(aliases=["vol"], help="Set the player volume from 0 to 200.")
    @commands.guild_only()
    async def volume(self, ctx: commands.Context, percent: Optional[int] = None) -> None:
        if not can_control(ctx):
            return await ctx.send("❌ You need the DJ role to use this command.")
            
        player = ctx.guild.voice_client
        if not isinstance(player, wavelink.Player):
            return await ctx.send("I am not connected to a voice channel.")
            
        if percent is None:
            return await ctx.send(f"🔊 Volume is {player.volume}%.")
            
        if not 0 <= percent <= 200:
            return await ctx.send("Volume must be between 0 and 200.")
            
        if not self.is_same_voice_channel(ctx):
            return await ctx.send("Join my voice channel before controlling playback.")
            
        self.saved_volumes[ctx.guild.id] = percent
        await player.set_volume(percent)
        await ctx.send(f"🔊 Volume set to {percent}%.")

    @commands.command(help="Seek to a specific position in the track (e.g. 1:30 or 90)")
    @commands.guild_only()
    async def seek(self, ctx: commands.Context, time_str: str) -> None:
        if not can_control(ctx):
            return await ctx.send("❌ You need the DJ role to use this command.")
        if not self.is_same_voice_channel(ctx):
            return await ctx.send("Join my voice channel before controlling playback.")
            
        player = ctx.guild.voice_client
        if not isinstance(player, wavelink.Player) or not player.current:
            return await ctx.send("Nothing is playing right now.")
            
        seconds = 0
        if ":" in time_str:
            parts = time_str.split(":")
            if len(parts) == 2:
                seconds = int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        else:
            seconds = int(time_str)
            
        ms = seconds * 1000
        await player.seek(ms)
        await ctx.send(f"⏩ Seeked to `{self.format_duration(ms)}`")

    @commands.command(help="Apply Bassboost or EQ filters (none, low, medium, high)")
    @commands.guild_only()
    async def bassboost(self, ctx: commands.Context, level: str = "medium") -> None:
        if not can_control(ctx):
            return await ctx.send("❌ You need the DJ role to use this command.")
        if not self.is_same_voice_channel(ctx):
            return await ctx.send("Join my voice channel before controlling playback.")
            
        player = ctx.guild.voice_client
        if not isinstance(player, wavelink.Player):
            return await ctx.send("I am not connected to a voice channel.")

        level = level.lower()
        if level in ["none", "off", "0"]:
            filters = player.filters
            filters.equalizer.set(bands=[])
            await player.set_filters(filters)
            return await ctx.send("🎛️ Bassboost turned OFF.")
            
        bands = []
        if level == "low":
            bands = [(0, 0.15), (1, 0.10), (2, 0.05)]
        elif level == "medium":
            bands = [(0, 0.35), (1, 0.25), (2, 0.15)]
        elif level in ["high", "max"]:
            bands = [(0, 0.55), (1, 0.45), (2, 0.35)]
        else:
            return await ctx.send("Invalid level. Choose `none`, `low`, `medium`, or `high`.")
            
        filters = player.filters
        filters.equalizer.set(bands=[wavelink.filters.EQBand(band=b[0], gain=b[1]) for b in bands])
        await player.set_filters(filters)
        await ctx.send(f"🎛️ Bassboost set to **{level.title()}**.")

    @commands.command(aliases=["ap"], help="Toggle autoplay.")
    @commands.guild_only()
    async def autoplay(self, ctx: commands.Context, state: Optional[str] = None) -> None:
        if not can_control(ctx):
            return await ctx.send("❌ You need the DJ role to use this command.")
        if not self.is_same_voice_channel(ctx):
            return await ctx.send("Join my voice channel before controlling playback.")
            
        if state is None:
            enabled = self.set_autoplay(ctx.guild.voice_client)
        elif state.lower() in {"on", "enable"}:
            enabled = self.set_autoplay(ctx.guild.voice_client, True)
        elif state.lower() in {"off", "disable"}:
            enabled = self.set_autoplay(ctx.guild.voice_client, False)
        else:
            return await ctx.send("Use `on` or `off`.")
            
        await ctx.send(f"♾️ Autoplay is now **{'ON' if enabled else 'OFF'}**.")

    @commands.command(help="Remove a track from queue.")
    @commands.guild_only()
    async def remove(self, ctx: commands.Context, position: int) -> None:
        if not can_control(ctx):
            return await ctx.send("❌ You need the DJ role to use this command.")
        if not self.is_same_voice_channel(ctx):
            return await ctx.send("Join my voice channel before controlling playback.")
            
        player = ctx.guild.voice_client
        if not 1 <= position <= len(player.queue):
            return await ctx.send("That queue position does not exist.")
            
        track = player.queue[position - 1]
        del player.queue[position - 1]
        await ctx.send(f"🗑️ Removed **{discord.utils.escape_markdown(track.title)}** from the queue.")

    @commands.command(aliases=["cq"], help="Clear all upcoming tracks.")
    @commands.guild_only()
    async def clearqueue(self, ctx: commands.Context) -> None:
        if not can_control(ctx):
            return await ctx.send("❌ You need the DJ role to use this command.")
        if not self.is_same_voice_channel(ctx):
            return await ctx.send("Join my voice channel before controlling playback.")
            
        player = ctx.guild.voice_client
        count = len(player.queue)
        player.queue.clear()
        await ctx.send(f"🗑️ Removed {count} queued tracks.")

    @commands.command(help="Show recently played tracks in this session.")
    @commands.guild_only()
    async def history(self, ctx: commands.Context) -> None:
        player = ctx.guild.voice_client
        if not isinstance(player, wavelink.Player):
            return await ctx.send("No tracks have played in this session yet.")
            
        history = list(player.queue.history or [])[-10:]
        description = "\n".join(
            f"`{index}.` {discord.utils.escape_markdown(track.title)}"
            for index, track in enumerate(reversed(history), start=1)
        )
        embed = discord.Embed(
            title=f"Recently played in {ctx.guild.name}",
            description=description or "No tracks have played in this session yet.",
            color=discord.Color.blurple(),
        )
        await ctx.send(embed=embed)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing an argument. Try `{ctx.prefix}help {ctx.command.qualified_name}`.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"That argument is not valid. Try `{ctx.prefix}help {ctx.command.qualified_name}`.")
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("Music commands can only be used in a server.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
        else:
            log.error("Lavalink music command failed", exc_info=error)
            await ctx.send("Something went wrong while handling that command.")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LavalinkMusic(bot))
