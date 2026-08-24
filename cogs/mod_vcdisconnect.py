# cogs/mod_vcdisconnect.py
import discord
from discord.ext import commands

class ModVcdisconnect(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="vcdisconnect", aliases=["vckick"])
    @commands.has_guild_permissions(move_members=True)
    async def vcdisconnect(self, ctx, member: discord.Member, *, reason: str = "Koi reason nahi diya gaya"):
        """Kisi member ko voice channel se bahar nikalne (disconnect) ke liye."""
        if not member.voice or not member.voice.channel:
            return await ctx.send("❌ Ye member kisi voice channel me nahi hai!")

        try:
            await member.edit(voice_channel=None, reason=f"VCDisconnect by {ctx.author}: {reason}")
            embed = discord.Embed(
                title="🚪 Voice Disconnected",
                description=f"✅ {member.mention} ko voice channel se nikal diya gaya hai.\n**Reason:** {reason}",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            try:
                await ctx.message.delete()
            except Exception:
                pass
        except discord.Forbidden:
            await ctx.send("❌ Mere paas is member ko disconnect karne ki permission nahi hai! (Higher role chahiye)")
        except Exception as e:
            await ctx.send(f"❌ Kuch gadbad ho gayi: {e}")

    @vcdisconnect.error
    async def vcdisconnect_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Aapke paas is command ko use karne ki permission nahi hai!")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ Member nahi mila! Sahi tag ya ID use karein.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}vcdisconnect @user [reason]`")
        else:
            await ctx.send(f"❌ Kuch gadbad hui: {error}")

async def setup(bot):
    await bot.add_cog(ModVcdisconnect(bot))
