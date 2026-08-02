# cogs/owner_spam.py
import discord
from discord.ext import commands
import asyncio

class OwnerSpam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="spam", hidden=True)
    @commands.is_owner() # 🔥 STRICT LOCK: Sirf Rishav bhai (Owner) hi chala sakte hain!
    async def owner_spam_command(self, ctx, channel: discord.TextChannel = None, amount: int = None, *, message_content: str = None):
        """👑 STRICT OWNER ONLY: Server ke kisi bhi channel me specified amount me fast spamming karne ke liye."""
        
        # --- CASE 1: Sahi formatting check matrix ---
        if not channel or not amount or not message_content:
            return await ctx.send(f"❌ Sahi tarika use karein Rishav bhai! \n👉 `{ctx.prefix}spam #channel <amount> <message>`\nExample: `{ctx.prefix}spam #general 50 Hello @User`")

        # --- CASE 2: Maximum Boundary Cap Safety ---
        if amount <= 0:
            return await ctx.send("❌ Amount 1 ya usse zyada hona chahiye bhai!")
            
        if amount > 150:
            return await ctx.send("🚨 Safety Alert! Ek baar me maximum 150 messages hi spam karein taaki Discord bot ko ban na kare.")

        # Delete the trigger command to keep it clean and stealthy
        try:
            await ctx.message.delete()
        except Exception:
            pass

        # Trigger message verification feedback in owner's DM or channel context execution
        # Hum log loop chala kar messages matrix fire karenge
        for i in range(amount):
            try:
                await channel.send(message_content)
                # 🔥 DISCORD API RATE LIMIT PROTECTION: 
                # 0.3 seconds ka delay pure sequence ko smooth rakhega aur speed bhi bullet jaisi aayegi!
                await asyncio.sleep(0.3)
            except discord.Forbidden:
                # Agar bot ke paas us channel me message bhejne ki perm nahi hai
                return await ctx.author.send(f"❌ Target channel {channel.mention} me mere paas permissions nahi hain bhai!")
            except Exception as e:
                return await ctx.author.send(f"❌ Spamming loop interrupted: {e}")

    @owner_spam_command.error
    async def spam_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("❌ **Access Denied!** Yeh ek highly destructive Owner-Only command hai. Aapke bas ki baat nahi hai launde! 😉")
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send("❌ Mujhe wo channel server me nahi mila bhai. Sahi se mention (#channel) karein.")

async def setup(bot):
    await bot.add_cog(OwnerSpam(bot))