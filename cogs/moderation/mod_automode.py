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
        try:
            cursor.execute('ALTER TABLE automod_config ADD COLUMN limit_amount INTEGER DEFAULT 5')
        except:
            pass
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

    @commands.group(name="automod", aliases=["am", "automode"], invoke_without_command=True)  # type: ignore
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

    async def smart_config(self, ctx, category, *args):
        valid_punishments = ["delete", "warn", "mute", "kick", "ban"]
        
        # Determine intent based on args
        if not args:
            # Simple toggle
            current = self.is_category_enabled(ctx.guild.id, category)
            new_state = 0 if current else 1
            
            cursor = self.bot.db.cursor()
            cursor.execute("UPDATE automod_config SET enabled = ? WHERE guild_id = ? AND category = ?", (new_state, str(ctx.guild.id), category))
            self.bot.db.commit()
            
            status = "ENABLED" if new_state else "DISABLED"
            return await ctx.send(f"✅ AutoMod `{category}` is now **{status}**.")
            
        args_lower = [arg.lower() for arg in args]
        
        # Explicit disable
        if args_lower[0] in ["disable", "off", "false"]:
            cursor = self.bot.db.cursor()
            cursor.execute("UPDATE automod_config SET enabled = 0 WHERE guild_id = ? AND category = ?", (str(ctx.guild.id), category))
            self.bot.db.commit()
            return await ctx.send(f"✅ AutoMod `{category}` is now **DISABLED**.")
            
        # Parse punishment, duration, limit
        punishment = None
        duration = None
        limit = None
        
        for arg in args_lower:
            if arg in ["enable", "on", "true"]:
                continue
            elif arg in valid_punishments:
                punishment = arg
            elif arg.isdigit():
                limit = int(arg)
            else:
                # Assume duration
                duration = arg
                
        # Fetch existing config
        cursor = self.bot.db.cursor()
        cursor.execute("SELECT punishment, duration, limit_amount FROM automod_config WHERE guild_id = ? AND category = ?", (str(ctx.guild.id), category))
        row = cursor.fetchone()
        
        curr_pun = row[0] if row else "delete"
        curr_dur = row[1] if row else None
        curr_lim = row[2] if row else 5
        
        punishment = punishment or curr_pun
        duration = duration or curr_dur
        limit = limit or curr_lim
        
        if punishment == "mute" and not duration:
            return await ctx.send("❌ Mute set karne ke liye duration zaruri hai (jaise: `1h`, `10m`)!")
            
        cursor.execute("INSERT OR REPLACE INTO automod_config (guild_id, category, enabled, punishment, duration, limit_amount) VALUES (?, ?, 1, ?, ?, ?)", 
                       (str(ctx.guild.id), category, punishment, duration, limit))
        self.bot.db.commit()
        
        msg = f"✅ AutoMod `{category}` is now **ENABLED**.\n> 🛡️ Punishment: **{punishment.title()}**"
        if duration and punishment == "mute": 
            msg += f" for **{duration}**"
        if category == "mentions": 
            msg += f"\n> 🔢 Mention Limit: **{limit} mentions**"
            
        await ctx.send(msg)

    # Shortcut commands as requested by user
    @am.command(name="links")
    @commands.has_permissions(manage_guild=True)
    async def am_links(self, ctx, *args):
        await self.smart_config(ctx, "links", *args)
        
    @am.command(name="invites")
    @commands.has_permissions(manage_guild=True)
    async def am_invites(self, ctx, *args):
        await self.smart_config(ctx, "invites", *args)

    @am.command(name="nsfw")
    @commands.has_permissions(manage_guild=True)
    async def am_nsfw(self, ctx, *args):
        await self.smart_config(ctx, "nsfw", *args)

    @am.command(name="spoilers")
    @commands.has_permissions(manage_guild=True)
    async def am_spoilers(self, ctx, *args):
        await self.smart_config(ctx, "spoilers", *args)

    @am.command(name="spam")
    @commands.has_permissions(manage_guild=True)
    async def am_spam(self, ctx, *args):
        await self.smart_config(ctx, "spam", *args)

    @am.command(name="mentions")
    @commands.has_permissions(manage_guild=True)
    async def am_mentions(self, ctx, *args):
        await self.smart_config(ctx, "mentions", *args)

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
            cursor = self.bot.db.cursor()
            cursor.execute("SELECT limit_amount FROM automod_config WHERE guild_id = ? AND category = 'mentions'", (str(message.guild.id),))
            row = cursor.fetchone()
            mention_limit = row[0] if (row and row[0] is not None) else 5
            
            if len(message.mentions) > mention_limit:
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
