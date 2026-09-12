import discord
from discord.ext import commands
import random

class InfluencerWork(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 3600, commands.BucketType.user) # 1 hour cooldown
    async def work(self, ctx):
        user_id = str(ctx.author.id)
        cursor = self.bot.db.cursor()
        
        # Ensure user exists
        cursor.execute("INSERT OR IGNORE INTO influencer_stats (user_id) VALUES (?)", (user_id,))
        self.bot.db.commit()

        cursor.execute("SELECT cash FROM influencer_stats WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        cash = row[0] if row else 0
        
        # Work outcomes
        work_messages = [
            "You edited a 10-hour long video for a famous YouTuber and earned",
            "You worked a shift at the local cafe while planning your next big video and earned",
            "You helped set up lighting for a photo shoot and got paid",
            "You wrote an amazing script for a sponsor and received",
            "You streamed for 5 hours straight playing Minecraft and earned"
        ]
        
        earned_cash = random.randint(100, 400)
        new_cash = cash + earned_cash
        
        cursor.execute("UPDATE influencer_stats SET cash = ? WHERE user_id = ?", (new_cash, user_id))
        self.bot.db.commit()
        
        embed = discord.Embed(
            title="💼 Work Completed!", 
            description=f"{random.choice(work_messages)} 💵 **{earned_cash:,}** Specie!",
            color=0x2b2d31
        )
        embed.set_footer(text=f"Total Specie: {new_cash:,}")
        
        await ctx.send(embed=embed)

    @work.error
    async def work_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            m, s = divmod(error.retry_after, 60)
            h, m = divmod(m, 60)
            time_str = ""
            if h > 0:
                time_str += f"{int(h)}h "
            if m > 0 or h > 0:
                time_str += f"{int(m)}m "
            time_str += f"{int(s)}s"
            
            await ctx.send(f"⚠️ You are too tired to work right now! Take a break and try again in `{time_str.strip()}`.")

    @commands.command()
    @commands.cooldown(1, 7200, commands.BucketType.user) # 2 hours cooldown
    async def crime(self, ctx):
        user_id = str(ctx.author.id)
        cursor = self.bot.db.cursor()
        
        # Ensure user exists
        cursor.execute("INSERT OR IGNORE INTO influencer_stats (user_id) VALUES (?)", (user_id,))
        self.bot.db.commit()

        cursor.execute("SELECT cash, clout FROM influencer_stats WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        cash = row[0] if row else 0
        clout = row[1] if row else 0
        
        # Crime chances: 40% success, 60% fail
        success = random.random() < 0.40
        
        if success:
            earned_cash = random.randint(500, 1500)
            new_cash = cash + earned_cash
            
            success_messages = [
                "You successfully view-botted a competitor's stream without getting caught and stole their sponsorships, earning",
                "You hacked a famous creator's Twitter account and promoted your own merch, making",
                "You leaked some fake drama and monetized the apology video, making a solid",
                "You scammed people with a fake NFT project and ran away with"
            ]
            
            cursor.execute("UPDATE influencer_stats SET cash = ? WHERE user_id = ?", (new_cash, user_id))
            self.bot.db.commit()
            
            embed = discord.Embed(
                title="😈 Crime Successful!", 
                description=f"{random.choice(success_messages)} 💵 **{earned_cash:,}** Specie!",
                color=0x00ff00
            )
            embed.set_footer(text=f"Total Specie: {new_cash:,}")
        else:
            lost_cash = random.randint(100, 500)
            # You can only lose up to what you have, or maybe go negative? Let's say min 0.
            new_cash = max(0, cash - lost_cash)
            lost_clout = random.randint(10, 50)
            new_clout = max(0, clout - lost_clout)
            
            fail_messages = [
                "You got caught view-botting and Discord disabled your account. You paid a fine of",
                "You tried to start fake drama but got cancelled on Twitter. You lost sponsors worth",
                "Your crypto scam was exposed by Coffeezilla and you had to refund",
                "You got sued for copyright infringement and had to pay"
            ]
            
            cursor.execute("UPDATE influencer_stats SET cash = ?, clout = ? WHERE user_id = ?", (new_cash, new_clout, user_id))
            self.bot.db.commit()
            
            embed = discord.Embed(
                title="🚨 BUSTED!", 
                description=f"{random.choice(fail_messages)} 💵 **{lost_cash:,}** Specie and lost ⭐ **{lost_clout}** Clout!",
                color=0xff0000
            )
            embed.set_footer(text=f"Total Specie: {new_cash:,} | Clout: {new_clout:,}")
            
        await ctx.send(embed=embed)

    @crime.error
    async def crime_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            m, s = divmod(error.retry_after, 60)
            h, m = divmod(m, 60)
            time_str = ""
            if h > 0:
                time_str += f"{int(h)}h "
            if m > 0 or h > 0:
                time_str += f"{int(m)}m "
            time_str += f"{int(s)}s"
            
            await ctx.send(f"🚓 The internet police are watching you closely. Lay low and try another crime in `{time_str.strip()}`.")

async def setup(bot):
    await bot.add_cog(InfluencerWork(bot))
