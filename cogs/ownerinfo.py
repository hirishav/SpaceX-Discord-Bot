import discord
from discord.ext import commands

class OwnerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ownerinfo", aliases=["owner"], help="Displays information about the bot creator Rishav.")
    async def owner_details(self, ctx): # Cogs me 'self' zaroori hai
        # Apni explicit public details yahan set karo
        owner_username = "phrenic_rishav" 
        owner_id = "727718500663033897" # Apni real numeric ID yahan daal dena
        github_link = "https://github.com/hirishav" # Apni profile link lagao
        
        embed = discord.Embed(
            title="🚀 SpaceX Bot Creator Info",
            description="Here are the public details of the developer behind SpaceX.",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="👑 Developer", value=owner_username, inline=True)
        embed.add_field(name="🆔 Discord ID", value=owner_id, inline=True)
        embed.add_field(name="🌐 GitHub", value=f"[Click Here]({github_link})", inline=True)
        embed.add_field(name="🛠️ Tech Stack", value="Python (Discord.py), Hosted on Render!", inline=False)
        
        # Discord avatar fetch karne ke liye (Cog format)
        try:
            user = await self.bot.fetch_user(int(owner_id))
            if user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
        except Exception:
            pass

        embed.set_footer(text="SpaceX Official Support • Secure & Verified Application")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OwnerInfo(bot))