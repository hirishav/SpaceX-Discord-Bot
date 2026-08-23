# cogs/botinfo.py

import discord
from discord.ext import commands
import platform
import datetime

class BotInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.datetime.now(datetime.timezone.utc)

    @commands.hybrid_command(name="botinfo", aliases=["bi", "info"])
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
        
        embed.add_field(name="🤴 Creator", value="<@727718500663033897>", inline=True)
        embed.add_field(name="🙎 Dev", value="<@1061268825913438358>", inline=True)
        embed.add_field(name="⏱️ Uptime", value=f"`{uptime_str}`", inline=True)
        embed.add_field(name="🌐 Total Servers", value=f"**{total_servers}** Servers", inline=True)
        embed.add_field(name="👥 Total Members", value=f"**{total_members}** Users", inline=True)
        embed.add_field(name="⚡ Library", value=f"Discord.py v{discord.__version__}", inline=True)
        embed.add_field(name="🐍 Python Version", value=f"v{platform.python_version()}", inline=True)
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        
        # BADAL DIYA: `ctx.message.delete()` wala block yahan se permanent hata diya hai!

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="ping", aliases=["latency"])
    async def ping(self, ctx):
        """Bot ka current response ping / latency dekhne ke liye."""
        latency = round(self.bot.latency * 1000)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Bot latency is **{latency}ms**",
            color=discord.Color.green() if latency < 150 else discord.Color.orange() if latency < 300 else discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="vote", aliases=["topgg"])
    async def vote(self, ctx):
        """Top.gg pe bot ko vote karne ke liye link."""
        bot_id = self.bot.user.id if self.bot.user else "863883947073200128"
        vote_url = f"https://top.gg/bot/{bot_id}/vote"
        
        embed = discord.Embed(
            title="🚀 Vote for SpaceX Bot!",
            description=f"Agar aapko mera bot pasand hai, toh kripya top.gg par vote karke support karein! ❤️\n\n🎁 **Voting Reward:** 1 Rep Point aur **5,000 Specie**!\n\n🔗 **[Click Here to Vote on Top.gg]({vote_url})**",
            color=discord.Color.gold()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url if self.bot.user else None)
        embed.set_footer(text="Aapke har ek vote se bot ki reach badhti hai! Thank you! 🙏")
        
        button = discord.ui.Button(label="Vote on Top.gg 🚀", url=vote_url, style=discord.ButtonStyle.link)
        view = discord.ui.View()
        view.add_item(button)
        
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="support")
    async def support(self, ctx):
        """Bot ke support server me join karne ke liye."""
        try:
            import config
            support_url = getattr(config, 'SUPPORT_SERVER_URL', 'https://discord.gg/xgHkpePc9J')
        except ImportError:
            support_url = 'https://discord.gg/xgHkpePc9J'
            
        embed = discord.Embed(
            title="🛠️ Support Server",
            description=f"Agar aapko koi madad chahiye ya koi bug report karna hai, toh hamare support server me join karein!\n\n🔗 **[Click Here to Join Support Server]({support_url})**",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url if self.bot.user else None)
        
        button = discord.ui.Button(label="Join Support Server 🛠️", url=support_url, style=discord.ButtonStyle.link)
        view = discord.ui.View()
        view.add_item(button)
        
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(BotInfo(bot))