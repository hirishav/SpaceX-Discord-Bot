import discord
from discord.ext import commands
import typing
import time
import re

def parse_duration(duration_str: str):
    if not duration_str:
        return -1
    match = re.match(r'^(\d+)(s|m|h|d|w|week|month|y|year)$', duration_str.lower())
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2)
    multiplier = 1
    if unit == 's': multiplier = 1
    elif unit == 'm': multiplier = 60
    elif unit == 'h': multiplier = 3600
    elif unit == 'd': multiplier = 86400
    elif unit in ['w', 'week']: multiplier = 604800
    elif unit == 'month': multiplier = 2592000
    elif unit in ['y', 'year']: multiplier = 31536000
    
    return int(time.time()) + (amount * multiplier)

class ModAllow(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="allow")
    @commands.has_permissions(administrator=True)
    async def allow_command(self, ctx, target: typing.Union[discord.User, discord.Role, str], command_or_module: str, duration: str, *, reason: str = "No reason provided"):
        """Allow a specific command or module for a user or role, bypassing permission checks."""
        # Clean target string if it's passed as everyone
        if isinstance(target, str):
            if target.lower() in ["everyone", "@everyone"]:
                target_id = ctx.guild.id
                target_mention = "@everyone"
            else:
                return await ctx.send("❌ Invalid target. Please mention a user, a role, or type `everyone`.")
        else:
            target_id = target.id
            target_mention = getattr(target, 'mention', str(target))

        # Check if it's a command or a module
        cmd = self.bot.get_command(command_or_module)
        is_module = False
        target_name = command_or_module
        
        if cmd:
            target_name = cmd.qualified_name.split()[0]
            # PROTECT OWNER COMMANDS
            if getattr(cmd, 'hidden', False) or (cmd.cog and cmd.cog.qualified_name.startswith("Owner")) or cmd.name in ["addprefixless", "eval", "sql", "sync", "removeprefixless", "listprefixless"]:
                return await ctx.send("❌ You cannot allow owner-only commands!")
                
            # VERIFY ADMIN CAN RUN IT
            try:
                can_run = await cmd.can_run(ctx)
                if not can_run:
                    return await ctx.send(f"❌ You cannot allow `{target_name}` because you yourself don't have permission to use it!")
            except commands.CommandError:
                return await ctx.send(f"❌ You cannot allow `{target_name}` because you yourself don't have permission to use it!")
                
        else:
            # Maybe it's a module
            valid_modules = ["moderation", "utility", "economy", "fun", "gif", "general"]
            if command_or_module.lower() in valid_modules:
                is_module = True
                target_name = command_or_module.lower()
            else:
                return await ctx.send("❌ Invalid command or module name. Please check and try again.")

        expires_at = parse_duration(duration)
        if expires_at is None:
            return await ctx.send("❌ Invalid duration format! Use 1s, 1m, 1h, 1d, 7d, 1week, 1month, 1year etc.")

        guild_id_int = ctx.guild.id
        cursor = self.bot.db.cursor()
        
        # Clean up existing entry if any
        cursor.execute("DELETE FROM command_allows WHERE guild_id = ? AND target_id = ? AND command_or_module = ?", 
                       (str(guild_id_int), str(target_id), target_name))

        cursor.execute("INSERT INTO command_allows (guild_id, target_id, command_or_module, expires_at, reason, allowed_by) VALUES (?, ?, ?, ?, ?, ?)",
                       (str(guild_id_int), str(target_id), target_name, expires_at, reason, str(ctx.author.id)))
        self.bot.db.commit()

        # Update Cache
        if guild_id_int not in self.bot.allowed_commands_cache:
            self.bot.allowed_commands_cache[guild_id_int] = {}
        if target_id not in self.bot.allowed_commands_cache[guild_id_int]:
            self.bot.allowed_commands_cache[guild_id_int][target_id] = {}
        
        self.bot.allowed_commands_cache[guild_id_int][target_id][target_name] = expires_at

        type_str = "Module" if is_module else "Command"
        embed = discord.Embed(
            title="✅ Permission Granted",
            description=f"**Target:** {target_mention}\n**{type_str}:** `{target_name}`\n**Duration:** `{duration}`\n**Reason:** {reason}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="disallow", aliases=["unallow"])
    @commands.has_permissions(administrator=True)
    async def disallow_command(self, ctx, target: typing.Union[discord.User, discord.Role, str], command_or_module: str):
        """Remove an allowed command/module override."""
        if isinstance(target, str):
            if target.lower() in ["everyone", "@everyone"]:
                target_id = ctx.guild.id
                target_mention = "@everyone"
            else:
                return await ctx.send("❌ Invalid target. Please mention a user, a role, or type `everyone`.")
        else:
            target_id = target.id
            target_mention = getattr(target, 'mention', str(target))

        cmd = self.bot.get_command(command_or_module)
        if cmd:
            target_name = cmd.qualified_name.split()[0]
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

            await ctx.send(f"✅ Removed allow override for **{target_name}** from {target_mention}.")
        else:
            await ctx.send("❌ No allow override found for that target and command/module.")

    @commands.command(name="listallows")
    @commands.has_permissions(administrator=True)
    async def list_allows(self, ctx):
        """List all active allowed command overrides in the server."""
        guild_id_int = ctx.guild.id
        
        # Clean up expired items first from DB
        current_time = int(time.time())
        cursor = self.bot.db.cursor()
        cursor.execute("DELETE FROM command_allows WHERE guild_id = ? AND expires_at != -1 AND expires_at <= ?", (str(guild_id_int), current_time))
        if cursor.rowcount > 0:
            self.bot.db.commit()
            
        cursor.execute("SELECT target_id, command_or_module, expires_at, reason FROM command_allows WHERE guild_id = ?", (str(guild_id_int),))
        rows = cursor.fetchall()
        
        if not rows:
            return await ctx.send("❌ There are no active allow overrides in this server.")
            
        embed = discord.Embed(title="✅ Allowed Command Overrides", color=discord.Color.blue())
        
        content = ""
        idx = 1
        for t_id, cmd_mod, exp, reason in rows:
            t_id_int = int(t_id)
            if t_id_int == guild_id_int:
                target_str = "@everyone"
            else:
                target_str = f"<@{t_id_int}> / <@&{t_id_int}>"
                
            time_str = "Permanent" if exp == -1 else f"<t:{exp}:R>"
            
            content += f"**{idx}.** {target_str}\n↳ **Item:** `{cmd_mod}` | **Expires:** {time_str}\n↳ **Reason:** {reason}\n\n"
            idx += 1
            
        if len(content) > 4096:
            content = content[:4000] + "... and more."
            
        embed.description = content
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ModAllow(bot))
