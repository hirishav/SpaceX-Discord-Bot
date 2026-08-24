# cogs/eco_daily.py
import discord
from discord.ext import commands
import database as sqlite3

class EcoDaily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "warnings.db"

    @commands.hybrid_command(name="daily")
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def daily(self, ctx):
        """Roz ka muft 💠 Specie claim karne ke liye."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO economy (user_id, wallet, bank) VALUES (?, 0, 0)", (str(ctx.author.id),))

        reward = 500

        cursor.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (reward, str(ctx.author.id)))
        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="🎁 Daily Reward",
            description=f"{ctx.author.mention}, aapko aapka roz ka **💠 {reward}** Specie mil gaya!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @daily.error
    async def daily_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            hours, remainder = divmod(int(error.retry_after), 3600)
            minutes, seconds = divmod(remainder, 60)
            await ctx.send(f"⏳ {ctx.author.mention}, aapna aaj ka claim kar liya hai! Try again after **{hours}h {minutes}m**.")
        else:
            await ctx.send(f"⚠️ Debug Daily Error: {error}")
            import traceback
            traceback.print_exc()

async def setup(bot):
    await bot.add_cog(EcoDaily(bot))
