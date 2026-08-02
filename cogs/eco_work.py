# cogs/eco_work.py
import discord
from discord.ext import commands
import sqlite3
import random
import asyncio

class EcoWork(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "warnings.db"
        self.cooldowns = {} # Dictionary to track custom cooldowns

    async def handle_cooldown(self, ctx):
        user_id = ctx.author.id
        current_time = asyncio.get_event_loop().time()
        
        if user_id in self.cooldowns:
            remaining = self.cooldowns[user_id] - current_time
            if remaining > 0:
                # Initial Countdown message
                msg = await ctx.send(f"⏳ {ctx.author.mention}, chill karo! Try again after **{int(remaining)} seconds**.")
                
                # Dynamic countdown loop
                while remaining > 0:
                    await asyncio.sleep(1)
                    remaining = self.cooldowns[user_id] - asyncio.get_event_loop().time()
                    if remaining <= 0:
                        break
                    try:
                        await msg.edit(content=f"⏳ {ctx.author.mention}, chill karo! Try again after **{int(remaining)} seconds**.")
                    except discord.NotFound:
                        return False # Msg already deleted manually
                
                try:
                    await msg.delete() # Countdown khatam, msg khatam!
                except discord.NotFound:
                    pass
                return False
        
        # Safe to execute, set naya 30s cooldown
        self.cooldowns[user_id] = current_time + 30
        return True

    @commands.command(name="work")
    async def work(self, ctx):
        """Mehnat ka kaam karke safe coins kamane ke liye."""
        if not await self.handle_cooldown(ctx):
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO economy (user_id, wallet, bank) VALUES (?, 0, 0)", (str(ctx.author.id),))

        earnings = random.randint(100, 500)
        jobs = ["McDonalds me burger banaya", "Rishav bhai ke bot ki coding ki", "Discord server manage kiya", "YouTube video edit ki"]
        job = random.choice(jobs)

        cursor.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (earnings, str(ctx.author.id)))
        conn.commit()
        conn.close()

        await ctx.send(f"💼 {ctx.author.mention}, aapne **{job}** aur badle me aapko **🪙 {earnings}** coins mile!")

async def setup(bot):
    await bot.add_cog(EcoWork(bot))