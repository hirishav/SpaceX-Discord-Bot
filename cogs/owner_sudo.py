import discord
from discord.ext import commands
import copy

class OwnerSudo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sudo")
    @commands.is_owner()
    async def sudo(self, ctx, target: discord.User, *, command_string: str):
        """Run a command as another user."""
        msg = copy.copy(ctx.message)
        msg.author = target
        msg.content = f"{ctx.prefix}{command_string}"
        await self.bot.process_commands(msg)

async def setup(bot):
    await bot.add_cog(OwnerSudo(bot))
