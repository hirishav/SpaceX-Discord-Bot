# cogs/mod_unban.py
import discord
from discord.ext import commands

class ModUnban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, user_input: str):
        """Kisi banned user ko unban karne ke liye (ID ya Username se)."""
        
        banned_users = [entry async for entry in ctx.guild.bans()]
        target_user = None

        # User input ko check karna (Kya wo ID hai ya Username)
        for ban_entry in banned_users:
            user = ban_entry.user
            if user_input == str(user.id) or user_input.lower() == user.name.lower() or user_input.lower() == f"{user.name}#{user.discriminator}".lower():
                target_user = user
                break

        if not target_user:
            return await ctx.send(f"❌ Mujhe Banned Users ki list me `{user_input}` naam ka koi banda nahi mila!")

        try:
            await ctx.guild.unban(target_user, reason=f"Unbanned by {ctx.author.name}")
            
            embed = discord.Embed(
                title="🔓 Member Unbanned",
                description=f"**{target_user.name}** ka ban hata diya gaya hai.",
                color=discord.Color.green()
            )
            embed.add_field(name="👤 User", value=f"{target_user.name} ({target_user.id})", inline=True)
            embed.add_field(name="🛡️ Staff", value=ctx.author.mention, inline=True)
            await ctx.send(embed=embed)

            try:
                await ctx.message.delete()
            except Exception:
                pass

        except discord.Forbidden:
            await ctx.send("❌ Mere paas is bande ko unban karne ki permission nahi hai!")

    @unban.error
    async def unban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            pass
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}unban <User_ID_Ya_Username>`\nExample: `{ctx.prefix}unban 727718500663033897`")

async def setup(bot):
    await bot.add_cog(ModUnban(bot))