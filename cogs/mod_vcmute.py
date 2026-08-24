# cogs/mod_vcmute.py
import discord
from discord.ext import commands

class ModVcmute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="vcmute")
    @commands.has_guild_permissions(mute_members=True)
    async def vcmute(self, ctx, member: discord.Member, *, reason: str = "Koi reason nahi diya gaya"):
        """Kisi member ko voice channel me server mute karne ke liye."""
        if not member.voice or not member.voice.channel:
            return await ctx.send("❌ Ye member kisi voice channel me nahi hai!")
            
        if member.voice.mute:
            return await ctx.send(f"⚠️ {member.mention} pehle se hi voice channel me mute hai!")

        try:
            await member.edit(mute=True, reason=f"VCMute by {ctx.author}: {reason}")
            embed = discord.Embed(
                title="🎙️ Voice Muted",
                description=f"✅ {member.mention} ko voice channel me mute kar diya gaya hai.\n**Reason:** {reason}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            try:
                await ctx.message.delete()
            except Exception:
                pass
        except discord.Forbidden:
            await ctx.send("❌ Mere paas is member ko mute karne ki permission nahi hai! (Higher role chahiye)")
        except Exception as e:
            await ctx.send(f"❌ Kuch gadbad ho gayi: {e}")

    @vcmute.error
    async def vcmute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Aapke paas is command ko use karne ki permission nahi hai!")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ Member nahi mila! Sahi tag ya ID use karein.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}vcmute @user [reason]`")
        else:
            await ctx.send(f"❌ Kuch gadbad hui: {error}")

async def setup(bot):
    await bot.add_cog(ModVcmute(bot))
