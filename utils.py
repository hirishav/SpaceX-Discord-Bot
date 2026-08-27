import re
import discord
from discord.ext import commands

class SmartRoleConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> discord.Role:
        """
        Custom Role Converter that:
        1. Tries to find an exact match by ID or mention.
        2. Performs a partial/fuzzy match on role names.
        3. If multiple roles match, prompts the user via a UI View to select the intended one.
        """
        # 1. Try exact match for ID or Mention
        is_id_or_mention = re.match(r'^<@&?\d+>$|^\d+$', argument.strip())
        if is_id_or_mention:
            try:
                role = await commands.RoleConverter().convert(ctx, argument)
                return role
            except commands.RoleNotFound:
                pass

        # 2. Try partial/fuzzy match for names
        argument_lower = argument.lower()
        matched_roles = [r for r in ctx.guild.roles if argument_lower in r.name.lower()]

        if len(matched_roles) == 0:
            raise commands.BadArgument(f"❌ Role `{argument}` server me nahi mila.")
        
        elif len(matched_roles) == 1:
            return matched_roles[0]
            
        else:
            # 3. Multiple matches, prompt user with Select Menu
            options = []
            for r in matched_roles[:25]: # Max 25 limit for SelectMenu
                options.append(discord.SelectOption(label=r.name[:100], value=str(r.id), description=f"ID: {r.id}"))
                
            class RoleSelect(discord.ui.Select):
                def __init__(self):
                    super().__init__(placeholder="Kripya ek role select karein...", min_values=1, max_values=1, options=options)
                    
                async def callback(self, interaction: discord.Interaction):
                    if interaction.user.id != ctx.author.id:
                        return await interaction.response.send_message("❌ Ye aapke liye nahi hai!", ephemeral=True)
                        
                    self.view.selected_role = ctx.guild.get_role(int(self.values[0]))
                    self.view.stop()
                    try:
                        await interaction.message.delete()
                    except:
                        pass
                        
            class RoleSelectView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=60)
                    self.selected_role = None
                    self.add_item(RoleSelect())
                    
                async def on_timeout(self):
                    try:
                        await self.message.delete()
                    except:
                        pass
                        
            view = RoleSelectView()
            msg = await ctx.send(
                f"⚠️ **{len(matched_roles)}** roles mile `{argument}` ke naam se. Kripya niche se ek chunein (ya message ignore karein cancel karne ke liye):", 
                view=view
            )
            view.message = msg
            
            # Wait for user interaction
            await view.wait()
            
            if view.selected_role:
                return view.selected_role
            else:
                raise commands.BadArgument("Role selection cancel ho gaya ya time out ho gaya.")
