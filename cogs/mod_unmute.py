# cogs/mod_unmute.py
import discord
from discord.ext import commands

class ModUnmute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="unmute", aliases=["untimeout"])
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kisi member ka timeout (mute) pehle hatane ke liye."""
        
        # Check karna ki banda timeout par hai bhi ya nahi
        if not member.timed_out_until:
            return await ctx.send(f"❌ {member.mention} pehle se hi unmuted hai!")

        try:
            # Timeout hatane ke liye None pass kiya jata hai
            await member.timeout(None, reason=f"Unmuted by {ctx.author.name} | Reason: {reason}")
            
            # Success Embed
            embed = discord.Embed(
                title="🔊 Member Unmuted",
                description=f"{member.mention} ka timeout hata diya gaya hai.",
                color=discord.Color.green()
            )
            embed.add_field(name="👤 Target", value=f"{member.name}", inline=True)
            embed.add_field(name="🛡️ Staff", value=ctx.author.mention, inline=True)
            embed.add_field(name="📝 Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)

            try:
                await ctx.message.delete()
            except Exception:
                pass

        except discord.Forbidden:
            await ctx.send("❌ Main is member ka timeout nahi hata sakta! Mera role is member se upar hona chahiye.")

    @unmute.error
    async def unmute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Aapke paas `Moderate Members` permission nahi hai!")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}unmute @user <reason>`")

async def setup(bot):
    await bot.add_cog(ModUnmute(bot))