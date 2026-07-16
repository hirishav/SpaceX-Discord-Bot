# cogs/stocks_news.py
import discord
from discord.ext import commands
import sqlite3
import random

class StocksNews(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 🔥 LOCK: Automatic loop background calls completely removed!

    # 🔥 FIX: `@tasks.loop` decorator ko poora hata diya hai taaki automatic trigger strictly dead ho jaye
    async def flash_market_news(self, ctx):
        # 🌏 SINGLE POPULAR STOCK TARGET DATABASE
        single_stock_news = [
            {
                "ticker": "SMSNG", 
                "type": "good", 
                "title": "🚨 SAMSUNG BREAKING: NEXT-GEN AI CHIP SUCCESS! 🚀",
                "text": "🔥 BREAKING: Samsung ne ek naya futuristic AI foldable chip hardware complete kiya! Market supply me heavy demand aane ki sambhavna!"
            },
            {
                "ticker": "SMSNG", 
                "type": "bad", 
                "title": "💥 SAMSUNG ALARMING ALERT: FACTORY HALT! 📉",
                "text": "⚠️ TECH ALERT: Samsung ke main semiconductor warehouse me heavy short-circuit, production lines temporary lock par!"
            },
            {
                "ticker": "NIFTY", 
                "type": "good", 
                "title": "📈 NIFTY 50 INDEX BREAKOUT: BULL RUN! 🇮🇳",
                "text": "📊 MARKET BULLS: Indian Union Budget reports aane ke baad Foreign Institutional Investors ne massive capital pump kiya! NIFTY Index records hit karne ke liye taiyar!"
            },
            {
                "ticker": "NIFTY", 
                "type": "bad", 
                "title": "📉 NIFTY 50 HEAVY CRASH: SEVERE LIQUIDATION PANIC! 🔻",
                "text": "🚨 CRASH WATCH: Regulatory transaction taxes badhne ke darr se operators ne index companies se billions of coins dump kiye! Market heavily red zone me!"
            },
            {
                "ticker": "APPL", 
                "type": "good", 
                "title": "🍏 APPLE INC. GLOBAL BREAKOUT: RECORD BUY ORDERS! 🚀",
                "text": "🌐 GLOBAL TECH: Apple Car ke internal engineering blueprints leak hone ke baad market caps heavily skyrocket ho rahe hain!"
            },
            {
                "ticker": "APPL", 
                "type": "bad", 
                "title": "⚠️ APPLE OS SYSTEM CRITICAL EXPLOIT: SHARES DOWN! 📉",
                "text": "💥 PANIC ALERT: Naye iOS device core architecture me massive security loophole pakda gaya, users security darr se shares dump kar rahe hain!"
            },
            {
                "ticker": "BTC", 
                "type": "good", 
                "title": "🐋 CRYPTO SUPREME PUMP: BITCOIN TO THE MOON! 🪙",
                "text": "🚀 BULL RUN CONFIRMED: US Government ne Bitcoin ko officially safe reserve asset ledger me whitelist kiya! Absolute green candle launch!"
            },
            {
                "ticker": "BTC", 
                "type": "bad", 
                "title": "🚫 CRYPTO DUMP REPORT: BLACK SWAN EVENT! 💀",
                "text": "💥 WHALE ALERT: Ek purane dormant wallet se 50,000 Bitcoins exchange liquidity pool par instant sell orders par throw kiye gaye! Bitcoin heavy panic down!"
            },
            {
                "ticker": "RELI", 
                "type": "good", 
                "title": "⛽ RELIANCE INDUSTRIAL GOLIATH BOOM! 📈",
                "text": "🚀 JIO BREAKOUT: Reliance Jio ne global satellite internet infrastructure rollout complete kiya, net profit sheets soaring high!"
            },
            {
                "ticker": "TATA", 
                "type": "good", 
                "title": "🚗 TATA MOTORS REAP EUROPEAN JACKPOT! 🏆",
                "text": "🥳 CAR DIVISION: Tata Motors ko European Union se 50,000 premium EVs ka massive business order mila! Share prices zoom!"
            }
        ]

        selected = random.choice(single_stock_news)
        ticker = selected["ticker"]
        news_type = selected["type"]
        alert_text = selected["text"]
        news_title = selected["title"]

        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        
        # Database verification checks mapping
        cursor.execute("SELECT current_price, company_name FROM stocks WHERE ticker = ?", (ticker,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return
            
        current_price, comp_name = row[0], row[1]
        
        # VOLATILITY CALCULATION MATRIX FOR ONLY THE TARGET STOCK
        if news_type == "good":
            factor = random.randint(25, 45)
            new_price = int(current_price * (1 + (factor / 100)))
            change_str = f"+{factor}% (News Pump)"
            color = discord.Color.green()
        else:
            factor = random.randint(20, 35)
            new_price = max(10, int(current_price * (1 - (factor / 100))))
            change_str = f"-{factor}% (News Crash)"
            color = discord.Color.red()
            
        # Target execution query locked
        cursor.execute("UPDATE stocks SET current_price = ?, last_change = ? WHERE ticker = ?", (new_price, change_str, ticker))
        conn.commit()
        conn.close()

        # Composite single output frame blueprint
        embed = discord.Embed(
            title=news_title, 
            description=f"### {alert_text}\n\n📊 **Market Rate Adjustment:**\n🔹 **{comp_name}** (`{ticker}`): `{current_price}` ➡️ **`{new_price} Coins`** (`{change_str}`)", 
            color=color
        )
        embed.set_footer(text="Baki saare stocks stable hain. !!stocks check karein!")

        await ctx.send(embed=embed)

    @commands.command(name="marketnews", aliases=["news"])
    async def force_news_trigger(self, ctx):
        """Live trading floor par instantly kisi ek popular stock ki flash news lane ke liye."""
        await ctx.send("📻 Single Asset Volatility News Matrix trigger kiya jaa raha hai...")
        await self.flash_market_news(ctx)

async def setup(bot):
    await bot.add_cog(StocksNews(bot))