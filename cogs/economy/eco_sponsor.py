import discord
from discord.ext import commands
import time

class InfluencerSponsor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['daily', 'branddeal'])
    @commands.cooldown(1, 86400, commands.BucketType.user) # 24 hours
    async def sponsor(self, ctx):
        user_id = str(ctx.author.id)
        cursor = self.bot.db.cursor()
        
        cursor.execute("INSERT OR IGNORE INTO influencer_stats (user_id) VALUES (?)", (user_id,))
        self.bot.db.commit()

        cursor.execute("SELECT clout FROM influencer_stats WHERE user_id = ?", (user_id,))
        clout = cursor.fetchone()[0]
        
        # Payout scales with clout
        if clout < 500: 
            payout = 500
            brand = "Raid Shadow Legends (Bronze Tier)"
        elif clout < 2000:
            payout = 2000
            brand = "G-Fuel"
        elif clout < 5000:
            payout = 5000
            brand = "NordVPN"
        elif clout < 15000:
            payout = 15000
            brand = "SeatGeek"
        elif clout < 30000:
            payout = 30000
            brand = "Manscaped"
        elif clout < 100000:
            payout = 75000
            brand = "Corsair"
        elif clout < 500000:
            payout = 150000
            brand = "Intel"
        elif clout < 2000000:
            payout = 300000
            brand = "MrBeast Burger"
        else:
            payout = 1000000
            brand = "Tesla"
            
        cursor.execute("UPDATE influencer_stats SET cash = cash + ?, last_sponsor = ? WHERE user_id = ?", 
                       (payout, int(time.time()), user_id))
        self.bot.db.commit()
        
        embed = discord.Embed(title="🤝 Brand Deal Secured!", color=0x2b2d31)
        embed.description = f"**{brand}** sponsored your latest content!"
        embed.add_field(name="Sponsorship Payout", value=f"💵 `💵 {payout:,}`")
        embed.set_footer(text="Earn more Clout to get better sponsors!")
        
        await ctx.send(embed=embed)
        
    @sponsor.error
    async def sponsor_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            m, s = divmod(error.retry_after, 60)
            h, m = divmod(m, 60)
            await ctx.send(f"⚠️ Brands are tired of you right now. Try again in `{int(h)}h {int(m)}m`.")

async def setup(bot):
    await bot.add_cog(InfluencerSponsor(bot))
