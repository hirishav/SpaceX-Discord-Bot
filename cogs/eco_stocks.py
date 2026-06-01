# cogs/eco_stocks.py
import discord
from discord.ext import commands, tasks
import random
import sqlite3
from cogs.stocks_core import get_db, init_stocks_db

class EcoStocks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_stocks_db()
        self.market_fluctuation.start()

    def cog_unload(self):
        self.market_fluctuation.cancel()

    @tasks.loop(minutes=5.0)
    async def market_fluctuation(self):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT ticker, current_price FROM stocks")
        all_stocks = cursor.fetchall()

        for ticker, price in all_stocks:
            # Random Flutter: Volatility engine locked (-15% to +18%) 24/7 trading loops
            change = random.randint(-15, 18)
            if change == 0: change = 3
            
            factor = 1 + (change / 100)
            new_price = max(10, int(price * factor)) 
            
            sign = "+" if change > 0 else ""
            change_str = f"{sign}{change}%"
            
            cursor.execute("UPDATE stocks SET current_price = ?, last_change = ? WHERE ticker = ?", (new_price, change_str, ticker))
            
        conn.commit()
        conn.close()

    @commands.command(name="stocks", aliases=["market", "sharemarket"])
    async def view_market(self, ctx, page: int = 1):
        """Top 200 Real-life stocks aur unki custom 10,000 available capacity dekhne ke liye."""
        if page < 1: page = 1
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT ticker, company_name, current_price, last_change, available_shares FROM stocks")
        rows = cursor.fetchall()
        conn.close()

        # Multi-page pagination management matrix layout
        items_per_page = 7
        total_pages = (len(rows) + items_per_page - 1) // items_per_page
        if page > total_pages: page = total_pages

        start = (page - 1) * items_per_page
        end = start + items_per_page

        embed = discord.Embed(title="📈 SpaceX Live 24/7 Global Stock Exchange 📉", color=discord.Color.dark_green())
        embed.description = f"### Market Pool Status (Page {page}/{total_pages})\nUse `{ctx.prefix}stocks <page_number>` baaki rates dekhne ke liye.\n\n"

        for ticker, name, price, change, available in rows[start:end]:
            emoji = "🔺" if "+" in change else "🔻"
            embed.add_field(
                name=f"🏢 {name} (`{ticker}`)",
                value=f"👉 Current Price: **{price} Coins**\n📊 Change Vector: `{change}` {emoji}\n📦 Available Supply: `{available}/10000` Shares Left",
                inline=False
            )
        embed.set_footer(text=f"Use {ctx.prefix}buystock to invest! Requested by {ctx.author.name}")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EcoStocks(bot))