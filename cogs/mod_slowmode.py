# cogs/mod_slowmode.py
import discord
from discord.ext import commands

class ModSlowmode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="slowmode", aliases=["sm", "cooldown"])
    @commands.has_permissions(manage_messages=True)
    async def slowmode(self, ctx, seconds: int = None):
        """Channel me slowmode cooldown set karne ke liye (Manage Messages)."""
        if seconds is None:
            current_sm = ctx.channel.slowmode_delay
            return await ctx.send(f"⏱️ Is channel ka current slowmode delay **{current_sm} seconds** hai.")

        if seconds < 0 or seconds > 21600:
            return await ctx.send("❌ Limit galat hai bhai! 0 se lekar 21600 seconds (6 hours) tak set karein.")

        try:
            await ctx.channel.edit(slowmode_delay=seconds)
            if seconds == 0:
                embed = discord.Embed(description=f"⚡ {ctx.author.mention} ne **Slowmode hata diya**! Chat ab normal hai.", color=discord.Color.green())
            else:
                embed = discord.Embed(description=f"⏱️ Is channel me **{seconds} seconds** ka Slowmode laga diya gaya hai.", color=discord.Color.orange())
            await ctx.send(embed=embed)
            try: await ctx.message.delete()
            except Exception: pass
        except discord.Forbidden:
            await ctx.send("❌ Mere paas is channel ko edit karne ki permission nahi hai!")

async def setup(bot):
    await bot.add_cog(ModSlowmode(bot))