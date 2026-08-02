# cogs/mod_mute.py
import discord
from discord.ext import commands
import datetime
import re
import asyncio

class ModMute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Helper function: Jo time string ko parse karta hai
    def parse_duration(self, time_str: str):
        time_match = re.match(r"(\d+)([smhd])", time_str.lower())
        if not time_match:
            return None
        
        amount = int(time_match.group(1))
        unit = time_match.group(2)
        
        if unit == 's':
            return datetime.timedelta(seconds=amount)
        elif unit == 'm':
            return datetime.timedelta(minutes=amount)
        elif unit == 'h':
            return datetime.timedelta(hours=amount)
        elif unit == 'd':
            return datetime.timedelta(days=amount)
        return None

    @commands.command(name="mute", aliases=["timeout"])
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, duration_str: str, *, reason: str = "No reason provided"):
        """Kisi member ko flexible time (10m/5s/1d) ke liye timeout karne ke liye (Super Fast)."""
        
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("❌ Aap apne se baray ya barabar ke role waale member ko mute nahi kar sakte!")

        duration = self.parse_duration(duration_str)
        if not duration:
            return await ctx.send("❌ Galat time format! Use karein: `s`, `m`, `h`, ya `d`. (Example: `10m`, `1d`)")

        if duration > datetime.timedelta(days=28):
            return await ctx.send("❌ Discord par aap kisi ko 28 days se zyada timeout nahi de sakte!")

        try:
            # Timeout apply karna
            await member.timeout(duration, reason=f"Muted by {ctx.author.name} | Reason: {reason}")
            
            # Embed Message taiyar karna (Timestamp ko sahi tarike se jora hai)
            embed = discord.Embed(
                title="🤫 Member Muted (Timeout)",
                description=f"{member.mention} ko kamyabi se mute kar diya gaya hai.",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.now(datetime.timezone.utc) # FIX: Sahi timestamp lagaya
            )
            embed.add_field(name="👤 Target", value=f"{member.name} ({member.id})", inline=True)
            embed.add_field(name="⏳ Duration", value=f"`{duration_str}`", inline=True)
            embed.add_field(name="🛡️ Staff", value=ctx.author.mention, inline=True)
            embed.add_field(name="📝 Reason", value=reason, inline=False)
            
            # Chat me instant reply jayega ab bina kisi delay ke
            await ctx.send(embed=embed)

            # Command message delete karne ka try
            try:
                await ctx.message.delete()
            except Exception:
                pass

            # DM System ko Background Task bana diya (Taaki bot wait na kare aur ping slow na lage)
            async def send_dm():
                try:
                    dm_embed = discord.Embed(
                        title=f"🤫 You have been muted in {ctx.guild.name}!",
                        description=f"Duration: **{duration_str}**\nReason: **{reason}**",
                        color=discord.Color.red(),
                        timestamp=datetime.datetime.now(datetime.timezone.utc)
                    )
                    await member.send(embed=dm_embed)
                except Exception:
                    pass

            asyncio.create_task(send_dm())

        except discord.Forbidden:
            await ctx.send("❌ Main is member ko mute nahi kar sakta! Mera role is member se upar hona chahiye.")
        except Exception as e:
            await ctx.send(f"❌ Kuch gadbad hui: {e}")

    @mute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            pass
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}mute @user <time> <reason>`\nExample: `{ctx.prefix}mute @user 10m Abusing`")

async def setup(bot):
    await bot.add_cog(ModMute(bot))