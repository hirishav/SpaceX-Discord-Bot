# cogs/eco_slut.py
import discord
from discord.ext import commands
import sqlite3
import random
import asyncio

class EcoSlut(commands.Cog):
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
                msg = await ctx.send(f"⏳ {ctx.author.mention}, sabr rkho! Try again after **{int(remaining)} seconds**.")
                while remaining > 0:
                    await asyncio.sleep(1)
                    remaining = self.cooldowns[user_id] - asyncio.get_event_loop().time()
                    if remaining <= 0: break
                    try: await msg.edit(content=f"⏳ {ctx.author.mention}, sabr rkho! Try again after **{int(remaining)} seconds**.")
                    except discord.NotFound: return False
                try: await msg.delete()
                except discord.NotFound: pass
                return False
        self.cooldowns[user_id] = current_time + 30
        return True

    @commands.command(name="slut")
    async def slut(self, ctx):
        """Risky tareeqon se paise kamane ke liye."""
        if not await self.handle_cooldown(ctx): return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO economy (user_id, wallet, bank) VALUES (?, 0, 0)", (str(ctx.author.id),))
        
        # Get wallet balance for fine checking
        cursor.execute("SELECT wallet FROM economy WHERE user_id = ?", (str(ctx.author.id),))
        wallet = cursor.fetchone()[0]

        success = random.choice([True, True, False]) # 66% chance success
        
        if success:
            earnings = random.randint(200, 800)
            cursor.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (earnings, str(ctx.author.id)))
            await ctx.send(f"💋 {ctx.author.mention}, aapne raste par ameer logon ko thoda entertain kiya aur **🪙 {earnings}** jhatak liye!")
        else:
            fine = random.randint(150, 400)
            if fine > wallet: fine = wallet
            cursor.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (fine, str(ctx.author.id)))
            await ctx.send(f"📸 {ctx.author.mention}, aap saste kamo me pakde gaye! Police ne aap par **🪙 {fine}** ka fine thok diya! 💀")

        conn.commit()
        conn.close()

async def setup(bot):
    await bot.add_cog(EcoSlut(bot))