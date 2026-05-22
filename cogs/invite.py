# cogs/invite.py
import discord
from discord.ext import commands

class Invite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="invite", aliases=["inv", "addbot"])
    async def invite(self, ctx):
        """Bot ko apne server me add karne ke liye invite link deta hai (No Delete Fix)."""
        
        bot_id = self.bot.user.id
        invite_link = f"https://discord.com/oauth2/authorize?client_id=1505527456155570196&permissions=7707175400501110&integration_type=0&scope=bot+applications.commands"

        embed = discord.Embed(
            title=f"🤝 Invite {self.bot.user.name} to Your Server!",
            description=f"Kya aap mujhe apne server me le jaana chahte hain? Niche diye gaye link par click karke aap mujhe aaram se add kapte hain!\n\n🔗 **[Click Here to Invite Me]({invite_link})**",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.add_field(name="💡 Note", value="Bot ko sahi se chalne ke liye server me `Administrator` permission zaroor dena.", inline=False)
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)

        # FIX: ctx.message.delete() wala block poori tarah hata diya hai!
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Invite(bot))