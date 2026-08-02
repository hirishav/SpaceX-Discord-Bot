# cogs/mod_ban.py
import discord
from discord.ext import commands

class ModBan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kisi member ko server se permanent ban karne ke liye (Role Check & DM Bug Fixed)."""
        
        # FIX: Agar target ka role bada ya barabar hai, toh 'return' lagakar code ko yahi rok do!
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("❌ Aap apne se unche ya barabar ke role waale member ko ban nahi kar sakte!")

        # Extra safety check: Bot khud se unche role wale ko ban nahi kar sakta
        if member.top_role >= ctx.guild.me.top_role:
            return await ctx.send("❌ Mera role is member se niche hai, main ise ban nahi kar sakta!")

        try:
            # Ab DM sirf tabhi jayega jab upar ke saare role check pass ho chuke honge!
            try:
                dm_embed = discord.Embed(
                    title=f"🔨 You have been PERMANENTLY BANNED from {ctx.guild.name}!",
                    description=f"**Reason:** {reason}",
                    color=discord.Color.red()
                )
                await member.send(embed=dm_embed)
            except Exception:
                pass

            # Member ban karna
            await member.ban(reason=f"Banned by {ctx.author.name} | Reason: {reason}", delete_message_days=1)

            embed = discord.Embed(
                title="🔨 Member Banned",
                description=f"**{member.name}** ko hamesha ke liye ban kar diya gaya hai.",
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
            await ctx.send("❌ Main is member ko ban nahi kar sakta! Kripya check karein ki mera role upar ho.")

    @ban.error
    async def ban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            pass
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}ban @user <reason>`")

async def setup(bot):
    await bot.add_cog(ModBan(bot))