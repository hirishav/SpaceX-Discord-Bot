# cogs/mod_role.py
import discord
from discord.ext import commands
import asyncio
from utils import SmartRoleConverter

class ModRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="role")
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx, action: str, target: str, *, role_query: str):
        """
        Kisi ko ya sabko ek role assign ya remove karein.
        Usage: 
        !!role add everyone <role>
        !!role remove @user <role>
        !!role add <TargetRole> <RoleToAdd>
        """
        action = action.lower()
        if action not in ['add', 'remove']:
            return await ctx.send("❌ Action must be either `add` or `remove`.")

        await ctx.typing()

        # Step 1: Resolve the role to assign/remove
        try:
            target_role = await SmartRoleConverter().convert(ctx, role_query)
        except commands.BadArgument as e:
            return await ctx.send(str(e))

        # Check hierarchy
        if ctx.author.id != ctx.guild.owner_id and target_role >= ctx.author.top_role:
            return await ctx.send("❌ Aap apne se unche ya barabar ke role ko modify nahi kar sakte!")
            
        if target_role >= ctx.guild.me.top_role:
            return await ctx.send("❌ Mera role is role se niche hai, main isko kisi ko assign ya remove nahi kar sakta!")

        members_to_modify = []
        target_description = ""

        # Step 2: Resolve the target (who gets the role)
        if target.lower() == "everyone" or target.lower() == "@everyone":
            members_to_modify = [m async for m in ctx.guild.fetch_members(limit=None) if not m.bot]
            target_description = "Everyone"
        else:
            # Try to resolve as Member
            try:
                member = await commands.MemberConverter().convert(ctx, target)
                members_to_modify = [member]
                target_description = f"{member.display_name}"
            except commands.BadArgument:
                # Try to resolve as Role
                try:
                    source_role = await SmartRoleConverter().convert(ctx, target)
                    # Fetch all members (including offline) to find who has this role
                    members_to_modify = [m async for m in ctx.guild.fetch_members(limit=None) if not m.bot and source_role in m.roles]
                    target_description = f"Users with {source_role.name} role"
                except commands.BadArgument:
                    return await ctx.send(f"❌ Target `{target}` na toh koi user hai, na role, aur na hi 'everyone'.")

        if not members_to_modify:
            return await ctx.send(f"⚠️ `{target_description}` me koi valid members nahi mile.")

        msg = await ctx.send(f"⏳ Processing `{action}` **{target_role.name}** for **{target_description}** ({len(members_to_modify)} members)...")

        success_count = 0
        failed_count = 0

        # Process in batches to avoid rate limits
        for member in members_to_modify:
            try:
                if action == 'add' and target_role not in member.roles:
                    await member.add_roles(target_role, reason=f"Mass role by {ctx.author}")
                    success_count += 1
                elif action == 'remove' and target_role in member.roles:
                    await member.remove_roles(target_role, reason=f"Mass role by {ctx.author}")
                    success_count += 1
                
                # Small delay for mass actions
                if len(members_to_modify) > 5:
                    await asyncio.sleep(0.5)
                    
            except discord.Forbidden:
                failed_count += 1
            except Exception:
                failed_count += 1

        embed = discord.Embed(
            title="✅ Role Update Complete",
            color=discord.Color.green() if action == 'add' else discord.Color.orange()
        )
        embed.add_field(name="Action", value=action.capitalize(), inline=True)
        embed.add_field(name="Role", value=target_role.mention, inline=True)
        embed.add_field(name="Target", value=target_description, inline=True)
        embed.add_field(name="Success", value=f"{success_count} members", inline=True)
        if failed_count > 0:
            embed.add_field(name="Failed", value=f"{failed_count} members (Check permissions)", inline=True)

        await msg.edit(content=None, embed=embed)

    @role.error
    async def role_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            pass
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}role <add/remove> <everyone/@user/@role> <RoleName>`\nExample: `{ctx.prefix}role add everyone Active Member`")

async def setup(bot):
    await bot.add_cog(ModRole(bot))
