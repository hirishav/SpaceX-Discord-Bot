# cogs/mod_role.py
import discord
from discord.ext import commands

class ModRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="role")
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx, member: discord.Member, *, role: discord.Role):
        """Kisi user ko role assign ya remove karne ke liye."""
        
        # Checking hierarchy
        if ctx.author.id != ctx.guild.owner_id and role >= ctx.author.top_role:
            return await ctx.send("❌ Aap apne se unche ya barabar ke role ko kisi ko nahi de sakte!")
            
        if role >= ctx.guild.me.top_role:
            return await ctx.send("❌ Mera role is role se niche hai, main isko kisi ko assign ya remove nahi kar sakta!")

        try:
            if role in member.roles:
                await member.remove_roles(role, reason=f"Role removed by {ctx.author.name}")
                embed = discord.Embed(
                    title="➖ Role Removed",
                    description=f"**{member.display_name}** se {role.mention} role hata diya gaya hai.",
                    color=discord.Color.orange()
                )
            else:
                await member.add_roles(role, reason=f"Role assigned by {ctx.author.name}")
                embed = discord.Embed(
                    title="➕ Role Added",
                    description=f"**{member.display_name}** ko {role.mention} role assign kar diya gaya hai.",
                    color=discord.Color.green()
                )
                
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ Permission denied! Check karein ki mera role is role se upar hai ya nahi.")
            
    @role.error
    async def role_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            pass
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}role @user <role name/id/@role>`")
        elif isinstance(error, commands.RoleNotFound):
            await ctx.send(f"❌ Ye role server me nahi mila.")
            
async def setup(bot):
    await bot.add_cog(ModRole(bot))
