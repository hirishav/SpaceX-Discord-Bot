import discord
from discord.ext import commands
import copy

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
    async def sudo(self, ctx, *, command_string: str):
        """Run a command bypassing all permission checks."""
        msg = copy.copy(ctx.message)
        msg.content = f"{ctx.prefix}{command_string}"
        
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
            def guild_permissions(self):
                return discord.Permissions.all()
                
        new_ctx.author = SudoAuthor(new_ctx.author)
        
        await self.bot.invoke(new_ctx)

async def setup(bot):
    await bot.add_cog(OwnerSudo(bot))
