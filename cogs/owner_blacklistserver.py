import discord
from discord.ext import commands

class OwnerBlacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="blacklistserver")
    @commands.is_owner()
    async def blacklistserver(self, ctx, server_id: str):
        """Blacklist a server so the bot leaves immediately."""
        cursor = self.bot.db.cursor()
        try:
            cursor.execute("INSERT INTO blacklisted_servers (server_id) VALUES (?)", (server_id,))
            self.bot.db.commit()
            
            guild = self.bot.get_guild(int(server_id))
            if guild:
                await guild.leave()
                await ctx.send(f"✅ Blacklisted server `{guild.name}` ({server_id}) and left it immediately!")
            else:
                await ctx.send(f"✅ Blacklisted server ID `{server_id}` for future invites!")
        except Exception as e:
            await ctx.send(f"❌ Error (maybe already blacklisted?): {e}")

    @commands.hybrid_command(name="whitelistserver")
    @commands.is_owner()
    async def whitelistserver(self, ctx, server_id: str):
        """Remove a server from the blacklist."""
        cursor = self.bot.db.cursor()
        cursor.execute("DELETE FROM blacklisted_servers WHERE server_id = ?", (server_id,))
        self.bot.db.commit()
        await ctx.send(f"✅ Removed server ID `{server_id}` from blacklist!")

async def setup(bot):
    await bot.add_cog(OwnerBlacklist(bot))
