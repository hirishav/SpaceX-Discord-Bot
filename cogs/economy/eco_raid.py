import discord
from discord.ext import commands
import random

class InfluencerRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_tier_level(self, clout):
        if clout < 500: return 0  # Noob
        if clout < 2000: return 1 # Beginner
        if clout < 5000: return 2 # Affiliate
        if clout < 15000: return 3 # Partner
        if clout < 30000: return 4 # Rising Star
        if clout < 100000: return 5 # Internet Celeb
        if clout < 500000: return 6 # Global Icon
        if clout < 2000000: return 7 # Mega Star
        return 8 # God of the Internet

    @commands.command()
    @commands.cooldown(1, 21600, commands.BucketType.user) # 6 hours
    async def raid(self, ctx, target: discord.Member = None):
        if not target:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"❌ Usage: `{ctx.prefix}raid @user`")
            
        if target.id == ctx.author.id:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ You can't raid your own chat.")
            
        if target.bot:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ Bots don't have clout.")

        user_id = str(ctx.author.id)
        target_id = str(target.id)
        
        cursor = self.bot.db.cursor()
        cursor.execute("INSERT OR IGNORE INTO influencer_stats (user_id) VALUES (?)", (user_id,))
        cursor.execute("INSERT OR IGNORE INTO influencer_stats (user_id) VALUES (?)", (target_id,))
        self.bot.db.commit()
        
        cursor.execute("SELECT clout FROM influencer_stats WHERE user_id = ?", (user_id,))
        user_clout = cursor.fetchone()[0]
        
        cursor.execute("SELECT clout FROM influencer_stats WHERE user_id = ?", (target_id,))
        target_clout = cursor.fetchone()[0]
        
        user_tier = self.get_tier_level(user_clout)
        target_tier = self.get_tier_level(target_clout)
        
        if user_tier == 0:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ You are a **Noob**. Get some more clout before trying to raid anyone!")
            
        if user_tier < target_tier:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"❌ **{target.display_name}** is a higher tier than you! You can only raid people below your tier or equal to Noobs.")
            
        if target_clout <= 0:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"❌ **{target.display_name}** has 0 Clout. There is nothing to steal.")
            
        # 20% chance to fail
        if random.random() < 0.20:
            lost_clout = int(user_clout * 0.05)
            cursor.execute("UPDATE influencer_stats SET clout = MAX(0, clout - ?) WHERE user_id = ?", (lost_clout, user_id))
            self.bot.db.commit()
            embed = discord.Embed(title="🚨 Raid Failed!", color=0xff0000)
            embed.description = f"You tried to raid **{target.display_name}** but their chat roasted you!"
            embed.add_field(name="Result", value=f"You lost ⭐ `{lost_clout:,}` Clout in the drama.")
            return await ctx.send(embed=embed)
            
        # Success: steal 5% of target's clout
        stolen_clout = max(1, int(target_clout * 0.05))
        
        cursor.execute("UPDATE influencer_stats SET clout = MAX(0, clout - ?) WHERE user_id = ?", (stolen_clout, target_id))
        cursor.execute("UPDATE influencer_stats SET clout = clout + ? WHERE user_id = ?", (stolen_clout, user_id))
        self.bot.db.commit()
        
        embed = discord.Embed(title="⚔️ Successful Raid!", color=0x2b2d31)
        embed.description = f"You brought your massive audience to **{target.display_name}**'s chat and stole the show!"
        embed.add_field(name="Result", value=f"You stole ⭐ `{stolen_clout:,}` Clout!")
        
        await ctx.send(embed=embed)

    @raid.error
    async def raid_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            m, s = divmod(error.retry_after, 60)
            h, m = divmod(m, 60)
            await ctx.send(f"⚠️ Your fans are tired from the last drama. Wait `{int(h)}h {int(m)}m` before raiding again.")

async def setup(bot):
    await bot.add_cog(InfluencerRaid(bot))
