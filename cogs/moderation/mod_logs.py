# cogs/moderation/mod_logs.py
import discord
from discord.ext import commands
import database as sqlite3
from utils import send_mod_log

class ModLogsSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_name = "warnings.db"
        self.valid_log_types = ["mod", "msg_delete", "msg_edit", "vcjoin", "vcleft", "vcdrag", "role_changes", "channel_changes", "perm_changes"]

    @commands.hybrid_command(name="logset")
    @commands.has_permissions(manage_guild=True)
    async def logset(self, ctx, log_type: str, channel: discord.TextChannel):
        """Set a channel for a specific log type (mod, msg_delete, msg_edit)."""
        log_type = log_type.lower()
        if log_type not in self.valid_log_types:
            return await ctx.send(f"❌ Invalid log type! Valid types are: `{', '.join(self.valid_log_types)}`")
            
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO log_channels (server_id, log_type, channel_id) VALUES (?, ?, ?)",
                (str(ctx.guild.id), log_type, str(channel.id))
            )
            conn.commit()
            conn.close()
            await ctx.send(f"✅ Successfully set `{log_type}` logs to {channel.mention}.")
        except Exception as e:
            await ctx.send(f"❌ Database error: {e}")

    @commands.hybrid_command(name="logremove")
    @commands.has_permissions(manage_guild=True)
    async def logremove(self, ctx, log_type: str):
        """Remove the log channel configuration for a specific log type."""
        log_type = log_type.lower()
        if log_type not in self.valid_log_types:
            return await ctx.send(f"❌ Invalid log type! Valid types are: `{', '.join(self.valid_log_types)}`")
            
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM log_channels WHERE server_id = ? AND log_type = ?",
                (str(ctx.guild.id), log_type)
            )
            conn.commit()
            conn.close()
            await ctx.send(f"✅ Successfully disabled `{log_type}` logs.")
        except Exception as e:
            await ctx.send(f"❌ Database error: {e}")

    @commands.hybrid_command(name="logconfig")
    @commands.has_permissions(manage_guild=True)
    async def logconfig(self, ctx):
        """View the current log channels configuration."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT log_type, channel_id FROM log_channels WHERE server_id = ?", (str(ctx.guild.id),))
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return await ctx.send("ℹ️ No log channels are currently configured for this server.")
                
            embed = discord.Embed(title="⚙️ Log Channels Configuration", color=discord.Color.blue())
            for log_type, channel_id in rows:
                channel = ctx.guild.get_channel(int(channel_id))
                channel_mention = channel.mention if channel else f"Unknown Channel ({channel_id})"
                embed.add_field(name=log_type, value=channel_mention, inline=False)
                
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Database error: {e}")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild:
            return
            
        embed = discord.Embed(
            title="🗑️ Message Deleted",
            description=message.content if message.content else "*No text content*",
            color=discord.Color.red()
        )
        embed.set_author(name=message.author.name, icon_url=message.author.display_avatar.url)
        
        files = []
        if message.attachments:
            # Join attachment URLs
            attachment_names = "\n".join([f"📎 [{att.filename}]({att.url})" for att in message.attachments])
            # Embed fields have a 1024 char limit
            if len(attachment_names) > 1000:
                attachment_names = attachment_names[:1000] + "..."
            embed.add_field(name="Attachments", value=attachment_names, inline=False)
            
            for att in message.attachments:
                if att.size < 8 * 1024 * 1024:  # Only attempt to download if less than 8MB
                    try:
                        file = await att.to_file(use_cached=True)
                        files.append(file)
                    except Exception as e:
                        print(f"Failed to download attachment for log: {e}")
            
            # Show first image in embed if available
            if files:
                first_image = next((f for f in files if f.filename.lower().endswith(('png', 'jpg', 'jpeg', 'gif', 'webp'))), None)
                if first_image:
                    embed.set_image(url=f"attachment://{first_image.filename}")
            
        if message.embeds:
            embed.add_field(name="Embeds", value=f"Message contained {len(message.embeds)} embed(s).", inline=False)
            
        embed.add_field(name="Channel", value=message.channel.mention)
        embed.set_footer(text=f"User ID: {message.author.id} | Message ID: {message.id}")
        
        await send_mod_log(self.bot, message.guild, "msg_delete", embed, files=files if files else None)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or not before.guild:
            return
            
        content_changed = before.content != after.content
        attachments_changed = len(before.attachments) != len(after.attachments)
        embeds_changed = len(before.embeds) != len(after.embeds)
        
        if not (content_changed or attachments_changed or embeds_changed):
            return
            
        # Ignore if only embeds changed (e.g., link unfurling or auto-embed) to avoid spam
        if embeds_changed and not (content_changed or attachments_changed):
            return
            
        embed = discord.Embed(
            title="✏️ Message Edited",
            url=after.jump_url,
            color=discord.Color.orange()
        )
        embed.set_author(name=before.author.name, icon_url=before.author.display_avatar.url)
        
        if content_changed:
            before_content = before.content[:1000] + "..." if len(before.content) > 1000 else before.content
            after_content = after.content[:1000] + "..." if len(after.content) > 1000 else after.content
            embed.add_field(name="Before", value=before_content or "*Empty*", inline=False)
            embed.add_field(name="After", value=after_content or "*Empty*", inline=False)
            
        if attachments_changed:
            embed.add_field(name="Attachments Changed", value=f"Before: {len(before.attachments)} | After: {len(after.attachments)}", inline=False)
            
        if embeds_changed:
            embed.add_field(name="Embeds Changed", value=f"Before: {len(before.embeds)} | After: {len(after.embeds)}", inline=False)
            
        embed.add_field(name="Channel", value=before.channel.mention)
        embed.set_footer(text=f"User ID: {before.author.id}")
        
        await send_mod_log(self.bot, before.guild, "msg_edit", embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot or not member.guild:
            return
            
        import asyncio
        if before.channel is None and after.channel is not None:
            # vcjoin
            embed = discord.Embed(title="🎙️ Joined Voice Channel", color=discord.Color.green())
            embed.set_author(name=member.name, icon_url=member.display_avatar.url)
            embed.add_field(name="Channel", value=after.channel.mention)
            embed.set_footer(text=f"User ID: {member.id}")
            await send_mod_log(self.bot, member.guild, "vcjoin", embed)
            
        elif before.channel is not None and after.channel is None:
            # vcleft
            embed = discord.Embed(title="🎙️ Left Voice Channel", color=discord.Color.red())
            
            kicker = None
            try:
                await asyncio.sleep(0.5)
                async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_disconnect):
                    if entry.target.id == member.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 10:
                        kicker = entry.user
                        break
            except Exception:
                pass
                
            if kicker:
                embed.title = "🎙️ Disconnected from Voice Channel"
                embed.set_author(name=f"{member.name} (Disconnected by {kicker.name})", icon_url=member.display_avatar.url)
            else:
                embed.set_author(name=member.name, icon_url=member.display_avatar.url)
                
            embed.add_field(name="Channel", value=before.channel.mention)
            embed.set_footer(text=f"User ID: {member.id}")
            await send_mod_log(self.bot, member.guild, "vcleft", embed)
            
        elif before.channel is not None and after.channel is not None and before.channel != after.channel:
            # vcdrag / move
            embed = discord.Embed(title="✈️ Moved Voice Channel", color=discord.Color.blue())
            
            mover = None
            try:
                await asyncio.sleep(0.5)
                async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_move):
                    if entry.target.id == member.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 10:
                        mover = entry.user
                        break
            except Exception:
                pass
                
            if mover:
                embed.set_author(name=f"{member.name} (Moved by {mover.name})", icon_url=member.display_avatar.url)
            else:
                embed.set_author(name=member.name, icon_url=member.display_avatar.url)
                
            embed.add_field(name="Before", value=before.channel.mention, inline=True)
            embed.add_field(name="After", value=after.channel.mention, inline=True)
            embed.set_footer(text=f"User ID: {member.id}")
            await send_mod_log(self.bot, member.guild, "vcdrag", embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        embed = discord.Embed(title="🎭 Role Created", description=f"Role: {role.mention}", color=discord.Color.green())
        
        creator = None
        try:
            import asyncio
            await asyncio.sleep(0.5)
            async for entry in role.guild.audit_logs(limit=3, action=discord.AuditLogAction.role_create):
                if entry.target.id == role.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 10:
                    creator = entry.user
                    break
        except Exception:
            pass
            
        if creator:
            embed.set_author(name=creator.name, icon_url=creator.display_avatar.url)
            
        embed.set_footer(text=f"Role ID: {role.id}")
        await send_mod_log(self.bot, role.guild, "role_changes", embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        embed = discord.Embed(title="🎭 Role Deleted", description=f"Role: **{role.name}**", color=discord.Color.red())
        
        deleter = None
        try:
            import asyncio
            await asyncio.sleep(0.5)
            async for entry in role.guild.audit_logs(limit=3, action=discord.AuditLogAction.role_delete):
                if entry.target.id == role.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 10:
                    deleter = entry.user
                    break
        except Exception:
            pass
            
        if deleter:
            embed.set_author(name=deleter.name, icon_url=deleter.display_avatar.url)
            
        embed.set_footer(text=f"Role ID: {role.id}")
        await send_mod_log(self.bot, role.guild, "role_changes", embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        embed = discord.Embed(title="📁 Channel Created", description=f"Channel: {channel.mention} ({channel.type})", color=discord.Color.green())
        
        creator = None
        try:
            import asyncio
            await asyncio.sleep(0.5)
            async for entry in channel.guild.audit_logs(limit=3, action=discord.AuditLogAction.channel_create):
                if entry.target.id == channel.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 10:
                    creator = entry.user
                    break
        except Exception:
            pass
            
        if creator:
            embed.set_author(name=creator.name, icon_url=creator.display_avatar.url)
            
        embed.set_footer(text=f"Channel ID: {channel.id}")
        await send_mod_log(self.bot, channel.guild, "channel_changes", embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        embed = discord.Embed(title="📁 Channel Deleted", description=f"Channel: **{channel.name}** ({channel.type})", color=discord.Color.red())
        
        deleter = None
        try:
            import asyncio
            await asyncio.sleep(0.5)
            async for entry in channel.guild.audit_logs(limit=3, action=discord.AuditLogAction.channel_delete):
                if entry.target.id == channel.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 10:
                    deleter = entry.user
                    break
        except Exception:
            pass
            
        if deleter:
            embed.set_author(name=deleter.name, icon_url=deleter.display_avatar.url)
            
        embed.set_footer(text=f"Channel ID: {channel.id}")
        await send_mod_log(self.bot, channel.guild, "channel_changes", embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        if before.permissions != after.permissions:
            embed = discord.Embed(title="🛡️ Role Permissions Changed", description=f"Role: {after.mention}", color=discord.Color.orange())
            
            # Fetch who made the change from audit logs
            modifier = None
            try:
                async for entry in after.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
                    if entry.target.id == after.id:
                        modifier = entry.user
                        break
            except discord.Forbidden:
                pass
            
            if modifier:
                embed.set_author(name=f"{modifier.name}", icon_url=modifier.display_avatar.url)

            added_perms = []
            removed_perms = []
            
            before_perms = dict(before.permissions)
            
            for perm, value in after.permissions:
                if before_perms.get(perm) != value:
                    formatted_perm = perm.replace('_', ' ').title()
                    if value:
                        added_perms.append(f"`{formatted_perm}`")
                    else:
                        removed_perms.append(f"`{formatted_perm}`")
            
            if added_perms:
                embed.add_field(name="✅ Added", value=", ".join(added_perms), inline=False)
            if removed_perms:
                embed.add_field(name="❌ Removed", value=", ".join(removed_perms), inline=False)
                
            embed.set_footer(text=f"Role ID: {after.id}")
            await send_mod_log(self.bot, after.guild, "perm_changes", embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        if before.overwrites != after.overwrites:
            embed = discord.Embed(title="🛡️ Channel Permissions Changed", description=f"Channel: {after.mention}", color=discord.Color.orange())
            
            modifier = None
            try:
                # Try to find the latest overwrite update
                async for entry in after.guild.audit_logs(limit=5):
                    if entry.target.id == after.id and entry.action in [
                        discord.AuditLogAction.overwrite_update,
                        discord.AuditLogAction.overwrite_create,
                        discord.AuditLogAction.overwrite_delete
                    ]:
                        modifier = entry.user
                        break
            except discord.Forbidden:
                pass
            
            if modifier:
                embed.set_author(name=f"{modifier.name}", icon_url=modifier.display_avatar.url)

            changed_targets = []
            for target, overwrite in after.overwrites.items():
                before_overwrite = before.overwrites.get(target)
                if before_overwrite != overwrite:
                    changed_targets.append((target, before_overwrite, overwrite))
            
            for target in before.overwrites:
                if target not in after.overwrites:
                    changed_targets.append((target, before.overwrites[target], None))
            
            for target, before_overwrite, after_overwrite in changed_targets:
                if before_overwrite is None:
                    before_dict = {}
                else:
                    before_dict = dict(before_overwrite)
                
                if after_overwrite is None:
                    # If overwrite was deleted, all perms revert to None (default)
                    after_dict = {perm: None for perm in before_dict}
                else:
                    after_dict = dict(after_overwrite)
                    
                target_added = []
                target_removed = []
                target_neutral = []
                
                all_perms = set(before_dict.keys()).union(after_dict.keys())
                for perm in all_perms:
                    b_val = before_dict.get(perm)
                    a_val = after_dict.get(perm)
                    if b_val != a_val:
                        formatted_perm = perm.replace('_', ' ').title()
                        if a_val is True:
                            target_added.append(f"`{formatted_perm}`")
                        elif a_val is False:
                            target_removed.append(f"`{formatted_perm}`")
                        elif a_val is None:
                            target_neutral.append(f"`{formatted_perm}`")
                
                if target_added or target_removed or target_neutral:
                    target_type = "Role" if isinstance(target, discord.Role) else "Member"
                    embed.add_field(name=f"Target: {target.name} ({target_type})", value="​", inline=False)
                    
                    if target_added:
                        embed.add_field(name="✅ Granted", value=", ".join(target_added), inline=False)
                    if target_removed:
                        embed.add_field(name="❌ Denied", value=", ".join(target_removed), inline=False)
                    if target_neutral:
                        embed.add_field(name="🔄 Reset", value=", ".join(target_neutral), inline=False)
                
            if len(embed.fields) > 0:
                embed.set_footer(text=f"Channel ID: {after.id}")
                await send_mod_log(self.bot, after.guild, "perm_changes", embed)
            
        elif before.name != after.name:
            embed = discord.Embed(title="📁 Channel Renamed", description=f"Channel: {after.mention}", color=discord.Color.blue())
            
            modifier = None
            try:
                async for entry in after.guild.audit_logs(limit=3, action=discord.AuditLogAction.channel_update):
                    if entry.target.id == after.id:
                        modifier = entry.user
                        break
            except discord.Forbidden:
                pass
                
            if modifier:
                embed.set_author(name=f"{modifier.name}", icon_url=modifier.display_avatar.url)
                
            embed.add_field(name="Before", value=before.name, inline=True)
            embed.add_field(name="After", value=after.name, inline=True)
            embed.set_footer(text=f"Channel ID: {after.id}")
            await send_mod_log(self.bot, after.guild, "channel_changes", embed)

async def setup(bot):
    await bot.add_cog(ModLogsSetup(bot))
