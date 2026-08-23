import discord
from discord.ext import commands
import database as sqlite3
import random

class EcoDaily(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "warnings.db"

    @commands.hybrid_command(name="daily")
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def daily(self, ctx):
        """Rozana muft Specie claim karein!"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO economy (user_id, wallet, bank) VALUES (?, 0, 0)", (str(ctx.author.id),))

        earnings = random.randint(1000, 5000)
        cursor.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (earnings, str(ctx.author.id)))
        
        # Get new total
        cursor.execute("SELECT wallet, bank FROM economy WHERE user_id = ?", (str(ctx.author.id),))
        row = cursor.fetchone()
        total_balance = row[0] + row[1] if row else earnings

        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="🎁 Daily Reward!",
            description=f"{ctx.author.mention}, aapne apna daily reward claim kar liya hai!\n\n**Aapko mile:** `💠 {earnings:,}` Specie\n**Total Balance:** `💠 {total_balance:,}` Specie",
            color=discord.Color.brand_green()
        )
        embed.set_footer(text="Agle reward ke liye 24 ghante baad aana!")
        await ctx.send(embed=embed)

    @daily.error
    async def daily_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            hours, remainder = divmod(int(error.retry_after), 3600)
            minutes, seconds = divmod(remainder, 60)
            time_left = ""
            if hours > 0: time_left += f"{hours}h "
            if minutes > 0: time_left += f"{minutes}m "
            time_left += f"{seconds}s"
            
            await ctx.send(f"⏳ {ctx.author.mention}, aapne apna daily reward pehle hi le liya hai! Agle reward ke liye **{time_left}** rukiye.")
        else:
            raise error

async def setup(bot):
    await bot.add_cog(EcoDaily(bot))
