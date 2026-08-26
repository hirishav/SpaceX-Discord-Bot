import discord
from discord.ext import commands
import copy
import typing

class SudoContext(commands.Context):
    is_sudo = True
    @property
    def permissions(self):
        return discord.Permissions.all()

class OwnerSudo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sudo")
    @commands.is_owner()
    async def sudo(self, ctx, target: typing.Optional[typing.Union[discord.Member, discord.User]] = None, *, command_string: str):
        """Run a command bypassing all permission checks, optionally as another user."""
        msg = copy.copy(ctx.message)
        msg.content = f"{ctx.prefix}{command_string}"
        if target:
            msg.author = target
            
        new_ctx = await self.bot.get_context(msg, cls=SudoContext)
        
        if not new_ctx.command:
            return await ctx.send(f"❌ Command `{command_string.split()[0]}` not found.")
            
        # Optional: Wrap author to bypass checks relying on ctx.author.guild_permissions
        class SudoAuthor:
            def __init__(self, member):
                self._member = member
            def __getattr__(self, name):
                return getattr(self._member, name)
            @property
            def __class__(self):
                return self._member.__class__
            @property
            def guild_permissions(self):
                return discord.Permissions.all()
                
        actual_target = target or new_ctx.author
        new_ctx.author = SudoAuthor(actual_target)
        
        try:
            await self.bot.invoke(new_ctx)
        except commands.CommandError as e:
            await ctx.send(f"⚠️ Sudo execution resulted in an error: {e}")

async def setup(bot):
    await bot.add_cog(OwnerSudo(bot))
