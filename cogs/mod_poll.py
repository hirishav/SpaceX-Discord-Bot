# cogs/mod_poll.py
import discord
from discord.ext import commands

class ModPoll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.poll_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    @commands.command(name="poll")
    @commands.has_permissions(manage_messages=True)  # 🛡️ Sirf Manage Messages perms
    async def poll(self, ctx, question: str = None, *options):
        """Server me dynamic options ke sath professional poll start karne ke liye."""
        
        if not question or len(options) < 2:
            embed_err = discord.Embed(
                title="❌ Galat Format!",
                description=f"Sahi tarika: `{ctx.prefix}poll \"Sawaal\" \"Option 1\" \"Option 2\" [Option 3] ...`",
                color=discord.Color.red()
            )
            embed_err.add_field(
                name="💡 Rules", 
                value="Sawaal aur saare options ko double quotes (`\" \"`) me likhein. Kam se kam 2 aur zyada se zyada 10 options allowed hain.", 
                inline=False
            )
            return await ctx.send(embed=embed_err)

        if len(options) > 10:
            return await ctx.send("❌ Bhai, maximum 10 options hi daal sakte ho ek baar me!")

        description_text = "### 🤔 " + question + "\n\n"
        for index, option in enumerate(options):
            description_text += f"{self.poll_emojis[index]} {option}\n\n"

        embed = discord.Embed(
            title="📊 SERVER OFFICIAL POLL",
            description=description_text,
            color=discord.Color.purple()
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text=f"Poll started by {ctx.author.name} • Vote niche karein!", icon_url=ctx.author.display_avatar.url)

        poll_msg = await ctx.send(embed=embed)
        
        for index in range(len(options)):
            await poll_msg.add_reaction(self.poll_emojis[index])

        try:
            await ctx.message.delete()
        except Exception:
            pass

    @poll.error
    async def poll_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            pass

async def setup(bot):
    await bot.add_cog(ModPoll(bot))