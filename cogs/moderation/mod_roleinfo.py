import discord
from discord.ext import commands
from utils import SmartRoleConverter

class ModRoleInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="roleinfo")
    @commands.has_permissions(manage_roles=True)
    async def roleinfo(self, ctx, *, role_query: str):
        """Kisi bhi role ke baare me detail info, perms, aur channel access jaanein."""
        
        try:
            role = await SmartRoleConverter().convert(ctx, role_query)
        except commands.BadArgument as e:
            return await ctx.send(str(e))

        embed = discord.Embed(
            title=f"Role Info: {role.name}",
            color=role.color if role.color.value != 0 else discord.Color.default(),
            description=f"**ID:** {role.id}\n**Mention:** {role.mention}\n**Created At:** {discord.utils.format_dt(role.created_at, style='F')}\n**Members:** {len(role.members)}"
        )

        # Check Special Permissions
        perms = role.permissions
        special_perms = []
        if perms.administrator: special_perms.append("Administrator")
        if perms.ban_members: special_perms.append("Ban Members")
        if perms.kick_members: special_perms.append("Kick Members")
        if perms.manage_guild: special_perms.append("Manage Server")
        if perms.manage_roles: special_perms.append("Manage Roles")
        if perms.manage_channels: special_perms.append("Manage Channels")
        if perms.manage_messages: special_perms.append("Manage Messages")
        if perms.view_audit_log: special_perms.append("View Audit Log")
        if perms.manage_webhooks: special_perms.append("Manage Webhooks")
        if perms.manage_emojis_and_stickers: special_perms.append("Manage Emojis")
        if perms.mention_everyone: special_perms.append("Mention Everyone")
        if perms.moderate_members: special_perms.append("Timeout Members")

        if special_perms:
            embed.add_field(name="⚠️ Special Permissions", value=", ".join(special_perms), inline=False)
        else:
            embed.add_field(name="⚠️ Special Permissions", value="None", inline=False)

        # Check Basic Permissions
        general = []
        if perms.send_messages: general.append("Send Messages")
        if perms.embed_links: general.append("Embed Links")
        if perms.attach_files: general.append("Attach Files")
        if perms.connect: general.append("Connect to VC")
        if perms.speak: general.append("Speak in VC")
        if perms.stream: general.append("Video/Stream")

        if general:
            embed.add_field(name="✅ Basic Permissions", value=", ".join(general), inline=False)
            
        # Check Channel/VC Overrides
        allowed_channels = []
        denied_channels = []
        
        for channel in ctx.guild.channels:
            override = channel.overwrites_for(role)
            if not override.is_empty():
                if override.view_channel == True or override.send_messages == True or override.connect == True:
                    if len(allowed_channels) < 10:
                        allowed_channels.append(channel.mention)
                elif override.view_channel == False or override.send_messages == False or override.connect == False:
                    if len(denied_channels) < 10:
                        denied_channels.append(channel.mention)
                        
        if allowed_channels:
            allow_text = ", ".join(allowed_channels)
            if len(allowed_channels) == 10:
                allow_text += " and more..."
            embed.add_field(name="🔓 Special Access (Allowed Channels/VCs)", value=allow_text, inline=False)
            
        if denied_channels:
            deny_text = ", ".join(denied_channels)
            if len(denied_channels) == 10:
                deny_text += " and more..."
            embed.add_field(name="🔒 Special Restrictions (Denied Channels/VCs)", value=deny_text, inline=False)

        # Other Role Properties
        misc = []
        if role.hoist: misc.append("Displayed separately (Hoisted)")
        if role.mentionable: misc.append("Mentionable by anyone")
        if role.is_bot_managed(): misc.append("Bot managed role")
        if role.is_integration(): misc.append("Integration managed role")
        if role.is_premium_subscriber(): misc.append("Server Booster role")
        
        if misc:
            embed.add_field(name="📌 Other Attributes", value="\n".join([f"- {m}" for m in misc]), inline=False)

        await ctx.send(embed=embed)

    @roleinfo.error
    async def roleinfo_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            pass
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}roleinfo <@role/id/name>`")

async def setup(bot):
    await bot.add_cog(ModRoleInfo(bot))
