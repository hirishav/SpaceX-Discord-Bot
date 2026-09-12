import discord
from discord.ext import commands

class ModVCUnhide(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="vcunhide")
    @commands.has_permissions(manage_channels=True)
    async def vcunhide(self, ctx, channel: discord.VoiceChannel = None):
        """Voice channel ko instantly unhide karne ke liye (wapas sabko dikhne lagega)."""
        channel = channel or (ctx.author.voice.channel if ctx.author.voice else None)
        
        if not channel:
            return await ctx.send("❌ Bhai pehle kisi voice channel me join kar, ya fir command me channel mention/ID de (`!!vcunhide <channel_id>`)")

        overwrite = channel.overwrites_for(ctx.guild.default_role)
        
        if overwrite.view_channel is True or overwrite.view_channel is None:
            return await ctx.send(f"⚠️ `{channel.name}` pehle se hi sabko dikh raha hai!")

        overwrite.view_channel = None
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"VC Unhidden by {ctx.author}")
        
        await ctx.send(f"👁️ **{channel.name}** successfully unhide kar diya gaya hai! Ab ye wapas sabko dikhega.")

async def setup(bot):
    await bot.add_cog(ModVCUnhide(bot))
