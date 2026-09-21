import discord
from discord.ext import commands

class ModUserInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="userinfo", aliases=["ui"])
    @commands.guild_only()
    async def userinfo(self, ctx, member: discord.Member = None):
        """🕵️ Kisi user ke roles, kisne assign kiya, aur dangerous perms ki deep detail."""
        member = member or ctx.author

        await ctx.typing()

        # Gather basic info
        roles = [r for r in member.roles if r.name != "@everyone"]
        
        # Sort roles by position, highest first
        roles.sort(key=lambda r: r.position, reverse=True)

        # Dictionary to store who gave which role
        role_givers = {}

        # Fetch audit logs to find role assigners (limit to 300 to not take too long)
        if ctx.guild.me.guild_permissions.view_audit_log:
            try:
                # We fetch a decent amount of logs for role updates. 
                # If a role was assigned a long time ago, it might not be covered by the 300 limit.
                async for entry in ctx.guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=300):
                    if entry.target.id == member.id:
                        # In discord.py, added roles are typically in entry.after.roles
                        added_roles = getattr(entry.after, 'roles', [])
                        
                        for role in added_roles:
                            if role.id not in role_givers:
                                giver_name = entry.user.name
                                if entry.user.bot and entry.reason:
                                    if "Mass role by" in entry.reason:
                                        mod = entry.reason.split("Mass role by")[1].split("|")[0].strip()
                                        giver_name = f"{entry.user.name} bot (Cmd by {mod})"
                                    elif "Temprole by" in entry.reason:
                                        mod = entry.reason.split("Temprole by")[1].split("|")[0].strip()
                                        giver_name = f"{entry.user.name} bot (Cmd by {mod})"
                                    else:
                                        giver_name = f"{entry.user.name} bot (Reason: {entry.reason})"
                                elif entry.user.bot:
                                    giver_name = f"{entry.user.name} bot"
                                
                                role_givers[role.id] = giver_name
            except Exception as e:
                print(f"Error fetching audit logs for userinfo: {e}")

        dangerous_permissions = [
            'administrator', 'ban_members', 'kick_members', 'manage_guild', 
            'manage_roles', 'manage_channels', 'manage_messages', 
            'manage_webhooks', 'mention_everyone'
        ]

        # Build the embed description
        if not roles:
            desc = "Is user ke paas koi roles nahi hain."
        else:
            desc = "**Roles & Assigners:**\n"
            for role in roles:
                giver = role_givers.get(role.id, "Unknown (Too old/Not found)")
                desc += f"• {role.mention} - Given by: **{giver}**\n"

        embed = discord.Embed(title=f"🕵️ User Info: {member.name}", description=desc, color=member.color)
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Check for dangerous permissions globally for the member
        user_dangerous_perms = []
        for perm, value in member.guild_permissions:
            if value and perm in dangerous_permissions:
                formatted_name = perm.replace('_', ' ').title()
                user_dangerous_perms.append(formatted_name)

        if user_dangerous_perms:
            embed.add_field(
                name="⚠️ Dangerous Permissions", 
                value=", ".join([f"`{p}`" for p in user_dangerous_perms]), 
                inline=False
            )
        else:
            embed.add_field(
                name="⚠️ Dangerous Permissions", 
                value="`None`", 
                inline=False
            )
            
        embed.set_footer(text=f"Requested by {ctx.author.name} • ID: {member.id}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ModUserInfo(bot))
