# cogs/mod_vcmove.py
import discord
from discord.ext import commands

class ModVcmove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="vcmove")
    @commands.has_permissions(move_members=True)
    async def vcmove(self, ctx, member: discord.Member, channel: discord.VoiceChannel, *, reason: str = "Koi reason nahi diya gaya"):
        """Kisi member ko ek voice channel se doosre me move karne ke liye."""
        if not member.voice or not member.voice.channel:
            return await ctx.send("❌ Ye member abhi kisi voice channel me nahi hai!")
            
        if member.voice.channel.id == channel.id:
            return await ctx.send("⚠️ Member pehle se hi ussi voice channel me hai!")

        try:
            await member.move_to(channel, reason=f"VCMove by {ctx.author}: {reason}")
            embed = discord.Embed(
                title="✈️ Voice Moved",
                description=f"✅ {member.mention} ko {channel.mention} me move kar diya gaya hai.\n**Reason:** {reason}",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ Mere paas is member ko move karne ki permission nahi hai! (Higher role chahiye)")
        except Exception as e:
            await ctx.send(f"❌ Kuch gadbad ho gayi: {e}")

async def setup(bot):
    await bot.add_cog(ModVcmove(bot))
