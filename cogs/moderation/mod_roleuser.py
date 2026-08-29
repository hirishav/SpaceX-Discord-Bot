# cogs/mod_roleuser.py
import discord
from discord.ext import commands
import typing

class RoleSelect(discord.ui.Select):
    def __init__(self, roles, bot_instance, original_ctx):
        options = []
        for role in roles[:25]:
            options.append(discord.SelectOption(label=role.name[:100], value=str(role.id)))
        super().__init__(placeholder="Choose a role...", min_values=1, max_values=1, options=options)
        self.bot_instance = bot_instance
        self.original_ctx = original_ctx

    async def callback(self, interaction: discord.Interaction):
        role_id = int(self.values[0])
        role = interaction.guild.get_role(role_id)
        if not role:
            await interaction.response.send_message("❌ Role not found.", ephemeral=True)
            return
        
        try:
            await interaction.message.delete()
        except discord.HTTPException:
            pass
            
        await interaction.response.defer()
        await self.bot_instance.send_role_members(self.original_ctx, role, interaction)

class RoleSelectView(discord.ui.View):
    def __init__(self, roles, bot_instance, original_ctx):
        super().__init__(timeout=60)
        self.ctx = original_ctx
        self.message = None
        self.add_item(RoleSelect(roles, bot_instance, original_ctx))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ You cannot use this menu.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.delete()
            except discord.HTTPException:
                pass


class ModRoleUser(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_role_members(self, ctx, role: discord.Role, interaction: discord.Interaction = None):
        # Ensure guild members are fully cached
        if not ctx.guild.chunked:
            await ctx.guild.chunk()
            
        members = role.members
        if not members:
            embed = discord.Embed(
                title=f"👥 Members with {role.name}",
                description="❌ Is role me koi member nahi hai.",
                color=role.color if role.color.value != 0 else discord.Color.blue()
            )
            if interaction:
                await interaction.followup.send(embed=embed)
            else:
                await ctx.send(embed=embed)
                
            try:
                if ctx.message:
                    await ctx.message.delete()
            except Exception:
                pass
            return

        # Format member list: 1. Username (ID)
        lines = []
        for index, member in enumerate(members, start=1):
            lines.append(f"`{index}.` {member.mention} - `{member.name}`")

        # Join and split if it exceeds Discord's description limits (4096 chars)
        description = "\n".join(lines)
        
        if len(description) <= 4000:
            embed = discord.Embed(
                title=f"👥 Members with {role.name} ({len(members)})",
                description=description,
                color=role.color if role.color.value != 0 else discord.Color.blue()
            )
            if interaction:
                await interaction.followup.send(embed=embed)
            else:
                await ctx.send(embed=embed)
        else:
            # Chunking the list if it's too long
            chunks = []
            current_chunk = ""
            for line in lines:
                if len(current_chunk) + len(line) + 1 > 4000:
                    chunks.append(current_chunk)
                    current_chunk = line + "\n"
                else:
                    current_chunk += line + "\n"
            if current_chunk:
                chunks.append(current_chunk)

            for i, chunk in enumerate(chunks, start=1):
                embed = discord.Embed(
                    title=f"👥 Members with {role.name} ({len(members)}) - Part {i}/{len(chunks)}",
                    description=chunk,
                    color=role.color if role.color.value != 0 else discord.Color.blue()
                )
                if interaction:
                    await interaction.followup.send(embed=embed)
                else:
                    await ctx.send(embed=embed)

        try:
            if ctx.message:
                await ctx.message.delete()
        except Exception:
            pass


    @commands.hybrid_command(name="roleuser", aliases=["roleusers", "inrole"])
    @commands.has_guild_permissions(manage_roles=True)
    async def roleuser(self, ctx, *, role: typing.Union[discord.Role, str]):
        """Kisi specific role ke members ki list dekhne ke liye."""
        
        if isinstance(role, str):
            roles = [r for r in ctx.guild.roles if role.lower() in r.name.lower()]
            if len(roles) == 0:
                await ctx.send("❌ Role nahi mila! Kripya sahi role mention karein ya ID daalein.", ephemeral=True)
                return
            elif len(roles) == 1:
                target_role = roles[0]
            else:
                view = RoleSelectView(roles, self, ctx)
                view.message = await ctx.send("🔍 Multiple roles found. Please select one:", view=view, ephemeral=True)
                return
        else:
            target_role = role
            
        await self.send_role_members(ctx, target_role)

    @roleuser.error
    async def roleuser_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Aapke paas is command ko use karne ki permission nahi hai!")
        elif isinstance(error, commands.RoleNotFound):
            await ctx.send("❌ Role nahi mila! Kripya sahi role mention karein ya ID daalein.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}roleuser @role`")
        else:
            await ctx.send(f"❌ Kuch gadbad hui: {error}")

async def setup(bot):
    await bot.add_cog(ModRoleUser(bot))
