# cogs/moderation/mod_logs.py
import discord
from discord.ext import commands
import database as sqlite3
from utils import send_mod_log

class ModLogsSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_name = "warnings.db"
        self.valid_log_types = ["mod", "msg_delete", "msg_edit"]

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

async def setup(bot):
    await bot.add_cog(ModLogsSetup(bot))
