# cogs/mod_prefix.py
import discord
from discord.ext import commands

class ModPrefix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setprefix", aliases=["changeprefix"])
    @commands.has_permissions(manage_guild=True)  # 🛡️ Sirf Manage Server perms wale change kar payenge
    async def setprefix(self, ctx, new_prefix: str = None):
        """Server ka default bot prefix badalne ke liye."""
        if not new_prefix:
            return await ctx.send(f"❌ Bhai, naya prefix toh batao! Example: `{ctx.prefix}setprefix $`")

        if len(new_prefix) > 5:
            return await ctx.send("❌ Prefix bohot bada hai! Maximum 5 characters tak ka hi prefix allowed hai.")

        try:
            # ⚡ SPEED HACK: main.py ka open global persistent connection use karo
            cursor = self.bot.db.cursor()
            
            # Upsert logic (insert or replace)
            cursor.execute("""
                INSERT INTO server_prefixes (server_id, prefix) 
                VALUES (?, ?) 
                ON CONFLICT(server_id) DO UPDATE SET prefix = excluded.prefix
            """, (str(ctx.guild.id), new_prefix))
            
            self.bot.db.commit()

            # 🔥 LIVE MEMORY SPEED CACHE UPDATE: Bina bot restart kiye instantly memory runtime sync
            self.bot.prefix_cache[ctx.guild.id] = new_prefix

            embed = discord.Embed(
                title="✅ Prefix Updated!",
                description=f"Is server me SpaceX Bot ka prefix ab badalkar **`{new_prefix}`** ho gaya hai.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Database error aayi: `{e}`")

    @setprefix.error
    async def setprefix_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            pass

async def setup(bot):
    await bot.add_cog(ModPrefix(bot))