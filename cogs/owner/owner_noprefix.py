# cogs/owner_noprefix.py
import discord
from discord.ext import commands
import typing
import time
import re

def parse_duration(duration_str: str):
    if not duration_str:
        return -1
    match = re.match(r'^(\d+)(s|m|h|d|w|week|month|y|year)$', duration_str.lower())
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2)
    multiplier = 1
    if unit == 's': multiplier = 1
    elif unit == 'm': multiplier = 60
    elif unit == 'h': multiplier = 3600
    elif unit == 'd': multiplier = 86400
    elif unit in ['w', 'week']: multiplier = 604800
    elif unit == 'month': multiplier = 2592000
    elif unit in ['y', 'year']: multiplier = 31536000
    
    return int(time.time()) + (amount * multiplier)

class OwnerNoPrefix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="addprefixless", aliases=["ap"], hidden=True)
    @commands.is_owner()
    async def add_prefixless(self, ctx, target: typing.Union[discord.Member, discord.User, discord.Role, discord.Object] = None, duration: str = None):
        """👑 Owner Only: Kisi member ya role ko bina prefix ke bot use karne ki permission dene ke liye."""
        if not target:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}addprefixless @user/@role [duration]`")

        target_id_str = str(target.id)
        target_name = getattr(target, "name", str(target.id))
        
        expires_at = parse_duration(duration) if duration else -1
        if expires_at is None:
            return await ctx.send("❌ Invalid duration format! Use 1s, 1m, 1h, 1d, 7d, 1month, 1year etc.")

        cursor = self.bot.db.cursor()
        
        # Clean up any existing entries in both tables
        cursor.execute("DELETE FROM prefixless_users WHERE user_id = ?", (target_id_str,))
        cursor.execute("DELETE FROM temp_prefixless_users WHERE user_id = ?", (target_id_str,))
        
        if hasattr(self.bot, 'prefixless_cache'):
            self.bot.prefixless_cache.discard(target.id)
        if hasattr(self.bot, 'temp_prefixless_users_cache'):
            self.bot.temp_prefixless_users_cache.pop(target.id, None)

        if expires_at == -1:
            cursor.execute("INSERT INTO prefixless_users (user_id) VALUES (?)", (target_id_str,))
            if hasattr(self.bot, 'prefixless_cache'):
                self.bot.prefixless_cache.add(target.id)
            msg = f"✅ **{target_name}** ko permanently prefixless access de diya gaya hai! Ab ye launda bina prefix ke aag laga sakta hai. 😎"
        else:
            cursor.execute("INSERT INTO temp_prefixless_users (user_id, expires_at) VALUES (?, ?)", (target_id_str, expires_at))
            if hasattr(self.bot, 'temp_prefixless_users_cache'):
                self.bot.temp_prefixless_users_cache[target.id] = expires_at
            msg = f"✅ **{target_name}** ko `{duration}` ke liye prefixless access de diya gaya hai! Ab ye launda bina prefix ke aag laga sakta hai. 😎"

        self.bot.db.commit()
        await ctx.send(msg)

    @commands.command(name="removeprefixless", aliases=["rp"], hidden=True)
    @commands.is_owner()
    async def remove_prefixless(self, ctx, target: typing.Union[discord.Member, discord.User, discord.Role, discord.Object] = None):
        """👑 Owner Only: Kisi user ya role ka prefixless access wapas chheen ne ke liye."""
        if not target:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}removeprefixless @user/@role`")

        target_id_str = str(target.id)
        target_name = getattr(target, "name", str(target.id))

        cursor = self.bot.db.cursor()
        cursor.execute("DELETE FROM prefixless_users WHERE user_id = ?", (target_id_str,))
        del1 = cursor.rowcount
        cursor.execute("DELETE FROM temp_prefixless_users WHERE user_id = ?", (target_id_str,))
        del2 = cursor.rowcount
        
        if del1 > 0 or del2 > 0:
            self.bot.db.commit()
            
            if hasattr(self.bot, 'prefixless_cache'):
                self.bot.prefixless_cache.discard(target.id)
            if hasattr(self.bot, 'temp_prefixless_users_cache'):
                self.bot.temp_prefixless_users_cache.pop(target.id, None)
            
            await ctx.send(f"🔓 **{target_name}** ka prefixless access saaf kar diya gaya hai! Ab isko normal system follow karna hoga.")
        else:
            await ctx.send("❌ Yeh target whitelisted list me nahi mila bhai!")

    @commands.command(name="listprefixless", aliases=["lp"], hidden=True)
    @commands.is_owner()
    async def list_prefixless(self, ctx):
        """👑 Owner Only: Saare whitelisted logo ki absolute matrix list dekhne ke liye."""
        cursor = self.bot.db.cursor()
        cursor.execute("SELECT user_id FROM prefixless_users")
        permanent = cursor.fetchall()
        
        cursor.execute("SELECT user_id, expires_at FROM temp_prefixless_users")
        temporary = cursor.fetchall()

        embed = discord.Embed(title="🌌 SpaceX Whitelisted Prefixless Matrix", color=discord.Color.blue())
        if not permanent and not temporary:
            embed.description = "❌ Abhi tak koi bhi whitelist nahi kiya gaya hai."
            return await ctx.send(embed=embed)

        users_text = ""
        idx = 1
        for (u_id,) in permanent:
            users_text += f"▪️ **#{idx}** <@{u_id}> / <@&{u_id}> — ID: `{u_id}` (Permanent)\n"
            idx += 1
            
        current_time = int(time.time())
        for (u_id, exp) in temporary:
            if exp > current_time:
                users_text += f"▪️ **#{idx}** <@{u_id}> / <@&{u_id}> — ID: `{u_id}` (Temp, <t:{exp}:R>)\n"
                idx += 1
        
        if not users_text:
            users_text = "❌ Abhi tak koi bhi active whitelist nahi hai."
            
        if len(users_text) > 4096:
            users_text = users_text[:4000] + "\n...and more."
            
        embed.description = users_text
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OwnerNoPrefix(bot))