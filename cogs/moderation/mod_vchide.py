import discord
from discord.ext import commands

class ModVCHide(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="vchide")
    @commands.has_permissions(manage_channels=True)
    async def vchide(self, ctx, channel: discord.VoiceChannel = None):
        """Voice channel ko instantly hide karne ke liye (list se gayab ho jayega)."""
        channel = channel or (ctx.author.voice.channel if ctx.author.voice else None)
        
        if not channel:
            return await ctx.send("❌ Bhai pehle kisi voice channel me join kar, ya fir command me channel mention/ID de (`!!vchide <channel_id>`)")

        overwrite = channel.overwrites_for(ctx.guild.default_role)
        
        if overwrite.view_channel is False:
            return await ctx.send(f"⚠️ `{channel.name}` pehle se hi hidden hai!")

        overwrite.view_channel = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"VC Hidden by {ctx.author}")
        
        await ctx.send(f"👻 **{channel.name}** successfully hide kar diya gaya hai! Ab ye kisi ko nahi dikhega.")

async def setup(bot):
    await bot.add_cog(ModVCHide(bot))
