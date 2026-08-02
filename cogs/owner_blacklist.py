# cogs/mod_blacklist.py
import discord
from discord.ext import commands
import sqlite3
import time

class ModBlacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "warnings.db"

    async def fetch_user_id(self, ctx, user_str):
        try:
            member = await commands.MemberConverter().convert(ctx, user_str)
            return str(member.id), member.name
        except Exception:
            try:
                user = await self.bot.fetch_user(int(user_str))
                return str(user.id), user.name
            except Exception:
                return None, None

    @commands.command(name="blacklist", aliases=["bl"])
    async def blacklist(self, ctx, user_str: str = None, duration_str: str = None, *, reason: str = "Bypassing rules of the bot"):
        """Kisi user ko bot commands use karne se globally block karne ke liye."""
        
        # 1. 🛑 NORMAL USER CHECK: Agar owner nahi hai toh troll dialogue!
        if not await self.bot.is_owner(ctx.author):
            return await ctx.send("Accha ji? Tum nahi karsakte janab. Bolo toh tumhe kardu.... xD")

        # Owner ke liye guide
        if not user_str or not duration_str:
            return await ctx.send(f"❌ Sahi format: `{ctx.prefix}blacklist @user/ID <duration/0> [reason]`\nExample: `{ctx.prefix}blacklist @User 7d Rules break`")

        user_id, username = await self.fetch_user_id(ctx, user_str)
        if not user_id:
            return await ctx.send("❌ Boss, sahi user tag karo ya sahi Discord ID daalo!")

        if user_id == str(ctx.author.id):
            return await ctx.send("❌ Khud ko blacklist nahi kar sakte Rishav bhai!")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 2. 🟢 UN-BLACKLIST (Agar '0' likha hai)
        if duration_str == "0":
            cursor.execute("DELETE FROM blacklist WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            if int(user_id) in self.bot.blacklist_cache:
                del self.bot.blacklist_cache[int(user_id)]
            return await ctx.send(f"✅ **Globally Un-blacklisted:** **{username}** (ID: `{user_id}`) ab bot use kar sakta hai!")

        # 3. ⏱️ TIME PARSER (30s, 1m, 7d, 30d, 1yr)
        time_multipliers = {
            's': 1,
            'm': 60,
            'h': 3600,
            'd': 86400,
            'yr': 31536000
        }

        unit = ""
        digits = ""
        for char in duration_str:
            if char.isdigit():
                digits += char
            else:
                unit += char

        if not digits:
            conn.close()
            return await ctx.send("❌ Time specify sahi se karo! Example: `30s`, `1m`, `7d`.")

        amount = int(digits)
        unit = unit.lower() if unit else 'm'

        if 'yr' in unit:
            multiplier = time_multipliers['yr']
        elif unit in time_multipliers:
            multiplier = time_multipliers[unit]
        else:
            conn.close()
            return await ctx.send("❌ Invalid time format! Sahi units: `s`, `m`, `h`, `d`, `yr`.")

        calculated_seconds = amount * multiplier
        expires_at = int(time.time()) + calculated_seconds

        # Database insert/replace
        cursor.execute("INSERT OR REPLACE INTO blacklist (user_id, expires_at, reason) VALUES (?, ?, ?)", (user_id, expires_at, reason))
        conn.commit()
        conn.close()
        
        self.bot.blacklist_cache[int(user_id)] = (expires_at, reason)

        await ctx.send(f"🚨 **Globally Blacklisted:** **{username}** (ID: `{user_id}`) ko **{duration_str}** ke liye blacklist kar diya gaya hai!\n📝 **Reason:** {reason}")

async def setup(bot):
    await bot.add_cog(ModBlacklist(bot))