import discord
from discord.ext import commands, tasks
import database as sqlite3
import random
from cogs.eco_stocks_core import get_stock_cap

class EcoStocksMarket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "warnings.db"
        self.market_loop.start()

    def cog_unload(self):
        self.market_loop.cancel()

    @tasks.loop(minutes=5)
    async def market_loop(self):
        """Randomly fluctuates stock prices to simulate a live market."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT ticker, current_price FROM stocks")
        stocks = cursor.fetchall()

        for ticker, price in stocks:
            # Fluctuate price between -5% and +5%
            change_percent = random.uniform(-0.05, 0.05)
            change_amount = int(price * change_percent)
            
            # Prevent 0 price
            if price + change_amount <= 0:
                change_amount = -price + 1
                
            new_price = price + change_amount
            
            # Enforce max cap
            cap = get_stock_cap(ticker)
            if new_price > cap:
                new_price = cap
                change_amount = new_price - price
            
            # Prevent tiny stocks from never moving (force at least 1 specie move if needed, 50% chance)
            if change_amount == 0 and random.random() < 0.5:
                change_amount = random.choice([-1, 1])
                new_price = max(1, min(cap, price + change_amount))
                
            if price > 0:
                final_percent = (change_amount / price) * 100
            else:
                final_percent = 0.0
                
            sign = "+" if change_amount >= 0 else ""
            last_change = f"{sign}{final_percent:.2f}%"

            cursor.execute("UPDATE stocks SET current_price = ?, last_change = ? WHERE ticker = ?", (new_price, last_change, ticker))
            
        conn.commit()
        conn.close()

    @market_loop.before_loop
    async def before_market_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(EcoStocksMarket(bot))
