# cogs/mod_vcundeafen.py
import discord
from discord.ext import commands

class ModVcundeafen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="vcundeafen")
    @commands.has_permissions(deafen_members=True)
    async def vcundeafen(self, ctx, member: discord.Member, *, reason: str = "Koi reason nahi diya gaya"):
        """Kisi member ka voice channel deafen hatane ke liye."""
        if not member.voice or not member.voice.channel:
            return await ctx.send("❌ Ye member kisi voice channel me nahi hai!")
            
        if not member.voice.deaf:
            return await ctx.send(f"⚠️ {member.mention} pehle se hi voice channel me undeafen hai!")

        try:
            await member.edit(deafen=False, reason=f"VCUndeafen by {ctx.author}: {reason}")
            embed = discord.Embed(
                title="🎧 Voice Undeafened",
                description=f"✅ {member.mention} ko voice channel me undeafen kar diya gaya hai.\n**Reason:** {reason}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ Mere paas is member ko undeafen karne ki permission nahi hai! (Higher role chahiye)")
        except Exception as e:
            await ctx.send(f"❌ Kuch gadbad ho gayi: {e}")

async def setup(bot):
    await bot.add_cog(ModVcundeafen(bot))
