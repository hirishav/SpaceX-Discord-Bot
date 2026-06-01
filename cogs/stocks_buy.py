# cogs/stocks_buy.py
import discord
from discord.ext import commands
import sqlite3
from cogs.stocks_core import get_db

class StocksBuy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="buystock", aliases=["buy-stock", "bstock"])
    async def buy_shares(self, ctx, ticker: str = None, amount: int = None):
        """10k limited tracking supply lines se safe assets buy karne ke liye."""
        if not ticker or not amount or amount <= 0:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}buystock <TICKER> <quantity>`\n👉 Example: `{ctx.prefix}buystock NIFTY 5`")

        ticker = ticker.upper().strip()
        user_id = str(ctx.author.id)

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT current_price, available_shares FROM stocks WHERE ticker = ?", (ticker,))
        stock = cursor.fetchone()
        
        if not stock:
            conn.close()
            return await ctx.send(f"❌ Market me `{ticker}` ticker ka koi stock active nahi hai!")

        price, available = stock[0], stock[1]
        if available < amount:
            conn.close()
            return await ctx.send(f"❌ **Market Shortage:** Is stock ke paas sirf `{available}` stock allocations bache hain!")

        total_cost = price * amount

        cursor.execute("SELECT wallet FROM economy WHERE user_id = ?", (user_id,))
        eco = cursor.fetchone()
        wallet = eco[0] if eco else 0

        if wallet < total_cost:
            conn.close()
            return await ctx.send(f"❌ **Insufficient Funds:** Total Cost: **{total_cost} Coins**, Wallet: **{wallet} Coins**.")

        # Atomic transaction loops blocks
        cursor.execute("UPDATE economy SET wallet = ? WHERE user_id = ?", (wallet - total_cost, user_id))
        cursor.execute("UPDATE stocks SET available_shares = ? WHERE ticker = ?", (available - amount, ticker))
        
        cursor.execute("INSERT OR IGNORE INTO portfolios (user_id, ticker, shares) VALUES (?, ?, 0)", (user_id, ticker))
        cursor.execute("SELECT shares FROM portfolios WHERE user_id = ? AND ticker = ?", (user_id, ticker))
        owned = cursor.fetchone()[0]
        
        cursor.execute("UPDATE portfolios SET shares = ? WHERE user_id = ? AND ticker = ?", (owned + amount, user_id, ticker))
        
        conn.commit()
        conn.close()

        embed = discord.Embed(title="✅ Shares Purchased!", color=discord.Color.green())
        embed.description = f"🥳 Tumne **{amount}** shares khareed liye hain **{ticker}** ke!\n💰 Total Deducted: **{total_cost} Coins**."
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(StocksBuy(bot))