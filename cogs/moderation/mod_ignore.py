import discord
from discord.ext import commands
import typing

class ModIgnore(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="ignore", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def ignore(self, ctx):
        """Ignore commands or modules for specific users or roles."""
        await ctx.send_help(ctx.command)

    @ignore.command(name="command")
    @commands.has_permissions(administrator=True)
    async def ignore_command(self, ctx, command_name: str, target: typing.Union[discord.User, discord.Role]):
        """Ignore a specific command for a user or role."""
        cmd = self.bot.get_command(command_name)
        if not cmd:
            return await ctx.send("❌ Invalid command name.")
            
        command_name = cmd.qualified_name.split()[0]
        if command_name in {"ignore", "unignore", "enable", "disable", "help"}:
            return await ctx.send("❌ You cannot ignore core commands.")
            
        is_role = 1 if isinstance(target, discord.Role) else 0
        target_id_str = str(target.id)
        
        cursor = self.bot.db.cursor()
        cursor.execute("SELECT 1 FROM ignored_commands_target WHERE server_id = ? AND target_id = ? AND command_name = ?", 
                       (str(ctx.guild.id), target_id_str, command_name))
        if cursor.fetchone():
            return await ctx.send(f"❌ Command `{command_name}` is already ignored for {target.mention}.")
            
        cursor.execute("INSERT INTO ignored_commands_target (server_id, target_id, is_role, command_name) VALUES (?, ?, ?, ?)",
                       (str(ctx.guild.id), target_id_str, is_role, command_name))
        self.bot.db.commit()
        
        if ctx.guild.id not in self.bot.ignored_commands_cache:
            self.bot.ignored_commands_cache[ctx.guild.id] = set()
        self.bot.ignored_commands_cache[ctx.guild.id].add((target_id_str, command_name))
        
        await ctx.send(f"✅ Ignored command `{command_name}` for {target.mention}.")

    @ignore.command(name="module")
    @commands.has_permissions(administrator=True)
    async def ignore_module(self, ctx, module_name: str, target: typing.Union[discord.User, discord.Role]):
        """Ignore an entire module for a user or role."""
        valid_modules = {"utility", "owner", "moderation", "economy", "fun", "general"}
        module_name = module_name.lower()
        if module_name not in valid_modules:
            return await ctx.send(f"❌ Invalid module name. Valid modules are: {', '.join(valid_modules)}")
            
        is_role = 1 if isinstance(target, discord.Role) else 0
        target_id_str = str(target.id)
        
        cursor = self.bot.db.cursor()
        cursor.execute("SELECT 1 FROM ignored_modules_target WHERE server_id = ? AND target_id = ? AND module_name = ?", 
                       (str(ctx.guild.id), target_id_str, module_name))
        if cursor.fetchone():
            return await ctx.send(f"❌ Module `{module_name}` is already ignored for {target.mention}.")
            
        cursor.execute("INSERT INTO ignored_modules_target (server_id, target_id, is_role, module_name) VALUES (?, ?, ?, ?)",
                       (str(ctx.guild.id), target_id_str, is_role, module_name))
        self.bot.db.commit()
        
        if ctx.guild.id not in self.bot.ignored_modules_cache:
            self.bot.ignored_modules_cache[ctx.guild.id] = set()
        self.bot.ignored_modules_cache[ctx.guild.id].add((target_id_str, module_name))
        
        await ctx.send(f"✅ Ignored module `{module_name}` for {target.mention}.")

    @commands.hybrid_group(name="unignore", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def unignore(self, ctx):
        """Unignore commands or modules for specific users or roles."""
        await ctx.send_help(ctx.command)

    @unignore.command(name="command")
    @commands.has_permissions(administrator=True)
    async def unignore_command(self, ctx, command_name: str, target: typing.Union[discord.User, discord.Role]):
        """Unignore a specific command for a user or role."""
        cmd = self.bot.get_command(command_name)
        if cmd:
            command_name = cmd.qualified_name.split()[0]
            
        target_id_str = str(target.id)
        
        cursor = self.bot.db.cursor()
        cursor.execute("DELETE FROM ignored_commands_target WHERE server_id = ? AND target_id = ? AND command_name = ?", 
                       (str(ctx.guild.id), target_id_str, command_name))
        if cursor.rowcount == 0:
            return await ctx.send(f"❌ Command `{command_name}` is not ignored for {target.mention}.")
            
        self.bot.db.commit()
        
        if ctx.guild.id in self.bot.ignored_commands_cache:
            self.bot.ignored_commands_cache[ctx.guild.id].discard((target_id_str, command_name))
        
        await ctx.send(f"✅ Unignored command `{command_name}` for {target.mention}.")

    @unignore.command(name="module")
    @commands.has_permissions(administrator=True)
    async def unignore_module(self, ctx, module_name: str, target: typing.Union[discord.User, discord.Role]):
        """Unignore an entire module for a user or role."""
        module_name = module_name.lower()
        target_id_str = str(target.id)
        
        cursor = self.bot.db.cursor()
        cursor.execute("DELETE FROM ignored_modules_target WHERE server_id = ? AND target_id = ? AND module_name = ?", 
                       (str(ctx.guild.id), target_id_str, module_name))
        if cursor.rowcount == 0:
            return await ctx.send(f"❌ Module `{module_name}` is not ignored for {target.mention}.")
            
        self.bot.db.commit()
        
        if ctx.guild.id in self.bot.ignored_modules_cache:
            self.bot.ignored_modules_cache[ctx.guild.id].discard((target_id_str, module_name))
        
        await ctx.send(f"✅ Unignored module `{module_name}` for {target.mention}.")

async def setup(bot):
    await bot.add_cog(ModIgnore(bot))
