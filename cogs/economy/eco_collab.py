import discord
from discord.ext import commands

class InfluencerCollab(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 21600, commands.BucketType.user) # 6 hours
    async def collab(self, ctx, target: discord.Member = None):
        if not target:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ You need to mention someone to collab with!")
            
        if target.id == ctx.author.id:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ You can't collab with yourself.")
            
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
        
        # Calculate shared clout
        gained_clout_user = int(target_clout * 0.1) + 100
        gained_clout_target = int(user_clout * 0.1) + 100
        
        cursor.execute("UPDATE influencer_stats SET clout = clout + ? WHERE user_id = ?", (gained_clout_user, user_id))
        cursor.execute("UPDATE influencer_stats SET clout = clout + ? WHERE user_id = ?", (gained_clout_target, target_id))
        self.bot.db.commit()
        
        embed = discord.Embed(title="🤝 Epic Collab!", color=0x2b2d31)
        embed.description = f"**{ctx.author.display_name}** and **{target.display_name}** just dropped a banger collab!"
        embed.add_field(name=f"{ctx.author.display_name} gained", value=f"⭐ `{gained_clout_user:,}` Clout")
        embed.add_field(name=f"{target.display_name} gained", value=f"⭐ `{gained_clout_target:,}` Clout")
        
        await ctx.send(embed=embed)

    @collab.error
    async def collab_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            m, s = divmod(error.retry_after, 60)
            h, m = divmod(m, 60)
            await ctx.send(f"⚠️ Your fans are overwhelmed. Wait `{int(h)}h {int(m)}m` before your next collab.")

async def setup(bot):
    await bot.add_cog(InfluencerCollab(bot))
