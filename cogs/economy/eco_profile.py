import discord
from discord.ext import commands

class InfluencerProfile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_tier(self, clout):
        if clout < 100: return "Nobody (0-100 🔥)"
        if clout < 1000: return "Small Streamer (100-1K 🔥)"
        if clout < 5000: return "Rising Star (1K-5K 🔥)"
        if clout < 20000: return "Internet Celeb (5K-20K 🔥)"
        if clout < 100000: return "Global Icon (20K-100K 🔥)"
        return "God of the Internet (100K+ 🔥)"

    @commands.command(aliases=['profile', 'bal', 'balance', 'stats'])
    async def influencer(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        cursor = self.bot.db.cursor()
        
        cursor.execute("SELECT cash, clout, last_stream, last_video FROM influencer_stats WHERE user_id = ?", (str(member.id),))
        row = cursor.fetchone()
        
        if not row:
            # First time user
            cash, clout = 0, 0
        else:
            cash, clout, _, _ = row
            
        # Get gear count
        cursor.execute("SELECT COUNT(*) FROM influencer_gear WHERE user_id = ?", (str(member.id),))
        gear_row = cursor.fetchone()
        gear_count = gear_row[0] if gear_row else 0

        tier = self.get_tier(clout)

        embed = discord.Embed(title=f"📹 {member.display_name}'s Profile", color=0x2b2d31)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="💰 Cash", value=f"`${cash:,}`", inline=True)
        embed.add_field(name="🔥 Clout", value=f"`{clout:,}`", inline=True)
        embed.add_field(name="⭐ Influencer Tier", value=f"`{tier}`", inline=False)
        embed.add_field(name="🖥️ Gear Owned", value=f"`{gear_count} items`", inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(InfluencerProfile(bot))
