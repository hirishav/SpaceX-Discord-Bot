import discord
from discord.ext import commands
import typing

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

class ResetAllConfirmationView(discord.ui.View):
    def __init__(self, ctx, allow_count: int, disallow_count: int):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.allow_count = allow_count
        self.disallow_count = disallow_count
        self.message = None

    @discord.ui.button(label="Confirm Reset", style=discord.ButtonStyle.danger, emoji="♻️")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("❌ Ye action sirf command chalane wale ke liye hai.", ephemeral=True)

        guild_id_int = self.ctx.guild.id
        cursor = self.ctx.bot.db.cursor()

        # Delete all allows and disallows for this server
        cursor.execute("DELETE FROM command_allows WHERE guild_id = ?", (str(guild_id_int),))
        cursor.execute("DELETE FROM command_disallows WHERE guild_id = ?", (str(guild_id_int),))
        self.ctx.bot.db.commit()

        # Clear active memory caches
        if guild_id_int in self.ctx.bot.allowed_commands_cache:
            self.ctx.bot.allowed_commands_cache[guild_id_int].clear()
        if hasattr(self.ctx.bot, 'disallowed_commands_cache') and guild_id_int in self.ctx.bot.disallowed_commands_cache:
            self.ctx.bot.disallowed_commands_cache[guild_id_int].clear()

        for child in self.children:
            child.disabled = True

        embed = discord.Embed(
            title="♻️ All Command Permissions Reset",
            description=(
                f"Is server (**{self.ctx.guild.name}**) ke sabhi command permissions successfully reset kar diye gaye hain!\n\n"
                f"✅ **Cleared Allows:** `{self.allow_count}` overrides\n"
                f"✅ **Cleared Disallows:** `{self.disallow_count}` restrictions\n\n"
                "Ab na koi command allow hai aur na hi disallow — sabhi default server permissions restore ho gayi hain."
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Reset by {self.ctx.author.name}")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="✖️")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("❌ Ye action sirf command chalane wale ke liye hai.", ephemeral=True)

        for child in self.children:
            child.disabled = True

        embed = discord.Embed(
            title="❌ Reset Cancelled",
            description="Command permissions reset cancel kar diya gaya hai. Koi changes nahi kiye gaye.",
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Cancelled by {self.ctx.author.name}")
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

class ModResetAllow(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="resetallow", aliases=["resetallows", "resetperm", "resetperms"])
    @is_manager_or_admin_check()
    async def resetallow_command(self, ctx, target: typing.Optional[typing.Union[discord.Member, discord.Role, str]] = None, command_or_module: typing.Optional[str] = None):
        """Server ya kisi specific target ke allows aur disallows reset karne ke liye (Managers & Admins)."""
        guild_id_int = ctx.guild.id
        cursor = self.bot.db.cursor()

        # Case 1: Server-wide reset (No target provided, or target is "all" / "server" / "everything")
        is_server_wide = False
        if target is None:
            is_server_wide = True
        elif isinstance(target, str) and target.lower() in ["all", "server", "everything", "guild"]:
            is_server_wide = True

        if is_server_wide:
            cursor.execute("SELECT COUNT(*) FROM command_allows WHERE guild_id = ?", (str(guild_id_int),))
            allow_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM command_disallows WHERE guild_id = ?", (str(guild_id_int),))
            disallow_count = cursor.fetchone()[0]

            total_count = allow_count + disallow_count
            if total_count == 0:
                embed = discord.Embed(
                    title="ℹ️ No Active Overrides",
                    description=f"**{ctx.guild.name}** me koi bhi active allow ya disallow override set nahi hai. Sabhi permissions pehle se hi default hain.",
                    color=discord.Color.blue()
                )
                embed.set_footer(text=f"Requested by {ctx.author.name}")
                return await ctx.send(embed=embed)

            view = ResetAllConfirmationView(ctx, allow_count, disallow_count)
            embed = discord.Embed(
                title="⚠️ Reset All Command Permissions?",
                description=(
                    f"Kya aap sach me is server (**{ctx.guild.name}**) ke **sabhi command permissions** reset karna chahte hain?\n\n"
                    f"📊 **Current Active Overrides:**\n"
                    f"• **Allowed Overrides:** `{allow_count}`\n"
                    f"• **Disallowed Restrictions:** `{disallow_count}`\n"
                    f"• **Total Overrides:** `{total_count}`\n\n"
                    "⚠️ *Is action se sabhi users, roles aur `@everyone` ke custom allows aur disallows permanently remove ho jayenge aur default permissions restore ho jayengi.*"
                ),
                color=discord.Color.gold()
            )
            embed.set_footer(text=f"Confirmation expires in 60s • Action by {ctx.author.name}")
            msg = await ctx.send(embed=embed, view=view)
            view.message = msg
            return

        # Case 2: Target-specific reset
        if isinstance(target, str):
            if target.lower() in ["everyone", "@everyone"]:
                target_id = ctx.guild.id
                target_mention = "@everyone"
            else:
                return await ctx.send("❌ Invalid target. Please mention a user, a role, type `everyone`, or leave blank to reset all.")
        else:
            target_id = target.id
            target_mention = getattr(target, 'mention', str(target))

        # Sub-case 2A: Specific command or module for this target
        if command_or_module:
            cmd = self.bot.get_command(command_or_module)
            if cmd:
                cmd_name = cmd.qualified_name.split()[0].lower()
            else:
                cmd_name = command_or_module.lower()

            cursor.execute("DELETE FROM command_allows WHERE guild_id = ? AND target_id = ? AND command_or_module = ?",
                           (str(guild_id_int), str(target_id), cmd_name))
            deleted_allows = cursor.rowcount

            cursor.execute("DELETE FROM command_disallows WHERE guild_id = ? AND target_id = ? AND command_or_module = ?",
                           (str(guild_id_int), str(target_id), cmd_name))
            deleted_disallows = cursor.rowcount

            if deleted_allows > 0 or deleted_disallows > 0:
                self.bot.db.commit()

                # Update caches
                if guild_id_int in self.bot.allowed_commands_cache and target_id in self.bot.allowed_commands_cache[guild_id_int]:
                    self.bot.allowed_commands_cache[guild_id_int][target_id].pop(cmd_name, None)
                    if not self.bot.allowed_commands_cache[guild_id_int][target_id]:
                        del self.bot.allowed_commands_cache[guild_id_int][target_id]

                if hasattr(self.bot, 'disallowed_commands_cache') and guild_id_int in self.bot.disallowed_commands_cache and target_id in self.bot.disallowed_commands_cache[guild_id_int]:
                    self.bot.disallowed_commands_cache[guild_id_int][target_id].pop(cmd_name, None)
                    if not self.bot.disallowed_commands_cache[guild_id_int][target_id]:
                        del self.bot.disallowed_commands_cache[guild_id_int][target_id]

                embed = discord.Embed(
                    title="♻️ Command Permission Reset",
                    description=(
                        f"Target: {target_mention}\n"
                        f"Command/Module: `{cmd_name}`\n\n"
                        f"✅ Reset done! Is target ke liye `{cmd_name}` ke sabhi allows aur disallows remove kar diye gaye hain."
                    ),
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"Reset by {ctx.author.name}")
                return await ctx.send(embed=embed)
            else:
                return await ctx.send(f"❌ {target_mention} ke liye `{cmd_name}` ka koi active allow ya disallow override nahi mila.")

        # Sub-case 2B: All commands/modules for this target
        cursor.execute("SELECT COUNT(*) FROM command_allows WHERE guild_id = ? AND target_id = ?", 
                       (str(guild_id_int), str(target_id)))
        allow_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM command_disallows WHERE guild_id = ? AND target_id = ?", 
                       (str(guild_id_int), str(target_id)))
        disallow_count = cursor.fetchone()[0]

        total_target_overrides = allow_count + disallow_count
        if total_target_overrides == 0:
            embed = discord.Embed(
                title="ℹ️ No Active Overrides",
                description=f"{target_mention} ke liye koi active allow ya disallow override set nahi hai.",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Requested by {ctx.author.name}")
            return await ctx.send(embed=embed)

        cursor.execute("DELETE FROM command_allows WHERE guild_id = ? AND target_id = ?", (str(guild_id_int), str(target_id)))
        cursor.execute("DELETE FROM command_disallows WHERE guild_id = ? AND target_id = ?", (str(guild_id_int), str(target_id)))
        self.bot.db.commit()

        # Update cache for this target
        if guild_id_int in self.bot.allowed_commands_cache and target_id in self.bot.allowed_commands_cache[guild_id_int]:
            del self.bot.allowed_commands_cache[guild_id_int][target_id]

        if hasattr(self.bot, 'disallowed_commands_cache') and guild_id_int in self.bot.disallowed_commands_cache and target_id in self.bot.disallowed_commands_cache[guild_id_int]:
            del self.bot.disallowed_commands_cache[guild_id_int][target_id]

        embed = discord.Embed(
            title="♻️ Target Permissions Reset",
            description=(
                f"{target_mention} ke sabhi command permissions successfully reset kar diye gaye hain!\n\n"
                f"✅ **Cleared Allows:** `{allow_count}` overrides\n"
                f"✅ **Cleared Disallows:** `{disallow_count}` restrictions\n\n"
                f"Ab {target_mention} ke paas na koi extra allow hai aur na hi disallow restriction."
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Reset by {ctx.author.name}")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ModResetAllow(bot))
