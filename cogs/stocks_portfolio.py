# cogs/stocks_portfolio.py
import discord
from discord.ext import commands
import sqlite3
from cogs.stocks_core import get_db

class StocksPortfolio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="portfolio", aliases=["pf", "mystocks"])
    async def view_portfolio(self, ctx, option_or_user: str = None):
        """Portfolio dekhne ya privacy set karne ke liye. Usage: !!pf / !!pf set private / !!pf @user"""
        user_id = str(ctx.author.id)
        
        # Action handler for dynamic privacy settings initialization loops
        if option_or_user and option_or_user.lower() == "set":
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}portfolio set private` ya `{ctx.prefix}portfolio set public`")

        if ctx.message.mentions:
            target_user = ctx.message.mentions[0]
        elif option_or_user and option_or_user.isdigit():
            target_user = self.bot.get_user(int(option_or_user)) or ctx.author
        else:
            target_user = ctx.author

        # Check sub-command array filters string mappings
        if option_or_user and option_or_user.lower() == "private" and ctx.message.content.split()[1].lower() == "set":
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO portfolios (user_id, ticker, shares, profile_privacy) VALUES (?, 'NIFTY', 0, 'private')", (user_id,))
            cursor.execute("UPDATE portfolios SET profile_privacy = 'private' WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            return await ctx.send("🔒 **Privacy Set:** Aapka asset investment layout portfolio ab private ho gaya hai!")

        if option_or_user and option_or_user.lower() == "public" and ctx.message.content.split()[1].lower() == "set":
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO portfolios (user_id, ticker, shares, profile_privacy) VALUES (?, 'NIFTY', 0, 'public')", (user_id,))
            cursor.execute("UPDATE portfolios SET profile_privacy = 'public' WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            return await ctx.send("🔓 **Privacy Set:** Aapka portfolio ab public ho gaya hai, ise koi bhi dekh sakta hai!")

        # Processing target user records array read
        target_id = str(target_user.id)
        conn = get_db()
        cursor = conn.cursor()
        
        # Privacy firewall extraction checks loop mapping
        cursor.execute("SELECT profile_privacy FROM portfolios WHERE user_id = ?", (target_id,))
        privacy_row = cursor.fetchone()
        privacy = privacy_row[0] if privacy_row else "public"

        if privacy == "private" and ctx.author.id != target_user.id:
            conn.close()
            return await ctx.send("🔒 **Access Denied:** Is user ka investment portfolio securely private lock par set hai!")

        cursor.execute("""
            SELECT p.ticker, p.shares, s.current_price, s.company_name 
            FROM portfolios p 
            JOIN stocks s ON p.ticker = s.ticker 
            WHERE p.user_id = ? AND p.shares > 0
        """, (target_id,))
        rows = cursor.fetchall()
        conn.close()

        embed = discord.Embed(title=f"💼 Investment Holdings Ledger: {target_user.name}", color=discord.Color.blue())
        embed.set_thumbnail(url=target_user.display_avatar.url)

        if not rows:
            embed.description = "❌ Is user ke paas filhaal koi active stock shares allocation table data nahi hai."
            return await ctx.send(embed=embed)

        total_value = 0
        text = ""
        for ticker, shares, price, name in rows:
            val = shares * price
            total_value += val
            text += f"🔹 **{name}** (`{ticker}`): `{shares}` Shares — Worth **{val} Coins**\n"

        embed.description = f"### 📊 Net Asset Holdings: **{total_value} Coins**\n\n{text}"
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(StocksPortfolio(bot))