# cogs/owner_addprefixless_server.py
import discord
from discord.ext import commands
import time
import re

class OwnerAddPrefixlessServer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def parse_duration(self, duration_str: str):
        if duration_str.lower() == "unlimited":
            return -1
        
        match = re.match(r"^(\d+)([smhd])$", duration_str.lower())
        if not match:
            return None
        
        amount = int(match.group(1))
        unit = match.group(2)
        
        if unit == "s":
            return amount
        elif unit == "m":
            return amount * 60
        elif unit == "h":
            return amount * 3600
        elif unit == "d":
            return amount * 86400
        return None

    @commands.command(name="addprefixless_server", aliases=["addprefixlessserver", "aps"])
    @commands.is_owner()
    async def add_prefixless_server(self, ctx, duration: str = None, server_id: str = None):
        """<a:owner:1453608135104270498> Owner Only: Kisi server me sabhi members ko prefixless access dene ke liye."""
        if not duration or not server_id:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}addprefixless_server unlimited/1d/1h/10m <serverid>`")
        
        try:
            server_id_int = int(server_id)
        except ValueError:
            return await ctx.send("❌ Server ID ek number hona chahiye!")

        duration_seconds = self.parse_duration(duration)
        if duration_seconds is None:
            return await ctx.send("❌ Invalid duration! Use `unlimited`, `1d`, `1h`, `10m`, etc.")

        expires_at = -1 if duration_seconds == -1 else int(time.time()) + duration_seconds

        cursor = self.bot.db.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO prefixless_servers (server_id, expires_at) VALUES (?, ?)", 
            (server_id, expires_at)
        )
        self.bot.db.commit()

        # Update cache
        if hasattr(self.bot, 'prefixless_servers_cache'):
            self.bot.prefixless_servers_cache[server_id_int] = expires_at

        embed = discord.Embed(
            title="<:verified_tick:837551087786393710> Prefixless Server Added", 
            description=f"Server ID **{server_id}** ab prefixless list me add ho gaya hai!", 
            color=discord.Color.green()
        )
        embed.add_field(name="Duration", value=f"`{duration}`", inline=True)
        if expires_at != -1:
            embed.add_field(name="Expires", value=f"<t:{expires_at}:R>", inline=True)
        else:
            embed.add_field(name="Expires", value="`Unlimited`", inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OwnerAddPrefixlessServer(bot))
