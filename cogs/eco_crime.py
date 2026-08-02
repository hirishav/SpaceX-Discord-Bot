# cogs/eco_crime.py
import discord
from discord.ext import commands
import sqlite3
import random
import asyncio

class EcoCrime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "warnings.db"
        self.cooldowns = {}

    async def handle_cooldown(self, ctx):
        user_id = ctx.author.id
        current_time = asyncio.get_event_loop().time()
        if user_id in self.cooldowns:
            remaining = self.cooldowns[user_id] - current_time
            if remaining > 0:
                msg = await ctx.send(f"⏳ {ctx.author.mention}, police dhoond rhi hai! Try again after **{int(remaining)} seconds**.")
                while remaining > 0:
                    await asyncio.sleep(1)
                    remaining = self.cooldowns[user_id] - asyncio.get_event_loop().time()
                    if remaining <= 0: break
                    try: await msg.edit(content=f"⏳ {ctx.author.mention}, police dhoond rhi hai! Try again after **{int(remaining)} seconds**.")
                    except discord.NotFound: return False
                try: await msg.delete()
                except discord.NotFound: pass
                return False
        self.cooldowns[user_id] = current_time + 30
        return True

    @commands.command(name="crime")
    async def crime(self, ctx):
        """High-risk, High-reward illegal kaam!"""
        if not await self.handle_cooldown(ctx): return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO economy (user_id, wallet, bank) VALUES (?, 0, 0)", (str(ctx.author.id),))
        
        cursor.execute("SELECT wallet FROM economy WHERE user_id = ?", (str(ctx.author.id),))
        wallet = cursor.fetchone()[0]

        success = random.choice([True, False, False]) # 33% chance success
        
        if success:
            earnings = random.randint(500, 1500)
            cursor.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (earnings, str(ctx.author.id)))
            await ctx.send(f"🥷 {ctx.author.mention}, aapne bank loot liya aur chupke se **🪙 {earnings}** uda le gye! Pura master-mind lagaya!")
        else:
            fine = random.randint(400, 1000)
            if fine > wallet: fine = wallet
            cursor.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (fine, str(ctx.author.id)))
            await ctx.send(f"🚨 {ctx.author.mention}, ATM ukhadte waqt alarm baj gya! Aapko bhaari fine bharna pada: **🪙 {fine}**! 💀")

        conn.commit()
        conn.close()

async def setup(bot):
    await bot.add_cog(EcoCrime(bot))