# cogs/eco_slut.py
import discord
from discord.ext import commands
import database as sqlite3
import random

class EcoSlut(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "warnings.db"

    @commands.hybrid_command(name="slut")
    @commands.cooldown(1, 15, commands.BucketType.user)
    async def slut(self, ctx):
        """Risky tareeqon se paise kamane ke liye."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO economy (user_id, wallet, bank) VALUES (?, 0, 0)", (str(ctx.author.id),))
        
        # Get wallet balance for fine checking
        cursor.execute("SELECT wallet FROM economy WHERE user_id = ?", (str(ctx.author.id),))
        wallet = cursor.fetchone()[0]

        success = random.choice([True, True, False]) # 66% chance success
        
        if success:
            earnings = random.randint(200, 800)
            cursor.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (earnings, str(ctx.author.id)))
            await ctx.send(f"💋 {ctx.author.mention}, aapne raste par ameer logon ko thoda entertain kiya aur **💠 {earnings}** jhatak liye!")
        else:
            fine = random.randint(150, 400)
            if fine > wallet: fine = wallet
            cursor.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (fine, str(ctx.author.id)))
            await ctx.send(f"📸 {ctx.author.mention}, aap saste kamo me pakde gaye! Police ne aap par **💠 {fine}** ka fine thok diya! 💀")

        conn.commit()
        conn.close()

    @slut.error
    async def slut_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ {ctx.author.mention}, sabr rkho! Try again after **{int(error.retry_after)} seconds**.")
        else:
            raise error

async def setup(bot):
    await bot.add_cog(EcoSlut(bot))