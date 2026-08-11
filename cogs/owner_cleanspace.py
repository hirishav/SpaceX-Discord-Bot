import discord
from discord.ext import commands

class OwnerCleanspace(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="cleanspace")
    @commands.is_owner()
    async def cleanspace(self, ctx, min_members: int = 10):
        """Leave servers with fewer than specified members."""
        await ctx.send(f"🧹 Scanning {len(self.bot.guilds)} servers for member count < {min_members}...")
        left = 0
        for guild in self.bot.guilds:
            if guild.member_count < min_members:
                try:
                    await guild.leave()
                    left += 1
                except:
                    pass
        await ctx.send(f"<a:owner:1453608135104270498> CleanSpace complete! Left {left} dead servers.")

async def setup(bot):
    await bot.add_cog(OwnerCleanspace(bot))
