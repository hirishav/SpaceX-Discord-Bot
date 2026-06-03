# cogs/mod_staffstats.py
import discord
from discord.ext import commands
import sqlite3
import datetime

class ModStaffStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "warnings.db"
        self.init_staff_db()

    def init_staff_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Master Log Ledger Matrix Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS staff_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT,
            staff_id TEXT,
            command_name TEXT,
            target_info TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
        conn.close()

    # 🔥 AUTOMATIC LISTENERS: Bina kisi extra code ke saare mod cogs ke operations automatic intercept karega
    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        mod_commands = [
            "warn", "warnings", "delwarn", "clearwarn", "mute", "unmute", 
            "kick", "ban", "unban", "purge", "clear", "clean", "slowmode", 
            "lock", "unlock", "lockdown", "say", "poll", "pin", "unpin", 
            "setprefix", "giveaway", "gstart", "giveawayend", "gend", "greroll", "reroll"
        ]
        
        if ctx.command.name not in mod_commands:
            return

        # Target extraction filter configurations
        target_info = "None/Global Action"
        if ctx.message.mentions:
            target_info = f"{ctx.message.mentions[0].name} ({ctx.message.mentions[0].id})"
        else:
            # Check string arguments array matrices for clean fallback
            args = ctx.message.content.split()
            if len(args) > 1 and args[1].isdigit():
                target_info = f"ID: {args[1]}"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO staff_logs (guild_id, staff_id, command_name, target_info) 
        VALUES (?, ?, ?, ?)
        """, (str(ctx.guild.id), str(ctx.author.id), ctx.command.name, target_info))
        conn.commit()
        conn.close()

    @commands.command(name="staffstats", aliases=["sstats", "modstats"])
    @commands.has_permissions(manage_messages=True)
    async def view_staff_stats(self, ctx, member: discord.Member = None):
        """Server ke moderators aur admins ke working records analytic dashboard dekhne ke liye."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if member:
            # --- CASE 1: Specific User Stats Analytic ---
            cursor.execute("""
                SELECT command_name, COUNT(command_name) 
                FROM staff_logs 
                WHERE guild_id = ? AND staff_id = ? 
                GROUP BY command_name
            """, (str(ctx.guild.id), str(member.id)))
            cmd_counts = cursor.fetchall()

            cursor.execute("""
                SELECT command_name, target_info, timestamp 
                FROM staff_logs 
                WHERE guild_id = ? AND staff_id = ? AND command_name IN ('warn', 'mute', 'kick', 'ban')
                ORDER BY timestamp DESC LIMIT 5
            """, (str(ctx.guild.id), str(member.id)))
            recent_actions = cursor.fetchall()
            conn.close()

            embed = discord.Embed(title=f"🛡️ Staff Analytics Profile: {member.name}", color=discord.Color.teal())
            embed.set_thumbnail(url=member.display_avatar.url)

            if not cmd_counts:
                embed.description = "❌ Is user ne abhi tak koi manager/admin execution route fire nahi kiya hai."
                return await ctx.send(embed=embed)

            metrics_text = ""
            for cmd, count in cmd_counts:
                metrics_text += f"▪️ Custom `{cmd}` Call: **{count} Baar**\n"
            embed.add_field(name="📊 Command Frequency Counters", value=metrics_text, inline=False)

            actions_text = ""
            if recent_actions:
                for cmd, target, ts in recent_actions:
                    actions_text += f"🔹 `{cmd.upper()}` ➡️ *{target}* \n"
            else:
                actions_text = "Koi structural critical action register nahi mila."
            embed.add_field(name="🚨 Recent Critical Punishment Logs", value=actions_text, inline=False)
            
            return await ctx.send(embed=embed)

        else:
            # --- CASE 2: Global Server Team Dashboard ---
            cursor.execute("""
                SELECT staff_id, COUNT(id) as total_actions 
                FROM staff_logs 
                WHERE guild_id = ? 
                GROUP BY staff_id 
                ORDER BY total_actions DESC LIMIT 10
            """, (str(ctx.guild.id),))
            top_staff = cursor.fetchall()
            conn.close()

            embed = discord.Embed(title="🏛️ Global Server Management Leaderboard", color=discord.Color.gold())
            embed.description = "Top active moderators aur unke aggregate total logged operations metrics layout:\n\n"

            if not top_staff:
                embed.description += "❌ Server logs ledger empty hai filhaal."
                return await ctx.send(embed=embed)

            for index, (staff_id, total) in enumerate(top_staff, 1):
                staff_user = ctx.guild.get_member(int(staff_id)) or await self.bot.fetch_user(int(staff_id))
                name_str = staff_user.mention if staff_user else f"Unknown Staff Member (`{staff_id}`)"
                embed.description += f"🏆 **#{index}** {name_str} — Total Logged Actions: **`{total}`**\n"
                
            embed.set_footer(text=f"Specific analysis ke liye: {ctx.prefix}staffstats @user")
            return await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ModStaffStats(bot))