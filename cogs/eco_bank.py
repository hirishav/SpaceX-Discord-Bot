# cogs/eco_bank.py
import discord
from discord.ext import commands
import sqlite3

class EcoBank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "warnings.db"

    def get_balances(self, user_id: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT wallet, bank FROM economy WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            cursor.execute("INSERT INTO economy (user_id, wallet, bank) VALUES (?, 0, 0)", (user_id,))
            conn.commit()
            return 0, 0
        conn.close()
        return row[0], row[1]

    @commands.command(name="deposit", aliases=["dep"])
    async def deposit(self, ctx, amount_str: str = None):
        """Wallet se paise Bank me jama karne ke liye."""
        if not amount_str:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}dep <amount/all/half>`")

        wallet, bank = self.get_balances(str(ctx.author.id))

        if wallet <= 0:
            return await ctx.send("❌ Aapka wallet pehle se khali hai, bank me kya khak daaloge!")

        if amount_str.lower() == "all":
            amount = wallet
        elif amount_str.lower() == "half":
            amount = wallet // 2
        else:
            try:
                amount = int(amount_str)
            except ValueError:
                return await ctx.send("❌ Valid amount likho (Number, all, ya half)!")

        if amount <= 0:
            return await ctx.send("❌ Amount 0 se bada hona chahiye bhai!")
        if amount > wallet:
            return await ctx.send(f"❌ Aapke wallet me itne paise nahi hain! Current Wallet: 🪙 `{wallet}`")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE economy SET wallet = wallet - ?, bank = bank + ? WHERE user_id = ?", (amount, amount, str(ctx.author.id)))
        conn.commit()
        conn.close()

        await ctx.send(f"🏦 {ctx.author.mention} ne **🪙 {amount:,}** coins apne bank me safe deposit kar diye!")

    @commands.command(name="withdraw", aliases=["with"])
    async def withdraw(self, ctx, amount_str: str = None):
        """Bank se paise Wallet me nikalne ke liye."""
        if not amount_str:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}with <amount/all/half>`")

        wallet, bank = self.get_balances(str(ctx.author.id))

        if bank <= 0:
            return await ctx.send("❌ Aapke bank me ek coin bhi nahi hai!")

        if amount_str.lower() == "all":
            amount = bank
        elif amount_str.lower() == "half":
            amount = bank // 2
        else:
            try:
                amount = int(amount_str)
            except ValueError:
                return await ctx.send("❌ Valid amount likho (Number, all, ya half)!")

        if amount <= 0:
            return await ctx.send("❌ Amount 0 se bada hona chahiye bhai!")
        if amount > bank:
            return await ctx.send(f"❌ Bank me itne coins nahi hain! Current Bank: 🪙 `{bank}`")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE economy SET wallet = wallet + ?, bank = bank - ? WHERE user_id = ?", (amount, amount, str(ctx.author.id)))
        conn.commit()
        conn.close()

        await ctx.send(f"💰 {ctx.author.mention} ne **🪙 {amount:,}** coins bank se nikal kar wallet me daal liye!")

async def setup(bot):
    await bot.add_cog(EcoBank(bot))