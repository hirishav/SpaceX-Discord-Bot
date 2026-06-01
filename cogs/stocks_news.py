# cogs/stocks_news.py
import discord
from discord.ext import commands, tasks
import sqlite3
import random
from cogs.stocks_core import get_db

class StocksNews(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.flash_market_news.start()

    def cog_unload(self):
        self.flash_market_news.cancel()

    # 📻 AUTOMATIC NEWS LOOP: Shuffles every 15 minutes trigger metrics
    @tasks.loop(minutes=15.0)
    async def flash_market_news(self):
        # 📢 Real-life simulation flash breaking scenarios matrix arrays
        news_database = [
            {"ticker": "SMSNG", "type": "good", "text": "🔥 BREAKING NEWS: Samsung ne ek naya futuristic AI foldable chip launch kiya! Stock me boom aane ki sambhavna!"},
            {"ticker": "SMSNG", "type": "bad", "text": "💥 ALARMING: Samsung ke lithium battery warehouse me heavy short-circuit, production lines halt par!"},
            {"ticker": "NIFTY", "type": "good", "text": "📈 MARKET ALERT: Indian economy ne 9.2% GDP growth hit kiya! NIFTY 50 skyrocket hone ke liye taiyar!"},
            {"ticker": "NIFTY", "type": "bad", "text": "📉 MARKET CRASH ALERT: Global inflation reports aane ke baad NIFTY 50 indices heavy sell-off ki taraf!"},
            {"ticker": "APPL", "type": "good", "text": "🍏 GLOBAL UPDATE: Apple Car ke internal blueprints leak hue, investors heavily buy orders laga rahe hain!"},
            {"ticker": "APPL", "type": "bad", "text": "⚠️ TECH NEWS: Apple ke naye iPhone updates me massive security exploit mila, global stocks down!"},
            {"ticker": "BTC", "type": "good", "text": "🚀 CRYPTO PUMP: US Federal Reserve ne Bitcoin ko safe reserve asset ghoshit kiya! Bull run alert!"},
            {"ticker": "BTC", "type": "bad", "text": "🐋 WHALE ALERT: Ek purane dormant wallet se 50,000 Bitcoins exchange par dump kiye gaye! Crypto market panic!"},
            {"ticker": "RELI", "type": "good", "text": "⛽ RELIANCE BOOM: Jio ne global satellite internet rollout complete kiya, market caps soaring!"},
            {"ticker": "TATA", "type": "good", "text": "🚗 TATA MOTORS UPDATE: Tata Motors ko Europe se 50,000 premium EVs ka order mila!"}
        ]

        selected_news = random.choice(news_database)
        ticker = selected_news["ticker"]
        news_type = selected_news["type"]
        alert_text = selected_news["text"]

        conn = get_db()
        cursor = conn.cursor()
        
        # Check if the target stock exist in database row
        cursor.execute("SELECT current_price, company_name FROM stocks WHERE ticker = ?", (ticker,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return
            
        current_price, comp_name = row[0], row[1]

        # Calculate massive artificial news volatility adjustments matrices
        if news_type == "good":
            pump_factor = random.randint(25, 40)
            new_price = int(current_price * (1 + (pump_factor / 100)))
            change_str = f"+{pump_factor}% (News Pump)"
            color = discord.Color.green()
            title = "🔔 SPACE-X MARKET BREAKING: GOOD NEWS! 📈"
        else:
            dump_factor = random.randint(20, 35)
            new_price = max(10, int(current_price * (1 - (dump_factor / 100))))
            change_str = f"-{dump_factor}% (News Crash)"
            color = discord.Color.red()
            title = "⚠️ SPACE-X MARKET BREAKING: CRASH ALERT! 📉"

        # Push artificial news overrides into master charts database
        cursor.execute("UPDATE stocks SET current_price = ?, last_change = ? WHERE ticker = ?", (new_price, change_str, ticker))
        conn.commit()
        conn.close()

        # Global system broadcast inside server channels
        embed = discord.Embed(title=title, description=f"### {alert_text}\n\n📊 **Affected Asset:** {comp_name} (`{ticker}`)\n💸 Old Value: `{current_price} Coins` -> Naya Price: **`{new_price} Coins`**", color=color)
        embed.set_footer(text="Ghar ka jua ya genuine trading? !!stocks check karein!")

        # Dynamic server announcement delivery routing loops channels map
        for guild in self.bot.guilds:
            # Server ke default/system text channel par news broadside fenkega
            channel = guild.system_channel or next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
            if channel:
                try: await channel.send(embed=embed)
                except Exception: pass

    @commands.command(name="marketnews", aliases=["news"])
    async def force_news_trigger(self, ctx):
        """Live trading floor par instantly naya flash check alert lane ke liye."""
        await ctx.send("📻 Dynamic News Broadcast Matrix manually active kiya jaa raha hai...")
        await self.flash_market_news()

async def setup(bot):
    await bot.add_cog(StocksNews(bot))