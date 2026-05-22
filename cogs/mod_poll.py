# cogs/mod_poll.py
import discord
from discord.ext import commands

class ModPoll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 10 dynamic number emojis ki matrix layout
        self.poll_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    @commands.command(name="poll")
    @commands.has_permissions(manage_messages=True)  # 🛡️ Sirf Manage Messages perms
    async def poll(self, ctx, question: str = None, *options):
        """Server me dynamic options ke sath professional poll start karne ke liye."""
        
        # Validation 1: Agar sawaal ya kam se kam 2 options na hon
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
            embed_err.add_field(
                name="👉 Example", 
                value=f'{ctx.prefix}poll "Konsa frame rate best hai?" "60 FPS" "90 FPS" "120 FPS"', 
                inline=False
            )
            return await ctx.send(embed=embed_err)

        # Validation 2: Discord standard reaction limits logic handler
        if len(options) > 10:
            return await ctx.send("❌ Bhai, maximum 10 options hi daal sakte ho ek baar me!")

        # Dynamic Description Matrix builder loop
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
        
        # Jitne options hain, utne hi dynamic reactions add karo
        for index in range(len(options)):
            await poll_msg.add_reaction(self.poll_emojis[index])

        # Delete trigger chat text
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @commands.command(name="pin")
    @commands.has_permissions(manage_messages=True)  # 🛡️ Lock to moderator perms
    async def pin_message(self, ctx, message_id: int = None):
        """Kisi bhi message ko uski ID ke zariye instantly pin karne ke liye."""
        if not message_id:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}pin <message_id>`")

        try:
            # Current channel se message fetch karo
            message = await ctx.channel.fetch_message(message_id)
            await message.pin()
            
            # Dynamic notice alert card popup
            embed = discord.Embed(
                description=f"📌 [This Message]({message.jump_url}) has been pinned successfully by {ctx.author.mention}.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
            # Moderator command msg cleanup
            try:
                await ctx.message.delete()
            except Exception:
                pass
                
        except discord.NotFound:
            await ctx.send("❌ Mujhe is channel me is ID ka koi message nahi mila! ID sahi daalo.")
        except discord.Forbidden:
            await ctx.send("❌ Mere paas messages pin karne ki explicit permissions nahi hain server roles me!")
        except Exception as e:
            await ctx.send(f"❌ Kuch gadbad hui: `{e}`")

    # Error Handler for overall Cog
    @poll.error
    @pin_message.error
    async def mod_commands_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ **Permission Denied:** Aapke paas is command ko chalane ke liye `Manage Messages` permission honi chahiye!")

async def setup(bot):
    await bot.add_cog(ModPoll(bot))