# cogs/welcome.py
import discord
from discord.ext import commands
import database as sqlite3
from datetime import datetime, timezone

# ─────────────────────────────────────────────────────────────
# 👋 WELCOME COG
# ─────────────────────────────────────────────────────────────

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "warnings.db"
        self.init_database()

    def get_connection(self):
        if hasattr(self.bot, 'db') and self.bot.db:
            return self.bot.db
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS welcome_config (
            guild_id TEXT PRIMARY KEY,
            channel_id TEXT,
            message TEXT DEFAULT 'Welcome {user} to {server}! 🎉',
            mention INTEGER DEFAULT 1,
            enabled INTEGER DEFAULT 1,
            member_counter INTEGER DEFAULT 0
        )
        """)
        conn.commit()

    def get_config(self, guild_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id, message, mention, enabled, member_counter FROM welcome_config WHERE guild_id = ?", (str(guild_id),))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "channel_id": int(row[0]) if row[0] else None,
            "message": row[1] or "Welcome {user} to {server}! 🎉",
            "mention": bool(row[2]),
            "enabled": bool(row[3]),
            "member_counter": row[4] or 0
        }

    def update_config(self, guild_id: int, **kwargs):
        conn = self.get_connection()
        cursor = conn.cursor()
        current = self.get_config(guild_id)
        if not current:
            cursor.execute("INSERT INTO welcome_config (guild_id) VALUES (?)", (str(guild_id),))
            current = {
                "channel_id": None,
                "message": "Welcome {user} to {server}! 🎉",
                "mention": True,
                "enabled": True,
                "member_counter": 0
            }

        for k, v in kwargs.items():
            current[k] = v

        cursor.execute("""
            UPDATE welcome_config
            SET channel_id = ?, message = ?, mention = ?, enabled = ?, member_counter = ?
            WHERE guild_id = ?
        """, (
            str(current["channel_id"]) if current["channel_id"] else None,
            current["message"],
            1 if current["mention"] else 0,
            1 if current["enabled"] else 0,
            current["member_counter"],
            str(guild_id)
        ))
        conn.commit()

    def format_account_age(self, created_at: datetime) -> str:
        now = datetime.now(timezone.utc)
        diff = now - created_at
        days = diff.days
        if days < 1:
            return "Less than a day"
        years = days // 365
        remaining_days = days % 365
        months = remaining_days // 30
        leftover_days = remaining_days % 30

        parts = []
        if years > 0:
            parts.append(f"{years} year{'s' if years > 1 else ''}")
        if months > 0:
            parts.append(f"{months} month{'s' if months > 1 else ''}")
        if years == 0 and leftover_days > 0 and not parts:
            parts.append(f"{leftover_days} day{'s' if leftover_days > 1 else ''}")
        elif years == 0 and len(parts) == 1 and leftover_days > 0:
            parts.append(f"{leftover_days} day{'s' if leftover_days > 1 else ''}")
        return ", ".join(parts) if parts else "1 day"

    def format_welcome_text(self, template: str, member: discord.Member, cfg: dict) -> str:
        mention_on = cfg.get("mention", True)
        user_placeholder = member.mention if mention_on else member.display_name
        account_age_str = self.format_account_age(member.created_at)
        pos = cfg.get("member_counter", 0)

        formatted = template.replace("{user}", user_placeholder)
        formatted = formatted.replace("{username}", member.name)
        formatted = formatted.replace("{displayname}", member.display_name)
        formatted = formatted.replace("{server}", member.guild.name)
        formatted = formatted.replace("{member_count}", str(member.guild.member_count))
        formatted = formatted.replace("{account_age}", account_age_str)
        formatted = formatted.replace("{position}", str(pos))
        formatted = formatted.replace("{join_position}", str(pos))
        return formatted

    # ─────────────────────────────────────────────────────────────
    # 🎉 EVENT LISTENER — MEMBER JOIN
    # ─────────────────────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        try:
            cfg = self.get_config(member.guild.id)
            if not cfg or not cfg["enabled"] or not cfg["channel_id"]:
                return

            channel = member.guild.get_channel(cfg["channel_id"])
            if not channel:
                return

            # Increment persistent join position counter per server
            counter = (cfg.get("member_counter") or 0) + 1
            self.update_config(member.guild.id, member_counter=counter)
            cfg["member_counter"] = counter

            msg_text = self.format_welcome_text(cfg["message"], member, cfg)
            mention_on = cfg.get("mention", True)
            allowed = discord.AllowedMentions(users=True) if mention_on else discord.AllowedMentions(users=False)

            embed = discord.Embed(
                title=f"👋 Welcome to {member.guild.name}!",
                description=msg_text,
                color=discord.Color.from_rgb(24, 26, 40),
                timestamp=datetime.now(timezone.utc)
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="👤 Member", value=f"`{member.name}`", inline=True)
            embed.add_field(name="📆 Account Age", value=self.format_account_age(member.created_at), inline=True)
            embed.add_field(name="📊 Member Count", value=f"#{member.guild.member_count}", inline=True)
            if member.guild.icon:
                embed.set_footer(text=f"SpaceX Welcome System • Member #{counter}", icon_url=member.guild.icon.url)
            else:
                embed.set_footer(text=f"SpaceX Welcome System • Member #{counter}")

            await channel.send(content=member.mention if mention_on else None, embed=embed, allowed_mentions=allowed)
        except Exception:
            # Welcome error should never crash bot
            pass

    # ─────────────────────────────────────────────────────────────
    # ⌨️ WELCOME COMMANDS (MODERATOR ONLY)
    # ─────────────────────────────────────────────────────────────

    @commands.hybrid_group(name="welcome", invoke_without_command=True)
    async def welcome(self, ctx):
        """SpaceX Welcome System — Naye members ka custom swagat configure karne ke liye."""
        cfg = self.get_config(ctx.guild.id)
        prefix = ctx.prefix

        status_str = "ENABLED ✅" if (cfg and cfg["enabled"]) else "DISABLED ❌"
        channel_str = f"<#{cfg['channel_id']}>" if (cfg and cfg.get("channel_id")) else "Not Set"
        mention_str = "ON (@User tag)" if (cfg and cfg.get("mention", True)) else "OFF (Sirf naam)"
        msg_str = cfg["message"] if cfg else "Welcome {user} to {server}! 🎉"

        embed = discord.Embed(
            title="👋 SpaceX Welcome System",
            description=f"Server me naye members ka custom swagat karne ke saare settings:\n\n**Current Status:** `{status_str}`\n**Welcome Channel:** {channel_str}\n**Mention Mode:** `{mention_str}`\n**Custom Message:** `{msg_str}`",
            color=discord.Color.from_rgb(24, 26, 40)
        )
        embed.add_field(name="⚙️ Configuration Commands (Admins Only)", value=(
            f"`{prefix}welcome setchannel #channel` — Welcome channel set karein\n"
            f"`{prefix}welcome setmessage <msg>` — Custom message set karein\n"
            f"`{prefix}welcome mention <on/off>` — Mention on ya off karein\n"
            f"`{prefix}welcome enable` — Welcome system chalu karein\n"
            f"`{prefix}welcome disable` — Welcome system band karein\n"
            f"`{prefix}welcome test` — Test welcome message bhejkar dekhein\n"
            f"`{prefix}welcome reset` — Sabhi settings reset karein"
        ), inline=False)
        embed.add_field(name="🏷️ Available Placeholders", value=(
            "`{user}` — Member mention / name\n"
            "`{username}` — User ka username\n"
            "`{displayname}` — User ka display name\n"
            "`{server}` — Server ka naam\n"
            "`{member_count}` — Current guild member count\n"
            "`{account_age}` — Account kitna purana hai\n"
            "`{position}` — Member join sequence number"
        ), inline=False)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @welcome.command(name="setchannel", aliases=["channel"])
    @commands.has_permissions(manage_guild=True)
    async def setchannel(self, ctx, channel: discord.TextChannel):
        """Welcome messages bhejne ke liye text channel set karein."""
        self.update_config(ctx.guild.id, channel_id=channel.id, enabled=True)
        embed = discord.Embed(
            title="✅ Welcome Channel Set!",
            description=f"Is server me ab welcome messages **{channel.mention}** me bheje jayenge.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @welcome.command(name="setmessage", aliases=["message", "msg"])
    @commands.has_permissions(manage_guild=True)
    async def setmessage(self, ctx, *, message: str):
        """Custom welcome message set karein with placeholders support."""
        if len(message) > 1500:
            return await ctx.send("❌ Welcome message bohot bada hai! Maximum 1500 characters tak ka message likhein.")

        self.update_config(ctx.guild.id, message=message)
        cfg = self.get_config(ctx.guild.id)
        preview = self.format_welcome_text(message, ctx.author, cfg)

        embed = discord.Embed(
            title="✅ Custom Welcome Message Updated!",
            description=f"Aapka naya welcome message save ho gaya hai.\n\n**📝 Raw Template:**\n`{message}`\n\n**🔍 Live Preview:**\n{preview}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @welcome.command(name="mention")
    @commands.has_permissions(manage_guild=True)
    async def mention(self, ctx, option: str):
        """Welcome message me naye member ko @mention karna on ya off karein."""
        opt = option.lower().strip()
        if opt in ["on", "true", "yes", "enable", "1"]:
            self.update_config(ctx.guild.id, mention=True)
            await ctx.send("✅ Welcome mention ab **ON** ho gaya hai! (@User tag hoga)")
        elif opt in ["off", "false", "no", "disable", "0"]:
            self.update_config(ctx.guild.id, mention=False)
            await ctx.send("✅ Welcome mention ab **OFF** ho gaya hai! (Sirf display name dikhega, tag nahi hoga)")
        else:
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}welcome mention on` ya `{ctx.prefix}welcome mention off`")

    @welcome.command(name="enable", aliases=["on"])
    @commands.has_permissions(manage_guild=True)
    async def enable(self, ctx):
        """Server me welcome messages enable karein."""
        self.update_config(ctx.guild.id, enabled=True)
        await ctx.send("✅ Welcome system is server me **ENABLE** kar diya gaya hai!")

    @welcome.command(name="disable", aliases=["off"])
    @commands.has_permissions(manage_guild=True)
    async def disable(self, ctx):
        """Server me welcome messages disable karein."""
        self.update_config(ctx.guild.id, enabled=False)
        await ctx.send("❌ Welcome system is server me **DISABLE** kar diya gaya hai.")

    @welcome.command(name="test")
    @commands.has_permissions(manage_guild=True)
    async def test(self, ctx):
        """Test welcome message bhejkar preview check karein."""
        cfg = self.get_config(ctx.guild.id)
        if not cfg:
            return await ctx.send(f"❌ Pehle welcome channel set karein! Example: `{ctx.prefix}welcome setchannel #welcome`")

        target_channel = ctx.guild.get_channel(cfg["channel_id"]) if cfg.get("channel_id") else ctx.channel
        if not target_channel:
            target_channel = ctx.channel

        await ctx.send("🧪 **Test welcome message bheja ja raha hai...**")

        counter = (cfg.get("member_counter") or 0) + 1
        cfg["member_counter"] = counter
        msg_text = self.format_welcome_text(cfg["message"], ctx.author, cfg)
        mention_on = cfg.get("mention", True)
        allowed = discord.AllowedMentions(users=True) if mention_on else discord.AllowedMentions(users=False)

        embed = discord.Embed(
            title=f"👋 Welcome to {ctx.guild.name}! (TEST)",
            description=msg_text,
            color=discord.Color.from_rgb(24, 26, 40),
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.add_field(name="👤 Member", value=f"`{ctx.author.name}`", inline=True)
        embed.add_field(name="📆 Account Age", value=self.format_account_age(ctx.author.created_at), inline=True)
        embed.add_field(name="📊 Member Count", value=f"#{ctx.guild.member_count}", inline=True)
        if ctx.guild.icon:
            embed.set_footer(text=f"SpaceX Welcome System • Member #{counter}", icon_url=ctx.guild.icon.url)
        else:
            embed.set_footer(text=f"SpaceX Welcome System • Member #{counter}")

        await target_channel.send(content=ctx.author.mention if mention_on else None, embed=embed, allowed_mentions=allowed)

    @welcome.command(name="reset")
    @commands.has_permissions(manage_guild=True)
    async def reset(self, ctx):
        """Welcome system ki sabhi settings ko default par reset karein."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM welcome_config WHERE guild_id = ?", (str(ctx.guild.id),))
        conn.commit()
        await ctx.send("♻️ Welcome configuration successfully reset ho gaya hai!")

    @setchannel.error
    @setmessage.error
    @mention.error
    @enable.error
    @disable.error
    @test.error
    @reset.error
    async def welcome_mod_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Ye command sirf moderators use kar sakte hain.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}welcome <command>` — Dekhein `{ctx.prefix}welcome`")


async def setup(bot):
    await bot.add_cog(Welcome(bot))
