# cogs/mod_lookup.py
import discord
from discord.ext import commands

class ModLookup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="lookup", aliases=["whois", "userinfo"])
    @commands.has_permissions(manage_messages=True)
    async def user_lookup(self, ctx, member: discord.Member = None):
        """Server ke kisi bhi user ka raw account matrix aur granular data analytics dekhne ke liye."""
        member = member or ctx.author

        # Gather clean sorting layout for safety perms checking
        dangerous_perms = []
        for perm, value in member.guild_permissions:
            if value and perm in ["administrator", "manage_guild", "manage_roles", "ban_members", "kick_members"]:
                dangerous_perms.append(perm.replace('_', ' ').title())

        roles = [role.mention for role in member.roles[1:]] # Skip @everyone
        roles.reverse() # High to low positioning order array

        embed = discord.Embed(title=f"🕵️ Deep Lookup Ledger: {member.name}", color=member.color)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        embed.add_field(name="👤 Global Identity Name:", value=f"`{member.name}`\n👉 ID: `{member.id}`", inline=False)
        embed.add_field(name="⏳ Account Created At:", value=f"<t:{int(member.created_at.timestamp())}:F> (<t:{int(member.created_at.timestamp())}:R>)", inline=False)
        embed.add_field(name="📥 Server Joined At:", value=f"<t:{int(member.joined_at.timestamp())}:F> (<t:{int(member.joined_at.timestamp())}:R>)", inline=False)
        
        embed.add_field(name=f"🎴 Assigned Roles ({len(roles)}):", value=" ".join(roles) if roles else "`No custom roles assigned`", inline=False)
        
        if dangerous_perms:
            embed.add_field(name="🚨 Critical Administrative Overrides:", value=", ".join([f"`{p}`" for p in dangerous_perms]), inline=False)
        else:
            embed.add_field(name="🚨 Critical Administrative Overrides:", value="`None (Regular Account Matrix)`", inline=False)

        embed.set_footer(text=f"Queried by: {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ModLookup(bot))