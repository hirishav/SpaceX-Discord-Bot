import discord
from discord.ext import commands
import asyncio
import time
import typing

class FakeConfirmDeleteView(discord.ui.View):
    def __init__(self, ctx, channel, timeout=60):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.channel = channel
        self.value = None

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.danger, custom_id="fake_confirm_delete_yes")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("❌ You cannot use this button.", ephemeral=True)

        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            content=f"⚠️ **CONFIRMED:** {self.channel.mention} is scheduled for permanent deletion in **10 seconds**!",
            embed=None,
            view=None
        )
        self.value = True
        self.stop()

        # 10 seconds dramatic back-counting
        for i in range(10, 0, -1):
            await asyncio.sleep(1)
            try:
                await self.channel.send(f"⚠️ **{i}...**")
            except Exception:
                pass

        await asyncio.sleep(1)
        try:
            await self.channel.send("💥 **0...**")
            await asyncio.sleep(0.5)
            await self.channel.send(f"✅ {self.channel.mention} has been **deleted**.")
            await asyncio.sleep(1.5)
            embed_prank = discord.Embed(
                title="🤡 PRANKED!",
                description=f"Chill karo sab log! {self.channel.mention} safe hai, koi channel delete nahi hua! 😂",
                color=discord.Color.green()
            )
            await self.channel.send(embed=embed_prank)
        except Exception:
            pass

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="fake_confirm_delete_cancel")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("❌ You cannot use this button.", ephemeral=True)

        await interaction.response.edit_message(content="❌ Channel deletion cancelled.", embed=None, view=None)
        self.value = False
        self.stop()

