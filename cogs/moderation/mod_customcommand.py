# cogs/moderation/mod_customcommand.py
import discord
from discord.ext import commands

class ModCustomCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Structure: {server_id: {command_name: {"action": "add/remove/text", "roles": [role_id1, role_id2], "response": "text"}}}
        self.custom_cmds_cache = {}

    async def cog_load(self):
        # Load all custom commands into memory for fast lookup
        cursor = self.bot.db.cursor()
        try:
            cursor.execute("SELECT server_id, command_name, action, role_ids, response_message FROM custom_commands")
            for row in cursor.fetchall():
                server_id, name, action, role_ids, response = row
                s_id = int(server_id)
                if s_id not in self.custom_cmds_cache:
                    self.custom_cmds_cache[s_id] = {}
                
                self.custom_cmds_cache[s_id][name] = {
                    "action": action,
                    "roles": [int(r) for r in role_ids.split(",")] if role_ids else [],
                    "response": response
                }
        except Exception as e:
            print(f"Failed to load custom commands: {e}")
        finally:
            cursor.close()

    @commands.hybrid_command(name="addcmd")
    @commands.has_permissions(manage_roles=True)
    async def addcmd(self, ctx, action: str, command_name: str, *, message: str):
        """Creates a custom command. Action can be 'add', 'remove', or 'text'.
        Example: !!addcmd text rules Please read the rules!
        Example: !!addcmd add staff @StaffRole Welcome {user}!"""
        action = action.lower()
        if action not in ["add", "remove", "text"]:
            return await ctx.send("❌ Action must be `add`, `remove`, or `text`.")
            
        command_name = command_name.lower()
        
        if command_name in self.bot.all_commands:
            return await ctx.send("❌ You cannot override an existing bot command.")
            
        roles = []
        if action in ["add", "remove"]:
            if not ctx.message.role_mentions:
                return await ctx.send("❌ You must mention at least one role for `add` or `remove` action.")
            roles = [role.id for role in ctx.message.role_mentions]
            
        cursor = self.bot.db.cursor()
        role_str = ",".join(str(r) for r in roles)
        
        cursor.execute("""
            INSERT INTO custom_commands (server_id, command_name, action, role_ids, response_message) 
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(server_id, command_name) 
            DO UPDATE SET action=excluded.action, role_ids=excluded.role_ids, response_message=excluded.response_message
        """, (str(ctx.guild.id), command_name, action, role_str, message))
        
        self.bot.db.commit()
        cursor.close()
        
        s_id = ctx.guild.id
        if s_id not in self.custom_cmds_cache:
            self.custom_cmds_cache[s_id] = {}
            
        self.custom_cmds_cache[s_id][command_name] = {
            "action": action,
            "roles": roles,
            "response": message
        }
        
        await ctx.send(f"✅ Custom command `{command_name}` has been saved!\nType `{ctx.prefix}{command_name}` to use it.")

    @commands.hybrid_command(name="delcmd")
    @commands.has_permissions(manage_roles=True)
    async def delcmd(self, ctx, command_name: str):
        """Deletes a custom command."""
        command_name = command_name.lower()
        s_id = ctx.guild.id
        
        if s_id not in self.custom_cmds_cache or command_name not in self.custom_cmds_cache[s_id]:
            return await ctx.send("❌ Custom command not found.")
            
        cursor = self.bot.db.cursor()
        cursor.execute("DELETE FROM custom_commands WHERE server_id = ? AND command_name = ?", (str(s_id), command_name))
        self.bot.db.commit()
        cursor.close()
        
        del self.custom_cmds_cache[s_id][command_name]
        await ctx.send(f"✅ Custom command `{command_name}` has been deleted.")

    @commands.hybrid_command(name="listcmds", aliases=["cc", "custom", "commands"])
    @commands.has_permissions(manage_roles=True)
    async def listcmds(self, ctx):
        """Lists all custom commands in this server."""
        s_id = ctx.guild.id
        
        if s_id not in self.custom_cmds_cache or not self.custom_cmds_cache[s_id]:
            return await ctx.send("❌ No custom commands found in this server.")
            
        embed = discord.Embed(
            title="🛠️ Custom Commands",
            color=discord.Color.blue()
        )
        
        for name, data in self.custom_cmds_cache[s_id].items():
            action = data["action"]
            if action == "text":
                val = "Text Response Only"
            else:
                roles_str = " ".join([f"<@&{r}>" for r in data["roles"]])
                val = f"Action: {action.capitalize()}\nRoles: {roles_str}"
                
            embed.add_field(name=f"{ctx.prefix}{name}", value=val, inline=False)
            
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
            
        # Get context to let discord.py parse the prefix and command invocation
        ctx = await self.bot.get_context(message)
        
        # If it's a valid built-in command, let it run normally
        if ctx.valid:
            return
            
        # If there's no prefix invoked, ignore
        if not ctx.prefix:
            return
            
        command_name = ctx.invoked_with
        if not command_name:
            return
            
        command_name = command_name.lower()
        s_id = message.guild.id
        
        if s_id in self.custom_cmds_cache and command_name in self.custom_cmds_cache[s_id]:
            cmd_data = self.custom_cmds_cache[s_id][command_name]
            action = cmd_data["action"]
            
            # Roles required actions
            if action in ["add", "remove"]:
                if not message.author.guild_permissions.manage_roles:
                    return await message.channel.send("❌ You need `Manage Roles` permission to use this custom command.")
                    
                if not message.mentions:
                    return await message.channel.send("❌ You need to mention a user to use this command.")
                    
                target = message.mentions[0]
                roles_to_modify = [message.guild.get_role(r_id) for r_id in cmd_data["roles"] if message.guild.get_role(r_id)]
                roles_to_modify = [r for r in roles_to_modify if r is not None]
                
                if not roles_to_modify:
                    return await message.channel.send("❌ The roles for this command no longer exist.")
                    
                try:
                    if action == "add":
                        await target.add_roles(*roles_to_modify)
                    elif action == "remove":
                        await target.remove_roles(*roles_to_modify)
                except discord.Forbidden:
                    return await message.channel.send("❌ I don't have permission to modify roles for this user. Make sure my role is higher.")
                    
                response_text = cmd_data["response"].replace("{user}", target.mention)
                
                # Optionally strip out role pings from the message so the bot doesn't ping the role itself
                # if the manager included the role in the setup message.
                for role in roles_to_modify:
                    response_text = response_text.replace(role.mention, f"@{role.name}")
                    
                await message.channel.send(response_text)
                
            # Text only action
            elif action == "text":
                # For text commands, everyone might be able to use it, or we can restrict it.
                # Usually text commands are for everyone. Let's allow everyone to use it.
                response_text = cmd_data["response"]
                if "{user}" in response_text:
                    target = message.mentions[0] if message.mentions else message.author
                    response_text = response_text.replace("{user}", target.mention)
                await message.channel.send(response_text)

async def setup(bot):
    await bot.add_cog(ModCustomCommand(bot))
