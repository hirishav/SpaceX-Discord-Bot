import discord
from discord.ext import commands

class OwnerSeeMine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def seemine(self, ctx, message_id: int):
        """Owner only: See where the mines are in an active mine game."""
        
        if not hasattr(self.bot, 'active_mine_games') or message_id not in self.bot.active_mine_games:
            return await ctx.send("❌ Koi active mine game nahi mila is message ID ke liye, ya fir game over ho chuka hai.")
            
        view = self.bot.active_mine_games[message_id]
        
        # Calculate mine positions based on the buttons in the view
        mines = []
        for btn in view.mine_buttons:
            if btn.is_mine:
                mines.append(str(btn.index + 1)) # +1 to make it 1-9 for readability
                
        mines_str = ", ".join(mines)
        
        embed = discord.Embed(
            title="🔍 Mine Locator (Admin)",
            description=f"**User:** {view.user.mention}\n**Mines at positions (1-9):** {mines_str}",
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Total mines: {view.mines_count}")
        
        await ctx.send(embed=embed, ephemeral=True)

    @seemine.error
    async def seemine_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("❌ Yeh command sirf owner use kar sakta hai!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}seemine <message_id>`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Message ID ek valid number hona chahiye.")
        else:
            await ctx.send(f"⚠️ Error: {error}")

async def setup(bot):
    await bot.add_cog(OwnerSeeMine(bot))
