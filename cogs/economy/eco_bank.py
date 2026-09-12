import discord
from discord.ext import commands
import random
import time

class EcoBank(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['deposit'])
    async def dep(self, ctx, amount: str = None):
        """Deposit cash into your bank."""
        if not amount:
            return await ctx.send(f"❌ Usage: `{ctx.prefix}dep <amount|all>`")
            
        cursor = self.bot.db.cursor()
        cursor.execute("INSERT OR IGNORE INTO influencer_stats (user_id) VALUES (?)", (str(ctx.author.id),))
        self.bot.db.commit()
        
        cursor.execute("SELECT cash, bank FROM influencer_stats WHERE user_id = ?", (str(ctx.author.id),))
        row = cursor.fetchone()
        cash = row[0]
        
        if amount.lower() == 'all':
            dep_amount = cash
        else:
            try:
                dep_amount = int(amount)
            except ValueError:
                return await ctx.send("❌ Amount must be a number or `all`.")
                
        if dep_amount <= 0:
            return await ctx.send("❌ Amount must be greater than 0.")
            
        if cash < dep_amount:
            return await ctx.send(f"❌ You don't have enough cash. You only have `💵 {cash:,}`.")
            
        cursor.execute("UPDATE influencer_stats SET cash = cash - ?, bank = bank + ? WHERE user_id = ?", (dep_amount, dep_amount, str(ctx.author.id)))
        self.bot.db.commit()
        
        await ctx.send(f"🏦 You deposited `💵 {dep_amount:,}` into your bank.")

    @commands.command(aliases=['withdraw'])
    async def with_(self, ctx, amount: str = None):
        """Withdraw cash from your bank."""
        if not amount:
            return await ctx.send(f"❌ Usage: `{ctx.prefix}with <amount|all>`")
            
        cursor = self.bot.db.cursor()
        cursor.execute("INSERT OR IGNORE INTO influencer_stats (user_id) VALUES (?)", (str(ctx.author.id),))
        self.bot.db.commit()
        
        cursor.execute("SELECT cash, bank FROM influencer_stats WHERE user_id = ?", (str(ctx.author.id),))
        row = cursor.fetchone()
        bank = row[1]
        
        if amount.lower() == 'all':
            with_amount = bank
        else:
            try:
                with_amount = int(amount)
            except ValueError:
                return await ctx.send("❌ Amount must be a number or `all`.")
                
        if with_amount <= 0:
            return await ctx.send("❌ Amount must be greater than 0.")
            
        if bank < with_amount:
            return await ctx.send(f"❌ You don't have enough in your bank. You only have `🏦 {bank:,}`.")
            
        cursor.execute("UPDATE influencer_stats SET cash = cash + ?, bank = bank - ? WHERE user_id = ?", (with_amount, with_amount, str(ctx.author.id)))
        self.bot.db.commit()
        
        await ctx.send(f"🏦 You withdrew `💵 {with_amount:,}` from your bank.")

    @commands.command()
    async def rob(self, ctx, target: discord.Member = None):
        """Rob someone's cash."""
        if not target:
            return await ctx.send(f"❌ Usage: `{ctx.prefix}rob @user`")
            
        if target.id == ctx.author.id:
            return await ctx.send("❌ You can't rob yourself.")
            
        cursor = self.bot.db.cursor()
        cursor.execute("INSERT OR IGNORE INTO influencer_stats (user_id) VALUES (?)", (str(ctx.author.id),))
        cursor.execute("INSERT OR IGNORE INTO influencer_stats (user_id) VALUES (?)", (str(target.id),))
        self.bot.db.commit()
        
        cursor.execute("SELECT cash FROM influencer_stats WHERE user_id = ?", (str(ctx.author.id),))
        my_cash = cursor.fetchone()[0]
        
        if my_cash < 500:
            return await ctx.send("❌ You need at least `💵 500` to attempt a robbery.")
            
        cursor.execute("SELECT cash FROM influencer_stats WHERE user_id = ?", (str(target.id),))
        target_cash = cursor.fetchone()[0]
        
        if target_cash < 500:
            return await ctx.send("❌ It's not worth it, they don't have enough cash.")
            
        success_chance = random.randint(1, 100)
        
        if success_chance > 50:
            # Success
            stolen = int(target_cash * random.uniform(0.1, 0.4))
            cursor.execute("UPDATE influencer_stats SET cash = cash + ? WHERE user_id = ?", (stolen, str(ctx.author.id)))
            cursor.execute("UPDATE influencer_stats SET cash = cash - ? WHERE user_id = ?", (stolen, str(target.id)))
            self.bot.db.commit()
            await ctx.send(f"🥷 You successfully robbed **{target.display_name}** and got away with `💵 {stolen:,}`!")
        else:
            # Fail
            fine = int(my_cash * random.uniform(0.1, 0.3))
            cursor.execute("UPDATE influencer_stats SET cash = cash - ? WHERE user_id = ?", (fine, str(ctx.author.id)))
            self.bot.db.commit()
            await ctx.send(f"🚓 You got caught trying to rob **{target.display_name}** and paid a fine of `💵 {fine:,}`!")

    @commands.command()
    async def weekly(self, ctx):
        """Claim your weekly reward."""
        cursor = self.bot.db.cursor()
        cursor.execute("INSERT OR IGNORE INTO influencer_stats (user_id) VALUES (?)", (str(ctx.author.id),))
        self.bot.db.commit()
        
        cursor.execute("SELECT last_weekly FROM influencer_stats WHERE user_id = ?", (str(ctx.author.id),))
        last_weekly = cursor.fetchone()[0]
        
        now = int(time.time())
        cooldown = 7 * 24 * 60 * 60
        
        if now - last_weekly < cooldown:
            remaining = cooldown - (now - last_weekly)
            days = remaining // (24 * 3600)
            hours = (remaining % (24 * 3600)) // 3600
            mins = (remaining % 3600) // 60
            return await ctx.send(f"⏳ You have already claimed your weekly reward. Come back in **{days}d {hours}h {mins}m**.")
            
        reward = random.randint(5000, 15000)
        cursor.execute("UPDATE influencer_stats SET cash = cash + ?, last_weekly = ? WHERE user_id = ?", (reward, now, str(ctx.author.id)))
        self.bot.db.commit()
        
        await ctx.send(f"🎁 You claimed your weekly reward of `💵 {reward:,}`!")

async def setup(bot):
    await bot.add_cog(EcoBank(bot))
