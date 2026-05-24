# cogs/owner_seeconfess.py
import discord
from discord.ext import commands
import sqlite3

class OwnerSeeConfess(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def resolve_user(self, ctx, user_str):
        try:
            member = await commands.MemberConverter().convert(ctx, user_str)
            return str(member.id)
        except Exception:
            try:
                user = await self.bot.fetch_user(int(user_str))
                return str(user.id)
            except Exception:
                return None

    @commands.command(name="seeconfess", aliases=["see-confess"], hidden=True)
    @commands.is_owner()
    async def see_confess(self, ctx, user_target: str = None):
        """Sirf Rishav bhai ke liye - Saare confessions log track karne ke liye."""
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()

        if user_target:
            user_id = await self.resolve_user(ctx, user_target)
            if not user_id:
                conn.close()
                return await ctx.send("❌ Valid user mention ya ID provide karein!")
            
            cursor.execute("SELECT user_name, confession, channel_id, timestamp FROM confessions WHERE user_id = ? ORDER BY id DESC", (user_id,))
            rows = cursor.fetchall()
            title_text = f"🕵️ Confessions Audit Logs for User ID: {user_id}"
        else:
            cursor.execute("SELECT user_name, confession, channel_id, timestamp FROM confessions ORDER BY id DESC LIMIT 10")
            rows = cursor.fetchall()
            title_text = "🕵️ Global Master Confessions Log (Last 10 Records)"

        conn.close()

        if not rows:
            return await ctx.send("📭 Database me koi confessions data log nahi mila!")

        embed = discord.Embed(title=title_text, color=discord.Color.red())
        
        for row in rows:
            user_name, confession, channel_id, timestamp = row[0], row[1], row[2], row[3]
            embed.add_field(
                name=f"👤 Author: {user_name} | 🕒 Date: {timestamp}",
                value=f"👉 **Confession:** `{confession}`\n📍 **Location:** <#{channel_id}>",
                inline=False
            )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OwnerSeeConfess(bot))