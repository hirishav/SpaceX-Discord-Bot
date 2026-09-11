# cogs/moderation/mod_seesay.py
import discord
from discord.ext import commands
import database as sqlite3

class ModSeeSay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_name = "warnings.db"

    @commands.hybrid_command(name="seesay")
    @commands.has_permissions(manage_messages=True)
    async def seesay(self, ctx, limit: int = 10):
        """Server managers ke liye: View recent 'say' command usages."""
        
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            
            # Fetch the latest logs for THIS server only
            cursor.execute(
                "SELECT user_id, username, message, timestamp FROM say_logs WHERE server_id = ? ORDER BY timestamp DESC LIMIT ?",
                (str(ctx.guild.id), limit)
            )
            logs = cursor.fetchall()
            conn.close()
            
            if not logs:
                return await ctx.send("❌ Is server me abhi tak kisi ne `say` command use nahi kiya hai.")
                
            embed = discord.Embed(
                title="🗣️ Recent Say Command Logs",
                description=f"Showing last {limit} messages sent via the `say` command.",
                color=discord.Color.blue()
            )
            
            for log in logs:
                user_id, username, message, timestamp = log
                
                # Truncate message if it's too long for embed field
                if len(message) > 900:
                    message = message[:900] + "..."
                    
                embed.add_field(
                    name=f"User: {username} ({user_id})",
                    value=f"**Message:** {message}\n**Time:** {timestamp}",
                    inline=False
                )
                
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Error fetching logs: {e}")

async def setup(bot):
    await bot.add_cog(ModSeeSay(bot))
