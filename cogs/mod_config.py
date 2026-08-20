# cogs/mod_config.py
import discord
from discord.ext import commands

VALID_MODULES = {"moderation", "economy", "fun", "utility", "general"}

class ModConfig(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="disable", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def disable(self, ctx):
        """Disable a module or command in this server or channel."""
        await ctx.send(f"❌ Sahi usage: `{ctx.prefix}disable module <name> [#channel]` ya `{ctx.prefix}disable command <name> [#channel]`")

    @disable.command(name="module")
    @commands.has_permissions(manage_guild=True)
    async def disable_module(self, ctx, module_name: str, channel: discord.TextChannel = None):
        """Disable an entire module (category) globally or for a specific channel."""
        module_name = module_name.lower()
        if module_name not in VALID_MODULES:
            return await ctx.send(f"❌ Invalid module! Valid modules hain: `{', '.join(VALID_MODULES)}`")
            
        guild_id = ctx.guild.id
        
        if channel:
            channel_id = channel.id
            if channel_id in getattr(self.bot, 'enabled_modules_channel_cache', {}) and module_name in self.bot.enabled_modules_channel_cache.get(channel_id, set()):
                self.bot.enabled_modules_channel_cache[channel_id].remove(module_name)
                
            if channel_id not in self.bot.disabled_modules_channel_cache:
                self.bot.disabled_modules_channel_cache[channel_id] = set()
            self.bot.disabled_modules_channel_cache[channel_id].add(module_name)
            
            cursor = self.bot.db.cursor()
            try:
                cursor.execute("DELETE FROM enabled_modules_channel WHERE channel_id = ? AND module_name = ?", (str(channel_id), module_name))
                cursor.execute("INSERT OR REPLACE INTO disabled_modules_channel (channel_id, module_name) VALUES (?, ?)", (str(channel_id), module_name))
                self.bot.db.commit()
            finally:
                cursor.close()
            
            await ctx.send(f"🚫 `{module_name.capitalize()}` module is now disabled in {channel.mention}.")
        else:
            if guild_id not in self.bot.disabled_modules_server_cache:
                self.bot.disabled_modules_server_cache[guild_id] = set()
            self.bot.disabled_modules_server_cache[guild_id].add(module_name)
            
            cursor = self.bot.db.cursor()
            try:
                cursor.execute("INSERT OR REPLACE INTO disabled_modules_server (server_id, module_name) VALUES (?, ?)", (str(guild_id), module_name))
                self.bot.db.commit()
            finally:
                cursor.close()
                
            await ctx.send(f"🚫 `{module_name.capitalize()}` module is now disabled globally in this server.")

    @disable.command(name="command")
    @commands.has_permissions(manage_guild=True)
    async def disable_command(self, ctx, command_name: str, channel: discord.TextChannel = None):
        """Disable a specific command globally or for a specific channel."""
        command_name = command_name.lower()
        if command_name in ["disable", "enable", "command", "help"]:
            return await ctx.send("❌ Bhai isko disable mat kar, system break ho jayega!")
            
        cmd = self.bot.get_command(command_name)
        if not cmd:
            return await ctx.send(f"❌ Command `{command_name}` nahi mila.")
        
        command_name = cmd.name # Get root name
        guild_id = ctx.guild.id
        
        if channel:
            channel_id = channel.id
            if channel_id in getattr(self.bot, 'enabled_commands_channel_cache', {}) and command_name in self.bot.enabled_commands_channel_cache.get(channel_id, set()):
                self.bot.enabled_commands_channel_cache[channel_id].remove(command_name)
                
            if channel_id not in self.bot.disabled_commands_channel_cache:
                self.bot.disabled_commands_channel_cache[channel_id] = set()
            self.bot.disabled_commands_channel_cache[channel_id].add(command_name)
            
            cursor = self.bot.db.cursor()
            try:
                cursor.execute("DELETE FROM enabled_commands_channel WHERE channel_id = ? AND command_name = ?", (str(channel_id), command_name))
                cursor.execute("INSERT OR REPLACE INTO disabled_commands_channel (channel_id, command_name) VALUES (?, ?)", (str(channel_id), command_name))
                self.bot.db.commit()
            finally:
                cursor.close()
                
            await ctx.send(f"🚫 Command `{command_name}` is now disabled in {channel.mention}.")
        else:
            if guild_id not in self.bot.disabled_commands_cache:
                self.bot.disabled_commands_cache[guild_id] = set()
            self.bot.disabled_commands_cache[guild_id].add(command_name)
            
            cursor = self.bot.db.cursor()
            try:
                cursor.execute("INSERT OR REPLACE INTO disabled_commands (server_id, command_name) VALUES (?, ?)", (str(guild_id), command_name))
                self.bot.db.commit()
            finally:
                cursor.close()
                
            await ctx.send(f"🚫 Command `{command_name}` is now disabled globally in this server.")

    @commands.hybrid_group(name="enable", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def enable(self, ctx):
        """Enable a module or command in this server or channel."""
        await ctx.send(f"❌ Sahi usage: `{ctx.prefix}enable module <name> [#channel]` ya `{ctx.prefix}enable command <name> [#channel]`")

    @enable.command(name="module")
    @commands.has_permissions(manage_guild=True)
    async def enable_module(self, ctx, module_name: str, channel: discord.TextChannel = None):
        """Enable an entire module globally or for a specific channel."""
        module_name = module_name.lower()
        if module_name not in VALID_MODULES:
            return await ctx.send(f"❌ Invalid module! Valid modules hain: `{', '.join(VALID_MODULES)}`")
            
        guild_id = ctx.guild.id
        
        cursor = self.bot.db.cursor()
        try:
            if channel:
                channel_id = channel.id
                if channel_id in self.bot.disabled_modules_channel_cache and module_name in self.bot.disabled_modules_channel_cache[channel_id]:
                    self.bot.disabled_modules_channel_cache[channel_id].remove(module_name)
                
                if channel_id not in self.bot.enabled_modules_channel_cache:
                    self.bot.enabled_modules_channel_cache[channel_id] = set()
                self.bot.enabled_modules_channel_cache[channel_id].add(module_name)
                
                cursor.execute("DELETE FROM disabled_modules_channel WHERE channel_id = ? AND module_name = ?", (str(channel_id), module_name))
                cursor.execute("INSERT OR REPLACE INTO enabled_modules_channel (channel_id, module_name) VALUES (?, ?)", (str(channel_id), module_name))
                self.bot.db.commit()
                await ctx.send(f"✅ `{module_name.capitalize()}` module enabled in {channel.mention}.")
            else:
                if guild_id in self.bot.disabled_modules_server_cache and module_name in self.bot.disabled_modules_server_cache[guild_id]:
                    self.bot.disabled_modules_server_cache[guild_id].remove(module_name)
                cursor.execute("DELETE FROM disabled_modules_server WHERE server_id = ? AND module_name = ?", (str(guild_id), module_name))
                self.bot.db.commit()
                await ctx.send(f"✅ `{module_name.capitalize()}` module enabled globally.")
        finally:
            cursor.close()

    @enable.command(name="command")
    @commands.has_permissions(manage_guild=True)
    async def enable_command(self, ctx, command_name: str, channel: discord.TextChannel = None):
        """Enable a specific command globally or for a specific channel."""
        command_name = command_name.lower()
        cmd = self.bot.get_command(command_name)
        if not cmd:
            return await ctx.send(f"❌ Command `{command_name}` nahi mila.")
            
        command_name = cmd.name
            
        guild_id = ctx.guild.id
        
        cursor = self.bot.db.cursor()
        try:
            if channel:
                channel_id = channel.id
                if channel_id in self.bot.disabled_commands_channel_cache and command_name in self.bot.disabled_commands_channel_cache[channel_id]:
                    self.bot.disabled_commands_channel_cache[channel_id].remove(command_name)
                
                if channel_id not in self.bot.enabled_commands_channel_cache:
                    self.bot.enabled_commands_channel_cache[channel_id] = set()
                self.bot.enabled_commands_channel_cache[channel_id].add(command_name)
                
                cursor.execute("DELETE FROM disabled_commands_channel WHERE channel_id = ? AND command_name = ?", (str(channel_id), command_name))
                cursor.execute("INSERT OR REPLACE INTO enabled_commands_channel (channel_id, command_name) VALUES (?, ?)", (str(channel_id), command_name))
                self.bot.db.commit()
                await ctx.send(f"✅ Command `{command_name}` enabled in {channel.mention}.")
            else:
                if guild_id in self.bot.disabled_commands_cache and command_name in self.bot.disabled_commands_cache[guild_id]:
                    self.bot.disabled_commands_cache[guild_id].remove(command_name)
                cursor.execute("DELETE FROM disabled_commands WHERE server_id = ? AND command_name = ?", (str(guild_id), command_name))
                self.bot.db.commit()
                await ctx.send(f"✅ Command `{command_name}` enabled globally.")
        finally:
            cursor.close()

async def setup(bot):
    await bot.add_cog(ModConfig(bot))
