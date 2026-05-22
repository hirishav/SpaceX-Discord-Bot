# cogs/mod_poll.py
import discord
from discord.ext import commands

class ModPoll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="poll")
    @commands.has_permissions(manage_messages=True)  # 🛡️ Sirf Manage Messages perms wale chala payenge
    async def poll(self, ctx, question: str = None, option1: str = None, option2: str = None):
        """Server me automatic reactions ke sath professional poll start karne ke liye."""
        
        # Validation Check: Agar parameters missing hain
        if not question or not option1 or not option2:
            embed_err = discord.Embed(
                title="❌ Galat Format!",
                description=f"Sahi tarika: `{ctx.prefix}poll \"Sawaal\" \"Option 1\" \"Option 2\"`",
                color=discord.Color.red()
            )
            embed_err.add_field(
                name="💡 Important Note", 
                value="Sawaal aur dono options ko double quotes (`\" \"`) ke andar likhna zaroori hai taaki bot unhe alag samajh sake.", 
                inline=False
            )
            embed_err.add_field(
                name="👉 Example", 
                value=f'{ctx.prefix}poll "Aaj konsa game khele?" "Valorant" "GTA V"', 
                inline=False
            )
            return await ctx.send(embed=embed_err)

        # Poll Embed Generation
        embed = discord.Embed(
            title="📊 SERVER OFFICIAL POLL",
            description=f"### 🤔 {question}\n\n1️⃣ {option1}\n\n2️⃣ {option2}",
            color=discord.Color.purple()
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text=f"Poll started by {ctx.author.name} • Vote niche karein!", icon_url=ctx.author.display_avatar.url)

        # Message send karke reactions add karna
        poll_msg = await ctx.send(embed=embed)
        
        await poll_msg.add_reaction("1️⃣")
        await poll_msg.add_reaction("2️⃣")

        # Command trigger message ko delete karna clean look ke liye
        try:
            await ctx.message.delete()
        except Exception:
            pass

    # Error Handler: Agar kisi ke paas permission nahi hai
    @poll.error
    async def poll_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ **Permission Denied:** Is command ko use karne ke liye aapke paas `Manage Messages` permission honi chahiye!")

async def setup(bot):
    await bot.add_cog(ModPoll(bot))