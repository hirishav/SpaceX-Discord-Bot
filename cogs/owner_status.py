# cogs/owner_status.py
import discord
from discord.ext import commands

class OwnerStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # setstatus command aur uska alias 'ss'
    @commands.command(name="setstatus", aliases=["ss"], hidden=True)
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
        await ctx.send(f"✅ Status badal kar **{status_type.upper()}** kar diya gaya hai!")

    @setstatus.error
    async def status_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("❌ You cannot use this command. This command belongs to the Owner!")

# Is file ka apna alag setup function
async def setup(bot):
    await bot.add_cog(OwnerStatus(bot))