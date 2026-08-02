# cogs/owner_maintenance.py
import discord
from discord.ext import commands
import time
import asyncio

class OwnerMaintenance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="maintenance", aliases=["mm"])
    @commands.is_owner()
    async def maintenance(self, ctx, duration_str: str = None):
        """Bot ko global maintenance lockdown engine par lagane ke liye."""
        
        # Turn off status handler trigger
        if duration_str == "0" or (duration_str and duration_str.lower() == "off"):
            if not self.bot.maintenance_mode:
                return await ctx.send("❌ Bot pehle se hi normal mode par chal raha hai bhai!")
            
            self.bot.maintenance_mode = False
            self.bot.maintenance_end = 0
            await ctx.send("✅ **Maintenance Manual Override:** Bot ko online mode par shift kiya jaa raha hai...")
            await self.notify_users()
            return

        if not duration_str:
            return await ctx.send(f"❌ Sahi format: `{ctx.prefix}maintenance <30s/1m/2h>`\n👉 Band karne ke liye: `{ctx.prefix}maintenance off`")

        # Time layout converter parser matrix
        time_multipliers = {'s': 1, 'm': 60, 'h': 3600}
        unit = ""
        digits = ""
        for char in duration_str:
            if char.isdigit():
                digits += char
            else:
                unit += char

        if not digits:
            return await ctx.send("❌ Time value proper specify karo! Example: `30s`, `45m`, `2h`.")

        amount = int(digits)
        unit = unit.lower() if unit else 'm'

        if unit not in time_multipliers:
            return await ctx.send("❌ Galat format! Format limits: `s` (seconds), `m` (minutes), `h` (hours).")

        calculated_seconds = amount * time_multipliers[unit]
        
        # Globals loading parameters register tracking
        self.bot.maintenance_mode = True
        self.bot.maintenance_end = int(time.time()) + calculated_seconds
        self.bot.interrupted_users = {} # Reset metrics logs queue

        await ctx.send(f"🚨 **GLOBAL LOCKDOWN:** Bot ko **{duration_str}** ke liye Maintenance Mode par daal diya gaya hai!")
        
        # Run notification execution trigger loop handler thread background asynchronously
        self.bot.loop.create_task(self.maintenance_timer_check(calculated_seconds))

    async def maintenance_timer_check(self, delay):
        await asyncio.sleep(delay)
        if self.bot.maintenance_mode and int(time.time()) >= self.bot.maintenance_end:
            self.bot.maintenance_mode = False
            self.bot.maintenance_end = 0
            await self.notify_users()

    async def notify_users(self):
        if not self.bot.interrupted_users:
            return

        # Local cache clone tracking target fields
        targets = dict(self.bot.interrupted_users)
        self.bot.interrupted_users = {}

        print(f"-> Sending dynamic recovery notifications to {len(targets)} active profiles...")
        
        for user_id, channel_id in targets.items():
            try:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    embed = discord.Embed(
                        title="🚀 We Are Back Online!",
                        description=f"<@{user_id}> Abhi aap aaram se bot ko bina kisi dikkat ke istemaal kar sakte hain.\n\n*Sorry for the inconvenience caused! Thank you for waiting.* ✨",
                        color=discord.Color.green()
                    )
                    await channel.send(content=f"<@{user_id}>", embed=embed)
                    await asyncio.sleep(0.5) # Anti spam rate limits check protection filter
            except Exception:
                continue

async def setup(bot):
    await bot.add_cog(OwnerMaintenance(bot))