# cogs/mod_automode.py
import discord
from discord.ext import commands
import re
import datetime
import time

class ModAutoMode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.init_db()

    def init_db(self):
        cursor = self.bot.db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS automod_config (
                guild_id TEXT,
                category TEXT,
                enabled INTEGER DEFAULT 0,
                punishment TEXT DEFAULT 'delete',
                duration TEXT DEFAULT NULL,
                PRIMARY KEY (guild_id, category)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS automod_bypass (
                guild_id TEXT,
                target_id TEXT,
                target_type TEXT,
                category TEXT,
                PRIMARY KEY (guild_id, target_id, category)
            )
        ''')
        # Global enabled status stored under category "global"
        self.bot.db.commit()

    def is_global_enabled(self, guild_id: int):
        cursor = self.bot.db.cursor()
        cursor.execute("SELECT enabled FROM automod_config WHERE guild_id = ? AND category = 'global'", (str(guild_id),))
        row = cursor.fetchone()
        return bool(row[0]) if row else False

    def is_category_enabled(self, guild_id: int, category: str):
        cursor = self.bot.db.cursor()
        cursor.execute("SELECT enabled FROM automod_config WHERE guild_id = ? AND category = ?", (str(guild_id), category))
        row = cursor.fetchone()
        return bool(row[0]) if row else False

    def get_punishment(self, guild_id: int, category: str):
        cursor = self.bot.db.cursor()
        cursor.execute("SELECT punishment, duration FROM automod_config WHERE guild_id = ? AND category = ?", (str(guild_id), category))
        row = cursor.fetchone()
        if row:
            return row[0], row[1]
        return "delete", None

    def is_bypassed(self, guild_id: int, member: discord.Member, category: str):
        if member.guild_permissions.administrator:
            return True
        cursor = self.bot.db.cursor()
        
        # Check user
        cursor.execute("SELECT 1 FROM automod_bypass WHERE guild_id = ? AND target_id = ? AND category = ?", (str(guild_id), str(member.id), category))
        if cursor.fetchone():
            return True
            
        # Check roles
        for role in member.roles:
            cursor.execute("SELECT 1 FROM automod_bypass WHERE guild_id = ? AND target_id = ? AND category = ?", (str(guild_id), str(role.id), category))
            if cursor.fetchone():
                return True
                
        return False

    def parse_duration(self, time_str: str):
        if not time_str:
            return None
        time_match = re.match(r"(\d+)([smhd])", time_str.lower())
        if not time_match:
            return None
        amount = int(time_match.group(1))
        unit = time_match.group(2)
        if unit == 's': return datetime.timedelta(seconds=amount)
        elif unit == 'm': return datetime.timedelta(minutes=amount)
        elif unit == 'h': return datetime.timedelta(hours=amount)
        elif unit == 'd': return datetime.timedelta(days=amount)
        return None

    @commands.group(name="am", aliases=["automod"], invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def am(self, ctx):
        """AutoMod System Configuration"""
        await ctx.send_help(ctx.command)

    @am.command(name="enable")
    @commands.has_permissions(manage_guild=True)
    async def am_enable(self, ctx):
        """Enable AutoMod globally"""
        cursor = self.bot.db.cursor()
        cursor.execute("INSERT OR REPLACE INTO automod_config (guild_id, category, enabled) VALUES (?, ?, ?)", (str(ctx.guild.id), 'global', 1))
        self.bot.db.commit()
        await ctx.send("✅ AutoMod is now **ENABLED** globally.")

    @am.command(name="disable")
    @commands.has_permissions(manage_guild=True)
    async def am_disable(self, ctx):
        """Disable AutoMod globally"""
        cursor = self.bot.db.cursor()
        cursor.execute("INSERT OR REPLACE INTO automod_config (guild_id, category, enabled) VALUES (?, ?, ?)", (str(ctx.guild.id), 'global', 0))
        self.bot.db.commit()
        await ctx.send("✅ AutoMod is now **DISABLED** globally.")

    @am.command(name="toggle")
    @commands.has_permissions(manage_guild=True)
    async def am_toggle(self, ctx, category: str):
        """Toggle a specific category (links, invites, nsfw, spoilers, spam, mentions)"""
        valid_cats = ["links", "invites", "nsfw", "spoilers", "spam", "mentions"]
        category = category.lower()
        if category not in valid_cats:
            return await ctx.send(f"❌ Invalid category. Valid categories: {', '.join(valid_cats)}")
            
        current = self.is_category_enabled(ctx.guild.id, category)
        new_state = 0 if current else 1
        
        cursor = self.bot.db.cursor()
        # Ensure we keep the punishment settings if they exist
        cursor.execute("SELECT punishment, duration FROM automod_config WHERE guild_id = ? AND category = ?", (str(ctx.guild.id), category))
        row = cursor.fetchone()
        punishment = row[0] if row else 'delete'
        duration = row[1] if row else None
        
        cursor.execute("INSERT OR REPLACE INTO automod_config (guild_id, category, enabled, punishment, duration) VALUES (?, ?, ?, ?, ?)", 
                       (str(ctx.guild.id), category, new_state, punishment, duration))
        self.bot.db.commit()
        
        status = "ENABLED" if new_state else "DISABLED"
        await ctx.send(f"✅ AutoMod category `{category}` is now **{status}**.")

    # Shortcut commands as requested by user
    @am.command(name="links")
    @commands.has_permissions(manage_guild=True)
    async def am_links(self, ctx):
        await self.am_toggle(ctx, "links")
        
    @am.command(name="invites")
    @commands.has_permissions(manage_guild=True)
    async def am_invites(self, ctx):
        await self.am_toggle(ctx, "invites")

    @am.command(name="nsfw")
    @commands.has_permissions(manage_guild=True)
    async def am_nsfw(self, ctx):
        await self.am_toggle(ctx, "nsfw")

    @am.command(name="spoilers")
    @commands.has_permissions(manage_guild=True)
    async def am_spoilers(self, ctx):
        await self.am_toggle(ctx, "spoilers")

    @am.command(name="spam")
    @commands.has_permissions(manage_guild=True)
    async def am_spam(self, ctx):
        await self.am_toggle(ctx, "spam")

    @am.command(name="mentions")
    @commands.has_permissions(manage_guild=True)
    async def am_mentions(self, ctx):
        await self.am_toggle(ctx, "mentions")

    @am.group(name="set", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def am_set(self, ctx):
        """Set configuration"""
        await ctx.send_help(ctx.command)

    @am_set.command(name="punishment")
    @commands.has_permissions(manage_guild=True)
    async def am_set_punishment(self, ctx, category: str, punishment: str, duration: str = None):
        """Set punishment for a category: delete, warn, mute, kick, ban"""
        valid_cats = ["links", "invites", "nsfw", "spoilers", "spam", "mentions"]
        valid_punishments = ["delete", "warn", "mute", "kick", "ban"]
        
        category = category.lower()
        if category not in valid_cats:
            return await ctx.send(f"❌ Invalid category. Valid categories: {', '.join(valid_cats)}")
            
        punishment = punishment.lower()
        if punishment not in valid_punishments:
            return await ctx.send(f"❌ Invalid punishment. Valid punishments: {', '.join(valid_punishments)}")
            
        if punishment == "mute" and not duration:
            return await ctx.send("❌ You must provide a duration for mute (e.g. 1h, 10m)")
            
        enabled = 1 if self.is_category_enabled(ctx.guild.id, category) else 0
        
        cursor = self.bot.db.cursor()
        cursor.execute("INSERT OR REPLACE INTO automod_config (guild_id, category, enabled, punishment, duration) VALUES (?, ?, ?, ?, ?)", 
                       (str(ctx.guild.id), category, enabled, punishment, duration))
        self.bot.db.commit()
        
        dur_text = f" for {duration}" if duration else ""
        await ctx.send(f"✅ Punishment for `{category}` set to **{punishment}**{dur_text}.")

    @am.command(name="bypass")
    @commands.has_permissions(manage_guild=True)
    async def am_bypass(self, ctx, target: discord.Object, category: str):
        """Bypass a user or role from a specific category"""
        valid_cats = ["links", "invites", "nsfw", "spoilers", "spam", "mentions", "all"]
        category = category.lower()
        if category not in valid_cats:
            return await ctx.send(f"❌ Invalid category. Valid categories: {', '.join(valid_cats)}")
            
        target_type = "user"
        if ctx.guild.get_role(target.id):
            target_type = "role"
            
        cats_to_bypass = ["links", "invites", "nsfw", "spoilers", "spam", "mentions"] if category == "all" else [category]
        
        cursor = self.bot.db.cursor()
        for cat in cats_to_bypass:
            cursor.execute("INSERT OR REPLACE INTO automod_bypass (guild_id, target_id, target_type, category) VALUES (?, ?, ?, ?)", 
                           (str(ctx.guild.id), str(target.id), target_type, cat))
        self.bot.db.commit()
        
        await ctx.send(f"✅ Bypassed `{category}` for ID {target.id}.")

    @am.command(name="unbypass")
    @commands.has_permissions(manage_guild=True)
    async def am_unbypass(self, ctx, target: discord.Object, category: str):
        """Remove a bypass"""
        valid_cats = ["links", "invites", "nsfw", "spoilers", "spam", "mentions", "all"]
        category = category.lower()
        if category not in valid_cats:
            return await ctx.send("❌ Invalid category.")
            
        cats_to_remove = ["links", "invites", "nsfw", "spoilers", "spam", "mentions"] if category == "all" else [category]
        
        cursor = self.bot.db.cursor()
        for cat in cats_to_remove:
            cursor.execute("DELETE FROM automod_bypass WHERE guild_id = ? AND target_id = ? AND category = ?", 
                           (str(ctx.guild.id), str(target.id), cat))
        self.bot.db.commit()
        
        await ctx.send(f"✅ Removed bypass of `{category}` for ID {target.id}.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
            
        if not self.is_global_enabled(message.guild.id):
            return

        # Initialize violation flags
        violations = []

        content = message.content.lower()

        # Check Spoilers
        if self.is_category_enabled(message.guild.id, "spoilers") and not self.is_bypassed(message.guild.id, message.author, "spoilers"):
            if "||" in content:
                violations.append("spoilers")

        # Check Discord Invites
        if self.is_category_enabled(message.guild.id, "invites") and not self.is_bypassed(message.guild.id, message.author, "invites"):
            if "discord.gg/" in content or "discord.com/invite/" in content:
                violations.append("invites")

        # Check Links (if not already caught by invites)
        if "invites" not in violations and self.is_category_enabled(message.guild.id, "links") and not self.is_bypassed(message.guild.id, message.author, "links"):
            url_regex = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
            if url_regex.search(content):
                violations.append("links")

        # Check NSFW (very basic keyword filter)
        if self.is_category_enabled(message.guild.id, "nsfw") and not self.is_bypassed(message.guild.id, message.author, "nsfw"):
            nsfw_keywords = ['porn', 'xnxx', 'xvideos', 'sex', 'nude', 'nsfw']
            if any(word in content for word in nsfw_keywords):
                violations.append("nsfw")

        # Check Mentions
        if self.is_category_enabled(message.guild.id, "mentions") and not self.is_bypassed(message.guild.id, message.author, "mentions"):
            if len(message.mentions) > 5:
                violations.append("mentions")

        if not violations:
            return

        # Handle the most severe violation or first one
        # To simplify, we handle the first one
        category = violations[0]
        punishment, duration = self.get_punishment(message.guild.id, category)

        try:
            await message.delete()
        except discord.NotFound:
            pass
        except discord.Forbidden:
            pass

        reason = f"AutoMod: Triggered {category} filter"

        if punishment == "warn":
            try:
                await message.channel.send(f"⚠️ {message.author.mention}, please do not send {category} here.")
            except:
                pass
        elif punishment == "mute":
            dur = self.parse_duration(duration) or datetime.timedelta(hours=1)
            try:
                await message.author.timeout(discord.utils.utcnow() + dur, reason=reason)
                await message.channel.send(f"🔇 {message.author.mention} has been muted for {duration} for triggering the {category} filter.")
            except:
                pass
        elif punishment == "kick":
            try:
                await message.author.kick(reason=reason)
                await message.channel.send(f"👢 {message.author.mention} was kicked for triggering the {category} filter.")
            except:
                pass
        elif punishment == "ban":
            try:
                await message.author.ban(reason=reason)
                await message.channel.send(f"🔨 {message.author.mention} was banned for triggering the {category} filter.")
            except:
                pass

async def setup(bot):
    await bot.add_cog(ModAutoMode(bot))
