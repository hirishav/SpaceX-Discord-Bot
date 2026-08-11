# cogs/owner_status.py
import discord
from discord.ext import commands

class OwnerStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # setstatus command aur uska alias 'ss'
    @commands.hybrid_command(name="setstatus", aliases=["ss"], hidden=True)
    @commands.is_owner()
    async def setstatus(self, ctx, status_type: str, activity_type: str = "playing", *, activity_name: str = None):
        """Bot ka status aur activity badalye."""
        status_type = status_type.lower()
        activity_type = activity_type.lower()
        
        # 1. Status check
        if status_type == "online":
            status = discord.Status.online
        elif status_type == "idle":
            status = discord.Status.idle
        elif status_type == "dnd":
            status = discord.Status.dnd
        elif status_type in ["offline", "invisible"]:
            status = discord.Status.offline
        else:
            return await ctx.send("❌ Galat status! Use: `online`, `idle`, `dnd`, ya `offline`.")

        # 2. Activity check
        if activity_name:
            if activity_type == "playing":
                activity = discord.Game(name=activity_name)
            elif activity_type == "watching":
                activity = discord.Activity(type=discord.ActivityType.watching, name=activity_name)
            elif activity_type == "listening":
                activity = discord.Activity(type=discord.ActivityType.listening, name=activity_name)
            else:
                activity = discord.Game(name=f"{activity_type} {activity_name}")
        else:
            activity = None

        await self.bot.change_presence(status=status, activity=activity)
        await ctx.send(f"<a:verified_tick:837551087786393710> Status badal kar **{status_type.upper()}** kar diya gaya hai!")

    @setstatus.error
    async def status_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("❌ You cannot use this command. This command belongs to the Owner!")

    @commands.hybrid_command(name="updatetopgg", aliases=["topggupdate", "poststats"], hidden=True)
    @commands.is_owner()
    async def updatetopgg(self, ctx):
        """Top.gg website par live server count direct update karein."""
        msg = await ctx.send("🚀 **Top.gg par server count post kiya ja raha hai...**")
        success, details = await self.bot.post_topgg_stats()
        if success:
            embed = discord.Embed(
                title="<a:verified_tick:837551087786393710> Top.gg Server Count Updated!",
                description=f"**Servers Posted:** `{len(self.bot.guilds)}`\n**API Response:** `{details}`",
                color=discord.Color.green()
            )
            await msg.edit(content=None, embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Top.gg Update Failed!",
                description=f"**Error Details:** `{details}`\n*Check karein ki TOPGG_TOKEN config.py ya .env me sahi set hai.*",
                color=discord.Color.red()
            )
            await msg.edit(content=None, embed=embed)

    @updatetopgg.error
    async def updatetopgg_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("❌ You cannot use this command. This command belongs to the Owner!")

# Is file ka apna alag setup function
async def setup(bot):
    await bot.add_cog(OwnerStatus(bot))