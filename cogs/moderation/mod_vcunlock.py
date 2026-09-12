import discord
from discord.ext import commands

class ModVCUnlock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="vcunlock")
    @commands.has_permissions(manage_channels=True)
    async def vcunlock(self, ctx, channel: discord.VoiceChannel = None):
        """Voice channel ko instantly unlock karne ke liye (koi bhi wapas join kar payega)."""
        channel = channel or (ctx.author.voice.channel if ctx.author.voice else None)
        
        if not channel:
            return await ctx.send("❌ Bhai pehle kisi voice channel me join kar, ya fir command me channel mention/ID de (`!!vcunlock <channel_id>`)")

        overwrite = channel.overwrites_for(ctx.guild.default_role)
        
        if overwrite.connect is True or overwrite.connect is None:
            return await ctx.send(f"⚠️ `{channel.name}` pehle se hi unlocked hai!")

        overwrite.connect = None
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"VC Unlocked by {ctx.author}")
        
        await ctx.send(f"🔓 **{channel.name}** successfully unlock kar diya gaya hai! Ab sab join kar sakte hain.")

async def setup(bot):
    await bot.add_cog(ModVCUnlock(bot))
