import discord
from discord.ext import commands
import random
import time
from cogs.economy.eco_shop import SHOP_ITEMS

class InfluencerVideo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['video'])
    @commands.cooldown(1, 43200, commands.BucketType.user) # 12 hours
    async def upload(self, ctx):
        user_id = str(ctx.author.id)
        cursor = self.bot.db.cursor()
        
        # Ensure user exists
        cursor.execute("INSERT OR IGNORE INTO influencer_stats (user_id) VALUES (?)", (user_id,))
        self.bot.db.commit()

        cursor.execute("SELECT cash, clout FROM influencer_stats WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        cash, clout = row[0], row[1]
        
        # Calculate multipliers based on gear
        cursor.execute("SELECT item_id FROM influencer_gear WHERE user_id = ?", (user_id,))
        gear_items = [r[0] for r in cursor.fetchall()]
        
        multiplier = 1.0
        for g in gear_items:
            if g in SHOP_ITEMS:
                # Video has slightly better scaling for gear
                multiplier += SHOP_ITEMS[g].get('multiplier', 0.0) * 1.5
        
        base_cash = random.randint(500, 2000)
        base_clout = random.randint(50, 200)
        
        earned_cash = int(base_cash * multiplier)
        earned_clout = int(base_clout * multiplier)
        
        # Random events
        event = random.choices(
            ["none", "trending", "cancel", "demonetized"], 
            weights=[60, 20, 5, 15], 
            k=1
        )[0]
        
        event_text = ""
        if event == "trending":
            earned_clout *= 2
            earned_cash *= 2
            event_text = "\n> 📈 **#1 ON TRENDING!** Your video blew up! Double rewards!"
        elif event == "cancel":
            earned_cash = 0
            earned_clout = -200 # lose a lot of clout
            event_text = "\n> 🛑 **CANCELLED!** You said something controversial. You got 0 cash and lost massive Clout!"
        elif event == "demonetized":
            earned_cash = 0
            event_text = "\n> 🟡 **DEMONETIZED!** YouTube struck your video. You got the Clout, but $0 Cash!"
            
        new_cash = max(0, cash + earned_cash)
        new_clout = max(0, clout + earned_clout)
        
        cursor.execute("UPDATE influencer_stats SET cash = ?, clout = ?, last_video = ? WHERE user_id = ?", 
                       (new_cash, new_clout, int(time.time()), user_id))
        self.bot.db.commit()
        
        embed = discord.Embed(title="🎬 Video Uploaded!", color=0x2b2d31)
        embed.description = f"You spent hours editing and finally uploaded your video!{event_text}"
        if event == "cancel":
            embed.color = 0xff0000
        
        embed.add_field(name="Earnings", value=f"💵 `💵 {earned_cash:,}`\n⭐ `{earned_clout:,}` Clout")
        embed.set_footer(text=f"Multiplier: {multiplier:.2f}x (from {len(gear_items)} gear items)")
        
        await ctx.send(embed=embed)

    @upload.error
    async def upload_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            m, s = divmod(error.retry_after, 60)
            h, m = divmod(m, 60)
            await ctx.send(f"⚠️ Editing takes time! You can upload again in `{int(h)}h {int(m)}m`.")

async def setup(bot):
    await bot.add_cog(InfluencerVideo(bot))
