# cogs/eco_work.py
import discord
from discord.ext import commands
import database as sqlite3
import random

class EcoWork(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "warnings.db"

    @commands.hybrid_command(name="work")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def work(self, ctx):
        """Mehnat ka kaam karke safe Specie kamane ke liye."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO economy (user_id, wallet, bank) VALUES (?, 0, 0)", (str(ctx.author.id),))

        earnings = random.randint(50, 200)
        jobs = ["McDonalds me burger banaya", "Rishav bhai ke bot ki coding ki", "Discord server manage kiya", "YouTube video edit ki"]
        job = random.choice(jobs)

        cursor.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (earnings, str(ctx.author.id)))
        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="💼 Work Completed!",
            description=f"{ctx.author.mention}, aapne **{job}** aur badle me aapko **💠 {earnings}** Specie mile!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @work.error
    async def work_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ {ctx.author.mention}, chill karo! Try again after **{int(error.retry_after)} seconds**.")
        else:
            await ctx.send(f"⚠️ Debug Work Error: {error}")
            import traceback
            traceback.print_exc()

async def setup(bot):
    await bot.add_cog(EcoWork(bot))