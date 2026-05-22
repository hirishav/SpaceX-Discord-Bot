# cogs/mod_poll.py
import discord
from discord.ext import commands

class ModPoll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 10 dynamic number emojis ki list
        self.poll_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    @commands.command(name="poll")
    @commands.has_permissions(manage_messages=True)  # 🛡️ Manage Messages Perms
    async def poll(self, ctx, question: str = None, *options):
        """Server me dynamic options ke sath professional poll start karne ke liye."""
        
        if not question or len(options) < 2:
            embed_err = discord.Embed(
                title="❌ Galat Format!",
                description=f"Sahi tarika: `{ctx.prefix}poll \"Sawaal\" \"Option 1\" \"Option 2\" [Option 3] ...`",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed_err)

        if len(options) > 10:
            return await ctx.send("❌ Bhai, maximum 10 options hi daal sakte ho!")

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
        embed.set_footer(text=f"Poll started by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)

        poll_msg = await ctx.send(embed=embed)
        
        for index in range(len(options)):
            await poll_msg.add_reaction(self.poll_emojis[index])

        try:
            await ctx.message.delete()
        except Exception:
            pass

    # ==========================================
    # 🔥 YEH RAHA PIN COMMAND (Isko mat chhodna)
    # ==========================================
    @commands.command(name="pin")
    @commands.has_permissions(manage_messages=True)  # 🛡️ Sirf Manage Messages wale chalayein
    async def pin_message(self, ctx, message_id: int = None):
        """Kisi bhi message ko uski ID ke zariye instantly pin karne ke liye."""
        if not message_id:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}pin <message_id>`")

        try:
            # Channel se message uthao
            message = await ctx.channel.fetch_message(message_id)
            await message.pin() # Discord pin function trigger
            
            # Success notification
            embed = discord.Embed(
                description=f"📌 [This Message]({message.jump_url}) has been pinned successfully by {ctx.author.mention}.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
            try:
                await ctx.message.delete()
            except Exception:
                pass
                
        except discord.NotFound:
            await ctx.send("❌ Mujhe is channel me is ID ka koi message nahi mila!")
        except discord.Forbidden:
            await ctx.send("❌ Mere paas messages pin karne ki permission nahi hai server roles me!")
        except Exception as e:
            await ctx.send(f"❌ Error: `{e}`")

    # Error Handler
    @poll.error
    @pin_message.error
    async def mod_commands_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ **Permission Denied:** Is command ko chalane ke liye aapke paas `Manage Messages` permission honi chahiye!")

async def setup(bot):
    await bot.add_cog(ModPoll(bot))