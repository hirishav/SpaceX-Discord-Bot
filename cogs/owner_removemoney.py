# cogs/owner_removemoney.py
import discord
from discord.ext import commands
import sqlite3
import re

class OwnerRemoveMoney(commands.Cog):
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

    def parse_amount(self, amount_str: str, current_wallet: int, current_bank: int):
        amount_str = amount_str.lower()
        total_balance = current_wallet + current_bank

        if amount_str == "all":
            return "all", total_balance
        if amount_str == "half":
            return "half", total_balance // 2

        if re.match(r"^\d+(\.\d+)?e\d+$", amount_str):
            try:
                val = int(float(amount_str))
                return "fixed", val
            except ValueError:
                return None, None
                
        if amount_str.isdigit():
            return "fixed", int(amount_str)
            
        return None, None

    @commands.command(name="removemoney", aliases=["rm"], hidden=True)
    @commands.is_owner()
    async def remove_money(self, ctx, user_str: str = None, amount_input: str = None):
        """Sirf Rishav bhai ke liye - Kisi ke account se globally coins remove/fine karne ke liye."""
        if not user_str or not amount_input:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}removemoney @user/ID <amount/all/half>`\n👉 Example: `{ctx.prefix}rm @User 4e5`")

        user_id, username = await self.fetch_user(ctx, user_str)
        if not user_id:
            return await ctx.send("❌ User nahi mila!")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT wallet, bank FROM economy WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return await ctx.send("❌ Is user ka economy database me koi bahi-khata hi nahi mila!")

        current_wallet, current_bank = row[0], row[1]
        mode, amount_to_remove = self.parse_amount(amount_input, current_wallet, current_bank)

        if amount_to_remove is None or amount_to_remove <= 0:
            conn.close()
            return await ctx.send("❌ Invalid amount format! Use normal digits, scientific text (`4e5`), `all`, ya `half`.")

        if mode == "all":
            cursor.execute("UPDATE economy SET wallet = 0, bank = 0 WHERE user_id = ?", (user_id,))
        elif mode == "half":
            rem_wallet = current_wallet // 2
            rem_bank = current_bank // 2
            cursor.execute("UPDATE economy SET wallet = ?, bank = ? WHERE user_id = ?", (rem_wallet, rem_bank, user_id))
        else:
            if amount_to_remove <= current_wallet:
                cursor.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (amount_to_remove, user_id))
            else:
                remaining = amount_to_remove - current_wallet
                new_bank = max(0, current_bank - remaining)
                cursor.execute("UPDATE economy SET wallet = 0, bank = ? WHERE user_id = ?", (new_bank, user_id))

        conn.commit()
        conn.close()

        display_amt = f"Pura Account (Reset)" if mode == "all" else f"🪙 `{amount_to_remove:,}` coins"
        await ctx.send(f"👑 **Owner Action:** **{username}** (ID: `{user_id}`) ke account se kamyabi se **{display_amt}** remove kar diye gaye hain!")

async def setup(bot):
    await bot.add_cog(OwnerRemoveMoney(bot))