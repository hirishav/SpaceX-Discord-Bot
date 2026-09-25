import discord
from discord.ext import commands, tasks
import json
import os
import time
import re

DISBOARD_ID = 302050872383242240
SETTINGS_FILE = "settings.json"

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    try:
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_settings(data):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def parse_time(time_str):
    """Parses time strings like '1h 30m' or '45m' into total seconds."""
    time_str = time_str.lower()
    hours = 0
    minutes = 0
    
    h_match = re.search(r'(\d+)\s*h', time_str)
    m_match = re.search(r'(\d+)\s*m', time_str)
    
    if h_match:
        hours = int(h_match.group(1))
    if m_match:
        minutes = int(m_match.group(1))
        
    total = hours * 3600 + minutes * 60
    return total if total > 0 else None


class ModBump(commands.Cog):
    """
    Commands to track and manage Disboard bumps.
    """
    def __init__(self, bot):
        self.bot = bot
        self.settings = load_settings()
        self.bump_loop.start()

    def cog_unload(self):
        self.bump_loop.cancel()

    def get_guild_settings(self, guild_id):
        guild_id = str(guild_id)
        # Reload safely in case other cogs write to settings.json concurrently
        self.settings = load_settings()
        if "bump_system" not in self.settings:
            self.settings["bump_system"] = {}
        if guild_id not in self.settings["bump_system"]:
            self.settings["bump_system"][guild_id] = {}
        return self.settings["bump_system"][guild_id]

    def update_setting(self, guild_id, key, value):
        guild_id = str(guild_id)
        self.settings = load_settings()
        if "bump_system" not in self.settings:
            self.settings["bump_system"] = {}
        if guild_id not in self.settings["bump_system"]:
            self.settings["bump_system"][guild_id] = {}
            
        self.settings["bump_system"][guild_id][key] = value
        save_settings(self.settings)

    @tasks.loop(minutes=1)
    async def bump_loop(self):
        current_time = time.time()
        self.settings = load_settings()
        bump_data = self.settings.get("bump_system", {})
        
        for guild_id, g_settings in list(bump_data.items()):
            next_bump = g_settings.get("next_bump_time")
            if next_bump and current_time >= next_bump:
                channel_id = g_settings.get("bump_channel")
                if channel_id:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        role_id = g_settings.get("bump_role")
                        content = f"<@&{role_id}>" if role_id else ""
                        
                        embed = discord.Embed(
                            title="⏰ It's Bump Time!",
                            description="Use `/bump` to bump the server on Disboard!",
                            color=discord.Color.blue()
                        )
                        try:
                            await channel.send(content=content, embed=embed)
                        except discord.Forbidden:
                            pass
                
                # Clear the next_bump_time after sending the reminder
                self.update_setting(guild_id, "next_bump_time", None)

    @bump_loop.before_loop
    async def before_bump_loop(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or message.author == self.bot.user:
            return

        ctx = await self.bot.get_context(message)
        guild_id = str(message.guild.id)
        g_settings = self.get_guild_settings(guild_id)
        restricted_channel_id = g_settings.get("bump_restricted_channel")



        # ----------------------------------------------------
        # Disboard Bot Listener
        # ----------------------------------------------------
        if message.author.id == DISBOARD_ID:
            if restricted_channel_id and message.channel.id != restricted_channel_id:
                return
            
            if message.embeds:
                embed = message.embeds[0]
                desc = (embed.description or "").lower()
                title = (embed.title or "").lower()

                # Success Bump
                if "bump done" in desc or "bump done" in title:
                    self.update_setting(guild_id, "bump_channel", message.channel.id)
                    self.update_setting(guild_id, "next_bump_time", time.time() + 7200) # 2 hours
                    await message.channel.send("⏱️ Bump detected! I will remind you to bump again in exactly 2 hours.")
                    return

                # Cooldown Bump
                if "wait another" in desc:
                    total_seconds = parse_time(desc)
                    if total_seconds:
                        self.update_setting(guild_id, "bump_channel", message.channel.id)
                        self.update_setting(guild_id, "next_bump_time", time.time() + total_seconds)
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        
                        time_str = ""
                        if hours > 0: time_str += f"{hours}h "
                        if minutes > 0: time_str += f"{minutes}m"
                        if not time_str.strip(): time_str = "less than a minute"
                        
                        await message.channel.send(f"⏱️ Cooldown detected! I'll remind you to bump again in {time_str.strip()}.")
                    return

        # ----------------------------------------------------
        # Prefix-less Shortcuts
        # ----------------------------------------------------
        if restricted_channel_id and message.channel.id == restricted_channel_id:
            if ctx.valid:
                return # Avoid double processing if user has global prefix-less access
                
            content_lower = message.content.lower().strip()
            
            if content_lower in ["bs", "bumpstatus"]:
                await self._bump_status_logic(message.channel, guild_id)
                return
            
            if message.author.guild_permissions.administrator:
                time_to_sync = None
                if content_lower.startswith("sb "):
                    time_to_sync = content_lower[3:]
                elif content_lower.startswith("bp "):
                    time_to_sync = content_lower[3:]
                elif re.fullmatch(r'^(\d+\s*h[a-z]*)?\s*(\d+\s*m[a-z]*)?$', content_lower):
                    time_to_sync = content_lower
                
                if time_to_sync:
                    parsed_seconds = parse_time(time_to_sync)
                    if parsed_seconds:
                        self.update_setting(guild_id, "next_bump_time", time.time() + parsed_seconds)
                        self.update_setting(guild_id, "bump_channel", message.channel.id)
                        await message.channel.send(f"✅ Timer manually synced to **{time_to_sync.strip()}** from now.")
                        return

    # ----------------------------------------------------
    # Commands
    # ----------------------------------------------------

    @commands.command(aliases=["sbr"])
    @commands.has_permissions(administrator=True)
    async def setbumprole(self, ctx, role: discord.Role = None):
        """Sets the role to ping when it's bump time. Leave empty to remove."""
        guild_id = str(ctx.guild.id)
        if role is None:
            self.update_setting(guild_id, "bump_role", None)
            await ctx.send("✅ Bump role has been removed.")
        else:
            self.update_setting(guild_id, "bump_role", role.id)
            await ctx.send(f"✅ Bump role has been set to **{role.name}**.")

    @commands.command(aliases=["sb"])
    @commands.has_permissions(administrator=True)
    async def setbump(self, ctx, *, arg: str):
        """
        Set bump settings.
        Examples:
        `!!setbump #channel` - Restrict tracking to a specific channel.
        `!!setbump remove` - Remove channel restriction.
        `!!setbump 1h 30m` - Manually set the bump timer.
        """
        guild_id = str(ctx.guild.id)
        arg_lower = arg.lower().strip()

        if arg_lower == "remove":
            self.update_setting(guild_id, "bump_restricted_channel", None)
            await ctx.send("✅ Bump channel restriction has been removed.")
            return

        if ctx.message.channel_mentions:
            channel = ctx.message.channel_mentions[0]
            self.update_setting(guild_id, "bump_restricted_channel", channel.id)
            await ctx.send(f"✅ Bump tracking and commands are now restricted to {channel.mention}.")
            return

        # Check if it's a time string
        parsed_seconds = parse_time(arg_lower)
        if parsed_seconds:
            self.update_setting(guild_id, "next_bump_time", time.time() + parsed_seconds)
            self.update_setting(guild_id, "bump_channel", ctx.channel.id)
            await ctx.send(f"✅ Timer manually synced to **{arg_lower}** from now.")
            return
        
        await ctx.send("❌ Invalid argument. Please provide a channel mention, a time string (e.g. 1h 30m), or 'remove'.")

    @commands.command(aliases=["bs"])
    async def bumpstatus(self, ctx):
        """Shows how much time is left until the next bump."""
        await self._bump_status_logic(ctx.channel, str(ctx.guild.id))

    async def _bump_status_logic(self, channel, guild_id):
        g_settings = self.get_guild_settings(guild_id)
        next_bump = g_settings.get("next_bump_time")
        
        if not next_bump:
            await channel.send("✅ The server can be bumped right now! Go ahead and use `/bump`.")
            return

        remaining = int(next_bump - time.time())
        if remaining <= 0:
            await channel.send("✅ The server can be bumped right now! Go ahead and use `/bump`.")
        else:
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            seconds = remaining % 60
            
            time_str = ""
            if hours > 0: time_str += f"{hours}h "
            if minutes > 0: time_str += f"{minutes}m "
            if seconds > 0: time_str += f"{seconds}s"
            if not time_str.strip(): time_str = "0s"
            
            await channel.send(f"⏰ Next bump is available in **{time_str.strip()}**.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def bumptest(self, ctx):
        """Immediately triggers a fake bump reminder in the current channel."""
        guild_id = str(ctx.guild.id)
        g_settings = self.get_guild_settings(guild_id)
        
        role_id = g_settings.get("bump_role")
        content = f"<@&{role_id}>" if role_id else ""
        
        embed = discord.Embed(
            title="⏰ [TEST] It's Bump Time!",
            description="Use `/bump` to bump the server on Disboard!",
            color=discord.Color.blue()
        )
        await ctx.send(content=content, embed=embed)


async def setup(bot):
    await bot.add_cog(ModBump(bot))
