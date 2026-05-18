# cogs/mod_lock.py
import discord
from discord.ext import commands
import asyncio

class ModLock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def parse_time(self, time_str: str):
        """Time string (30m, 1h, 10s) ko seconds me convert karne ke liye."""
        if not time_str: return None
        try:
            unit = time_str[-1].lower()
            amount = int(time_str[:-1])
            if unit == 's': return amount
            elif unit == 'm': return amount * 60
            elif unit == 'h': return amount * 3600
        except Exception:
            return None
        return None

    @commands.command(name="lock", aliases=["freeze"])
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx, channel: discord.TextChannel = None, time_str: str = None, *, reason: str = "No reason provided"):
        """Kisi channel ko timer aur reason ke sath lock karne ke liye (!!lock #channel 30m Spamming!)"""
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)

        if overwrite.send_messages is False:
            return await ctx.send(f"🔒 {channel.mention} pehle se hi locked hai!")

        duration = self.parse_time(time_str) if time_str else None

        try:
            overwrite.send_messages = False
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Locked by {ctx.author.name}")

            embed = discord.Embed(title="🔒 Channel Locked", color=discord.Color.red())
            embed.add_field(name="📺 Channel", value=channel.mention, inline=True)
            embed.add_field(name="🛡️ Staff", value=ctx.author.mention, inline=True)
            embed.add_field(name="⏱️ Duration", value=f"`{time_str}`" if time_str else "`Permanent`", inline=True)
            embed.add_field(name="📝 Reason", value=reason, inline=False)
            await ctx.send(embed=embed)

            try: await ctx.message.delete()
            except Exception: pass

            # Agar timer lagaya hai toh auto-unlock logic trigger hoga
            if duration:
                await asyncio.sleep(duration)
                # Fresh overwrite status check karenge check karne ke liye ki bich me manually unlock toh nahi hua
                fresh_overwrite = channel.overwrites_for(ctx.guild.default_role)
                if fresh_overwrite.send_messages is False:
                    fresh_overwrite.send_messages = None
                    await channel.set_permissions(ctx.guild.default_role, overwrite=fresh_overwrite, reason="Auto-Unlocked by Timer")
                    await channel.send("🔓 **Timer khatam!** Yeh channel automatic unlock ho gaya hai.")

        except discord.Forbidden:
            await ctx.send("❌ Mere paas permissions nahi hain!")

    @commands.command(name="unlock")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """Channel ko manually unlock karne ke liye."""
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)

        if overwrite.send_messages is not False:
            return await ctx.send(f"🔓 {channel.mention} pehle se hi unlocked hai!")

        try:
            overwrite.send_messages = None # None karne se default permissions par chala jata hai
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Unlocked by {ctx.author.name}")
            await ctx.send(f"🔓 {channel.mention} ko officially unlock kar diya gaya hai!")
        except discord.Forbidden:
            await ctx.send("❌ Permissions check kijiye!")

async def setup(bot):
    await bot.add_cog(ModLock(bot))