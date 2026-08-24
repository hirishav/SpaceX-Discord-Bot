# cogs/eco_crime.py
import discord
from discord.ext import commands
import database as sqlite3
import random

class EcoCrime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "warnings.db"

    @commands.hybrid_command(name="crime")
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def crime(self, ctx):
        """High-risk, High-reward illegal kaam!"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO economy (user_id, wallet, bank) VALUES (?, 0, 0)", (str(ctx.author.id),))
        
        cursor.execute("SELECT wallet FROM economy WHERE user_id = ?", (str(ctx.author.id),))
        wallet = cursor.fetchone()[0]

        if wallet > 1000000:
            success = random.random() < 0.10  # 10% chance for millionaires
            fine = int(wallet * random.uniform(0.05, 0.10)) # 5-10% fine
        elif wallet > 250000:
            success = random.random() < 0.25  # 25% chance for rich
            fine = random.randint(5000, 15000)
        elif wallet > 50000:
            success = random.random() < 0.45  # 45% chance for middle class
            fine = random.randint(1000, 3000)
        else:
            success = random.random() < 0.75  # 75% chance for beginners
            fine = random.randint(400, 1000)

        if success:
            earnings = random.randint(500, 2000)
            cursor.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (earnings, str(ctx.author.id)))
            
            embed = discord.Embed(
                title="🥷 Crime Successful!",
                description=f"{ctx.author.mention}, aapne bank loot liya aur chupke se **💠 {earnings:,}** uda le gye! Pura master-mind lagaya!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            if fine > wallet: fine = wallet
            cursor.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (fine, str(ctx.author.id)))
            
            embed = discord.Embed(
                title="🚨 Busted!",
                description=f"{ctx.author.mention}, ATM ukhadte waqt alarm baj gya! Aapko bhaari fine bharna pada: **💠 {fine:,}**! 💀",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

        conn.commit()
        conn.close()

    @crime.error
    async def crime_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            hours, remainder = divmod(int(error.retry_after), 3600)
            minutes, seconds = divmod(remainder, 60)
            time_left = ""
            if hours > 0: time_left += f"{hours}h "
            if minutes > 0: time_left += f"{minutes}m "
            time_left += f"{seconds}s".strip()
            await ctx.send(f"⏳ {ctx.author.mention}, police dhoond rhi hai! Try again after **{time_left}**.")
        else:
            raise error

async def setup(bot):
    await bot.add_cog(EcoCrime(bot))