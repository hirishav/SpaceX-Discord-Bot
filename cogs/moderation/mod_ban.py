# cogs/mod_ban.py
import discord
from discord.ext import commands
from utils import send_mod_log

class ModBan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kisi member ko server se permanent ban karne ke liye (Role Check & DM Bug Fixed)."""
        
        if member.guild_permissions.administrator:
            return await ctx.send("❌ Aap kisi Admin ko ban nahi kar sakte!")

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
            
            await send_mod_log(self.bot, ctx.guild, "mod", embed)

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
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ Ye member mujhe server me nahi mila! Sahi ID ya mention provide karein.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}ban @user <reason>`")

    @commands.hybrid_command(name="forceban")
    @commands.has_permissions(ban_members=True)
    async def forceban(self, ctx, user: discord.User, *, reason: str = "Force banned (not in server)"):
        """Kisi user ko uske ID se permanent ban karne ke liye (chahe wo server me na ho)."""
        
        # Check if the user is actually in the server. If so, apply the same checks as normal ban.
        member = ctx.guild.get_member(user.id)
        if member:
            if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
                return await ctx.send("❌ Ye user server me hai aur aap apne se unche ya barabar ke role waale member ko ban nahi kar sakte!")
            if member.top_role >= ctx.guild.me.top_role:
                return await ctx.send("❌ Mera role is member se niche hai, main ise ban nahi kar sakta!")

        try:
            await ctx.guild.ban(user, reason=f"Forcebanned by {ctx.author.name} | Reason: {reason}", delete_message_days=1)
            
            embed = discord.Embed(
                title="🔨 User Force Banned",
                description=f"**{user.name}** ko hamesha ke liye ban kar diya gaya hai.",
                color=discord.Color.red()
            )
            embed.add_field(name="👤 Target", value=f"{user.mention} (`{user.id}`)", inline=True)
            embed.add_field(name="🛡️ Staff", value=ctx.author.mention, inline=True)
            embed.add_field(name="📝 Reason", value=reason, inline=False)
            await ctx.send(embed=embed)
            
            await send_mod_log(self.bot, ctx.guild, "mod", embed)
            
        except discord.Forbidden:
            await ctx.send("❌ Main is user ko ban nahi kar sakta! Kripya permissions check karein.")

    @forceban.error
    async def forceban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            pass
        elif isinstance(error, (commands.MissingRequiredArgument, commands.UserNotFound)):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}forceban <user_id> [reason]`")

    @commands.hybrid_command(name="tempban")
    @commands.has_permissions(ban_members=True)
    async def tempban(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kisi member ko immediately ban aur unban karne ke liye taaki unke messages delete ho jayein."""
        
        if member.guild_permissions.administrator:
            return await ctx.send("❌ Aap kisi Admin ko tempban nahi kar sakte!")

        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("❌ Aap apne se unche ya barabar ke role waale member ko tempban nahi kar sakte!")

        if member.top_role >= ctx.guild.me.top_role:
            return await ctx.send("❌ Mera role is member se niche hai, main ise tempban nahi kar sakta!")

        try:
            try:
                dm_embed = discord.Embed(
                    title=f"🔨 You have been TEMPBANNED from {ctx.guild.name}!",
                    description=f"**Reason:** {reason}\n*Note: This was a temporary ban to clear your messages. You can rejoin the server if you have an invite.*",
                    color=discord.Color.orange()
                )
                await member.send(embed=dm_embed)
            except Exception:
                pass

            # Ban to delete messages
            await member.ban(reason=f"Tempbanned by {ctx.author.name} | Reason: {reason}", delete_message_days=7)
            # Unban immediately
            await ctx.guild.unban(discord.Object(id=member.id), reason="Tempban - Auto unban")

            embed = discord.Embed(
                title="🔨 Member Temp-Banned",
                description=f"**{member.name}** ko tempban karke unke messages delete kar diye gaye hain.",
                color=discord.Color.orange()
            )
            embed.add_field(name="👤 Target", value=f"{member.mention} ({member.id})", inline=True)
            embed.add_field(name="🛡️ Staff", value=ctx.author.mention, inline=True)
            embed.add_field(name="📝 Reason", value=reason, inline=False)
            await ctx.send(embed=embed)
            
            await send_mod_log(self.bot, ctx.guild, "mod", embed)

            try:
                await ctx.message.delete()
            except Exception:
                pass

        except discord.Forbidden:
            await ctx.send("❌ Main is member ko tempban nahi kar sakta! Kripya check karein ki mera role upar ho.")

    @tempban.error
    async def tempban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            pass
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ Ye member mujhe server me nahi mila! Sahi ID ya mention provide karein.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}tempban @user <reason>`")

    @commands.hybrid_command(name="hardban")
    @commands.has_permissions(administrator=True)
    async def hardban(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kisi member ko severely hardban karne ke liye (Admins Only)."""
        
        if member.guild_permissions.administrator:
            return await ctx.send("❌ Aap kisi Admin ko hardban nahi kar sakte!")

        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("❌ Aap apne se unche ya barabar ke role waale member ko hardban nahi kar sakte!")

        if member.top_role >= ctx.guild.me.top_role:
            return await ctx.send("❌ Mera role is member se niche hai, main ise hardban nahi kar sakta!")

        try:
            try:
                dm_embed = discord.Embed(
                    title=f"🛑 HARDBAN NOTICE 🛑",
                    description=f"You have been **HARDBANNED** from **{ctx.guild.name}**!\n\n**Reason:** {reason}\n\n*Your recent messages have been wiped from the server. This action is final and appeals will not be considered.*",
                    color=discord.Color.dark_red()
                )
                await member.send(embed=dm_embed)
            except Exception:
                pass

            await member.ban(reason=f"HARDBAN by {ctx.author.name} | Reason: {reason}", delete_message_days=7)

            embed = discord.Embed(
                title="🛑 Member Hardbanned!",
                description=f"**{member.name}** ko successfully server se hardban kar diya gaya hai. Unke pichle 7 din ke saare messages mita diye gaye hain.",
                color=discord.Color.dark_red()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="👤 Target", value=f"{member.mention} ({member.id})", inline=True)
            embed.add_field(name="🛡️ Admin", value=ctx.author.mention, inline=True)
            embed.add_field(name="📝 Reason", value=reason, inline=False)
            embed.set_footer(text="Strict Action Taken • Hardban Protocol")
            await ctx.send(embed=embed)
            
            await send_mod_log(self.bot, ctx.guild, "mod", embed)

            try:
                await ctx.message.delete()
            except Exception:
                pass

        except discord.Forbidden:
            await ctx.send("❌ Main is member ko hardban nahi kar sakta! Kripya permissions check karein.")

    @hardban.error
    async def hardban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            pass
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ Ye member mujhe server me nahi mila! Sahi ID ya mention provide karein.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}hardban @user <reason>`")

    @commands.hybrid_command(name="ipban")
    @commands.has_permissions(ban_members=True)
    async def ipban(self, ctx, user: discord.User, *, reason: str = "IP Ban requested"):
        """Kisi user ko IP ban karne ke liye (Discord inherently IP bans users on normal bans)."""
        
        member = ctx.guild.get_member(user.id)
        if member:
            if member.guild_permissions.administrator:
                return await ctx.send("❌ Aap kisi Admin ko IP ban nahi kar sakte!")

            if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
                return await ctx.send("❌ Aap apne se unche ya barabar ke role waale member ko IP ban nahi kar sakte!")

            if member.top_role >= ctx.guild.me.top_role:
                return await ctx.send("❌ Mera role is member se niche hai, main ise IP ban nahi kar sakta!")

        try:
            if member:
                try:
                    dm_embed = discord.Embed(
                        title=f"🌐 IP BANNED from {ctx.guild.name}!",
                        description=f"**Reason:** {reason}\n\n*Your IP address and all associated accounts have been banned from this server.*",
                        color=discord.Color.from_rgb(255, 0, 0)
                    )
                    await member.send(embed=dm_embed)
                except Exception:
                    pass

            await ctx.guild.ban(user, reason=f"IP Banned by {ctx.author.name} | Reason: {reason}", delete_message_days=1)

            embed = discord.Embed(
                title="🌐 User IP Banned",
                description=f"**{user.name}** ko IP Ban kar diya gaya hai. Unki is IP se koi bhi alt account ab server join nahi kar payega.",
                color=discord.Color.from_rgb(255, 0, 0)
            )
            embed.add_field(name="👤 Target", value=f"{user.mention} (`{user.id}`)", inline=True)
            embed.add_field(name="🛡️ Staff", value=ctx.author.mention, inline=True)
            embed.add_field(name="📝 Reason", value=reason, inline=False)
            await ctx.send(embed=embed)
            
            await send_mod_log(self.bot, ctx.guild, "mod", embed)

            try:
                await ctx.message.delete()
            except Exception:
                pass

        except discord.Forbidden:
            await ctx.send("❌ Main is user ko IP ban nahi kar sakta! Kripya permissions check karein.")

    @ipban.error
    async def ipban_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            pass
        elif isinstance(error, (commands.MissingRequiredArgument, commands.UserNotFound)):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}ipban <user_id> [reason]`")

async def setup(bot):
    await bot.add_cog(ModBan(bot))