import discord
from discord.ext import commands
import asyncio
from typing import Literal, Optional

class OwnerSync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sync", aliases=["forcesync"])
    @commands.is_owner()
    async def sync(self, ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~", "*", "^", "all"]] = None) -> None:
        """
        Owner Only: Force syncs slash commands to Discord.
        
        Usage:
        !!sync -> Global sync (takes up to 1 hour to propagate)
        !!sync ~ -> Sync to the current server instantly
        !!sync * -> Copies global commands to current server and syncs instantly
        !!sync ^ -> Clears all commands from current server
        !!sync all -> Syncs to ALL connected servers instantly (Rate limit warning)
        """
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            elif spec == "all":
                msg = await ctx.send(f"⏳ **Force Syncing** slash commands to all {len(self.bot.guilds)} servers... \n*This will take about {len(self.bot.guilds)} seconds to avoid rate limits.*")
                synced_count = 0
                for guild in self.bot.guilds:
                    try:
                        self.bot.tree.copy_global_to(guild=guild)
                        await self.bot.tree.sync(guild=guild)
                        synced_count += 1
                        await asyncio.sleep(1.2)  # Anti rate-limit buffer
                    except discord.HTTPException:
                        pass
                
                await msg.edit(content=f"✅ **Success!** Forcefully synced slash commands to **{synced_count}/{len(self.bot.guilds)}** servers! Everyone should see them instantly now.")
                return
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(f"✅ Synced {len(synced)} commands {'globally' if spec is None else 'to this server'}.")
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"✅ Synced the tree to {ret}/{len(guilds)} servers.")

async def setup(bot):
    await bot.add_cog(OwnerSync(bot))
