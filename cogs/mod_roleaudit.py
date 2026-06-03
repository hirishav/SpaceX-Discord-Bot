# cogs/mod_roleaudit.py
import discord
from discord.ext import commands

class ModRoleAudit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roleaudit", aliases=["auditperms", "checkadmins"])
    @commands.has_permissions(administrator=True)
    async def role_audit_command(self, ctx):
        """Server ke dangerous permissions wale log aur total role counting analyze karne ke liye."""
        await ctx.send("🔍 Server permissions matrix audit kiya jaa raha hai...")

        admin_list = []
        manager_list = []

        for member in ctx.guild.members:
            if member.bot: continue
            if member.guild_permissions.administrator:
                admin_list.append(member.mention)
            elif member.guild_permissions.manage_guild or member.guild_permissions.manage_roles:
                manager_list.append(member.mention)

        embed = discord.Embed(title="🛡️ SpaceX Security Audit Ledger", color=discord.Color.dark_purple())
        
        embed.add_field(
            name=f"👑 Server Admins ({len(admin_list)})", 
            value=", ".join(admin_list) if admin_list else "Koi admin nahi mila (Khatra Mukt!)", 
            inline=False
        )
        embed.add_field(
            name=f"⚙️ Managers/Role Editors ({len(manager_list)})", 
            value=", ".join(manager_list) if manager_list else "Koi manager nahi mila.", 
            inline=False
        )
        
        embed.set_footer(text=f"Audited by: {ctx.author.name} | Security Status: Verified")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ModRoleAudit(bot))