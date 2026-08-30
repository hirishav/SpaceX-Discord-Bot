# cogs/fun_match.py
import discord
from discord.ext import commands
import random

class FunMatch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="match")
    async def match(self, ctx, user1: discord.Member, user2: discord.Member = None):
        """Do dosto ke beech ka love/friendship checker status layout."""
        if user2 is None:
            user2 = user1
            user1 = ctx.author

        score = random.randint(1, 100)
        
        if score > 85:
            comments = [
                "👑 Ekdum Rab Ne Bana Di Jodi! Inhe koi juda nahi kar sakta.",
                "💖 Laila Majnu fail hain inke aage! Kya bond hai bhai.",
                "💍 Seedha shaadi ka card chhapwao, perfect match hai!",
                "🔥 Aag laga denge dono milke! Ekdum top class compatibility.",
                "✨ Inka alag hi parallel universe chal raha hai. Best duo!"
            ]
        elif score > 50:
            comments = [
                "🤝 Dosti badiya hai, par kabhi bhi kalesh ho sakta hai!",
                "👍 Thik-thak hai, thodi aur mehnat ki zarurat hai dono ko.",
                "⚖️ 50-50 chance hai, ya toh best friends banenge ya dushman.",
                "👀 Dosti gehri hai, par peeth pichhe chugli chalu rehti hai.",
                "🤔 Thoda complicated rishta hai, aage bhagwan hi maalik hai."
            ]
        else:
            comments = [
                "🗑️ Bilkul kachra compatibility! Ek doosre ka sar phod denge ye dono.",
                "💀 Ek minute ek kamre me nahi reh sakte dono, WW3 ho jayega.",
                "🐍 Aasteen ke saanp hain dono ek dusre ke liye. Dur raho!",
                "🚫 Ye rishta kya kehlata hai? Toxic! Ekdum toxic!",
                "🤡 Dono ek dusre ko pagal kar denge, isse accha akele raho."
            ]
            
        comment = random.choice(comments)

        embed = discord.Embed(title="❤️ Compatibility Matrix Calculator", color=discord.Color.magenta())
        embed.description = f"👉 **{user1.mention}** & **{user2.mention}**\n\n🎯 Score: **{score}%**\n📝 **Verdict:** {comment}"
        embed.set_footer(text=f"Checked by {ctx.author.name}")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(FunMatch(bot))