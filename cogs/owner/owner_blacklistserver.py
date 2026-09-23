import discord
from discord.ext import commands

class OwnerBlacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="blacklistserver", aliases=["bls"])
    @commands.is_owner()
    async def blacklistserver(self, ctx, action: str, server_id: str = None):
        """Blacklist or unblacklist a server, or show blacklisted servers."""
        action = action.lower()
        if action not in ["add", "remove", "show"]:
            return await ctx.send("❌ Sahi tarika: `!!blacklistserver <add/remove/show> [server_id]`")
            
        cursor = self.bot.db.cursor()
        
        if action == "show":
            cursor.execute("SELECT server_id FROM blacklisted_servers")
            rows = cursor.fetchall()
            if not rows:
                return await ctx.send("✅ Koi bhi server blacklist me nahi hai.")
                
            servers_list = []
            for (sid,) in rows:
                guild = self.bot.get_guild(int(sid))
                name = guild.name if guild else "Unknown Server"
                servers_list.append(f"• **{name}** (`{sid}`)")
                
            # If the list is too long, we might need to truncate it, but for now we will just join them
            desc = "\n".join(servers_list)
            if len(desc) > 4000:
                desc = desc[:3990] + "...\n(Aur bhi hain)"
                
            embed = discord.Embed(
                title="🚫 Blacklisted Servers",
                description=desc,
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
            
        if not server_id:
            return await ctx.send("❌ `add` ya `remove` ke liye `server_id` dena zaroori hai!")
        
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
