# cogs/stocks_news.py
import discord
from discord.ext import commands, tasks
import sqlite3
import random

class StocksNews(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.flash_market_news.start()

    def cog_unload(self):
        self.flash_market_news.cancel()

    @tasks.loop(minutes=15.0)
    async def flash_market_news(self):
        # 🌍 MASSIVE SECTOR CO-RELATION NEWS ARRAYS
        sector_news = [
            {
                "title": "🚨 GLOBAL TECH BOOM: SECTOR PUMP IMMINENT! 🚀",
                "tickers": ["SMSNG", "APPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META"],
                "type": "good",
                "text": "🔥 BREAKING: Artificial Intelligence chips ke tech infrastructure business me record boom! Saare global tech stocks heavily rocket hone ke liye taiyar!"
            },
            {
                "title": "💥 TECH SECTOR CRASH ALERT: PANIC SELL-OFF! 📉",
                "tickers": ["SMSNG", "APPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META"],
                "type": "bad",
                "text": "⚠️ TECH ALERT: Semi-conductor suppliers ne structural transport halt ghoshit kiya. Saare leading tech giants ke production data heavily crash ho rahe hain!"
            },
            {
                "title": "📈 INDIAN ECONOMY REAP JACKPOT: BLUECHIPS RUSH! 🇮🇳",
                "tickers": ["RELI", "TATA", "TCS", "INFY", "HDFCB", "ICICIB", "SBIN", "ITC"],
                "type": "good",
                "text": "📊 MARKET BULLS: Indian Union Budget reports out! Foreign institutional investors ne massive funding inject ki, saare top Indian bluechips upar jaane ke liye ready!"
            },
            {
                "title": "📉 INDIAN NIFTY INDEX HEAVY CRASH: SEVERE DRAINDOWN! 🔻",
                "tickers": ["RELI", "TATA", "TCS", "INFY", "HDFCB", "ICICIB", "SBIN", "ITC"],
                "type": "bad",
                "text": "🚨 CRASH WATCH: Regulatory transaction taxes badhne ke darr se investors ne leading companies se billions of coins liquidate kiye! Market index red zone me!"
            },
            {
                "title": "🐋 CRYPTO SUPER RUN ACTIVE: GREEN WAVE! 🪙",
                "tickers": ["BTC", "ETH", "SOL", "BNB"],
                "type": "good",
                "text": "🚀 BULL RUN CONFIRMED: Massive institutional investment firms ne saare primary crypto tokens holdings legal balance sheet me accept kar liye hain! Prices skyrocketing!"
            },
            {
                "title": "📉 CRYPTO INSECURE EXPLOIT: LIQUIDATION PANIC! 🚫",
                "tickers": ["BTC", "ETH", "SOL", "BNB"],
                "type": "bad",
                "text": "💥 PANIC ALERT: Major web3 network protocols me bug leak hone se markets me short-selling peak par! Saare asset tokens down!"
            }
        ]

        selected = random.choice(sector_news)
        tickers_list = selected["tickers"]
        news_type = selected["type"]
        alert_text = selected["text"]
        news_title = selected["title"]

        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        
        affected_details = ""
        
        # 🔥 MULTI-STOCK PROCESSOR LOOP: Ek sath list ke saare tickers ko select karke prices badlega
        for ticker in tickers_list:
            cursor.execute("SELECT current_price, company_name FROM stocks WHERE ticker = ?", (ticker,))
            row = cursor.fetchone()
            if not row: continue
            
            current_price, comp_name = row[0], row[1]
            
            if news_type == "good":
                factor = random.randint(20, 35)
                new_price = int(current_price * (1 + (factor / 100)))
                change_str = f"+{factor}% (Sector Pump)"
            else:
                factor = random.randint(15, 30)
                new_price = max(10, int(current_price * (1 - (factor / 100))))
                change_str = f"-{factor}% (Sector Crash)"
                
            cursor.execute("UPDATE stocks SET current_price = ?, last_change = ? WHERE ticker = ?", (new_price, change_str, ticker))
            affected_details += f"🔹 **{comp_name}** (`{ticker}`): `{current_price}` ➡️ **`{new_price} Coins`**\n"
            
        conn.commit()
        conn.close()

        # Build composite output embed channel notifications
        embed = discord.Embed(
            title=news_title, 
            description=f"### {alert_text}\n\n📊 **Sector Rate Adjustments:**\n{affected_details}", 
            color=discord.Color.green() if news_type == "good" else discord.Color.red()
        )
        embed.set_footer(text="Ghar ka jua ya professional trading? !!stocks check karein!")

        for guild in self.bot.guilds:
            channel = guild.system_channel or next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
            if channel:
                try: await channel.send(embed=embed)
                except Exception: pass

    @commands.command(name="marketnews", aliases=["news"])
    async def force_news_trigger(self, ctx):
        """Live trading floor par instantly poore sector ki flash news lane ke liye."""
        await ctx.send("📻 Sector Volatility News Matrix manually trigger kiya jaa raha hai...")
        await self.flash_market_news()

async def setup(bot):
    await bot.add_cog(StocksNews(bot))