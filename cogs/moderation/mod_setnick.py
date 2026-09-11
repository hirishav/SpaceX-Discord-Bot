import discord
from discord.ext import commands

class ModSetNick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="setnick", aliases=["nickname", "changenick"])
    @commands.has_permissions(manage_messages=True)
    async def setnick(self, ctx, member: discord.Member, *, nickname: str = None):
        """Kisi member ka nickname change karne ke liye. (Requires Manage Messages)"""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("❌ Aap apne se unche ya barabar ke role waale member ka nickname change nahi kar sakte!")

        try:
            old_nick = member.display_name
            await member.edit(nick=nickname, reason=f"Nickname changed by {ctx.author.name}")

            embed = discord.Embed(
                title="📝 Nickname Changed",
                description=f"**{member.name}** ka nickname update ho gaya hai.",
                color=discord.Color.green()
            )
            embed.add_field(name="👤 User", value=f"{member.mention} ({member.id})", inline=False)
            embed.add_field(name="🛡️ Moderator", value=ctx.author.mention, inline=False)
            if nickname:
                embed.add_field(name="🔄 Changes", value=f"`{old_nick}` ➔ `{nickname}`", inline=False)
            else:
                embed.add_field(name="🔄 Changes", value=f"Nickname reset to `{member.name}`", inline=False)
            
            await ctx.send(embed=embed)

            try:
                await ctx.message.delete()
            except Exception:
                pass

        except discord.Forbidden:
            await ctx.send("❌ Main is member ka nickname change nahi kar sakta! Mera role inke upar hona chahiye, aur mere paas 'Manage Nicknames' permission honi chahiye.")
        except Exception as e:
            await ctx.send(f"❌ Ek error aagaya: {e}")

    @setnick.error
    async def setnick_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            pass
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}setnick @user <new nickname>`\n*Note: Leave nickname blank to reset it.*")

async def setup(bot):
    await bot.add_cog(ModSetNick(bot))
