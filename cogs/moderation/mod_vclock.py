import discord
from discord.ext import commands

class ModVCLock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="vclock")
    @commands.has_permissions(manage_channels=True)
    async def vclock(self, ctx, channel: discord.VoiceChannel = None):
        """Voice channel ko instantly lock karne ke liye (koi aur join nahi kar payega)."""
        channel = channel or (ctx.author.voice.channel if ctx.author.voice else None)
        
        if not channel:
            return await ctx.send("❌ Bhai pehle kisi voice channel me join kar, ya fir command me channel mention/ID de (`!!vclock <channel_id>`)")

        overwrite = channel.overwrites_for(ctx.guild.default_role)
        
        if overwrite.connect is False:
            return await ctx.send(f"⚠️ `{channel.name}` pehle se hi locked hai!")

        overwrite.connect = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"VC Locked by {ctx.author}")
        
        await ctx.send(f"🔒 **{channel.name}** successfully lock kar diya gaya hai! Ab yahan aur koi join nahi kar payega.")

async def setup(bot):
    await bot.add_cog(ModVCLock(bot))
