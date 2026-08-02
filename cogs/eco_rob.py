# cogs/eco_rob.py
import discord
from discord.ext import commands
import sqlite3
import random
import asyncio

class EcoRob(commands.Cog):
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
                msg = await ctx.send(f"⏳ {ctx.author.mention}, ruko bhai daka dalna itna aasan nhi! Try again after **{int(remaining)} seconds**.")
                while remaining > 0:
                    await asyncio.sleep(1)
                    remaining = self.cooldowns[user_id] - asyncio.get_event_loop().time()
                    if remaining <= 0: break
                    try: await msg.edit(content=f"⏳ {ctx.author.mention}, ruko bhai daka dalna itna aasan nhi! Try again after **{int(remaining)} seconds**.")
                    except discord.NotFound: return False
                try: await msg.delete()
                except discord.NotFound: pass
                return False
        self.cooldowns[user_id] = current_time + 30
        return True

    @commands.command(name="rob", aliases=["steal"])
    async def rob(self, ctx, member: discord.Member = None):
        """Kisi doosre user ke wallet se chori karne ke liye."""
        if not member:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}rob @user`")
        if member.id == ctx.author.id:
            return await ctx.send("❌ Khud ke pocket se chori karoge kya?")

        if not await self.handle_cooldown(ctx): return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Both user balance fetching
        cursor.execute("INSERT OR IGNORE INTO economy (user_id, wallet, bank) VALUES (?, 0, 0)", (str(ctx.author.id),))
        cursor.execute("INSERT OR IGNORE INTO economy (user_id, wallet, bank) VALUES (?, 0, 0)", (str(member.id),))
        
        cursor.execute("SELECT wallet FROM economy WHERE user_id = ?", (str(ctx.author.id),))
        author_wallet = cursor.fetchone()[0]
        
        cursor.execute("SELECT wallet FROM economy WHERE user_id = ?", (str(member.id),))
        target_wallet = cursor.fetchone()[0]

        if target_wallet < 200:
            # Revert cooldown because act didn't happen
            self.cooldowns[ctx.author.id] = 0
            conn.close()
            return await ctx.send(f"❌ {member.mention} pehle se hi bhikari hai, kam se kam wallet me 200 coins toh hone chahiye lootne ke liye!")

        success = random.choice([True, False]) # 50% chance

        if success:
            stolen = random.randint(100, int(target_wallet * 0.5)) # Up to 50% of target cash
            cursor.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (stolen, str(ctx.author.id)))
            cursor.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (stolen, str(member.id)))
            await ctx.send(f"🥷 **Chori Kamyab!** {ctx.author.mention} ne chupke se {member.mention} ke pocket se **🪙 {stolen}** coins uda liye!")
        else:
            fine = random.randint(100, 300)
            if fine > author_wallet: fine = author_wallet
            cursor.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (fine, str(ctx.author.id)))
            cursor.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (fine, str(member.id)))
            await ctx.send(f"💥 **Chori Na-kamyab!** {ctx.author.mention}, {member.mention} ne aapko rrange hatho pakad liya aur fine ke taur par **🪙 {fine}** aapse le liye!")

        conn.commit()
        conn.close()

async def setup(bot):
    await bot.add_cog(EcoRob(bot))