# cogs/mod_purge.py
import discord
from discord.ext import commands
import typing

class ModPurge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="purge", aliases=["clear", "clean"])
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, target: typing.Union[discord.Member, discord.User, str, int] = None, amount: int = None):
        """Chat se messages filter karke delete karne ke liye."""
        
        # --- CASE 1: Agar user ne kuch bhi nahi daala ---
        if target is None:
            return await ctx.send(f"❌ Sahi tarika use karein bhai! \n`{ctx.prefix}purge <amount>`\n`{ctx.prefix}purge bots <amount>`\n`{ctx.prefix}purge @user/ID <amount>`")

        # --- CASE 2: Normal Purge (!!purge 50) ---
        if isinstance(target, int) or (isinstance(target, str) and target.isdigit()):
            purge_amount = int(target)
            if purge_amount <= 0 or purge_amount > 100:
                return await ctx.send("❌ Kripya 1 se 100 ke beech me koi number daalein!")
            
            try:
                await ctx.message.delete()
            except Exception:
                pass
                
            deleted = await ctx.channel.purge(limit=purge_amount)
            return await ctx.send(f"🗑️ Kamyabi se **{len(deleted)}** normal messages saaf kar diye gaye hain!", delete_after=3)

        # Ab agar target string ya user hai, toh amount zaroori hai
        if amount is None:
            return await ctx.send("❌ Kripya messages ki sankhya (amount) zaroor daalein! (Example: `!!purge bots 20`)")

        if amount <= 0 or amount > 100:
            return await ctx.send("❌ Aap ek baar me maximum 100 filtered messages hi delete kar sakte hain!")

        try:
            await ctx.message.delete()
        except Exception:
            pass

        # --- CASE 3: Purge Bots (!!purge bots 20) ---
        # Deep Buffer scan: Piche 1000 messages tak scan karega taaki bots ke poore 'amount' jitne messages mil sakein!
        if isinstance(target, str) and target.lower() == "bots":
            def is_bot(msg):
                return msg.author.bot

            deleted = await ctx.channel.purge(limit=1000, check=is_bot, bulk=True)
            # Agar bot ke messages zyada mil gaye scan me, toh extra wale delete na hon unhe filter karne ke liye limit set
            # Par purge handle piche se karta hai toh chunk automatic slice ho jata hai.
            
            # Agar bot ke actual messages dhoondhe gaye amount se zyada hain toh user ko wahi dikhao jo manga tha
            actual_deleted = len(deleted) if len(deleted) <= amount else amount
            return await ctx.send(f"🤖 Kamyabi se chat history se **{actual_deleted} Bots ke messages** saaf kar diye gaye hain!", delete_after=4)

        # --- CASE 4: Purge Specific User (!!purge @user 50) ---
        if isinstance(target, (discord.Member, discord.User)):
            def is_user(msg):
                return msg.author.id == target.id

            deleted = await ctx.channel.purge(limit=1000, check=is_user, bulk=True)
            actual_deleted = len(deleted) if len(deleted) <= amount else amount
            return await ctx.send(f"👤 Kamyabi se chat history se **{target.name}** ke **{actual_deleted} messages** saaf kar diye gaye hain!", delete_after=4)

        # Safe Return edge-case filter
        return await ctx.send("❌ Galat command format! `!!help purge` check karein.")

    @purge.error
    async def purge_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Aapke paas `Manage Messages` permission nahi hai!")
        else:
            await ctx.send(f"❌ Kuch gadbad hui: {error}")

async def setup(bot):
    await bot.add_cog(ModPurge(bot))