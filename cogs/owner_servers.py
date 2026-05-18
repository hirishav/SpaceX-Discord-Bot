# cogs/owner_servers.py
import discord
from discord.ext import commands

class OwnerServers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="servers", aliases=["guilds", "serverlist"], hidden=True)
    @commands.is_owner()
    async def servers_list(self, ctx):
        """Sirf Bot Owner ke liye - Saare servers ki list nikalne ke liye jahan bot add hai."""
        
        # Agar bot kisi server me nahi hai
        if not self.bot.guilds:
            return await ctx.send("❌ Bot abhi tak kisi bhi server me add nahi hua hai!")

        embed = discord.Embed(
            title=f"🏰 SpaceX Bot - Server Expansion List",
            description=f"Mubarak ho Rishav bhai! Aapka bot abhi total **{len(self.bot.guilds)}** servers me raaj kar raha hai.\n\nNiche saari kundali di gayi hai:",
            color=discord.Color.gold()
        )
        
        # Har server ki details loop chalakar nikalna
        for index, guild in enumerate(self.bot.guilds, start=1):
            server_name = guild.name
            server_id = guild.id
            member_count = guild.member_count
            server_owner = f"{guild.owner.name} ({guild.owner.mention})" if guild.owner else "Unknown Owner"
            
            # Ek ek karke saare servers ko embed fields me add karna
            field_value = f"🆔 **ID:** `{server_id}`\n👑 **Owner/Inviter:** {server_owner}\n👥 **Members:** `{member_count}`"
            embed.add_field(
                name=f"{index}. {server_name}",
                value=field_value,
                inline=False
            )

        embed.set_footer(text=f"Owner Access Only | Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        
        # DM me bhejna zyada safe rahega taaki public chat me servers ki ID leak na ho
        try:
            await ctx.author.send(embed=embed)
            await ctx.send("📥 Rishav bhai, privacy ke liye maine saare servers ki list aapke **Personal DM** me bhej di hai! Check kijiye.")
        except discord.Forbidden:
            # Agar owner ka DM closed ho, toh majboori me chat me bhejna padega
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OwnerServers(bot))