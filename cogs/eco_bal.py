# cogs/eco_bal.py
import discord
from discord.ext import commands
import sqlite3

class EcoBal(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "warnings.db"

    def get_user_balance(self, user_id: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT wallet, bank FROM economy WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        
        if not row:
            cursor.execute("INSERT INTO economy (user_id, wallet, bank) VALUES (?, 0, 0)", (user_id,))
            conn.commit()
            row = (0, 0)
            
        conn.close()
        return row[0], row[1]

    @commands.command(name="balance", aliases=["bal", "money"])
    async def balance(self, ctx, member: discord.Member = None):
        """User ka global wallet aur bank balance check karne ke liye."""
        member = member or ctx.author
        wallet, bank = self.get_user_balance(str(member.id))
        total = wallet + bank

        embed = discord.Embed(title=f"💰 {member.name}'s Global Balance", color=discord.Color.green())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="👛 Wallet (Cash)", value=f"🪙 `{wallet:,}` coins", inline=True)
        embed.add_field(name="🏦 Bank Account", value=f"🪙 `{bank:,}` coins", inline=True)
        embed.add_field(name="📊 Total Net Worth", value=f"✨ `{total:,}` coins", inline=False)
        embed.set_footer(text="SpaceX Economy • Global System")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EcoBal(bot))