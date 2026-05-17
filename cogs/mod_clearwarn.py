# cogs/mod_clearwarn.py
import discord
from discord.ext import commands
import sqlite3

class ModClearWarn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_name = "warnings.db"

    @commands.command(name="clearwarn", aliases=["clearwarns"])
    @commands.has_permissions(manage_guild=True) # BADAL DIYA: Ab sirf Manage Server waale hi chala payenge
    async def clearwarn(self, ctx, member: discord.Member):
        """Kisi user ki saari warnings ek baar me clear karne ke liye (Manage Server Required)."""
        
        server_id = str(ctx.guild.id)
        user_id = str(member.id)

        # 1. Pehle check karte hain ki unke paas sach me koi warning hai ya nahi
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM warnings WHERE server_id = ? AND user_id = ?",
            (server_id, user_id)
        )
        count = cursor.fetchone()[0]

        if count == 0:
            conn.close()
            # Agar pehle se saaf hai, toh ek sundar green embed dikhao
            no_warn_embed = discord.Embed(
                title="✅ All Clean!",
                description=f"{member.mention} ke paas pehle se hi koi warning nahi hai.",
                color=discord.Color.green()
            )
            return await ctx.send(embed=no_warn_embed)

        # 2. Agar warnings hain, toh saari ek sath delete karna database se
        cursor.execute(
            "DELETE FROM warnings WHERE server_id = ? AND user_id = ?",
            (server_id, user_id)
        )
        conn.commit()
        conn.close()

        # Chat me confirmation embed bhejna
        embed = discord.Embed(
            title="🧹 Warnings Cleared!",
            description=f"{member.mention} ki saari **{count}** warnings ko poori tarah saaf kar diya gaya hai.",
            color=discord.Color.green()
        )
        embed.add_field(name="🛡️ Staff", value=ctx.author.mention, inline=True)
        
        await ctx.send(embed=embed)

        try:
            await ctx.message.delete()
        except Exception:
            pass

    @clearwarn.error
    async def clearwarn_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Aapke paas is command ko use karne ki `Manage Server` (Manage Guild) permission nahi hai! (Higher Staff Only)")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}clearwarn @user`")

async def setup(bot):
    await bot.add_cog(ModClearWarn(bot))