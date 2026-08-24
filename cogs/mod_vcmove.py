# cogs/mod_vcmove.py
import discord
from discord.ext import commands

class ModVcmove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="vcmove")
    @commands.has_guild_permissions(move_members=True)
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
            try:
                await ctx.message.delete()
            except Exception:
                pass
        except discord.Forbidden:
            await ctx.send("❌ Mere paas is member ko move karne ki permission nahi hai! (Higher role chahiye)")
        except Exception as e:
            await ctx.send(f"❌ Kuch gadbad ho gayi: {e}")

    @vcmove.error
    async def vcmove_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Aapke paas is command ko use karne ki permission nahi hai!")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ Member nahi mila! Sahi tag ya ID use karein.")
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send("❌ Channel nahi mila! Sahi channel ID use karein.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}vcmove @user <channel_id> [reason]`")
        else:
            await ctx.send(f"❌ Kuch gadbad hui: {error}")

async def setup(bot):
    await bot.add_cog(ModVcmove(bot))
