# cogs/eco_roulette.py
import discord
from discord.ext import commands
import sqlite3
import random

class EcoRoulette(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "warnings.db"

    def get_wallet(self, user_id: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT wallet FROM economy WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0

    @commands.command(name="roulette", aliases=["rt"])
    async def roulette(self, ctx, amount_str: str = None, color_choice: str = None):
        """Casino Roulette! !!roulette <amount/all/half> <red/black/green>"""
        if not amount_str or not color_choice or color_choice.lower() not in ["red", "black", "green", "r", "b", "g"]:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}roulette <amount/all/half> <red/black/green>`")

        user_color = "red" if color_choice.lower() in ["red", "r"] else ("black" if color_choice.lower() in ["black", "b"] else "green")
        wallet = self.get_wallet(str(ctx.author.id))

        if wallet <= 0: return await ctx.send("❌ Wallet khali hai!")

        if amount_str.lower() == "all": amount = wallet
        elif amount_str.lower() == "half": amount = wallet // 2
        else:
            try: amount = int(amount_str)
            except ValueError: return await ctx.send("❌ Amount invalid hai!")

        if amount <= 0 or amount > wallet: return await ctx.send("❌ Coins check kijiye apne!")

        # Roulette Spinning System (0-36)
        # 0 is Green. 1-18 Red, 19-36 Black
        spin = random.randint(0, 36)
        winning_color = "green" if spin == 0 else ("red" if spin <= 18 else "black")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if user_color == winning_color:
            multiplier = 14 if winning_color == "green" else 2
            winnings = amount * (multiplier - 1)
            cursor.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (winnings, str(ctx.author.id)))
            embed = discord.Embed(title="🎡 Roulette Wheel - WIN!", description=f"Wheel ruka number `{spin}` (**{winning_color.upper()}**) par!\nAapka andaza sahi tha! Aap **`🪙 {amount * multiplier}`** coins jeet gaye! 💰", color=discord.Color.green())
        else:
            cursor.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (amount, str(ctx.author.id)))
            embed = discord.Embed(title="🎡 Roulette Wheel - LOST!", description=f"Wheel ruka number `{spin}` (**{winning_color.upper()}**) par!\nWrong bet! Aapne **`🪙 {amount}`** coins gawa diye. 💸", color=discord.Color.red())

        conn.commit()
        conn.close()
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EcoRoulette(bot))