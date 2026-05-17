# cogs/invite.py
import discord
from discord.ext import commands

class Invite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # BADAL DIYA: command se hybrid_command kar diya
    @commands.hybrid_command(name="invite", description="Bot ko apne server me add karne ke liye invite link deta hai.")
    async def invite(self, ctx):
        bot_id = self.bot.user.id
        invite_link = f"https://discord.com/api/oauth2/authorize?client_id={bot_id}&permissions=8&scope=bot%20applications.commands"

        embed = discord.Embed(
            title=f"🤝 Invite {self.bot.user.name} to Your Server!",
            description=f"🔗 **[Click Here to Invite Me]({invite_link})**",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Invite(bot))