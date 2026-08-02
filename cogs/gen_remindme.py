# cogs/gen_remindme.py
import discord
from discord.ext import commands
import asyncio

class GenRemindme(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="remindme")
    async def remindme(self, ctx, time_str: str = None, *, task: str = None):
        """Aapko kisi specific kaam ke liye ping karke yaad dilane ke liye."""
        if not time_str or not task:
            embed_err = discord.Embed(
                title="❌ Galat Format!",
                description=f"Sahi tarika: `{ctx.prefix}remindme <time><s/m/h> <work>`\n\n💡 **Examples:**\n👉 `{ctx.prefix}remindme 20m Padhne jana hai`\n👉 `{ctx.prefix}rm 1h Video edit karni hai`",
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
            description=f"Thik hai buddy, main aapko **{time_str}** baad yaad dila dunga.\n\n📌 **Task:** {task}",
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

        await asyncio.sleep(calculated_seconds)

        alert_embed = discord.Embed(
            title="🔔 REMINDER ALERT!",
            description=f"Hey <@{ctx.author.id}>, aapne ye yaad dilane ko bola tha:\n\n📝 **Kaam:** {task}",
            color=discord.Color.gold()
        )
        alert_embed.set_footer(text="SpaceX Reminder System", icon_url=self.bot.user.display_avatar.url)
        
        await ctx.send(content=f"<@{ctx.author.id}>", embed=alert_embed)

async def setup(bot):
    await bot.add_cog(GenRemindme(bot))