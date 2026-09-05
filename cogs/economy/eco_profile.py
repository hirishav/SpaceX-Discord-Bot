import discord
from discord.ext import commands

class InfluencerProfile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_tier_and_playbutton(self, clout):
        if clout < 500: return ("Noob (0-500 ⭐)", None)
        if clout < 2000: return ("Beginner (500-2K ⭐)", None)
        if clout < 5000: return ("Affiliate (2K-5K ⭐)", None)
        if clout < 15000: return ("Partner (5K-15K ⭐)", "🥈 Silver Playbutton")
        if clout < 30000: return ("Rising Star (15K-30K ⭐)", "🥈 Silver Playbutton")
        if clout < 100000: return ("Internet Celeb (30K-100K ⭐)", "🥇 Gold Playbutton")
        if clout < 500000: return ("Global Icon (100K-500K ⭐)", "💎 Diamond Playbutton")
        if clout < 2000000: return ("Mega Star (500K-2M ⭐)", "🛑 Custom Creator Award")
        return ("God of the Internet (2M+ ⭐)", "🔴 Red Diamond Playbutton")

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

        tier, playbutton = self.get_tier_and_playbutton(clout)

        embed = discord.Embed(title=f"👤 {member.display_name}'s Profile", color=0x2b2d31)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="💵 Cash", value=f"`💵 {cash:,}`", inline=True)
        embed.add_field(name="⭐ Clout", value=f"`{clout:,}`", inline=True)
        embed.add_field(name="📈 Influencer Tier", value=f"`{tier}`", inline=False)
        if playbutton:
            embed.add_field(name="🏆 Playbutton", value=f"`{playbutton}`", inline=True)
        embed.add_field(name="🛒 Gear Owned", value=f"`{gear_count} items`", inline=True)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(InfluencerProfile(bot))
