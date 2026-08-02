# cogs/fun_dm.py
import discord
from discord.ext import commands

class FunDM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_target(self, ctx, user_str):
        try:
            member = await commands.MemberConverter().convert(ctx, user_str)
            return member
        except Exception:
            try:
                user = await self.bot.fetch_user(int(user_str))
                return user
            except Exception:
                return None

    @commands.command(name="dm")
    async def dm_user(self, ctx, user_target: str = None, *, message: str = None):
        """Kisi user ko bot ke through direct DM bhejkar embed preview display karta hai."""
        if not user_target or not message:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}dm @user/ID <your_message>`")

        member = await self.fetch_target(ctx, user_target)
        if not member:
            return await ctx.send("❌ User nahi mila! Valid tag ya account ID daalein.")

        try:
            await member.send(f"📩 **New Message from {ctx.author.name} (via SpaceX Bot):**\n\n{message}")
            
            embed = discord.Embed(title="✅ DM Dispatch Status: SUCCESS", color=discord.Color.green())
            embed.add_field(name="👤 Target User", value=f"{member.name} (ID: `{member.id}`)", inline=True)
            embed.add_field(name="🛡️ Sender Author", value=ctx.author.mention, inline=True)
            embed.add_field(name="📝 Transmitted Content Logs", value=f"\"{message}\"", inline=False)
            embed.set_footer(text="SpaceX Delivery Engine Pipeline")
            
            await ctx.send(embed=embed)

        except discord.Forbidden:
            await ctx.send(f"❌ **Delivery Blocked:** Main `{member.name}` ko DM nahi bhej sakta! Unke privacy settings block hain.")
        except Exception as e:
            await ctx.send(f"❌ Message sending loop error occurred: `{e}`")

async def setup(bot):
    await bot.add_cog(FunDM(bot))