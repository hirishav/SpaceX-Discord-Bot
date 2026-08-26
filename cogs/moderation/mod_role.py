# cogs/mod_role.py
import discord
from discord.ext import commands

class ModRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="role")
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx, member: discord.Member, *, role_query: str):
        """Kisi user ko role assign ya remove karne ke liye."""
        
        async def process_role(role: discord.Role):
            # Checking hierarchy
            if ctx.author.id != ctx.guild.owner_id and role >= ctx.author.top_role:
                return await ctx.send("❌ Aap apne se unche ya barabar ke role ko kisi ko nahi de sakte!")
                
            if role >= ctx.guild.me.top_role:
                return await ctx.send("❌ Mera role is role se niche hai, main isko kisi ko assign ya remove nahi kar sakta!")

            try:
                if role in member.roles:
                    await member.remove_roles(role, reason=f"Role removed by {ctx.author.name}")
                    embed = discord.Embed(
                        title="➖ Role Removed",
                        description=f"**{member.display_name}** se {role.mention} role hata diya gaya hai.",
                        color=discord.Color.orange()
                    )
                else:
                    await member.add_roles(role, reason=f"Role assigned by {ctx.author.name}")
                    embed = discord.Embed(
                        title="➕ Role Added",
                        description=f"**{member.display_name}** ko {role.mention} role assign kar diya gaya hai.",
                        color=discord.Color.green()
                    )
                    
                await ctx.send(embed=embed)
            except discord.Forbidden:
                await ctx.send("❌ Permission denied! Check karein ki mera role is role se upar hai ya nahi.")

        # Pehle try exact match / ID / Mention with RoleConverter
        try:
            role = await commands.RoleConverter().convert(ctx, role_query)
            return await process_role(role)
        except commands.RoleNotFound:
            pass

        # Partial matching
        matched_roles = [r for r in ctx.guild.roles if role_query.lower() in r.name.lower()]

        if len(matched_roles) == 0:
            return await ctx.send("❌ Ye role server me nahi mila.")
        
        elif len(matched_roles) == 1:
            await process_role(matched_roles[0])
            
        else:
            # Multiple matches, create a select menu
            options = []
            for r in matched_roles[:25]: # Max 25 limits for discord.ui.Select
                options.append(discord.SelectOption(label=r.name[:100], value=str(r.id), description=f"ID: {r.id}"))
                
            class RoleSelect(discord.ui.Select):
                def __init__(self):
                    super().__init__(placeholder="Kripya ek role select karein...", min_values=1, max_values=1, options=options)
                    
                async def callback(self, interaction: discord.Interaction):
                    if interaction.user.id != ctx.author.id:
                        return await interaction.response.send_message("❌ Ye aapke liye nahi hai!", ephemeral=True)
                        
                    selected_role = ctx.guild.get_role(int(self.values[0]))
                    if selected_role:
                        try:
                            await interaction.response.defer()
                        except:
                            pass
                        await interaction.message.delete()
                        await process_role(selected_role)
                    else:
                        await interaction.response.send_message("❌ Role nahi mila.", ephemeral=True)
                        
            class RoleSelectView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=60)
                    self.add_item(RoleSelect())
                    
                async def on_timeout(self):
                    try:
                        await self.message.delete()
                    except:
                        pass
                        
            view = RoleSelectView()
            msg = await ctx.send(f"⚠️ **{len(matched_roles)}** roles mile `{role_query}` ke naam se. Kripya niche se ek chunein:", view=view)
            view.message = msg
            
    @role.error
    async def role_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            pass
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}role @user <role name/id/@role>`")
            
async def setup(bot):
    await bot.add_cog(ModRole(bot))
