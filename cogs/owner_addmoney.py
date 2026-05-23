# cogs/owner_addmoney.py
import discord
from discord.ext import commands
import sqlite3
import re

class OwnerAddMoney(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "warnings.db"

    async def fetch_user(self, ctx, user_str):
        try:
            member = await commands.MemberConverter().convert(ctx, user_str)
            return str(member.id), member.name
        except Exception:
            try:
                user = await self.bot.fetch_user(int(user_str))
                return str(user.id), user.name
            except Exception:
                return None, None

    def parse_amount(self, amount_str: str):
        if re.match(r"^\d+(\.\d+)?e\d+$", amount_str.lower()):
            try:
                return int(float(amount_str.lower()))
            except ValueError:
                return None
        if amount_str.isdigit():
            return int(amount_str)
        return None

    @commands.command(name="addmoney", aliases=["am"], hidden=True)
    @commands.is_owner()
    async def add_money(self, ctx, user_str: str = None, type_str: str = None, amount_str: str = None):
        """Sirf Rishav bhai ke liye - Kisi ke wallet ya bank me globally paise add karne ke liye."""
        if not user_str or not type_str or not amount_str:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}addmoney @user/ID <wallet/bank> <amount>`\n👉 Example: `{ctx.prefix}am @User bank 3e3`")

        target_type = type_str.lower()
        if target_type not in ["wallet", "bank"]:
            return await ctx.send("❌ Kripya batayein ki paise kahan add karne hain: `wallet` ya `bank`?")

        amount = self.parse_amount(amount_str)
        if amount is None or amount <= 0:
            return await ctx.send("❌ Kripya sahi amount daalein! (Jaise `50000` ya `3e3`)")

        user_id, username = await self.fetch_user(ctx, user_str)
        if not user_id:
            return await ctx.send("❌ User nahi mila! Sahi tag ya valid ID daalein.")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO economy (user_id, wallet, bank) VALUES (?, 0, 0)", (user_id,))
        
        if target_type == "wallet":
            cursor.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (amount, user_id))
        else:
            cursor.execute("UPDATE economy SET bank = bank + ? WHERE user_id = ?", (amount, user_id))
            
        conn.commit()
        conn.close()

        await ctx.send(f"👑 **Owner Action:** Kamyabi se **{username}** ke **{target_type.upper()}** me 🪙 `{amount:,}` coins add kar diye gaye!")

async def setup(bot):
    await bot.add_cog(OwnerAddMoney(bot))