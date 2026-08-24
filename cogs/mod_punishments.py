# cogs/mod_punishments.py
import discord
from discord.ext import commands
import time
import datetime

class ModPunishments(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="punishments", aliases=["activepunishments", "activepunish"])
    @commands.has_permissions(moderate_members=True)
    async def punishments(self, ctx):
        """Dekhein server me active punishments (Mutes aur Temproles) kya hain."""
        
        await ctx.send("🔍 Active punishments dhoondh raha hoon... thoda wait karein.")

        active_punishments = []

        # 1. Active Timeouts (Mutes)
        muted_members = [m for m in ctx.guild.members if m.is_timed_out()]
        
        # Cache recent audit logs to find moderators
        timeout_logs = {}
        role_logs = {}
        
        if muted_members or self.bot.db:
            try:
                async for entry in ctx.guild.audit_logs(limit=200):
                    if entry.action == discord.AuditLogAction.member_update and hasattr(entry.after, 'communication_disabled_until'):
                        if entry.target.id not in timeout_logs:
                            timeout_logs[entry.target.id] = entry.user
                    elif entry.action == discord.AuditLogAction.member_role_update:
                        # Find added roles
                        added_roles = [r for r in entry.after.roles if r not in entry.before.roles]
                        for r in added_roles:
                            key = f"{entry.target.id}_{r.id}"
                            if key not in role_logs:
                                role_logs[key] = entry.user
            except discord.Forbidden:
                pass

        for member in muted_members:
            mod = timeout_logs.get(member.id)
            mod_mention = mod.mention if mod else "Unknown (Logs)"
            
            # Use discord timestamp format for relative time
            expiry = member.timed_out_until
            if expiry:
                expiry_ts = int(expiry.timestamp())
                time_str = f"<t:{expiry_ts}:R>"
            else:
                time_str = "Unknown"

            active_punishments.append(
                f"**[Mute]** {member.mention}\n"
                f"└ Expiring: {time_str}\n"
                f"└ Moderator: {mod_mention}"
            )

        # 2. Active Temproles
        try:
            cursor = self.bot.db.cursor()
            cursor.execute("SELECT user_id, role_id, expires_at FROM temproles WHERE guild_id = ?", (str(ctx.guild.id),))
            temproles = cursor.fetchall()

            for user_id, role_id, expires_at in temproles:
                member = ctx.guild.get_member(int(user_id))
                role = ctx.guild.get_role(int(role_id))
                
                member_str = member.mention if member else f"<@{user_id}>"
                role_str = role.mention if role else f"Deleted Role"
                
                key = f"{user_id}_{role_id}"
                mod = role_logs.get(int(user_id)) # We might not match exactly, but let's try
                mod_mention = "Unknown (Logs)"
                if key in role_logs:
                    mod_mention = role_logs[key].mention

                time_str = f"<t:{int(expires_at)}:R>"

                active_punishments.append(
                    f"**[Temprole]** {member_str} ({role_str})\n"
                    f"└ Expiring: {time_str}\n"
                    f"└ Moderator: {mod_mention}"
                )
        except Exception as e:
            print(f"Error fetching temproles: {e}")

        if not active_punishments:
            embed = discord.Embed(
                title="🛡️ Active Punishments",
                description="✅ Is server me koi bhi active mute ya temprole nahi hai. Ekdum shanti hai!",
                color=discord.Color.green()
            )
            return await ctx.channel.send(embed=embed)

        # Pagination / Chunking if there are too many
        chunks = []
        current_chunk = ""
        for punish in active_punishments:
            if len(current_chunk) + len(punish) + 2 > 4000:
                chunks.append(current_chunk)
                current_chunk = punish + "\n\n"
            else:
                current_chunk += punish + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk)

        for i, chunk in enumerate(chunks, start=1):
            embed = discord.Embed(
                title=f"🛡️ Active Punishments ({len(active_punishments)})" + (f" - Part {i}/{len(chunks)}" if len(chunks) > 1 else ""),
                description=chunk,
                color=discord.Color.orange()
            )
            await ctx.channel.send(embed=embed)

        try:
            await ctx.message.delete()
        except Exception:
            pass

    @punishments.error
    async def punishments_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Aapke paas is command ko use karne ki permission nahi hai (Moderate Members chahiye)!")
        else:
            await ctx.send(f"❌ Kuch gadbad hui: {error}")

async def setup(bot):
    await bot.add_cog(ModPunishments(bot))
