# cogs/stocks_sell.py
import discord
from discord.ext import commands
import sqlite3
from cogs.stocks_core import get_db

class StocksSell(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sellstock", aliases=["sell-stock", "sstock"])
    async def sell_shares(self, ctx, ticker: str = None, amount: int = None):
        """Holdings liquidated karke available pool capacity restore karne ke liye."""
        if not ticker or not amount or amount <= 0:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}sellstock <TICKER> <quantity>`")

        ticker = ticker.upper().strip()
        user_id = str(ctx.author.id)

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT shares FROM portfolios WHERE user_id = ? AND ticker = ?", (user_id, ticker))
        port = cursor.fetchone()
        owned = port[0] if port else 0

        if owned < amount:
            conn.close()
            return await ctx.send(f"❌ Tere paas itne shares nahi hain! Owned asset check metrics: `{owned}`")

        cursor.execute("SELECT current_price, available_shares FROM stocks WHERE ticker = ?", (ticker,))
        stock = cursor.fetchone()
        price, available = stock[0], stock[1]
        
        total_payout = price * amount

        cursor.execute("SELECT wallet FROM economy WHERE user_id = ?", (user_id,))
        wallet = cursor.fetchone()[0] or 0

        cursor.execute("UPDATE portfolios SET shares = ? WHERE user_id = ? AND ticker = ?", (owned - amount, user_id, ticker))
        cursor.execute("UPDATE economy SET wallet = ? WHERE user_id = ?", (wallet + total_payout, user_id))
        cursor.execute("UPDATE stocks SET available_shares = ? WHERE ticker = ?", (available + amount, ticker))

        conn.commit()
        conn.close()

        embed = discord.Embed(title="💵 Liquidation Complete!", color=discord.Color.gold())
        embed.description = f"🚀 Tumne **{amount}** shares bech diye hain **{ticker}** ke!\n💰 Wallet Credited: **{total_payout} Coins**."
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(StocksSell(bot))