class FunFake(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_staff_or_allowed(self, ctx):
        if not ctx.guild:
            return False
        if ctx.author.id == ctx.guild.owner_id or ctx.author.id in self.bot.owner_ids:
            return True
        perms = getattr(ctx.author, 'guild_permissions', None)
        if perms and (perms.administrator or perms.manage_guild or perms.manage_messages or perms.manage_roles):
            return True
        if hasattr(self.bot, 'allowed_commands_cache') and ctx.guild.id in self.bot.allowed_commands_cache:
            targets = [ctx.author.id] + [r.id for r in getattr(ctx.author, 'roles', [])] + [ctx.guild.id]
            current_time = int(time.time())
            for t_id in targets:
                allowed_items = self.bot.allowed_commands_cache[ctx.guild.id].get(t_id, {})
                for check_name in ('fake', 'FunFake', 'fun'):
                    if check_name in allowed_items:
                        exp = allowed_items[check_name]
                        if exp == -1 or current_time < exp:
                            return True
        return False

    async def cog_check(self, ctx):
        if not ctx.guild:
            return False
        if not self.is_staff_or_allowed(ctx):
            raise commands.CheckFailure("Yeh command sirf Server Managers aur Admins ke liye hai!")
        return True

    def check_hierarchy(self, ctx, user):
        if user.id == ctx.guild.owner_id:
            return "❌ You cannot perform this action on the server owner."
        if self.bot.user and user.id == self.bot.user.id:
            return "❌ I cannot perform this action on myself."
        return None

    @commands.group(name="fake", aliases=["f"], invoke_without_command=True)
    async def fake(self, ctx):
        """Fake moderation/utility commands group for fun."""
        embed = discord.Embed(
            title="🤡 Fake Moderation & Prank Commands",
            description=(
                "🛡️ **Server Managers & Admins ke prank moderation commands:**\n\n"
                f"• `{ctx.prefix}fake ban @user [reason]`\n"
                f"• `{ctx.prefix}fake mute @user [reason]`\n"
                f"• `{ctx.prefix}fake kick @user [reason]`\n"
                f"• `{ctx.prefix}fake warn @user [reason]`\n"
                f"• `{ctx.prefix}fake delchannel [#channel]`\n"
                f"• `{ctx.prefix}fake tic create`\n"
                f"• `{ctx.prefix}fake afk [reason]`\n"
                f"• `{ctx.prefix}fake role add @user [role]`\n"
                f"• `{ctx.prefix}fake temprole @user [duration] [role]`\n"
                f"• `{ctx.prefix}fake hide all`\n"
                f"• `{ctx.prefix}fake unhide all`\n"
                f"• `{ctx.prefix}fake slowmode [duration]`"
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Requested by {ctx.author.name} | Staff Only")
        await ctx.send(embed=embed, delete_after=25)
        try: await ctx.message.delete()
        except: pass

    @fake.command(name="ban")
    async def fake_ban(self, ctx, user: typing.Union[discord.Member, discord.User], *, reason: str = "No reason provided"):
        error = self.check_hierarchy(ctx, user)
        if error:
            return await ctx.send(error)
        embed = discord.Embed(
            title="🔨 Member Banned",
            description=f"**{user.name}** ko hamesha ke liye ban kar diya gaya hai.",
            color=discord.Color.red()
        )
        embed.add_field(name="👤 Target", value=f"{user.mention} (`{user.id}`)", inline=True)
        embed.add_field(name="🛡️ Staff", value=ctx.author.mention, inline=True)
        embed.add_field(name="📝 Reason", value=reason, inline=False)
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    @fake.command(name="mute")
    async def fake_mute(self, ctx, user: typing.Union[discord.Member, discord.User], *, reason: str = "No reason provided"):
        error = self.check_hierarchy(ctx, user)
        if error:
            return await ctx.send(error)
        embed = discord.Embed(
            title="🔇 Member Muted",
            description=f"**{user.name}** ko server me mute kar diya gaya hai.",
            color=discord.Color.red()
        )
        embed.add_field(name="👤 Target", value=f"{user.mention} (`{user.id}`)", inline=True)
        embed.add_field(name="🛡️ Staff", value=ctx.author.mention, inline=True)
        embed.add_field(name="📝 Reason", value=reason, inline=False)
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    @fake.command(name="kick")
    async def fake_kick(self, ctx, user: typing.Union[discord.Member, discord.User], *, reason: str = "No reason provided"):
        error = self.check_hierarchy(ctx, user)
        if error:
            return await ctx.send(error)
        embed = discord.Embed(
            title="👢 Member Kicked",
            description=f"**{user.name}** ko server se kick kar diya gaya hai.",
            color=discord.Color.orange()
        )
        embed.add_field(name="👤 Target", value=f"{user.mention} (`{user.id}`)", inline=True)
        embed.add_field(name="🛡️ Staff", value=ctx.author.mention, inline=True)
        embed.add_field(name="📝 Reason", value=reason, inline=False)
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    @fake.command(name="warn")
    async def fake_warn(self, ctx, user: typing.Union[discord.Member, discord.User], *, reason: str = "No reason provided"):
        error = self.check_hierarchy(ctx, user)
        if error:
            return await ctx.send(error)
        embed = discord.Embed(
            title="⚠️ Member Warned",
            description=f"**{user.name}** ko ek warning di gayi hai.",
            color=discord.Color.orange()
        )
        embed.add_field(name="👤 Target", value=f"{user.mention} (`{user.id}`)", inline=True)
        embed.add_field(name="🛡️ Staff", value=ctx.author.mention, inline=True)
        embed.add_field(name="📝 Reason", value=reason, inline=False)
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    @fake.command(name="delchannel")
    async def fake_delchannel(self, ctx, channel: discord.abc.GuildChannel = None):
        """Delete channel prank with realistic confirmation and dramatic 10s countdown."""
        channel = channel or ctx.channel

        try:
            await ctx.message.delete()
        except Exception:
            pass

        embed = discord.Embed(
            title="⚠️ Delete Channel Confirmation",
            description=f"Are you sure you want to delete {channel.mention}?",
            color=discord.Color.red()
        )
        embed.set_footer(text="This action cannot be undone.")

        view = FakeConfirmDeleteView(ctx, channel)
        msg = await ctx.send(embed=embed, view=view)

        await view.wait()
        if view.value is None:
            try:
                await msg.edit(content="⏳ Command timed out.", embed=None, view=None)
            except discord.NotFound:
                pass

    # 'fake tic' and 'fake tic create'
    @fake.group(name="tic", invoke_without_command=True)  # type: ignore
    async def fake_tic(self, ctx):
        await ctx.send(f"Usage: `{ctx.prefix}fake tic create`", delete_after=10)
        try: await ctx.message.delete()
        except: pass

    @fake_tic.command(name="create")
    async def fake_tic_create(self, ctx):
        embed = discord.Embed(
            description=f"✅ Ticket created successfully in <#{ctx.channel.id}>",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    @fake.command(name="afk")
    async def fake_afk(self, ctx, *, reason: str = "I'm AFK"):
        embed = discord.Embed(
            description=f"✅ {ctx.author.mention} your AFK is now set to: **{reason}**",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    # 'fake role' and 'fake role add'
    @fake.group(name="role", invoke_without_command=True)  # type: ignore
    async def fake_role(self, ctx):
        await ctx.send(f"Usage: `{ctx.prefix}fake role add @user [Role]`", delete_after=10)
        try: await ctx.message.delete()
        except: pass

    @fake_role.command(name="add")
    async def fake_role_add(self, ctx, user: typing.Union[discord.Member, discord.User], role_name: str = "Admin", *, reason: str = "No reason provided"):
        error = self.check_hierarchy(ctx, user)
        if error:
            return await ctx.send(error)
        embed = discord.Embed(
            description=f"✅ Added role **{role_name}** to {user.mention} | {reason}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    @fake.command(name="temprole")
    async def fake_temprole(self, ctx, user: typing.Union[discord.Member, discord.User], duration: str = "1h", role_name: str = "VIP"):
        error = self.check_hierarchy(ctx, user)
        if error:
            return await ctx.send(error)
        embed = discord.Embed(
            description=f"✅ Added temp role **{role_name}** to {user.mention} for **{duration}**.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    # 'fake hide' and 'fake hide all'
    @fake.group(name="hide", invoke_without_command=True)  # type: ignore
    async def fake_hide(self, ctx):
        await ctx.send(f"Usage: `{ctx.prefix}fake hide all`", delete_after=10)
        try: await ctx.message.delete()
        except: pass

    @fake_hide.command(name="all")
    async def fake_hide_all(self, ctx):
        embed = discord.Embed(
            description="✅ All channels have been **hidden** from everyone.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    # 'fake unhide' and 'fake unhide all'
    @fake.group(name="unhide", invoke_without_command=True)  # type: ignore
    async def fake_unhide(self, ctx):
        await ctx.send(f"Usage: `{ctx.prefix}fake unhide all`", delete_after=10)
        try: await ctx.message.delete()
        except: pass

    @fake_unhide.command(name="all")
    async def fake_unhide_all(self, ctx):
        embed = discord.Embed(
            description="✅ All channels have been **unhidden** for everyone.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    @fake.command(name="slowmode")
    async def fake_slowmode(self, ctx, duration: str = "1h"):
        embed = discord.Embed(
            description=f"⏱️ Is channel me **{duration}** ka Slowmode laga diya gaya hai.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

async def setup(bot):
    await bot.add_cog(FunFake(bot))
