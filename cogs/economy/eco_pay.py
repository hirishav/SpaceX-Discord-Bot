import discord
from discord.ext import commands

class InfluencerPay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['give', 'transfer', 'donate'])
    async def pay(self, ctx, target: discord.Member = None, amount: int = None):
        if not target or not amount:
            return await ctx.send("❌ Usage: `!pay @user <amount>`")
            
        if amount <= 0:
            return await ctx.send("❌ Amount must be greater than 0.")
            
        if target.id == ctx.author.id:
            return await ctx.send("❌ You can't pay yourself.")

        user_id = str(ctx.author.id)
        target_id = str(target.id)
        
        cursor = self.bot.db.cursor()
        cursor.execute("INSERT OR IGNORE INTO influencer_stats (user_id) VALUES (?)", (user_id,))
        cursor.execute("INSERT OR IGNORE INTO influencer_stats (user_id) VALUES (?)", (target_id,))
        self.bot.db.commit()
        
        cursor.execute("SELECT cash FROM influencer_stats WHERE user_id = ?", (user_id,))
        cash = cursor.fetchone()[0]
        
        if cash < amount:
            return await ctx.send(f"❌ You don't have enough cash. You only have `${cash:,}`.")
            
        cursor.execute("UPDATE influencer_stats SET cash = cash - ? WHERE user_id = ?", (amount, user_id))
        cursor.execute("UPDATE influencer_stats SET cash = cash + ? WHERE user_id = ?", (amount, target_id))
        self.bot.db.commit()
        
        await ctx.send(f"💸 **{ctx.author.display_name}** donated `${amount:,}` to **{target.display_name}**!")

async def setup(bot):
    await bot.add_cog(InfluencerPay(bot))
