# cogs/serverinfo.py
import discord
from discord.ext import commands

class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="serverinfo", aliases=["si", "guildinfo"])
    async def serverinfo(self, ctx):
        """Server ki poori jankari dikhata hai (Command text delete nahi hoga)."""
        print(f"DEBUG: serverinfo command triggered by {ctx.author} in {ctx.guild}")
        
        guild = ctx.guild
        if not guild:
            return await ctx.send("Ye command sirf servers me chalta hai!")
            
        total_members = guild.member_count
        bot_count = sum(1 for member in guild.members if member.bot)
        human_count = total_members - bot_count

        admins = []
        managers = []
        moderators = []

        for member in guild.members:
            if member.bot:
                continue
                
            perms = member.guild_permissions
            
            if perms.administrator and member.id != guild.owner_id:
                admins.append(member.mention)
            elif (perms.manage_guild or perms.manage_channels) and member.id != guild.owner_id:
                managers.append(member.mention)
            elif (perms.kick_members or perms.ban_members or perms.manage_messages) and member.id != guild.owner_id:
                moderators.append(member.mention)

        admins_str = ", ".join(admins) if admins else "No Admins"
        managers_str = ", ".join(managers) if managers else "No Managers"
        mods_str = ", ".join(moderators) if moderators else "No Moderators"

        if len(admins_str) > 1024: admins_str = admins_str[:1020] + "..."
        if len(managers_str) > 1024: managers_str = managers_str[:1020] + "..."
        if len(mods_str) > 1024: mods_str = mods_str[:1020] + "..."

        created_at = guild.created_at.strftime("%d %B %Y")

        embed = discord.Embed(
            title=f"🏰 {guild.name} Server Information",
            color=discord.Color.blue()
        )
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="👑 Server Owner", value=f"<@{guild.owner_id}>", inline=False)
        embed.add_field(name="📅 Creation Date", value=f"**{created_at}**", inline=True)
        embed.add_field(name="🆔 Server ID", value=f"`{guild.id}`", inline=True)
        
        count_value = f"👥 Total: **{total_members}**\n👤 Humans: **{human_count}**\n🤖 Bots: **{bot_count}**"
        embed.add_field(name="📊 Member Counts", value=count_value, inline=False)

        embed.add_field(name="🔴 Server Admins", value=admins_str, inline=False)
        embed.add_field(name="🟠 Server Managers", value=managers_str, inline=False)
        embed.add_field(name="🟡 Server Moderators", value=mods_str, inline=False)

        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        
        # BADAL DIYA: Isme se bhi message delete karne ka jhanjhat saaf!
        try:
            await ctx.send(embed=embed)
            print("DEBUG: serverinfo embed sent successfully!")
        except Exception as e:
            print(f"DEBUG ERROR in serverinfo send: {e}")

async def setup(bot):
    await bot.add_cog(ServerInfo(bot))