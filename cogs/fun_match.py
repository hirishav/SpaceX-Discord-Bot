# cogs/fun_match.py
import discord
from discord.ext import commands
import random

class FunMatch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="match")
    async def match(self, ctx, user1: discord.Member, user2: discord.Member):
        """Do dosto ke beech ka love/friendship checker status layout."""
        score = random.randint(1, 100)
        
        if score > 85: comment = "👑 Ekdum Rab Ne Bana Di Jodi! Inhe koi juda nahi kar sakta."
        elif score > 50: comment = "🤝 Dosti badiya hai, par kabhi bhi kalesh ho sakta hai!"
        else: comment = "🗑️ Bilkul kachra compatibility! Ek doosre ka sar phod denge ye dono."

        embed = discord.Embed(title="❤️ Compatibility Matrix Calculator", color=discord.Color.magenta())
        embed.description = f"👉 **{user1.mention}** & **{user2.mention}**\n\n🎯 Score: **{score}%**\n📝 **Verdict:** {comment}"
        embed.set_footer(text=f"Checked by {ctx.author.name}")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(FunMatch(bot))