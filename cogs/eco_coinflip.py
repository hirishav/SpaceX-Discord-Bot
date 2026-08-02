# cogs/eco_coinflip.py
import discord
from discord.ext import commands
import sqlite3
import random

class EcoCoinflip(commands.Cog):
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

    @commands.command(name="coinflip", aliases=["cf", "flip"])
    async def coinflip(self, ctx, amount_str: str = None, choice: str = None):
        """Kismat aazmaiye! !!coinflip <amount/all/half> <heads/tails>"""
        if not amount_str or not choice or choice.lower() not in ["heads", "tails", "h", "t"]:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}coinflip <amount/all/half> <heads/tails>`")

        user_choice = "heads" if choice.lower() in ["heads", "h"] else "tails"
        wallet = self.get_wallet(str(ctx.author.id))

        if wallet <= 0:
            return await ctx.send("❌ Aapke paas jua khelne ke liye ek coin bhi nahi hai!")

        if amount_str.lower() == "all": amount = wallet
        elif amount_str.lower() == "half": amount = wallet // 2
        else:
            try: amount = int(amount_str)
            except ValueError: return await ctx.send("❌ Amount thik se likho!")

        if amount <= 0 or amount > wallet:
            return await ctx.send("❌ Galat amount! Check kijiye aapke pass kitne coins hain.")

        bot_flip = random.choice(["heads", "tails"])
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if user_choice == bot_flip:
            cursor.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (amount, str(ctx.author.id)))
            embed = discord.Embed(title="🪙 Coinflip - JEET GAYE!", description=f"Coin par **{bot_flip.upper()}** aaya!\nAapne lagaaye the `🪙 {amount}` aur aap **`🪙 {amount}`** coins jeet gaye! 🎉", color=discord.Color.green())
        else:
            cursor.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (amount, str(ctx.author.id)))
            embed = discord.Embed(title="🪙 Coinflip - HAR GAYE!", description=f"Coin par **{bot_flip.upper()}** aaya!\nAapne kismat me `🪙 {amount}` coins gawa diye! 💀", color=discord.Color.red())

        conn.commit()
        conn.close()
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EcoCoinflip(bot))