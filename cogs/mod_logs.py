# cogs/mod_logs.py
import discord
from discord.ext import commands
import sqlite3

class ModLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "warnings.db"

    async def fetch_user_id(self, ctx, user_str):
        try:
            member = await commands.MemberConverter().convert(ctx, user_str)
            return str(member.id), member.name
        except Exception:
            try:
                user = await self.bot.fetch_user(int(user_str))
                return str(user.id), user.name
            except Exception:
                return None, None

    @commands.command(name="modlogs", aliases=["logs"])
    @commands.has_permissions(manage_messages=True)
    async def modlogs(self, ctx, user_str: str = None):
        """Kisi user ke saare moderation history/stats dekhne ke liye."""
        if not user_str:
            return await ctx.send(f"❌ Sahi format: `{ctx.prefix}modlogs @user/ID`")

        user_id, username = await self.fetch_user_id(ctx, user_str)
        if not user_id:
            return await ctx.send("❌ Sahi user tag karo ya valid ID daalo bhai!")

        await ctx.send(f"📊 **{username}** ki history dhoondh raha hoon...")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 1. Fetch data from central mod_logs
        cursor.execute("SELECT action, moderator_id, reason, timestamp FROM mod_logs WHERE server_id = ? AND user_id = ? ORDER BY timestamp DESC", (str(ctx.guild.id), user_id))
        logs = cursor.fetchall()

        # 2. Fetch data from legacy warnings table (for backward compatibility)
        cursor.execute("SELECT id, reason, timestamp FROM warnings WHERE server_id = ? AND user_id = ? ORDER BY timestamp DESC", (str(ctx.guild.id), user_id))
        legacy_warns = cursor.fetchall()
        
        conn.close()

        # Formatting Logs
        embed = discord.Embed(title=f"🛡️ Moderation History: {username}", color=discord.Color.red())
        embed.set_footer(text=f"User ID: {user_id} • SpaceX Moderation")

        log_text = ""
        
        # Central logs add karein
        if logs:
            for action, mod_id, reason, ts in logs:
                log_text += f"➡️ **[{action.upper()}]** \n⏰ *{ts}* | Staff: <@{mod_id}>\n📝 Reason: `{reason}`\n\n"

        # Legacy warnings add karein (agar mod_logs me abhi tak entries nahi hui hain)
        if legacy_warns:
            log_text += "⚠️ **[ACTIVE WARNINGS]**\n"
            for w_id, reason, ts in legacy_warns:
                log_text += f"🆔 ID: `{w_id}` | ⏰ *{ts}*\n📝 Reason: `{reason}`\n\n"

        if not log_text:
            embed.description = "✅ Is user ka koi purana moderation record nahi mila. Ekdum sharif banda hai!"
            embed.color = discord.Color.green()
        else:
            # Discord limit handle karne ke liye slicing
            if len(log_text) > 4000:
                log_text = log_text[:3900] + "\n...Logs bohot lambe hain!"
            embed.description = log_text

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ModLogs(bot))