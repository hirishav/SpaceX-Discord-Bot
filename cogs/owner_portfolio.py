# cogs/owner_portfolio.py
import discord
from discord.ext import commands
import sqlite3
from cogs.stocks_core import get_db

class OwnerPortfolio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ownerportfolio", aliases=["opf"])
    @commands.is_owner()
    async def admin_view_portfolio(self, ctx, member: discord.Member = None):
        """👑 SECURE OWNER LOCK: Kisi ka bhi portfolio bypass karke dekhne ke liye."""
        if not member: return await ctx.send("❌ Kisi user ko mention karein!")
        
        user_id = str(member.id)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.ticker, p.shares, s.current_price, s.company_name 
            FROM portfolios p 
            JOIN stocks s ON p.ticker = s.ticker 
            WHERE p.user_id = ? AND p.shares > 0
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()

        embed = discord.Embed(title=f"👑 Admin Override Ledger View: {member.name}", color=discord.Color.purple())
        
        total_value = 0
        text = ""
        for ticker, shares, price, name in rows:
            val = shares * price
            total_value += val
            text += f"🔹 **{name}** (`{ticker}`): `{shares}` Shares — Worth **{val} Coins**\n"

        embed.description = f"### 📊 Target Account Total Holdings: **{total_value} Coins**\n\n{text if text else 'Khali Portfolio Data'}"
        await ctx.send(embed=embed)

    @commands.command(name="addstock")
    @commands.is_owner()
    async def add_custom_stock(self, ctx, ticker: str, name: str, price: int):
        """👑 Admin command se pool me instant naya stock insert register karne ke liye."""
        ticker = ticker.upper().strip()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO stocks (ticker, company_name, current_price, available_shares) VALUES (?, ?, ?, 10000)", (ticker, name, price))
        conn.commit()
        conn.close()
        await ctx.send(f"👑 **Success:** Asset `{name}` (`{ticker}`) registered into core database arrays with 10k pools at initial cost **{price} Coins**!")

    @commands.command(name="setshares")
    @commands.is_owner()
    async def modify_stock_shares(self, ctx, ticker: str, qty: int):
        """👑 Pool supply limits quantities ko manually drop ya force increase karne ke liye."""
        ticker = ticker.upper().strip()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE stocks SET available_shares = ? WHERE ticker = ?", (qty, ticker))
        conn.commit()
        conn.close()
        await ctx.send(f"👑 **Success:** Available shares capacity for `{ticker}` manually rewritten to exactly `{qty}` slots!")

async def setup(bot):
    await bot.add_cog(OwnerPortfolio(bot))