# cogs/fun_actions.py
import discord
from discord.ext import commands
import aiohttp

class FunActions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_base = "https://nekos.life/api/v2/img/"

    async def fetch_gif(self, endpoint: str) -> str:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.api_base + endpoint) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("url")
            except Exception as e:
                print(f"Error fetching GIF from {endpoint}: {e}")
        return None

    async def action_command(self, ctx, member: discord.Member, action_name: str, past_tense: str, emoji: str):
        if member.id == ctx.author.id:
            return await ctx.send(f"❌ Aap apne aap ko {action_name} nahi kar sakte!")
        if member.id == self.bot.user.id:
            return await ctx.send(f"😳 Aap mujhe {action_name} kar rahe ho? >///<")

        gif_url = await self.fetch_gif(action_name)
        
        embed = discord.Embed(
            description=f"**{ctx.author.display_name}** ne **{member.display_name}** ko {past_tense}! {emoji}",
            color=discord.Color.random()
        )
        if gif_url:
            embed.set_image(url=gif_url)
        else:
            embed.set_footer(text="Failed to load GIF.")
            
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="kiss")
    async def kiss(self, ctx, member: discord.Member):
        """Kisi member ko kiss karne ke liye!"""
        await self.action_command(ctx, member, "kiss", "kiss kiya", "💋")

    @commands.hybrid_command(name="hug")
    async def hug(self, ctx, member: discord.Member):
        """Kisi member ko gale (hug) lagane ke liye!"""
        await self.action_command(ctx, member, "hug", "hug kiya", "🫂")

    @commands.hybrid_command(name="slap")
    async def slap(self, ctx, member: discord.Member):
        """Kisi member ko thappad marne ke liye!"""
        await self.action_command(ctx, member, "slap", "thappad mara", "👋")

    @commands.hybrid_command(name="spank")
    async def spank(self, ctx, member: discord.Member):
        """Kisi member ko spank karne ke liye!"""
        await self.action_command(ctx, member, "spank", "spank kiya", "🍑👋")

    @commands.hybrid_command(name="tickle")
    async def tickle(self, ctx, member: discord.Member):
        """Kisi member ko gudgudi karne ke liye!"""
        await self.action_command(ctx, member, "tickle", "gudgudi (tickle) ki", "🤏😂")

    # Error handling for all these commands
    @kiss.error
    @hug.error
    @slap.error
    @spank.error
    @tickle.error
    async def action_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Kisko {ctx.command.name} karna hai bhai? `@user` mention karo!\n**Sahi tarika:** `{ctx.prefix}{ctx.command.name} @user`")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ Ye member mujhe server me nahi mila!")

async def setup(bot):
    await bot.add_cog(FunActions(bot))
