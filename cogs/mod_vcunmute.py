# cogs/mod_vcunmute.py
import discord
from discord.ext import commands

class ModVcunmute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="vcunmute")
    @commands.has_guild_permissions(mute_members=True)
    async def vcunmute(self, ctx, member: discord.Member, *, reason: str = "Koi reason nahi diya gaya"):
        """Kisi member ka voice channel mute hatane ke liye."""
        if not member.voice or not member.voice.channel:
            return await ctx.send("❌ Ye member kisi voice channel me nahi hai!")
            
        if not member.voice.mute:
            return await ctx.send(f"⚠️ {member.mention} pehle se hi voice channel me unmute hai!")

        try:
            await member.edit(mute=False, reason=f"VCUnmute by {ctx.author}: {reason}")
            embed = discord.Embed(
                title="🎙️ Voice Unmuted",
                description=f"✅ {member.mention} ko voice channel me unmute kar diya gaya hai.\n**Reason:** {reason}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ Mere paas is member ko unmute karne ki permission nahi hai! (Higher role chahiye)")
        except Exception as e:
            await ctx.send(f"❌ Kuch gadbad ho gayi: {e}")

    @vcunmute.error
    async def vcunmute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Aapke paas is command ko use karne ki permission nahi hai!")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ Member nahi mila! Sahi tag ya ID use karein.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}vcunmute @user [reason]`")
        else:
            await ctx.send(f"❌ Kuch gadbad hui: {error}")

async def setup(bot):
    await bot.add_cog(ModVcunmute(bot))
