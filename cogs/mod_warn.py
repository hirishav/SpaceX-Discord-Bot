# cogs/mod_warn.py
import discord
from discord.ext import commands
import sqlite3

class ModWarn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_name = "warnings.db"

    @commands.command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kisi user ko warn karne ke liye (Sari errors se mukt code)."""
        
        server_id = str(ctx.guild.id)
        user_id = str(member.id)

        # 1. Database me save karna (Yeh sahi chal raha hai)
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO warnings (server_id, user_id, reason) VALUES (?, ?, ?)",
            (server_id, user_id, reason)
        )
        conn.commit()

        # Total warnings count karna
        cursor.execute(
            "SELECT COUNT(*) FROM warnings WHERE server_id = ? AND user_id = ?",
            (server_id, user_id)
        )
        total_warns = cursor.fetchone()[0]
        conn.close()

        # 2. CHAT EMBED (Ekdum basic bina kisi extra settings ke jo block ho sake)
        chat_embed = discord.Embed(
            title="⚠️ User Warned!", 
            description=f"{member.mention} ko kamyabi se warn kar diya gaya hai.",
            color=discord.Color.red()
        )
        chat_embed.add_field(name="👤 Target User", value=f"{member.name} ({member.id})", inline=True)
        chat_embed.add_field(name="🛡️ Staff", value=ctx.author.mention, inline=True)
        chat_embed.add_field(name="📝 Reason", value=reason, inline=False)
        chat_embed.add_field(name="🔢 Total Warnings", value=f"**{total_warns}**", inline=False)
        
        # Sabse pehle chat me embed bhejenge!
        await ctx.send(embed=chat_embed)

        # 3. MOD KA MESSAGE DELETE (Isko end me ekdum separate try me daal rahe hain taaki agar ye fail ho toh embed par asar na pade)
        try:
            await ctx.message.delete()
        except Exception:
            pass

        # 4. DM SYSTEM (Separate try block taaki agar user ka DM close ho toh chat embed na ruke)
        try:
            dm_embed = discord.Embed(
                title=f"⚠️ You have been warned in {ctx.guild.name}!", 
                description=f"Reason: **{reason}**\nTotal Warnings: **{total_warns}**",
                color=discord.Color.orange()
            )
            await member.send(embed=dm_embed)
        except Exception:
            # Agar DM fail hua toh chupchap skip karega, bot ko tang nahi karega
            pass

    @warn.error
    async def warn_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            pass
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}warn @user <reason>`")

async def setup(bot):
    await bot.add_cog(ModWarn(bot))