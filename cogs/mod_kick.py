# cogs/mod_kick.py
import discord
from discord.ext import commands

class ModKick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kisi member ko server se kick karne ke liye."""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("❌ Aap apne se unche ya barabar ke role waale member ko kick nahi kar sakte!")

        try:
            # Kick karne se pehle use DM me batana
            try:
                dm_embed = discord.Embed(
                    title=f"👢 You have been kicked from {ctx.guild.name}!",
                    description=f"**Reason:** {reason}",
                    color=discord.Color.red()
                )
                await member.send(embed=dm_embed)
            except Exception:
                pass

            await member.kick(reason=f"Kicked by {ctx.author.name} | Reason: {reason}")

            embed = discord.Embed(
                title="👢 Member Kicked",
                description=f"**{member.name}** ko server se nikal diya gaya hai.",
                color=discord.Color.red()
            )
            embed.add_field(name="👤 Target", value=f"{member.mention} ({member.id})", inline=True)
            embed.add_field(name="🛡️ Staff", value=ctx.author.mention, inline=True)
            embed.add_field(name="📝 Reason", value=reason, inline=False)
            await ctx.send(embed=embed)

            try:
                await ctx.message.delete()
            except Exception:
                pass

        except discord.Forbidden:
            await ctx.send("❌ Main is member ko kick nahi kar sakta! Mera role is member se upar hona chahiye.")

    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            pass
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}kick @user <reason>`")

async def setup(bot):
    await bot.add_cog(ModKick(bot))