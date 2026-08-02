# cogs/fun_confess.py
import discord
from discord.ext import commands
import sqlite3
import datetime

class FunConfess(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS confessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                user_name TEXT,
                confession TEXT,
                channel_id TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
        conn.close()

    @commands.command(name="confess")
    async def confess(self, ctx, channel: discord.TextChannel = None, *, message: str = None):
        """Mentioned channel me ek anonymous confession embed bhejta hai."""
        if not channel or not message:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}confess #channel-mention <confession_message>`\n👉 Example: `{ctx.prefix}confess #confessions I Love You Kriti`")

        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO confessions (user_id, user_name, confession, channel_id, timestamp) VALUES (?, ?, ?, ?, ?)",
            (str(ctx.author.id), ctx.author.name, message, str(channel.id), now_str)
        )
        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="🤫 Anonymous Confession",
            description=f'"{message}"',
            color=discord.Color.dark_purple()
        )
        embed.set_footer(text="Kisi ne chupke se apni baat kahi hai...")
        
        try:
            await channel.send(embed=embed)
            try:
                await ctx.message.delete()
            except Exception:
                pass
            await ctx.send("✅ Aapka confession anonymously bhej diya gaya hai!", delete_after=5)
        except discord.Forbidden:
            await ctx.send(f"❌ Mera paas {channel.mention} me message bhejne ki permission nahi hai!")

async def setup(bot):
    await bot.add_cog(FunConfess(bot))