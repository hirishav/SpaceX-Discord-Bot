# cogs/botinfo.py
import discord
from discord.ext import commands
import platform
import datetime

class BotInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.datetime.now(datetime.timezone.utc)

    @commands.command(name="botinfo", aliases=["bi", "info"])
    async def botinfo(self, ctx):
        """Bot ki saari jankari dekhne ke liye (Command text delete nahi hoga)."""
        
        total_servers = len(self.bot.guilds)
        total_members = sum(guild.member_count for guild in self.bot.guilds)
        
        current_time = datetime.datetime.now(datetime.timezone.utc)
        uptime_duration = current_time - self.start_time
        
        days = uptime_duration.days
        hours, remainder = divmod(uptime_duration.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        uptime_str = f"{days}d {hours}h {minutes}m"

        embed = discord.Embed(
            title=f"📊 {self.bot.user.name} Live Statistics",
            color=discord.Color.purple()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        embed.add_field(name="👑 Bot Creator", value="<@727718500663033897>", inline=True)
        embed.add_field(name="⏱️ Uptime", value=f"`{uptime_str}`", inline=True)
        embed.add_field(name="🌐 Total Servers", value=f"**{total_servers}** Servers", inline=True)
        embed.add_field(name="👥 Total Members", value=f"**{total_members}** Users", inline=True)
        embed.add_field(name="⚡ Library", value=f"Discord.py v{discord.__version__}", inline=True)
        embed.add_field(name="🐍 Python Version", value=f"v{platform.python_version()}", inline=True)
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        
        # BADAL DIYA: `ctx.message.delete()` wala block yahan se permanent hata diya hai!
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BotInfo(bot))