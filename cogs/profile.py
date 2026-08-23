import discord
from discord.ext import commands
import sqlite3

class UserProfile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "warnings.db"

    def get_user_data(self, user_id: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Fetch Economy
        cursor.execute("SELECT wallet, bank FROM economy WHERE user_id = ?", (user_id,))
        eco_row = cursor.fetchone()
        wallet, bank = eco_row if eco_row else (0, 0)
        
        # Fetch Badges
        cursor.execute("SELECT badge FROM user_badges WHERE user_id = ?", (user_id,))
        badges = [row[0] for row in cursor.fetchall()]
        
        # Fetch Warnings Count
        cursor.execute("SELECT COUNT(*) FROM warnings WHERE user_id = ?", (user_id,))
        warn_count = cursor.fetchone()[0]
        
        conn.close()
        return wallet, bank, badges, warn_count

    @commands.hybrid_command(name="profile", aliases=["userinfo", "pr"])
    async def profile(self, ctx, member: discord.Member = None):
        """User ki puri profile aur badges dekhne ke liye."""
        member = member or ctx.author
        
        wallet, bank, badges, warn_count = self.get_user_data(str(member.id))
        total_wealth = wallet + bank
        
        embed = discord.Embed(title=f"👤 {member.name}'s Profile", color=member.color if member.color != discord.Color.default() else discord.Color.blue())
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Badges Description
        if badges:
            embed.description = "**Badges:**\n" + " | ".join(badges)
        else:
            embed.description = "*No badges yet.*"

        # Economy Details
        embed.add_field(name="💰 Net Worth", value=f"✨ `{total_wealth:,}` Specie\n(Wallet: {wallet:,} | Bank: {bank:,})", inline=False)
        
        # Account Info
        joined_server = member.joined_at.strftime("%d %b %Y") if member.joined_at else "Unknown"
        joined_discord = member.created_at.strftime("%d %b %Y")
        embed.add_field(name="📅 Joined Server", value=joined_server, inline=True)
        embed.add_field(name="🌐 Joined Discord", value=joined_discord, inline=True)
        
        # Moderation Info
        if warn_count > 0:
            embed.add_field(name="⚠️ Warnings", value=f"`{warn_count}` active warnings", inline=False)
            
        embed.set_footer(text=f"Requested by {ctx.author.name} • ID: {member.id}", icon_url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(UserProfile(bot))
