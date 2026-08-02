# cogs/util_avatar.py
import discord
from discord.ext import commands

class UtilAvatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="avatar", aliases=["av", "pfp"])
    async def avatar(self, ctx, member: discord.Member = None):
        """Kisi bhi member ki profile picture (avatar) dekhne ke liye."""
        # Agar koi member tag nahi kiya, toh command chalane wale ka avatar dikhao
        member = member or ctx.author

        embed = discord.Embed(
            title=f"🖼️ {member.name}'s Avatar",
            color=discord.Color.blue()
        )
        embed.set_image(url=member.display_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UtilAvatar(bot))