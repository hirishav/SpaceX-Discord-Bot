# cogs/eco_rob.py
import discord
from discord.ext import commands
import database as sqlite3
import random

class EcoRob(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "warnings.db"

    @commands.hybrid_command(name="rob", aliases=["steal"])
    @commands.cooldown(1, 10800, commands.BucketType.user)
    async def rob(self, ctx, member: discord.Member = None):
        """Kisi doosre user ke wallet se chori karne ke liye."""
        if not member:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}rob @user`")
        if member.id == ctx.author.id:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ Khud ke pocket se chori karoge kya?")

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
            ctx.command.reset_cooldown(ctx)
            conn.close()
            return await ctx.send(f"❌ {member.mention} pehle se hi bhikari hai, kam se kam wallet me 200 Specie toh hone chahiye lootne ke liye!")

        success = random.choice([True, False]) # 50% chance

        if success:
            stolen = random.randint(100, int(target_wallet * 0.5)) # Up to 50% of target cash
            cursor.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (stolen, str(ctx.author.id)))
            cursor.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (stolen, str(member.id)))
            await ctx.send(f"🥷 **Chori Kamyab!** {ctx.author.mention} ne chupke se {member.mention} ke pocket se **💠 {stolen}** Specie uda liye!")
        else:
            fine = random.randint(100, 300)
            if fine > author_wallet: fine = author_wallet
            cursor.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (fine, str(ctx.author.id)))
            cursor.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (fine, str(member.id)))
            await ctx.send(f"💥 **Chori Na-kamyab!** {ctx.author.mention}, {member.mention} ne aapko rrange hatho pakad liya aur fine ke taur par **💠 {fine}** aapse le liye!")

        conn.commit()
        conn.close()

    @rob.error
    async def rob_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            hours, remainder = divmod(int(error.retry_after), 3600)
            minutes, seconds = divmod(remainder, 60)
            time_left = ""
            if hours > 0: time_left += f"{hours}h "
            if minutes > 0: time_left += f"{minutes}m "
            time_left += f"{seconds}s"
            await ctx.send(f"⏳ {ctx.author.mention}, ruko bhai daka dalna itna aasan nhi! Try again after **{time_left}**.")
        else:
            raise error

async def setup(bot):
    await bot.add_cog(EcoRob(bot))