# cogs/mod_say.py
import discord
from discord.ext import commands

import database as sqlite3

class ModSay(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_name = "warnings.db"

    @commands.hybrid_command(name="say", aliases=["echo", "repeat"])
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx, *, message_content: str = None):
        """Bot se apni marzi ka message bulwane ke liye (Moderation Command)."""
        
        if message_content is None:
            return await ctx.send(f"❌ Rishav bhai, kuch likho toh sahi! Sahi tarika: `{ctx.prefix}say <aapka message>`")

        try:
            await ctx.message.delete()
        except Exception:
            pass

        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            server_id = str(ctx.guild.id) if ctx.guild else "DM"
            cursor.execute(
                "INSERT INTO say_logs (server_id, user_id, username, message) VALUES (?, ?, ?, ?)",
                (server_id, str(ctx.author.id), str(ctx.author.name), message_content)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Failed to log say command: {e}")

        await ctx.send(message_content)

    @say.error
    async def say_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Aapke paas `Manage Messages` ki permission nahi hai is command ko use karne ke liye!")

async def setup(bot):
    await bot.add_cog(ModSay(bot))