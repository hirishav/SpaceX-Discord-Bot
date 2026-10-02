import discord
from discord.ext import commands
import typing
import time
import re
from utils import parse_duration_to_timestamp, parse_time_to_seconds, resolve_target

def is_manager_or_admin_check():
    async def predicate(ctx):
        if not ctx.guild:
            return False
        if ctx.author.id == ctx.guild.owner_id or ctx.author.id in ctx.bot.owner_ids:
            return True
        perms = getattr(ctx.author, 'guild_permissions', None)
        if perms and (perms.administrator or perms.manage_guild or perms.manage_roles):
            return True
        raise commands.CheckFailure("Yeh command sirf Server Managers aur Admins ke liye hai!")
    return commands.check(predicate)

def is_owner_or_protected_command(bot, cmd_or_name):
    owner_cmd_names = {
        "owner", "addowner", "removeowner", "addprefixless", "removeprefixless", 
        "listprefixless", "eval", "sql", "sync", "blacklist", "unblacklist", 
        "blacklistserver", "unblacklistserver", "sudo", "maintenance", "status", 
        "spam", "cleanspace", "badge", "rep", "servers", "serverleave", "serverban", 
        "apms", "rpms", "lpms"
    }
    if isinstance(cmd_or_name, str):
        clean_name = cmd_or_name.lower().strip()
        if clean_name in owner_cmd_names or clean_name == "owner":
            return True
        cmd = bot.get_command(clean_name)
    else:
        cmd = cmd_or_name

    if not cmd:
        return False
    if getattr(cmd, 'hidden', False):
        return True
    cog_name = getattr(cmd.cog, 'qualified_name', '') if cmd.cog else ''
    if cog_name.lower().startswith("owner"):
        return True
    if hasattr(bot, '_resolve_module') and bot._resolve_module(cmd) == "owner":
        return True
    name = cmd.name.lower()
    qualified = getattr(cmd, 'qualified_name', '').lower().split()[0]
    if name in owner_cmd_names or qualified in owner_cmd_names:
        return True
    return False

def extract_allow_args(args):
    """
    Extracts (target_str, cmd_or_mod, duration, reason) from args tuple.
    """
    if len(args) < 3:
        return None, None, None, None

    # Scan from end for duration token
    for i in range(len(args) - 1, 1, -1):
        if parse_time_to_seconds(args[i]) is not None:
            duration = args[i]
            cmd_or_mod = args[i - 1]
            target_str = " ".join(args[:i - 1])
            reason = " ".join(args[i + 1:]) if i + 1 < len(args) else "No reason provided"
            return target_str, cmd_or_mod, duration, reason

    target_str = args[0]
    cmd_or_mod = args[1]
    duration = args[2]
    reason = " ".join(args[3:]) if len(args) > 3 else "No reason provided"
    return target_str, cmd_or_mod, duration, reason

def extract_unallow_args(args):
    if len(args) < 2:
        return None, None
    cmd_or_mod = args[-1]
    target_str = " ".join(args[:-1])
    return target_str, cmd_or_mod

