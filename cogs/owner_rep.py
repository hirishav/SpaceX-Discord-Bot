# cogs/owner_rep.py
import discord
from discord.ext import commands
import database as sqlite3

class OwnerRep(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

    @commands.hybrid_command(name="addrep", hidden=True)
    @commands.is_owner()
    async def add_rep(self, ctx, user_str: str = None, amount_str: str = None):
        """Add rep points to a user. Usage: !!addrep @user 10"""
        if not user_str or not amount_str:
            return await ctx.send(f"❌ Usage: `{ctx.prefix}addrep @user/ID <amount>`")

        if not amount_str.isdigit():
            return await ctx.send("❌ Amount must be a valid number!")
            
        amount = int(amount_str)
        if amount <= 0:
            return await ctx.send("❌ Amount must be greater than 0!")

        user_id, username = await self.fetch_user(ctx, user_str)
        if not user_id:
            return await ctx.send("❌ User not found!")

        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO reps (user_id, rep_points) VALUES (?, 0)", (user_id,))
        cursor.execute("UPDATE reps SET rep_points = rep_points + ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        conn.close()

        await ctx.send(f"<a:owner:1453608135104270498> **Owner Action:** Added `{amount}` rep points to **{username}**!")

    @commands.hybrid_command(name="removerep", hidden=True)
    @commands.is_owner()
    async def remove_rep(self, ctx, user_str: str = None, amount_str: str = None):
        """Remove rep points from a user. Usage: !!removerep @user all/10"""
        if not user_str or not amount_str:
            return await ctx.send(f"❌ Usage: `{ctx.prefix}removerep @user/ID <amount/all>`")

        user_id, username = await self.fetch_user(ctx, user_str)
        if not user_id:
            return await ctx.send("❌ User not found!")

        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()

        if amount_str.lower() == "all":
            cursor.execute("UPDATE reps SET rep_points = 0 WHERE user_id = ?", (user_id,))
            msg = f"<a:owner:1453608135104270498> **Owner Action:** Removed all rep points from **{username}**!"
        else:
            if not amount_str.isdigit():
                conn.close()
                return await ctx.send("❌ Amount must be a valid number or 'all'!")
            
            amount = int(amount_str)
            if amount <= 0:
                conn.close()
                return await ctx.send("❌ Amount must be greater than 0!")

            cursor.execute("SELECT rep_points FROM reps WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            if not result or result[0] < amount:
                amount = result[0] if result else 0
                
            cursor.execute("UPDATE reps SET rep_points = rep_points - ? WHERE user_id = ?", (amount, user_id))
            msg = f"<a:owner:1453608135104270498> **Owner Action:** Removed `{amount}` rep points from **{username}**!"

        conn.commit()
        conn.close()

        await ctx.send(msg)

async def setup(bot):
    await bot.add_cog(OwnerRep(bot))
