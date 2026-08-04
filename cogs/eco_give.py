# cogs/eco_give.py
import discord
from discord.ext import commands
import database as sqlite3

class EcoGive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "warnings.db"

    def get_wallet(self, user_id: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT wallet FROM economy WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            cursor.execute("INSERT INTO economy (user_id, wallet, bank) VALUES (?, 0, 0)", (user_id,))
            conn.commit()
            conn.close()
            return 0
        conn.close()
        return row[0]

    @commands.command(name="give", aliases=["share", "pay"])
    async def give(self, ctx, member: discord.Member = None, amount_str: str = None):
        """Kisi doosre member ko apne wallet se paise dene ke liye."""
        if not member or not amount_str:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}give @user <amount/all/half>`")
            
        if member.id == ctx.author.id:
            return await ctx.send("❌ Apne aap ko paise dene ka kya faida bhai?")

        author_wallet = self.get_wallet(str(ctx.author.id))
        self.get_wallet(str(member.id)) # Target register check

        if author_wallet <= 0:
            return await ctx.send("❌ Aapka wallet khali hai, aap kya daan karoge!")

        # Parse amount_str (all / half / number)
        if amount_str.lower() == "all":
            amount = author_wallet
        elif amount_str.lower() == "half":
            amount = author_wallet // 2
        else:
            try:
                amount = int(amount_str)
            except ValueError:
                return await ctx.send("❌ Valid amount likho bhai (Number, all, ya half)!")

        if amount <= 0:
            return await ctx.send("❌ Amount 0 se bada hona chahiye!")
        if amount > author_wallet:
            return await ctx.send(f"❌ Aapke paas itne coins nahi hain! Current wallet: 🪙 `{author_wallet}`")

        # Update Database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (amount, str(ctx.author.id)))
        cursor.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (amount, str(member.id)))
        conn.commit()
        conn.close()

        await ctx.send(f"💸 {ctx.author.mention} ne {member.mention} ko 🪙 `{amount:,}` coins transfer kar diye!")

async def setup(bot):
    await bot.add_cog(EcoGive(bot))