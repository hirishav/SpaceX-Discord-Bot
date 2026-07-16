# cogs/mod_unmute.py
import discord
from discord.ext import commands
import datetime

class ModUnmute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="unmute", aliases=["untimeout"])
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kisi member ka timeout (mute) pehle hatane ke liye."""
        
        # 🔥 FIX: Check karna ki timeout real me active hai ya khatam ho chuka hai
        now = datetime.datetime.now(datetime.timezone.utc)
        if not member.timed_out_until or member.timed_out_until <= now:
            return await ctx.send(f"❌ {member.mention} pehle se hi unmuted hai bhai! Is par koi active timeout nahi hai.")

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
        except Exception as e:
            await ctx.send(f"❌ Kuch gadbad hui: {e}")

    @unmute.error
    async def unmute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            pass
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}unmute @user <reason>`")

async def setup(bot):
    await bot.add_cog(ModUnmute(bot))