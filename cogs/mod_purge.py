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
        """Chat se messages filter karke delete karne ke liye.
        Usage: 
        !!purge 50 -> Last 50 normal messages
        !!purge bots 50 -> Last 50 me se sirf bots ke messages
        !!purge @user 50 -> Last 50 me se sirf us user ke messages
        """
        
        # --- CASE 1: Agar user ne sirf !!purge daala bina kisi argument ke ---
        if target is None:
            return await ctx.send(f"❌ Sahi tarika use karein bhai! \n`{ctx.prefix}purge <amount>`\n`{ctx.prefix}purge bots <amount>`\n`{ctx.prefix}purge @user/ID <amount>`")

        # --- CASE 2: Normal Purge (!!purge 50) ---
        # Agar pehla argument hi number hai, toh target hi hamara amount ban jayega
        if isinstance(target, int) or (isinstance(target, str) and target.isdigit()):
            purge_amount = int(target)
            if purge_amount <= 0 or purge_amount > 100:
                return await ctx.send("❌ Kripya 1 se 100 ke beech me koi number daalein!")
            
            await ctx.message.delete() # Mod ka command delete karo
            deleted = await ctx.channel.purge(limit=purge_amount)
            return await ctx.send(f"🗑️ Kamyabi se **{len(deleted)}** normal messages saaf kar diye gaye hain!", delete_after=3)

        # Agar target string ya user hai, toh amount ka hona zaroori hai (e.g., !!purge bots 50)
        if amount is None:
            return await ctx.send("❌ Kripya messages ki sankhya (amount) zaroor daalein! (Example: `!!purge bots 20`)")

        if amount <= 0 or amount > 100:
            return await ctx.send("❌ Aap ek baar me maximum 100 messages ke andar hi filter kar sakte hain!")

        # Mod ka command message pehle hi delete kar dete hain
        await ctx.message.delete()

        # --- CASE 3: Purge Bots (!!purge bots 50) ---
        if isinstance(target, str) and target.lower() == "bots":
            # Filter function: Jo sirf bots ke messages pakdega
            def is_bot(msg):
                return msg.author.bot

            deleted = await ctx.channel.purge(limit=amount, check=is_bot)
            return await ctx.send(f"🤖 Kamyabi se pichle {amount} messages me se saare **{len(deleted)} Bots ke messages** saaf kar diye gaye hain!", delete_after=4)

        # --- CASE 4: Purge Specific User (!!purge @user 50 ya !!purge ID 50) ---
        # Agar target discord.Member ya User object hai
        if isinstance(target, (discord.Member, discord.User)):
            def is_user(msg):
                return msg.author.id == target.id

            deleted = await ctx.channel.purge(limit=amount, check=is_user)
            return await ctx.send(f"👤 Kamyabi se pichle {amount} messages me se **{target.name}** ke saare **{len(deleted)} messages** saaf kar diye gaye hain!", delete_after=4)

        # Agar upar waala koi bhi case match na kare
        await ctx.send("❌ Galat command format! `!!help purge` check karein.")

    @purge.error
    async def purge_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Aapke paas `Manage Messages` permission nahi hai!")
        else:
            await ctx.send(f"❌ Kuch gadbad hui: {error}")

async def setup(bot):
    await bot.add_cog(ModPurge(bot))