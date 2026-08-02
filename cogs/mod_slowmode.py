# cogs/mod_slowmode.py
import discord
from discord.ext import commands

class ModSlowmode(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="slowmode", aliases=["sm", "cooldown"])
    @commands.has_permissions(manage_messages=True)
    async def slowmode(self, ctx, seconds_input: str = None):
        """Channel me slowmode cooldown set karne ke liye (Manage Messages)."""
        if seconds_input is None:
            current_sm = ctx.channel.slowmode_delay
            return await ctx.send(f"⏱️ Is channel ka current slowmode delay **{current_sm} seconds** hai.")

        seconds = 0
        seconds_input = seconds_input.lower()
        if seconds_input.endswith('s'):
            try: seconds = int(seconds_input[:-1])
            except ValueError: return await ctx.send("❌ Sahi format: `10s`, `1m`, `1h` ya sirf number `10`")
        elif seconds_input.endswith('m'):
            try: seconds = int(seconds_input[:-1]) * 60
            except ValueError: return await ctx.send("❌ Sahi format: `10s`, `1m`, `1h` ya sirf number `10`")
        elif seconds_input.endswith('h'):
            try: seconds = int(seconds_input[:-1]) * 3600
            except ValueError: return await ctx.send("❌ Sahi format: `10s`, `1m`, `1h` ya sirf number `10`")
        else:
            try: seconds = int(seconds_input)
            except ValueError: return await ctx.send("❌ Sahi format: `10s`, `1m`, `1h` ya sirf number `10`")

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