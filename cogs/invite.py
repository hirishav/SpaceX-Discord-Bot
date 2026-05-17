# cogs/invite.py
import discord
from discord.ext import commands

class Invite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="invite", aliases=["inv", "addbot"])
    async def invite(self, ctx):
        """Bot ko apne server me add karne ke liye invite link deta hai."""
        
        # Bot ka application ID nikalna automatic (Manually paste karne ka jhanjhat nahi)
        bot_id = self.bot.user.id
        
        # Administrator aur baaki sabhi sahi moderation permissions ke sath link (Oauth2)
        # Yeh link bot ko saari permissions automatic de dega jo humne use ki hain
        invite_link = f"https://discord.com/api/oauth2/authorize?client_id={bot_id}&permissions=8&scope=bot%20applications.commands"

        # Sunder Sunder Embed Banayein
        embed = discord.Embed(
            title=f"🤝 Invite {self.bot.user.name} to Your Server!",
            description=f"Kya aap mujhe apne server me le jaana chahte hain? Niche diye gaye link par click karke aap mujhe aaram se add kar sakte hain!\n\n🔗 **[Click Here to Invite Me]({invite_link})**",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.add_field(name="💡 Note", value="Bot ko sahi se chalne ke liye server me `Administrator` permission zaroor dena.", inline=False)
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

        # Command message delete karne ka try
        try:
            await ctx.message.delete()
        except Exception:
            pass

async def setup(bot):
    await bot.add_cog(Invite(bot))