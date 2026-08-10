# cogs/mod_command.py
import discord
from discord.ext import commands

class ModCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="command")
    @commands.has_permissions(manage_guild=True)
    async def toggle_command(self, ctx, command_name: str):
        """Enable or disable a specific command in this server."""
        command_name = command_name.lower()
        
        if command_name == "command":
            return await ctx.send("❌ You cannot disable the command manager itself.")
            
        cmd = self.bot.get_command(command_name)
        if not cmd:
            return await ctx.send(f"❌ Command `{command_name}` not found.")
            
        # Get actual root command name in case an alias was provided
        command_name = cmd.name
            
        guild_id = ctx.guild.id
        
        # Check current status
        if guild_id not in self.bot.disabled_commands_cache:
            self.bot.disabled_commands_cache[guild_id] = set()
            
        if command_name in self.bot.disabled_commands_cache[guild_id]:
            # It's disabled, so enable it
            self.bot.disabled_commands_cache[guild_id].remove(command_name)
            cursor = self.bot.db.cursor()
            cursor.execute("DELETE FROM disabled_commands WHERE server_id = ? AND command_name = ?", (str(guild_id), command_name))
            self.bot.db.commit()
            
            embed = discord.Embed(
                title="Command Enabled",
                description=f"✅ The `{command_name}` command has been successfully **enabled** in this server.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            # It's enabled, so disable it
            self.bot.disabled_commands_cache[guild_id].add(command_name)
            cursor = self.bot.db.cursor()
            cursor.execute("INSERT OR REPLACE INTO disabled_commands (server_id, command_name) VALUES (?, ?)", (str(guild_id), command_name))
            self.bot.db.commit()
            
            embed = discord.Embed(
                title="Command Disabled",
                description=f"🚫 The `{command_name}` command has been successfully **disabled** in this server.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ModCommand(bot))
