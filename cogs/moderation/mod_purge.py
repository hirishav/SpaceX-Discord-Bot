# cogs/mod_purge.py
import discord
from discord.ext import commands
import typing
import re

class ModPurge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def do_purge(self, ctx, amount: int, check=None, success_msg: str=""):
        if amount <= 0 or amount > 100:
            return await ctx.send("❌ Kripya 1 se 100 ke beech me koi number daalein!")
        
        try: await ctx.message.delete()
        except Exception: pass
        
        deleted = []
        try:
            if check is None:
                deleted = await ctx.channel.purge(limit=amount)
            else:
                count = 0
                def internal_check(msg):
                    nonlocal count
                    if count >= amount:
                        return False
                    if check(msg):
                        count += 1
                        return True
                    return False
                
                deleted = await ctx.channel.purge(limit=1000, check=internal_check, bulk=True)
                
            await ctx.send(f"{success_msg.replace('{count}', str(len(deleted)))}", delete_after=5)
        except discord.Forbidden:
            await ctx.send("❌ Mere paas messages delete karne ki permission nahi hai! Kripya 'Manage Messages' permission check karein.")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Error deleting messages: {e}")

    @commands.hybrid_group(name="purge", aliases=["clean", "clear"], invoke_without_command=True)
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int = None):
        """Chat se messages saaf karne ke liye normal command."""
        if amount is None:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}purge <amount>` ya subcommands use karein like `{ctx.prefix}purge bots 50`\nHelp ke liye `{ctx.prefix}help purge` dekhein.")
        
        await self.do_purge(ctx, amount, None, "🗑️ Kamyabi se **{count}** normal messages saaf kar diye gaye hain!")

    @purge.command(name="text")
    @commands.has_permissions(manage_messages=True)
    async def purge_text(self, ctx, amount: int):
        """Purge text messages (no images, embeds, or links)"""
        def check(msg):
            has_link = re.search(r'https?://[^\s]+', msg.content)
            return len(msg.attachments) == 0 and len(msg.embeds) == 0 and not has_link
        await self.do_purge(ctx, amount, check, "📝 Kamyabi se **{count}** pure text messages saaf kar diye gaye hain!")

    @purge.command(name="humans", aliases=["human"])
    @commands.has_permissions(manage_messages=True)
    async def purge_humans(self, ctx, amount: int):
        """Purge messages sent only by humans"""
        await self.do_purge(ctx, amount, lambda msg: not msg.author.bot, "👤 Kamyabi se humans ke **{count}** messages saaf kar diye gaye hain!")

    @purge.command(name="bots", aliases=["bot"])
    @commands.has_permissions(manage_messages=True)
    async def purge_bots(self, ctx, amount: int):
        """Purge messages sent only by bots"""
        await self.do_purge(ctx, amount, lambda msg: msg.author.bot, "🤖 Kamyabi se bots ke **{count}** messages saaf kar diye gaye hain!")

    @purge.command(name="user")
    @commands.has_permissions(manage_messages=True)
    async def purge_user(self, ctx, user: typing.Union[discord.Member, discord.User], amount: int):
        """Purge messages from a specific user"""
        await self.do_purge(ctx, amount, lambda msg: msg.author.id == user.id, f"🎯 Kamyabi se **{user.name}** ke **{{count}}** messages saaf kar diye gaye hain!")

    @purge.command(name="images", aliases=["files", "attachments", "pics"])
    @commands.has_permissions(manage_messages=True)
    async def purge_images(self, ctx, amount: int):
        """Purge messages containing images or attachments"""
        def check(msg):
            return len(msg.attachments) > 0 or len(msg.embeds) > 0
        await self.do_purge(ctx, amount, check, "🖼️ Kamyabi se **{count}** photo/file attachments saaf kar diye gaye hain!")

    @purge.command(name="links", aliases=["urls", "link"])
    @commands.has_permissions(manage_messages=True)
    async def purge_links(self, ctx, amount: int):
        """Purge messages containing HTTP/HTTPS links"""
        def check(msg):
            return re.search(r'https?://[^\s]+', msg.content) is not None
        await self.do_purge(ctx, amount, check, "🔗 Kamyabi se **{count}** URL links wale messages saaf kar diye gaye hain!")

    @purge.command(name="startswith")
    @commands.has_permissions(manage_messages=True)
    async def purge_startswith(self, ctx, word: str, amount: int):
        """Purge messages starting with a specific word"""
        keyword = word.lower()
        await self.do_purge(ctx, amount, lambda msg: msg.content.lower().startswith(keyword), f"🧼 Kamyabi se **\"{word}\"** se shuru hone wale **{{count}}** messages saaf kar diye gaye hain!")

    @purge.command(name="endswith")
    @commands.has_permissions(manage_messages=True)
    async def purge_endswith(self, ctx, word: str, amount: int):
        """Purge messages ending with a specific word"""
        keyword = word.lower()
        await self.do_purge(ctx, amount, lambda msg: msg.content.lower().endswith(keyword), f"🧼 Kamyabi se **\"{word}\"** par khatam hone wale **{{count}}** messages saaf kar diye gaye hain!")

    @purge.command(name="match", aliases=["word", "contains"])
    @commands.has_permissions(manage_messages=True)
    async def purge_match(self, ctx, word: str, amount: int):
        """Purge messages matching or containing a specific word"""
        keyword = word.lower()
        await self.do_purge(ctx, amount, lambda msg: keyword in msg.content.lower(), f"🧼 Kamyabi se **\"{word}\"** keyword wale **{{count}}** messages saaf kar diye gaye hain!")

    @purge.error
    @purge_text.error
    @purge_humans.error
    @purge_bots.error
    @purge_user.error
    @purge_images.error
    @purge_links.error
    @purge_startswith.error
    @purge_endswith.error
    @purge_match.error
    async def purge_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            pass
        elif isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Galat usage! Kripya command ka format check karein: `{ctx.prefix}help purge`")
        else:
            await ctx.send(f"❌ Kuch gadbad hui: {error}")

async def setup(bot):
    await bot.add_cog(ModPurge(bot))