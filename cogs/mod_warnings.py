# cogs/mod_warnings.py
import discord
from discord.ext import commands
import sqlite3

class ModWarnings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_name = "warnings.db"

    @commands.command(name="warnings", aliases=["warns"])
    @commands.has_permissions(manage_messages=True)
    async def warnings(self, ctx, member: discord.Member):
        """Kisi user ki saari warnings database se nikalne ke liye."""
        
        server_id = str(ctx.guild.id)
        user_id = str(member.id)

        # Database se saari reasons nikalna
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT reason FROM warnings WHERE server_id = ? AND user_id = ?",
            (server_id, user_id)
        )
        rows = cursor.fetchall()
        conn.close()

        # NAYA UPDATE: Agar koi warning nahi mili, toh ab text nahi balki EMBED aayega!
        if not rows:
            clean_embed = discord.Embed(
                title="😇 Clean Record!",
                description=f"{member.mention} ke paas koi warning nahi hai! Ekdum shareef banda hai. ✅",
                color=discord.Color.green()
            )
            clean_embed.set_thumbnail(url=member.display_avatar.url)
            return await ctx.send(embed=clean_embed)

        # Agar warnings hain, toh purana list wala embed dikhao
        embed = discord.Embed(title=f"📋 Warnings List: {member.name}", color=discord.Color.yellow())
        embed.set_thumbnail(url=member.display_avatar.url)

        for index, row in enumerate(rows, start=1):
            reason = row[0]
            embed.add_field(name=f"Warning #{index}", value=reason, inline=False)

        await ctx.send(embed=embed)

    @warnings.error
    async def warnings_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Aapke paas is command ko use karne ki `Manage Messages` permission nahi hai!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}warnings @user`")

async def setup(bot):
    await bot.add_cog(ModWarnings(bot))