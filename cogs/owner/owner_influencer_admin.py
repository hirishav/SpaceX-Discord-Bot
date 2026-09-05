import discord
from discord.ext import commands

class InfluencerAdmin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command()
    async def addcash(self, ctx, target: discord.Member, amount: int):
        cursor = self.bot.db.cursor()
        cursor.execute("INSERT OR IGNORE INTO influencer_stats (user_id) VALUES (?)", (str(target.id),))
        cursor.execute("UPDATE influencer_stats SET cash = cash + ? WHERE user_id = ?", (amount, str(target.id)))
        self.bot.db.commit()
        await ctx.send(f"✅ Added `💵 {amount:,}` to **{target.display_name}**.")

    @commands.command()
    async def addclout(self, ctx, target: discord.Member, amount: int):
        cursor = self.bot.db.cursor()
        cursor.execute("INSERT OR IGNORE INTO influencer_stats (user_id) VALUES (?)", (str(target.id),))
        cursor.execute("UPDATE influencer_stats SET clout = clout + ? WHERE user_id = ?", (amount, str(target.id)))
        self.bot.db.commit()
        await ctx.send(f"✅ Added `{amount:,}` Clout to **{target.display_name}**.")
        
    @commands.command()
    async def removecash(self, ctx, target: discord.Member, amount: int):
        cursor = self.bot.db.cursor()
        cursor.execute("UPDATE influencer_stats SET cash = MAX(0, cash - ?) WHERE user_id = ?", (amount, str(target.id)))
        self.bot.db.commit()
        await ctx.send(f"✅ Removed `💵 {amount:,}` from **{target.display_name}**.")
        
    @commands.command()
    async def removeclout(self, ctx, target: discord.Member, amount: int):
        cursor = self.bot.db.cursor()
        cursor.execute("UPDATE influencer_stats SET clout = MAX(0, clout - ?) WHERE user_id = ?", (amount, str(target.id)))
        self.bot.db.commit()
        await ctx.send(f"✅ Removed `{amount:,}` Clout from **{target.display_name}**.")
        
    @commands.command()
    async def resetinfluencer(self, ctx, target: discord.Member):
        cursor = self.bot.db.cursor()
        cursor.execute("DELETE FROM influencer_stats WHERE user_id = ?", (str(target.id),))
        cursor.execute("DELETE FROM influencer_gear WHERE user_id = ?", (str(target.id),))
        self.bot.db.commit()
        await ctx.send(f"✅ Reset all influencer stats and gear for **{target.display_name}**.")

async def setup(bot):
    await bot.add_cog(InfluencerAdmin(bot))
