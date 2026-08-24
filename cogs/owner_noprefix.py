# cogs/owner_noprefix.py
import discord
from discord.ext import commands

class OwnerNoPrefix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="addprefixless", hidden=True)
    @commands.is_owner()
    async def add_prefixless(self, ctx, member: discord.Member = None):
        """👑 Owner Only: Kisi member ko bina prefix ke bot use karne ki permission dene ke liye."""
        if not member:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}addprefixless @user`")

        # ⚡ SPEED HACK: Global connection cursor mapping
        cursor = self.bot.db.cursor()
        try:
            cursor.execute("INSERT INTO prefixless_users (user_id) VALUES (?)", (str(member.id),))
            self.bot.db.commit()
            
            # 🔥 LIVE MEMORY CACHE INJECTION: Direct inject hash integer to run-time set
            if hasattr(self.bot, 'prefixless_cache'):
                self.bot.prefixless_cache.add(member.id)
            
            await ctx.send(f"✅ **{member.name}** ko prefixless access de diya gaya hai! Ab ye launda bina prefix ke aag laga sakta hai. 😎")
        except Exception:
            # Handle standard unique integrity violation array checks
            await ctx.send("❌ Yeh banda pehle se hi whitelisted hai bhai!")

    @commands.command(name="removeprefixless", aliases=["rp"], hidden=True)
    @commands.is_owner()
    async def remove_prefixless(self, ctx, member: discord.Member = None):
        """👑 Owner Only: Kisi user ka prefixless access wapas chheen ne ke liye."""
        if not member:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}removeprefixless @user`")

        cursor = self.bot.db.cursor()
        cursor.execute("DELETE FROM prefixless_users WHERE user_id = ?", (str(member.id),))
        
        if cursor.rowcount > 0:
            self.bot.db.commit()
            
            # 🔥 LIVE MEMORY CACHE DISCARD: Memory structure clean discard route
            if hasattr(self.bot, 'prefixless_cache'):
                self.bot.prefixless_cache.discard(member.id)
            
            await ctx.send(f"🔓 **{member.name}** ka prefixless access saaf kar diya gaya hai! Ab isko normal system follow karna hoga.")
        else:
            await ctx.send("❌ Yeh user whitelisted list me nahi mila bhai!")

    @commands.command(name="listprefixless", aliases=["lp"], hidden=True)
    @commands.is_owner()
    async def list_prefixless(self, ctx):
        """👑 Owner Only: Saare whitelisted logo ki absolute matrix list dekhne ke liye."""
        cursor = self.bot.db.cursor()
        cursor.execute("SELECT user_id FROM prefixless_users")
        rows = cursor.fetchall()

        embed = discord.Embed(title="🌌 SpaceX Whitelisted Prefixless Matrix", color=discord.Color.blue())
        if not rows:
            embed.description = "❌ Abhi tak koi bhi user whitelist nahi kiya gaya hai."
            return await ctx.send(embed=embed)

        users_text = ""
        for index, (user_id,) in enumerate(rows, 1):
            users_text += f"▪️ **#{index}** <@{user_id}> — ID: `{user_id}`\n"
        
        embed.description = users_text
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OwnerNoPrefix(bot))