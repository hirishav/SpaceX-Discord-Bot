# cogs/botinfo.py
import discord
from discord.ext import commands
import platform
import datetime

class BotInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.datetime.now(datetime.timezone.utc)

    # BADAL DIYA: hybrid_command banaya
    @commands.hybrid_command(name="botinfo", description="Bot ki live statistics dekhne ke liye.")
    async def botinfo(self, ctx):
        total_servers = len(self.bot.guilds)
        total_members = sum(guild.member_count for guild in self.bot.guilds)
        
        current_time = datetime.datetime.now(datetime.timezone.utc)
        uptime_duration = current_time - self.start_time
        uptime_str = f"{uptime_duration.days}d {uptime_duration.seconds // 3600}h {(uptime_duration.seconds % 3600) // 60}m"

        embed = discord.Embed(title=f"📊 {self.bot.user.name} Statistics", color=discord.Color.purple())
        embed.add_field(name="👑 Bot Creator", value="<@727718500663033897>", inline=True)
        embed.add_field(name="⏱️ Uptime", value=f"`{uptime_str}`", inline=True)
        embed.add_field(name="🌐 Total Servers", value=f"**{total_servers}**", inline=True)
        embed.add_field(name="👥 Total Members", value=f"**{total_members}**", inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BotInfo(bot))