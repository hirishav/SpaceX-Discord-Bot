import discord
from discord.ext import commands
import random
import time
from cogs.economy.eco_shop import SHOP_ITEMS

class InfluencerStream(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['live', 'golive'])
    @commands.cooldown(1, 7200, commands.BucketType.user) # 2 hours
    async def stream(self, ctx):
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
                multiplier += SHOP_ITEMS[g].get('multiplier', 0.0)
        
        base_cash = random.randint(100, 500)
        base_clout = random.randint(10, 50)
        
        earned_cash = int(base_cash * multiplier)
        earned_clout = int(base_clout * multiplier)
        
        # Random events
        event = random.choices(
            ["none", "raid", "swat", "viral"], 
            weights=[70, 10, 5, 15], 
            k=1
        )[0]
        
        event_text = ""
        if event == "raid":
            earned_clout *= 3
            event_text = "\n> 🎉 **RAID!** A big streamer raided you! 3x Clout!"
        elif event == "swat":
            earned_cash = 0
            earned_clout = -50 # lose some clout
            event_text = "\n> 🚓 **SWATTED!** Your stream got interrupted. You lost all cash from this stream and some clout!"
        elif event == "viral":
            earned_cash *= 2
            event_text = "\n> 📈 **VIRAL!** Your stream clipped and went viral! 2x Cash!"
            
        new_cash = max(0, cash + earned_cash)
        new_clout = max(0, clout + earned_clout)
        
        cursor.execute("UPDATE influencer_stats SET cash = ?, clout = ?, last_stream = ? WHERE user_id = ?", 
                       (new_cash, new_clout, int(time.time()), user_id))
        self.bot.db.commit()
        
        embed = discord.Embed(title="🔴 You went LIVE!", color=0x2b2d31)
        embed.description = f"You streamed for a few hours and gained some traction!{event_text}"
        embed.add_field(name="Earnings", value=f"💵 `💵 {earned_cash:,}`\n⭐ `{earned_clout:,}` Clout")
        embed.set_footer(text=f"Multiplier: {multiplier:.2f}x (from {len(gear_items)} gear items)")
        
        await ctx.send(embed=embed)

    @stream.error
    async def stream_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            m, s = divmod(error.retry_after, 60)
            h, m = divmod(m, 60)
            await ctx.send(f"⚠️ You just streamed! Take a break. Try again in `{int(h)}h {int(m)}m`.")

async def setup(bot):
    await bot.add_cog(InfluencerStream(bot))
