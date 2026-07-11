# cogs/mod_purge.py
import discord
from discord.ext import commands
import typing
import re

class ModPurge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="purge", aliases=["clean"])
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, target: typing.Union[discord.Member, discord.User, str, int] = None, amount: int = None):
        """Chat se messages filter karke delete karne ke liye."""
        
        # --- CASE 1: Agar user ne kuch bhi nahi daala ---
        if target is None:
            return await ctx.send(f"❌ Sahi tarika use karein bhai! \n👉 Normal Purge: `{ctx.prefix}purge <amount>`\n👉 Filter Bots: `{ctx.prefix}purge bots <amount>`\n👉 User Wise: `{ctx.prefix}purge @user/ID <amount>`\n👉 Filter Links: `{ctx.prefix}purge links <amount>`\n👉 Filter Attachments: `{ctx.prefix}purge images <amount>`\n👉 Keyword Content Match: `{ctx.prefix}purge word \"gaali\" <amount>`")

        # --- CASE 2: Normal Purge (!!purge 50) ---
        if isinstance(target, int) or (isinstance(target, str) and target.isdigit()):
            purge_amount = int(target)
            if purge_amount <= 0 or purge_amount > 100:
                return await ctx.send("❌ Kripya 1 se 100 ke beech me koi number daalein!")
            
            try: await ctx.message.delete()
            except Exception: pass
                
            deleted = await ctx.channel.purge(limit=purge_amount)
            return await ctx.send(f"🗑️ Kamyabi se **{len(deleted)}** normal messages saaf kar diye gaye hain!", delete_after=3)

        # Ab agar advanced routing checks chalte hain, toh amount check validation loop zaroori hai
        if amount is None:
            return await ctx.send("❌ Kripya filtered messages ki sankhya (amount) zaroor daalein! (Example: `!!purge links 20`)")

        if amount <= 0 or amount > 100:
            return await ctx.send("❌ Aap ek baar me maximum 100 filtered messages hi delete kar sakte hain!")

        try: await ctx.message.delete()
        except Exception: pass

        # --- CASE 3: Purge Bots (!!purge bots 20) ---
        if isinstance(target, str) and target.lower() == "bots":
            def is_bot(msg):
                return msg.author.bot

            deleted = await ctx.channel.purge(limit=1000, check=is_bot, bulk=True)
            actual_deleted = len(deleted) if len(deleted) <= amount else amount
            return await ctx.send(f"🤖 Kamyabi se chat history se **{actual_deleted} Bots ke messages** saaf kar diye gaye hain!", delete_after=4)

        # --- CASE 4: Purge Specific User (!!purge @user 50) ---
        if isinstance(target, (discord.Member, discord.User)):
            def is_user(msg):
                return msg.author.id == target.id

            deleted = await ctx.channel.purge(limit=1000, check=is_user, bulk=True)
            actual_deleted = len(deleted) if len(deleted) <= amount else amount
            return await ctx.send(f"👤 Kamyabi se chat history se **{target.name}** ke **{actual_deleted} messages** saaf kar diye gaye hain!", delete_after=4)

        # 🔥 --- CASE 5: Advanced Hyper-Filters Setup Matrix (Links, Images, Custom Words) ---
        target_str = str(target).lower().strip()

        if target_str == "links":
            def has_link(msg):
                # Regex mapping filters standard out explicit http/https urls
                return re.search(r'https?://[^\s]+', msg.content) is not None

            deleted = await ctx.channel.purge(limit=1000, check=has_link, bulk=True)
            actual_deleted = len(deleted) if len(deleted) <= amount else amount
            return await ctx.send(f"🔗 Kamyabi se chat history se **{actual_deleted} URL Links wale messages** saaf kar diye gaye hain!", delete_after=4)

        elif target_str in ["images", "files", "attachments", "pics"]:
            def has_file(msg):
                return len(msg.attachments) > 0 or len(msg.embeds) > 0

            deleted = await ctx.channel.purge(limit=1000, check=has_file, bulk=True)
            actual_deleted = len(deleted) if len(deleted) <= amount else amount
            return await ctx.send(f"🖼️ Kamyabi se chat history se **{actual_deleted} Photos/Files attachments** saaf kar diye gaye hain!", delete_after=4)

        elif target_str in ["word", "text", "match", "string"]:
            # Command pattern fetch text argument context sequence layout
            args = ctx.message.content.split()
            # Dynamic recovery check parameters extraction pattern matches
            keyword = ""
            try:
                # Extracts word wrapped inside internal text variables boundaries
                match = re.search(r'"([^"]*)"', ctx.message.content)
                if match: keyword = match.group(1).lower()
                else: keyword = args[2].lower()
            except Exception:
                return await ctx.send("❌ Word formatting context parse target parameters fail! Correct usage: `!!purge word \"gaali\" 20`")

            def has_word(msg):
                return keyword in msg.content.lower()

            deleted = await ctx.channel.purge(limit=1000, check=has_word, bulk=True)
            actual_deleted = len(deleted) if len(deleted) <= amount else amount
            return await ctx.send(f"🧼 Kamyabi se chat history se specific keyword **\"{keyword}\"** wale **{actual_deleted} messages** saaf kar diye gaye hain!", delete_after=4)

        return await ctx.send("❌ Galat command format! `!!help purge` check karein.")

    @purge.error
    async def purge_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Aapke paas `Manage Messages` permission nahi hai!")
        else:
            await ctx.send(f"❌ Kuch gadbad hui: {error}")

async def setup(bot):
    await bot.add_cog(ModPurge(bot))