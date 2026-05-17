# cogs/mod_delwarn.py
import discord
from discord.ext import commands
import sqlite3

class ModDelWarn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_name = "warnings.db"

    @commands.command(name="delwarn", aliases=["deletewarn", "unwarn"])
    @commands.has_permissions(manage_messages=True)
    async def delwarn(self, ctx, member: discord.Member, warn_num: int):
        """Kisi user ki koi ek specific warning number delete karne ke liye."""
        
        server_id = str(ctx.guild.id)
        user_id = str(member.id)

        # 1. Database se pehle us bande ki saari warnings nikalte hain sequence dekhne ke liye
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, reason FROM warnings WHERE server_id = ? AND user_id = ? ORDER BY id ASC",
            (server_id, user_id)
        )
        rows = cursor.fetchall()

        # Agar koi warning mili hi nahi
        if not rows:
            conn.close()
            return await ctx.send(f"❌ {member.mention} ke paas koi warning nahi hai jise delete kiya ja sake.")

        # Check karna ki jo number user ne daala hai (jaise 1 ya 2) wo list me hai ya nahi
        if warn_num < 1 or warn_num > len(rows):
            conn.close()
            return await ctx.send(f"❌ Galat warning number! {member.name} ke paas sirf **{len(rows)}** warnings hain.")

        # Sahi warning mil gayi! Uska asli database ID nikalna
        target_warn_id = rows[warn_num - 1][0]
        deleted_reason = rows[warn_num - 1][1]

        # 2. Database se us specific ID ko delete karna
        cursor.execute("DELETE FROM warnings WHERE id = ?", (target_warn_id,))
        conn.commit()
        conn.close()

        # Chat me confirmation embed bhejna
        embed = discord.Embed(
            title="✅ Warning Removed",
            description=f"{member.mention} ki **Warning #{warn_num}** kamyabi se mita di gayi hai.",
            color=discord.Color.green()
        )
        embed.add_field(name="📝 Deleted Warning Reason", value=deleted_reason, inline=False)
        embed.add_field(name="🛡️ Staff", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)

        # Moderator ka message delete karne ki koshish
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @delwarn.error
    async def delwarn_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Aapke paas `Manage Messages` permission nahi hai!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}delwarn @user <warning_number>`\nExample: `{ctx.prefix}delwarn @user 1`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Warning number hamesha ek number (integer) hona chahiye! (e.g., 1, 2, 3)")

async def setup(bot):
    await bot.add_cog(ModDelWarn(bot))