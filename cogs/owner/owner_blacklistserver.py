import discord
from discord.ext import commands

class OwnerBlacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="blacklistserver")
    @commands.is_owner()
    async def blacklistserver(self, ctx, action: str, server_id: str):
        """Blacklist or unblacklist a server."""
        action = action.lower()
        if action not in ["add", "remove"]:
            return await ctx.send("❌ Sahi tarika: `!!blacklistserver <add/remove> <server_id>`")
            
        cursor = self.bot.db.cursor()
        
        if action == "add":
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
                
        elif action == "remove":
            cursor.execute("DELETE FROM blacklisted_servers WHERE server_id = ?", (server_id,))
            if cursor.rowcount > 0:
                self.bot.db.commit()
                await ctx.send(f"✅ Removed server ID `{server_id}` from blacklist!")
            else:
                await ctx.send(f"⚠️ Server ID `{server_id}` blacklist me nahi hai.")

async def setup(bot):
    await bot.add_cog(OwnerBlacklist(bot))
