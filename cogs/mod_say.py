# cogs/mod_say.py
import discord
from discord.ext import commands

class ModSay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="say", aliases=["echo", "repeat"])
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx, *, message_content: str = None):
        """Bot se apni marzi ka message bulwane ke liye (Moderation Command)."""
        
        if message_content is None:
            return await ctx.send(f"❌ Rishav bhai, kuch likho toh sahi! Sahi tarika: `{ctx.prefix}say <aapka message>`")

        try:
            await ctx.message.delete()
        except Exception:
            pass

        await ctx.send(message_content)

    @say.error
    async def say_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            pass

async def setup(bot):
    await bot.add_cog(ModSay(bot))