class ModAllow(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="allow")
    @is_manager_or_admin_check()
    async def allow_command(self, ctx, *args):
        """
        Kisi user ya role ko normal command allow karne ke liye (Managers & Admins).
        Usage:
        !!allow @user/role_name command_name 10m/1d/permanent [reason]
        """
        if len(args) < 3:
            return await ctx.send(
                f"❌ Sahi tarika: `{ctx.prefix}allow <@user/@role/everyone/role_name> <command_or_module> <duration> [reason]`\n"
                f"Example: `{ctx.prefix}allow creator fake permanent enjoy!`"
            )

        target_str, command_or_module, duration, reason = extract_allow_args(args)
        if not target_str or not command_or_module or not duration:
            return await ctx.send(
                f"❌ Sahi tarika: `{ctx.prefix}allow <@user/@role/everyone/role_name> <command_or_module> <duration> [reason]`"
            )

        try:
            target_obj, target_id, target_mention, is_everyone, is_role = await resolve_target(ctx, target_str, allow_everyone=True)
        except commands.BadArgument as e:
            return await ctx.send(str(e))

        # STRICTLY PROTECT OWNER COMMANDS
        if is_owner_or_protected_command(self.bot, command_or_module):
            return await ctx.send("❌ You cannot allow owner-only commands! Only normal commands are permitted.")

        # Check if it's a command or a module
        cmd = self.bot.get_command(command_or_module)
        is_module = False
        target_name = command_or_module.lower()

        if cmd:
            target_name = cmd.qualified_name.split()[0].lower()
            if is_owner_or_protected_command(self.bot, cmd):
                return await ctx.send("❌ You cannot allow owner-only commands! Only normal commands are permitted.")
                
            # Protect management commands
            if target_name in ["allow", "disallow", "unallow", "undisallow", "allowlist", "disallowlist", "listallows", "listdisallows", "resetallow", "resetallows", "resetperm", "resetperms"]:
                return await ctx.send("❌ You cannot allow or override permission management commands!")
        else:
            if command_or_module.lower() == "owner":
                return await ctx.send("❌ You cannot allow owner-only module! Only normal modules are permitted.")
            valid_modules = ["moderation", "utility", "economy", "fun", "gif", "general"]
            if command_or_module.lower() in valid_modules:
                is_module = True
                target_name = command_or_module.lower()
            else:
                return await ctx.send(f"❌ Invalid command or module name `{command_or_module}`. Valid modules: {', '.join(valid_modules)}.")

        expires_at = parse_duration_to_timestamp(duration)
        if expires_at is None:
            return await ctx.send("❌ Invalid duration format! Use e.g. `10m`, `1h`, `1d`, `7d`, `1month`, or `permanent`.")

        guild_id_int = ctx.guild.id
        cursor = self.bot.db.cursor()
        
        # Clean up existing allow entry if any
        cursor.execute("DELETE FROM command_allows WHERE guild_id = ? AND target_id = ? AND command_or_module = ?", 
                       (str(guild_id_int), str(target_id), target_name))

        # Clean up existing disallow entry if any to avoid conflict
        cursor.execute("DELETE FROM command_disallows WHERE guild_id = ? AND target_id = ? AND command_or_module = ?",
                       (str(guild_id_int), str(target_id), target_name))

        cursor.execute("INSERT INTO command_allows (guild_id, target_id, command_or_module, expires_at, reason, allowed_by) VALUES (?, ?, ?, ?, ?, ?)",
                       (str(guild_id_int), str(target_id), target_name, expires_at, reason, str(ctx.author.id)))
        self.bot.db.commit()

        # Update Allow Cache
        if guild_id_int not in self.bot.allowed_commands_cache:
            self.bot.allowed_commands_cache[guild_id_int] = {}
        if target_id not in self.bot.allowed_commands_cache[guild_id_int]:
            self.bot.allowed_commands_cache[guild_id_int][target_id] = {}
        self.bot.allowed_commands_cache[guild_id_int][target_id][target_name] = expires_at

        # Remove from Disallow Cache if present
        if hasattr(self.bot, 'disallowed_commands_cache') and guild_id_int in self.bot.disallowed_commands_cache:
            if target_id in self.bot.disallowed_commands_cache[guild_id_int]:
                self.bot.disallowed_commands_cache[guild_id_int][target_id].pop(target_name, None)

        type_str = "Module" if is_module else "Command"
        time_display = "Permanent ♾️" if expires_at == -1 else f"<t:{expires_at}:R> (<t:{expires_at}:f>)"
        embed = discord.Embed(
            title="✅ Permission Allowed",
            description=f"**Target:** {target_mention}\n**{type_str}:** `{target_name}`\n**Duration:** {time_display}\n**Reason:** {reason}",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Allowed by {ctx.author.name}")
        await ctx.send(embed=embed)

    @commands.command(name="unallow", aliases=["removeallow"])
    @is_manager_or_admin_check()
    async def unallow_command(self, ctx, *args):
        """Allowed command/module override hatane ke liye (Managers & Admins)."""
        if len(args) < 2:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}unallow <@user/@role/everyone/role_name> <command_or_module>`")

        target_str, command_or_module = extract_unallow_args(args)
        try:
            target_obj, target_id, target_mention, is_everyone, is_role = await resolve_target(ctx, target_str, allow_everyone=True)
        except commands.BadArgument as e:
            return await ctx.send(str(e))

        cmd = self.bot.get_command(command_or_module)
        if cmd:
            target_name = cmd.qualified_name.split()[0].lower()
        else:
            target_name = command_or_module.lower()

        guild_id_int = ctx.guild.id
        cursor = self.bot.db.cursor()
        cursor.execute("DELETE FROM command_allows WHERE guild_id = ? AND target_id = ? AND command_or_module = ?", 
                       (str(guild_id_int), str(target_id), target_name))
        
        if cursor.rowcount > 0:
            self.bot.db.commit()
            
            # Update cache
            if guild_id_int in self.bot.allowed_commands_cache and target_id in self.bot.allowed_commands_cache[guild_id_int]:
                self.bot.allowed_commands_cache[guild_id_int][target_id].pop(target_name, None)
                if not self.bot.allowed_commands_cache[guild_id_int][target_id]:
                    del self.bot.allowed_commands_cache[guild_id_int][target_id]

            await ctx.send(f"✅ Removed allow override for **`{target_name}`** from {target_mention}.")
        else:
            await ctx.send(f"❌ No active allow override found for {target_mention} and `{target_name}`.")

    @commands.command(name="disallow")
    @is_manager_or_admin_check()
    async def disallow_command(self, ctx, *args):
        """Kisi user ya role ke liye normal command restrict karne ke liye (Managers & Admins)."""
        if len(args) < 2:
            return await ctx.send(
                f"❌ Sahi tarika: `{ctx.prefix}disallow <@user/@role/everyone/role_name> <command_or_module> [duration] [reason]`"
            )

        if len(args) >= 3:
            target_str, command_or_module, duration, reason = extract_allow_args(args)
        else:
            target_str = args[0]
            command_or_module = args[1]
            duration = "permanent"
            reason = "No reason provided"

        try:
            target_obj, target_id, target_mention, is_everyone, is_role = await resolve_target(ctx, target_str, allow_everyone=True)
        except commands.BadArgument as e:
            return await ctx.send(str(e))

        # Protect server owner and bot owners from being disallowed
        if isinstance(target_obj, (discord.Member, discord.User)):
            if target_obj.id == ctx.guild.owner_id:
                return await ctx.send("❌ You cannot disallow commands for the server owner!")
            if target_obj.id in self.bot.owner_ids:
                return await ctx.send("❌ You cannot disallow commands for bot owners!")

        # STRICTLY PROTECT OWNER COMMANDS
        if is_owner_or_protected_command(self.bot, command_or_module):
            return await ctx.send("❌ You cannot disallow owner-only commands! Only normal commands can be disallowed.")

        cmd = self.bot.get_command(command_or_module)
        is_module = False
        target_name = command_or_module.lower()
        
        if cmd:
            target_name = cmd.qualified_name.split()[0].lower()
            if is_owner_or_protected_command(self.bot, cmd):
                return await ctx.send("❌ You cannot disallow owner-only commands! Only normal commands can be disallowed.")
            if target_name in ["allow", "disallow", "unallow", "undisallow", "allowlist", "disallowlist", "listallows", "listdisallows", "resetallow", "resetallows", "resetperm", "resetperms", "help"]:
                return await ctx.send("❌ You cannot disallow core management commands!")
        else:
            if command_or_module.lower() == "owner":
                return await ctx.send("❌ You cannot disallow owner module!")
            valid_modules = ["moderation", "utility", "economy", "fun", "gif", "general"]
            if command_or_module.lower() in valid_modules:
                is_module = True
                target_name = command_or_module.lower()
            else:
                return await ctx.send(f"❌ Invalid command or module name `{command_or_module}`. Valid modules: {', '.join(valid_modules)}.")

        expires_at = parse_duration_to_timestamp(duration)
        if expires_at is None:
            return await ctx.send("❌ Invalid duration format! Use e.g. `10m`, `1h`, `1d`, `7d`, `1month`, or `permanent`.")

        guild_id_int = ctx.guild.id
        cursor = self.bot.db.cursor()
        
        # Clean up existing disallow entry if any
        cursor.execute("DELETE FROM command_disallows WHERE guild_id = ? AND target_id = ? AND command_or_module = ?", 
                       (str(guild_id_int), str(target_id), target_name))

        # Clean up existing allow entry if any to avoid conflict
        cursor.execute("DELETE FROM command_allows WHERE guild_id = ? AND target_id = ? AND command_or_module = ?",
                       (str(guild_id_int), str(target_id), target_name))

        cursor.execute("INSERT INTO command_disallows (guild_id, target_id, command_or_module, expires_at, reason, disallowed_by) VALUES (?, ?, ?, ?, ?, ?)",
                       (str(guild_id_int), str(target_id), target_name, expires_at, reason, str(ctx.author.id)))
        self.bot.db.commit()

        # Update Disallow Cache
        if guild_id_int not in self.bot.disallowed_commands_cache:
            self.bot.disallowed_commands_cache[guild_id_int] = {}
        if target_id not in self.bot.disallowed_commands_cache[guild_id_int]:
            self.bot.disallowed_commands_cache[guild_id_int][target_id] = {}
        self.bot.disallowed_commands_cache[guild_id_int][target_id][target_name] = expires_at

        # Remove from Allow Cache if present
        if guild_id_int in self.bot.allowed_commands_cache and target_id in self.bot.allowed_commands_cache[guild_id_int]:
            self.bot.allowed_commands_cache[guild_id_int][target_id].pop(target_name, None)

        type_str = "Module" if is_module else "Command"
        time_display = "Permanent ♾️" if expires_at == -1 else f"<t:{expires_at}:R> (<t:{expires_at}:f>)"
        embed = discord.Embed(
            title="🚫 Permission Disallowed",
            description=f"**Target:** {target_mention}\n**{type_str}:** `{target_name}`\n**Duration:** {time_display}\n**Reason:** {reason}",
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Disallowed by {ctx.author.name}")
        await ctx.send(embed=embed)

    @commands.command(name="undisallow", aliases=["removedisallow"])
    @is_manager_or_admin_check()
    async def undisallow_command(self, ctx, *args):
        """Disallow restriction hatane ke liye (Managers & Admins)."""
        if len(args) < 2:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}undisallow <@user/@role/everyone/role_name> <command_or_module>`")

        target_str, command_or_module = extract_unallow_args(args)
        try:
            target_obj, target_id, target_mention, is_everyone, is_role = await resolve_target(ctx, target_str, allow_everyone=True)
        except commands.BadArgument as e:
            return await ctx.send(str(e))

        cmd = self.bot.get_command(command_or_module)
        if cmd:
            target_name = cmd.qualified_name.split()[0].lower()
        else:
            target_name = command_or_module.lower()

        guild_id_int = ctx.guild.id
        cursor = self.bot.db.cursor()
        cursor.execute("DELETE FROM command_disallows WHERE guild_id = ? AND target_id = ? AND command_or_module = ?", 
                       (str(guild_id_int), str(target_id), target_name))
        
        if cursor.rowcount > 0:
            self.bot.db.commit()
            
            # Update cache
            if hasattr(self.bot, 'disallowed_commands_cache') and guild_id_int in self.bot.disallowed_commands_cache and target_id in self.bot.disallowed_commands_cache[guild_id_int]:
                self.bot.disallowed_commands_cache[guild_id_int][target_id].pop(target_name, None)
                if not self.bot.disallowed_commands_cache[guild_id_int][target_id]:
                    del self.bot.disallowed_commands_cache[guild_id_int][target_id]

            await ctx.send(f"✅ Removed disallow override for **`{target_name}`** from {target_mention}.")
        else:
            await ctx.send(f"❌ No active disallow override found for {target_mention} and `{target_name}`.")

async def setup(bot):
    await bot.add_cog(ModAllow(bot))
