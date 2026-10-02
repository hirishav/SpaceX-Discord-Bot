import discord
from discord.ext import commands, tasks
import asyncio
import time
import re
from utils import parse_time_to_seconds, format_duration

async def resolve_channel(ctx, token: str):
    if not token:
        return None
    token = token.strip()
    # Check mention <#123> or numerical ID
    match = re.match(r'^<#?(\d+)>$', token)
    if match:
        ch_id = int(match.group(1))
        ch = ctx.guild.get_channel(ch_id)
        if ch:
            return ch
        try:
            ch = await ctx.guild.fetch_channel(ch_id)
            if ch:
                return ch
        except Exception:
            pass

    # Check by exact name or without leading '#'
    clean_name = token.lstrip('#').lower()
    for ch in ctx.guild.channels:
        if ch.name.lower() == clean_name:
            return ch

    # Fallback to standard GuildChannelConverter
    try:
        return await commands.GuildChannelConverter().convert(ctx, token)
    except Exception:
        return None

class ModHide(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.init_db()
        self.check_hidden_channels.start()

    def cog_unload(self):
        self.check_hidden_channels.cancel()

    def init_db(self):
        try:
            cursor = self.bot.db.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS hidden_channels (
                channel_id TEXT PRIMARY KEY,
                previous_view_channel TEXT,
                expires_at INTEGER DEFAULT -1,
                guild_id TEXT
            )
            """)
            cursor.execute("PRAGMA table_info(hidden_channels)")
            cols = [info[1] for info in cursor.fetchall()]
            if 'expires_at' not in cols:
                cursor.execute("ALTER TABLE hidden_channels ADD COLUMN expires_at INTEGER DEFAULT -1")
            if 'guild_id' not in cols:
                cursor.execute("ALTER TABLE hidden_channels ADD COLUMN guild_id TEXT")
            self.bot.db.commit()
        except Exception as e:
            print(f"Error initializing hidden_channels schema: {e}")

    @commands.hybrid_command(name="hide")
    @commands.has_permissions(manage_channels=True)
    async def hide(self, ctx, *, args: str = None):
        """
        Channel ko hide karne ke liye flexible timers ke sath.
        Examples:
        !!hide (current channel permanent)
        !!hide 10m / 1h / 1d / 1month / permanent
        !!hide #channel 1d
        !!hide 1234567890 2h
        !!hide all 1h
        !!hide off / !!hide off #channel / !!hide off all
        """
        if not args:
            return await self.hide_channel(ctx, ctx.channel, -1, -1)

        args_clean = args.strip()
        args_lower = args_clean.lower()

        # Handle "off" actions
        if args_lower == "off":
            return await self.unhide_channel(ctx, ctx.channel)
        if args_lower in ["off all", "all off"]:
            return await self.unhide_all_channels(ctx)
        if args_lower.startswith("off "):
            target_token = args_clean[4:].strip()
            if target_token.lower() == "all":
                return await self.unhide_all_channels(ctx)
            ch = await resolve_channel(ctx, target_token)
            if ch:
                return await self.unhide_channel(ctx, ch)
            return await ctx.send(f"❌ Channel `{target_token}` server me nahi mila!")

        # Handle "all" mass hide
        tokens = args_clean.split()
        if "all" in [t.lower() for t in tokens]:
            other_tokens = [t for t in tokens if t.lower() != "all"]
            dur_str = " ".join(other_tokens) if other_tokens else "permanent"
            dur_secs = parse_time_to_seconds(dur_str)
            if dur_secs is None:
                return await ctx.send(f"❌ Invalid duration `{dur_str}`! Examples: `10m`, `1h`, `1d`, `1month`, `permanent`.")
            expires_at = -1 if dur_secs == -1 else int(time.time()) + dur_secs
            return await self.hide_all_channels(ctx, expires_at, dur_secs)

        # Check if entire argument is just a duration for current channel (e.g. "10m", "1s", "1month", "permanent")
        dur_secs = parse_time_to_seconds(args_clean)
        if dur_secs is not None:
            expires_at = -1 if dur_secs == -1 else int(time.time()) + dur_secs
            return await self.hide_channel(ctx, ctx.channel, expires_at, dur_secs)

        # Check if first token is a channel (e.g. "!!hide #channel 1d" or "!!hide 123456789 2h")
        ch_first = await resolve_channel(ctx, tokens[0])
        if ch_first:
            dur_tokens = " ".join(tokens[1:]).strip()
            if not dur_tokens:
                return await self.hide_channel(ctx, ch_first, -1, -1)
            dur_secs = parse_time_to_seconds(dur_tokens)
            if dur_secs is None:
                return await ctx.send(f"❌ Invalid duration format `{dur_tokens}`! Examples: `10m`, `1h`, `1d`, `1month`, `permanent`.")
            expires_at = -1 if dur_secs == -1 else int(time.time()) + dur_secs
            return await self.hide_channel(ctx, ch_first, expires_at, dur_secs)

        # Check if last token is a channel (e.g. "!!hide 1d #channel")
        ch_last = await resolve_channel(ctx, tokens[-1])
        if ch_last:
            dur_tokens = " ".join(tokens[:-1]).strip()
            dur_secs = parse_time_to_seconds(dur_tokens)
            if dur_secs is None:
                return await ctx.send(f"❌ Invalid duration format `{dur_tokens}`! Examples: `10m`, `1h`, `1d`, `1month`, `permanent`.")
            expires_at = -1 if dur_secs == -1 else int(time.time()) + dur_secs
            return await self.hide_channel(ctx, ch_last, expires_at, dur_secs)

        return await ctx.send(
            "❌ Channel ya duration format recognize nahi hua!\n"
            "**Sahi Tarika (Examples):**\n"
            f"• `{ctx.prefix}hide` (current channel permanent)\n"
            f"• `{ctx.prefix}hide 10m` ya `1h` ya `1d` ya `1month` ya `permanent`\n"
            f"• `{ctx.prefix}hide #channel 1d` ya `{ctx.prefix}hide <channel_id> 1d`\n"
            f"• `{ctx.prefix}hide all 1h` (mass hide all channels)\n"
            f"• `{ctx.prefix}hide off` ya `{ctx.prefix}unhide` (unhide channel)"
        )

    @commands.hybrid_command(name="unhide")
    @commands.has_permissions(manage_channels=True)
    async def unhide(self, ctx, *, target: str = None):
        """Hidden channel ko wapas dikhane aur purani permissions restore karne ke liye."""
        if not target:
            return await self.unhide_channel(ctx, ctx.channel)
            
        target_lower = target.lower().strip()
        if target_lower == "all":
            return await self.unhide_all_channels(ctx)
            
        channel = await resolve_channel(ctx, target)
        if channel:
            return await self.unhide_channel(ctx, channel)
        return await ctx.send("❌ Channel not found! Use `all` ya channel mention/ID provide karein.")

    async def hide_channel(self, ctx, channel, expires_at: int = -1, dur_secs: int = -1):
        if not isinstance(channel, discord.abc.GuildChannel):
            return await ctx.send("❌ You can only hide server channels!")

        cursor = self.bot.db.cursor()
        cursor.execute("SELECT previous_view_channel FROM hidden_channels WHERE channel_id = ?", (str(channel.id),))
        row = cursor.fetchone()

        if row is not None:
            # Already tracked: update timer & guild
            cursor.execute(
                "UPDATE hidden_channels SET expires_at = ?, guild_id = ? WHERE channel_id = ?",
                (expires_at, str(ctx.guild.id), str(channel.id))
            )
            self.bot.db.commit()
            time_display = "Permanent ♾️" if expires_at == -1 else f"<t:{expires_at}:R> (<t:{expires_at}:f>)"
            embed = discord.Embed(
                title="👻 Channel Hide Duration Updated",
                description=f"{channel.mention} is already hidden. Duration timer has been updated.",
                color=discord.Color.dark_grey(),
                timestamp=discord.utils.utcnow()
            )
            embed.add_field(name="📺 Channel", value=f"{channel.mention} (`{channel.id}`)", inline=True)
            embed.add_field(name="⏳ New Duration", value=time_display, inline=True)
            embed.add_field(name="🛡️ Staff", value=ctx.author.mention, inline=True)
            return await ctx.send(embed=embed)

        # Save previous state
        current_val = channel.overwrites_for(ctx.guild.default_role).view_channel
        val_str = str(current_val)

        cursor.execute(
            "INSERT INTO hidden_channels (channel_id, previous_view_channel, expires_at, guild_id) VALUES (?, ?, ?, ?)",
            (str(channel.id), val_str, expires_at, str(ctx.guild.id))
        )
        self.bot.db.commit()

        # Hide it
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Hidden by {ctx.author}")
        
        time_display = "Permanent ♾️" if expires_at == -1 else f"<t:{expires_at}:R> (<t:{expires_at}:f>)"
        embed = discord.Embed(
            title="👻 Channel Hidden",
            description=f"{channel.mention} has been hidden from everyone.",
            color=discord.Color.dark_grey(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="📺 Channel", value=f"{channel.mention} (`{channel.id}`)", inline=True)
        embed.add_field(name="⏳ Duration", value=time_display, inline=True)
        embed.add_field(name="🛡️ Staff", value=ctx.author.mention, inline=True)
        await ctx.send(embed=embed)

    async def unhide_channel(self, ctx, channel):
        if not isinstance(channel, discord.abc.GuildChannel):
            return await ctx.send("❌ You can only unhide server channels!")

        cursor = self.bot.db.cursor()
        cursor.execute("SELECT previous_view_channel FROM hidden_channels WHERE channel_id = ?", (str(channel.id),))
        row = cursor.fetchone()

        if row is None:
            # Fallback: remove overwrite if not tracked in DB
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            if overwrite.view_channel is False:
                overwrite.view_channel = None
                if overwrite.is_empty():
                    await channel.set_permissions(ctx.guild.default_role, overwrite=None, reason=f"Unhidden by {ctx.author}")
                else:
                    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Unhidden by {ctx.author}")
                return await ctx.send(f"✅ {channel.mention} unhidden (was not tracked in DB, reset to default).")
            return await ctx.send("❌ This channel is not marked as hidden!")

        val_str = row[0]
        if val_str == "True":
            new_val = True
        elif val_str == "False":
            new_val = False
        else:
            new_val = None

        cursor.execute("DELETE FROM hidden_channels WHERE channel_id = ?", (str(channel.id),))
        self.bot.db.commit()

        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = new_val
        if overwrite.is_empty():
            await channel.set_permissions(ctx.guild.default_role, overwrite=None, reason=f"Unhidden by {ctx.author}")
        else:
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Unhidden by {ctx.author}")

        embed = discord.Embed(
            title="👁️ Channel Unhidden",
            description=f"{channel.mention} has been unhidden. Restored original permissions.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.add_field(name="📺 Channel", value=f"{channel.mention} (`{channel.id}`)", inline=True)
        embed.add_field(name="🛡️ Staff", value=ctx.author.mention, inline=True)
        await ctx.send(embed=embed)

    async def hide_all_channels(self, ctx, expires_at: int = -1, dur_secs: int = -1):
        time_display = "Permanent ♾️" if expires_at == -1 else f"<t:{expires_at}:R> (<t:{expires_at}:f>)"
        msg = await ctx.send(f"🔄 Hiding all text and voice channels for **{time_display}**... Please wait.")
        cursor = self.bot.db.cursor()
        count = 0
        
        channels = [c for c in ctx.guild.channels if isinstance(c, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel))]
        
        for channel in channels:
            cursor.execute("SELECT previous_view_channel FROM hidden_channels WHERE channel_id = ?", (str(channel.id),))
            row = cursor.fetchone()
            if row is not None:
                cursor.execute(
                    "UPDATE hidden_channels SET expires_at = ?, guild_id = ? WHERE channel_id = ?",
                    (expires_at, str(ctx.guild.id), str(channel.id))
                )
            else:
                current_val = channel.overwrites_for(ctx.guild.default_role).view_channel
                val_str = str(current_val)
                cursor.execute(
                    "INSERT INTO hidden_channels (channel_id, previous_view_channel, expires_at, guild_id) VALUES (?, ?, ?, ?)",
                    (str(channel.id), val_str, expires_at, str(ctx.guild.id))
                )
            
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.view_channel = False
            try:
                await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Mass hidden by {ctx.author}")
                count += 1
            except discord.Forbidden:
                pass

        self.bot.db.commit()
        await msg.edit(content=f"✅ Successfully hidden **{count}** channels ({time_display}).")

    async def unhide_all_channels(self, ctx):
        msg = await ctx.send("🔄 Unhiding all tracked channels... Please wait.")
        cursor = self.bot.db.cursor()
        
        channels = [c for c in ctx.guild.channels if isinstance(c, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel))]
        hidden_ids = [str(c.id) for c in channels]
            
        if not hidden_ids:
            return await msg.edit(content="✅ No channels to unhide.")

        placeholders = ','.join('?' for _ in hidden_ids)
        cursor.execute(f"SELECT channel_id, previous_view_channel FROM hidden_channels WHERE channel_id IN ({placeholders})", hidden_ids)
        rows = cursor.fetchall()
        
        count = 0
        for channel_id_str, val_str in rows:
            channel = ctx.guild.get_channel(int(channel_id_str))
            if not channel:
                continue
                
            if val_str == "True":
                new_val = True
            elif val_str == "False":
                new_val = False
            else:
                new_val = None
                
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.view_channel = new_val
            
            try:
                if overwrite.is_empty():
                    await channel.set_permissions(ctx.guild.default_role, overwrite=None, reason=f"Mass unhidden by {ctx.author}")
                else:
                    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Mass unhidden by {ctx.author}")
                
                cursor.execute("DELETE FROM hidden_channels WHERE channel_id = ?", (channel_id_str,))
                count += 1
            except discord.Forbidden:
                pass
            
        self.bot.db.commit()
        await msg.edit(content=f"✅ Successfully unhidden **{count}** channels and restored original permissions.")

    @tasks.loop(seconds=5)
    async def check_hidden_channels(self):
        await self.bot.wait_until_ready()
        current_time = int(time.time())
        try:
            cursor = self.bot.db.cursor()
            cursor.execute(
                "SELECT channel_id, previous_view_channel, guild_id FROM hidden_channels WHERE expires_at != -1 AND expires_at <= ?",
                (current_time,)
            )
            expired = cursor.fetchall()
            if not expired:
                return

            for ch_id_str, val_str, g_id_str in expired:
                try:
                    ch_id = int(ch_id_str)
                    channel = self.bot.get_channel(ch_id)
                    if not channel:
                        try:
                            channel = await self.bot.fetch_channel(ch_id)
                        except Exception:
                            channel = None

                    if channel:
                        if val_str == "True":
                            new_val = True
                        elif val_str == "False":
                            new_val = False
                        else:
                            new_val = None

                        guild = channel.guild
                        overwrite = channel.overwrites_for(guild.default_role)
                        overwrite.view_channel = new_val
                        if overwrite.is_empty():
                            await channel.set_permissions(guild.default_role, overwrite=None, reason="Hide duration expired (Auto-Unhide)")
                        else:
                            await channel.set_permissions(guild.default_role, overwrite=overwrite, reason="Hide duration expired (Auto-Unhide)")

                        embed = discord.Embed(
                            title="👁️ Channel Unhidden (Timer Expired)",
                            description=f"{channel.mention} has automatically been unhidden. Original permissions restored.",
                            color=discord.Color.green(),
                            timestamp=discord.utils.utcnow()
                        )
                        try:
                            await channel.send(embed=embed)
                        except Exception:
                            pass
                except Exception as e:
                    print(f"Error auto-unhiding channel {ch_id_str}: {e}")
                finally:
                    cursor.execute("DELETE FROM hidden_channels WHERE channel_id = ?", (ch_id_str,))

            self.bot.db.commit()
        except Exception as e:
            print(f"Error in check_hidden_channels loop: {e}")

async def setup(bot):
    await bot.add_cog(ModHide(bot))
