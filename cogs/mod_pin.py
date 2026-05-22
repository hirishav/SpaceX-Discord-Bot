# cogs/mod_pin.py
import discord
from discord.ext import commands

class ModPin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="pin")
    @commands.has_permissions(manage_messages=True)  # 🛡️ Lock to moderator perms
    async def pin_message(self, ctx, message_id: int = None):
        """Kisi bhi message ko uski ID ke zariye instantly pin karne ke liye."""
        if not message_id:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}pin <message_id>`")

        try:
            message = await ctx.channel.fetch_message(message_id)
            await message.pin()
            
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
            await ctx.send("❌ Mere paas messages pin karne ki explicit permissions nahi hain server roles me!")
        except Exception as e:
            await ctx.send(f"❌ Kuch gadbad hui: `{e}`")

    @commands.command(name="unpin")
    @commands.has_permissions(manage_messages=True)  # 🛡️ Lock to moderator perms
    async def unpin_message(self, ctx, message_id: int = None):
        """Channel ke kisi bhi pinned message ko ID ke zariye unpin karne ke liye."""
        if not message_id:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}unpin <message_id>`")

        try:
            message = await ctx.channel.fetch_message(message_id)
            await message.unpin()
            
            embed = discord.Embed(
                description=f"🔓 [This Message]({message.jump_url}) has been unpinned successfully by {ctx.author.mention}.",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            
            try:
                await ctx.message.delete()
            except Exception:
                pass
                
        except discord.NotFound:
            await ctx.send("❌ Mujhe is channel me is ID ka koi message nahi mila pinned list me!")
        except discord.Forbidden:
            await ctx.send("❌ Mere paas messages unpin karne ki permission nahi hai server roles me!")
        except Exception as e:
            await ctx.send(f"❌ Kuch gadbad hui: `{e}`")

    # Error Handler Common for Pin/Unpin
    @pin_message.error
    @unpin_message.error
    async def pin_unpin_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ **Permission Denied:** Aapke paas is command ko chalane ke liye `Manage Messages` permission honi chahiye!")

async def setup(bot):
    await bot.add_cog(ModPin(bot))