# cogs/mod_lockdown.py
import discord
from discord.ext import commands

class ModLockdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="lockdown")
    @commands.has_permissions(manage_guild=True) # Sirf badw admins ke liye (Manage Server)
    async def lockdown(self, ctx, status: str = None):
        """Poore server ke saare text channels ko ek sath lock/unlock karne ke liye (!!lockdown / !!lockdown off)"""
        if status is None:
            # Emergency Lock lagana
            await ctx.send("🚨 **SERVER LOCKDOWN STARTED!** Saare channels freeze kiye jaa rahe hain, kripya thoda wait karein...")
            
            locked_count = 0
            for channel in ctx.guild.text_channels:
                overwrite = channel.overwrites_for(ctx.guild.default_role)
                if overwrite.send_messages is not False:
                    try:
                        overwrite.send_messages = False
                        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Server Lockdown by {ctx.author.name}")
                        locked_count += 1
                    except Exception:
                        continue
            
            embed = discord.Embed(
                title="🚨 SERVER UNDER LOCKDOWN",
                description=f"Server ke total **{locked_count}** text channels ko freeze kar diya gaya hai due to emergency.",
                color=discord.Color.dark_red()
            )
            embed.set_footer(text=f"Action taken by {ctx.author.name}")
            await ctx.send(embed=embed)

        elif status.lower() == "off":
            # Lockdown hatana
            await ctx.send("🔓 **SERVER LOCKDOWN LIFTING!** Saare channels restore kiye jaa rahe hain...")
            
            unlocked_count = 0
            for channel in ctx.guild.text_channels:
                overwrite = channel.overwrites_for(ctx.guild.default_role)
                if overwrite.send_messages is False:
                    try:
                        overwrite.send_messages = None
                        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Lockdown lifted by {ctx.author.name}")
                        unlocked_count += 1
                    except Exception:
                        continue

            embed = discord.Embed(
                title="🔓 LOCKDOWN LIFTED",
                description=f"Server ke **{unlocked_count}** channels wapas normal kar diye gaye hain. Members ab chat kar sakte hain!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ Galat format bhai! Sahi upaye: `{ctx.prefix}lockdown` (Chalu karne ke liye) ya `{ctx.prefix}lockdown off` (Band karne ke liye).")

async def setup(bot):
    await bot.add_cog(ModLockdown(bot))