# cogs/gen_remindme.py
import discord
from discord.ext import commands
import asyncio
import time

class GenRemindme(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_reminders = {}

    @commands.hybrid_command(name="remindme")
    async def remindme(self, ctx, time_str: str = None, *, task: str = None):
        """Aapko kisi specific kaam ke liye ping karke yaad dilane ke liye."""
        
        if not time_str and not task:
            user_reminders = self.active_reminders.get(ctx.author.id, [])
            if not user_reminders:
                embed = discord.Embed(
                    title="📝 Active Reminders",
                    description=f"Aapka koi bhi active reminder nahi hai.\nReminder set karne ke liye: `{ctx.prefix or '/'}remindme <time> <task>`",
                    color=discord.Color.red()
                )
                return await ctx.send(embed=embed)
            
            description = ""
            current_time = time.time()
            valid_reminders = []
            
            for idx, rem in enumerate(user_reminders, 1):
                remaining = int(rem['end_time'] - current_time)
                if remaining > 0:
                    valid_reminders.append(rem)
                    description += f"**{len(valid_reminders)}.** {rem['task']} (in <t:{int(rem['end_time'])}:R>)\n"
            
            if not description:
                description = "Aapka koi bhi active reminder nahi hai."
                
            embed = discord.Embed(
                title="📝 Aapke Active Reminders",
                description=description,
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed)

        if not time_str or not task:
            embed_err = discord.Embed(
                title="❌ Galat Format!",
                description=f"Sahi tarika: `{ctx.prefix or '/'}remindme <time><s/m/h> <work>`\n\n💡 **Examples:**\n👉 `{ctx.prefix or '/'}remindme 20m Padhne jana hai`\n👉 `{ctx.prefix or '/'}rm 1h Video edit karni hai`",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed_err)

        time_multipliers = {'s': 1, 'm': 60, 'h': 3600}
        unit = ""
        digits = ""
        
        for char in time_str:
            if char.isdigit():
                digits += char
            else:
                unit += char

        if not digits:
            return await ctx.send("❌ Bhai, time sahi se specify karo! (Example: `10s`, `20m`, `2h`) ⏰")

        amount = int(digits)
        unit = unit.lower() if unit else 'm'

        if unit not in time_multipliers:
            return await ctx.send("❌ Galat time unit! Sirf `s`, `m`, aur `h` allowed hain.")

        calculated_seconds = amount * time_multipliers[unit]

        embed = discord.Embed(
            title="⏰ Reminder Set Successfully!",
            description=f"Done bhai! Main tujhe **{time_str}** baad pakka yaad dila dunga.\n\n📌 **Kaam:** {task}",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

        end_time = time.time() + calculated_seconds
        reminder_obj = {'task': task, 'end_time': end_time}
        
        if ctx.author.id not in self.active_reminders:
            self.active_reminders[ctx.author.id] = []
        self.active_reminders[ctx.author.id].append(reminder_obj)

        await asyncio.sleep(calculated_seconds)

        if ctx.author.id in self.active_reminders and reminder_obj in self.active_reminders[ctx.author.id]:
            self.active_reminders[ctx.author.id].remove(reminder_obj)

        alert_embed = discord.Embed(
            title="🔔 REMINDER ALERT!",
            description=f"Hey <@{ctx.author.id}>, aapne ye yaad dilane ko bola tha:\n\n📝 **Kaam:** {task}",
            color=discord.Color.gold()
        )
        alert_embed.set_footer(text="SpaceX Reminder System", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.send(content=f"<@{ctx.author.id}>", embed=alert_embed)

async def setup(bot):
    await bot.add_cog(GenRemindme(bot))