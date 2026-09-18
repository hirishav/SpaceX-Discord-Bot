import discord
from discord.ext import commands

class ConfirmDeleteView(discord.ui.View):
    def __init__(self, ctx, channel, timeout=60):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.channel = channel
        self.value = None

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.danger, custom_id="confirm_delete_yes")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("❌ You cannot use this button.", ephemeral=True)
        
        await interaction.response.edit_message(content=f"✅ {self.channel.name} is being deleted...", embed=None, view=None)
        try:
            await self.channel.delete(reason=f"Deleted by {self.ctx.author}")
        except discord.Forbidden:
            if self.ctx.channel.id != self.channel.id:
                await self.ctx.send(f"❌ I don't have permission to delete {self.channel.mention}.")
        except Exception as e:
            if self.ctx.channel.id != self.channel.id:
                await self.ctx.send(f"❌ An error occurred: {e}")
        self.value = True
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="confirm_delete_cancel")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("❌ You cannot use this button.", ephemeral=True)
        
        await interaction.response.edit_message(content="❌ Channel deletion cancelled.", embed=None, view=None)
        self.value = False
        self.stop()


class ModDelChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="delchannel", aliases=["deletechannel", "dc"])
    @commands.has_guild_permissions(manage_channels=True)
    async def delchannel(self, ctx, channel: discord.abc.GuildChannel = None):
        """Delete the current or specified channel (voice or text)."""
        if channel is None:
            channel = ctx.channel

        embed = discord.Embed(
            title="⚠️ Delete Channel Confirmation",
            description=f"Are you sure you want to delete {channel.mention}?",
            color=discord.Color.red()
        )
        embed.set_footer(text="This action cannot be undone.")

        view = ConfirmDeleteView(ctx, channel)
        msg = await ctx.send(embed=embed, view=view)

        await view.wait()
        if view.value is None:
            try:
                await msg.edit(content="⏳ Command timed out.", embed=None, view=None)
            except discord.NotFound:
                pass

    @delchannel.error
    async def delchannel_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Aapke paas is command ko use karne ki permission nahi hai!")
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send("❌ Channel nahi mila! Sahi channel ID use karein.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(str(error))
        else:
            await ctx.send(f"❌ Kuch gadbad hui: {error}")


async def setup(bot):
    await bot.add_cog(ModDelChannel(bot))
