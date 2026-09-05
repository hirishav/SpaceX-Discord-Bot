import discord
from discord.ext import commands

class InfluencerLeaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, aliases=['lb', 'top'])
    async def leaderboard(self, ctx):
        await ctx.send("🏆 Use `!top clout` or `!top cash` to see the leaderboards.")
        
    @leaderboard.command()
    async def clout(self, ctx):
        cursor = self.bot.db.cursor()
        cursor.execute("SELECT user_id, clout FROM influencer_stats ORDER BY clout DESC LIMIT 10")
        rows = cursor.fetchall()
        
        if not rows:
            return await ctx.send("No one has any Clout yet!")
            
        desc = ""
        for idx, (user_id, clout) in enumerate(rows, 1):
            desc += f"**{idx}.** <@{user_id}> — 🔥 `{clout:,}` Clout\n"
            
        embed = discord.Embed(title="🔥 Global Clout Leaderboard", description=desc, color=0x2b2d31)
        await ctx.send(embed=embed)
        
    @leaderboard.command()
    async def cash(self, ctx):
        cursor = self.bot.db.cursor()
        cursor.execute("SELECT user_id, cash FROM influencer_stats ORDER BY cash DESC LIMIT 10")
        rows = cursor.fetchall()
        
        if not rows:
            return await ctx.send("No one has any Cash yet!")
            
        desc = ""
        for idx, (user_id, cash) in enumerate(rows, 1):
            desc += f"**{idx}.** <@{user_id}> — 💰 `${cash:,}`\n"
            
        embed = discord.Embed(title="💰 Global Cash Leaderboard", description=desc, color=0x2b2d31)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(InfluencerLeaderboard(bot))
