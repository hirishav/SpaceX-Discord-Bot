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

    async def action_command(self, ctx, member: discord.Member, action_name: str, past_tense: str, emoji: str, is_targeted: bool = True):
        if is_targeted:
            if member is None:
                return await ctx.send(f"❌ Kisko {action_name} karna hai bhai? `@user` mention karo!")
            if member.id == ctx.author.id:
                return await ctx.send(f"❌ Aap apne aap ko {action_name} nahi kar sakte!")
            if member.id == self.bot.user.id:
                return await ctx.send(f"😳 Aap mujhe {action_name} kar rahe ho? >///<")
            description = f"**{ctx.author.display_name}** ne **{member.display_name}** {past_tense}! {emoji}"
        else:
            description = f"**{ctx.author.display_name}** {past_tense} {emoji}"
        
        gif_url = await self.fetch_gif(action_name)
        
        embed = discord.Embed(
            description=description,
            color=discord.Color.random()
        )
        if gif_url:
            embed.set_image(url=gif_url)
        else:
            embed.set_footer(text="Failed to load GIF.")
            
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="bang")
    async def bang(self, ctx, member: discord.Member):
        """Kisi member ko bang karne ke liye!"""
        await self.action_command(ctx, member, "bang", "bang kiya", "💥", True)

    @commands.hybrid_command(name="bite")
    async def bite(self, ctx, member: discord.Member):
        """Kisi member ko bite karne ke liye!"""
        await self.action_command(ctx, member, "bite", "kaat liya (bite)", "🦷", True)

    @commands.hybrid_command(name="cuddle")
    async def cuddle(self, ctx, member: discord.Member):
        """Kisi member ko cuddle karne ke liye!"""
        await self.action_command(ctx, member, "cuddle", "cuddle kiya", "🤗", True)

    @commands.hybrid_command(name="greet")
    async def greet(self, ctx, member: discord.Member):
        """Kisi member ko greet karne ke liye!"""
        await self.action_command(ctx, member, "greet", "greet kiya", "👋", True)

    @commands.hybrid_command(name="handholding")
    async def handholding(self, ctx, member: discord.Member):
        """Kisi member ko handholding karne ke liye!"""
        await self.action_command(ctx, member, "handholding", "ka haath pakda", "🤝", True)

    @commands.hybrid_command(name="highfive")
    async def highfive(self, ctx, member: discord.Member):
        """Kisi member ko highfive karne ke liye!"""
        await self.action_command(ctx, member, "highfive", "ko highfive diya", "🙌", True)

    @commands.hybrid_command(name="hug")
    async def hug(self, ctx, member: discord.Member):
        """Kisi member ko hug karne ke liye!"""
        await self.action_command(ctx, member, "hug", "hug kiya", "🫂", True)

    @commands.hybrid_command(name="insult")
    async def insult(self, ctx, member: discord.Member):
        """Kisi member ko insult karne ke liye!"""
        await self.action_command(ctx, member, "insult", "ko insult kiya", "🤬", True)

    @commands.hybrid_command(name="kiss")
    async def kiss(self, ctx, member: discord.Member):
        """Kisi member ko kiss karne ke liye!"""
        await self.action_command(ctx, member, "kiss", "kiss kiya", "💋", True)

    @commands.hybrid_command(name="lick")
    async def lick(self, ctx, member: discord.Member):
        """Kisi member ko lick karne ke liye!"""
        await self.action_command(ctx, member, "lick", "lick kiya", "👅", True)

    @commands.hybrid_command(name="nom")
    async def nom(self, ctx, member: discord.Member):
        """Kisi member ko nom karne ke liye!"""
        await self.action_command(ctx, member, "nom", "ko nom kiya", "😋", True)

    @commands.hybrid_command(name="pat")
    async def pat(self, ctx, member: discord.Member):
        """Kisi member ko pat karne ke liye!"""
        await self.action_command(ctx, member, "pat", "pat kiya", "pat", True)

    @commands.hybrid_command(name="poke")
    async def poke(self, ctx, member: discord.Member):
        """Kisi member ko poke karne ke liye!"""
        await self.action_command(ctx, member, "poke", "poke kiya", "👉", True)

    @commands.hybrid_command(name="punch")
    async def punch(self, ctx, member: discord.Member):
        """Kisi member ko punch karne ke liye!"""
        await self.action_command(ctx, member, "punch", "punch kiya", "👊", True)

    @commands.hybrid_command(name="slap")
    async def slap(self, ctx, member: discord.Member):
        """Kisi member ko slap karne ke liye!"""
        await self.action_command(ctx, member, "slap", "thappad mara", "👋", True)

    @commands.hybrid_command(name="spank")
    async def spank(self, ctx, member: discord.Member):
        """Kisi member ko spank karne ke liye!"""
        await self.action_command(ctx, member, "spank", "spank kiya", "🍑👋", True)

    @commands.hybrid_command(name="stare")
    async def stare(self, ctx, member: discord.Member):
        """Kisi member ko stare karne ke liye!"""
        await self.action_command(ctx, member, "stare", "ko ghoora (stare)", "👁️", True)

    @commands.hybrid_command(name="tickle")
    async def tickle(self, ctx, member: discord.Member):
        """Kisi member ko tickle karne ke liye!"""
        await self.action_command(ctx, member, "tickle", "gudgudi (tickle) ki", "🤏😂", True)

    @commands.hybrid_command(name="waifu_insult")
    async def waifu_insult(self, ctx, member: discord.Member):
        """Kisi member ko waifu_insult karne ke liye!"""
        await self.action_command(ctx, member, "waifu_insult", "ko waifu insult di", "💔", True)

    @commands.hybrid_command(name="baka")
    async def baka(self, ctx, member: discord.Member):
        """Kisi member ko baka karne ke liye!"""
        await self.action_command(ctx, member, "baka", "kaha ki baka hai", "💢", True)

    @commands.hybrid_command(name="delet_this")
    async def delet_this(self, ctx, member: discord.Member):
        """Kisi member ko delet_this karne ke liye!"""
        await self.action_command(ctx, member, "delet_this", "se kaha delete this", "🗑️", True)

    @commands.hybrid_command(name="animal_cat")
    async def animal_cat(self, ctx):
        """Apne actions express karne ke liye (animal_cat)!"""
        await self.action_command(ctx, None, "animal_cat", "ne ek cat pic dekhi", "🐱", False)

    @commands.hybrid_command(name="animal_dog")
    async def animal_dog(self, ctx):
        """Apne actions express karne ke liye (animal_dog)!"""
        await self.action_command(ctx, None, "animal_dog", "ne ek dog pic dekhi", "🐶", False)

    @commands.hybrid_command(name="awoo")
    async def awoo(self, ctx):
        """Apne actions express karne ke liye (awoo)!"""
        await self.action_command(ctx, None, "awoo", "awoo kar raha hai", "🐺", False)

    @commands.hybrid_command(name="banghead")
    async def banghead(self, ctx):
        """Apne actions express karne ke liye (banghead)!"""
        await self.action_command(ctx, None, "banghead", "apna sir patak raha hai", "🤦", False)

    @commands.hybrid_command(name="blush")
    async def blush(self, ctx):
        """Apne actions express karne ke liye (blush)!"""
        await self.action_command(ctx, None, "blush", "blush kar raha hai", "😳", False)

    @commands.hybrid_command(name="capybara")
    async def capybara(self, ctx):
        """Apne actions express karne ke liye (capybara)!"""
        await self.action_command(ctx, None, "capybara", "ne capybara dekha", "🦦", False)

    @commands.hybrid_command(name="clagwimoth")
    async def clagwimoth(self, ctx):
        """Apne actions express karne ke liye (clagwimoth)!"""
        await self.action_command(ctx, None, "clagwimoth", "clagwimoth mode me hai", "🤔", False)

    @commands.hybrid_command(name="cry")
    async def cry(self, ctx):
        """Apne actions express karne ke liye (cry)!"""
        await self.action_command(ctx, None, "cry", "ro raha hai", "😭", False)

    @commands.hybrid_command(name="dab")
    async def dab(self, ctx):
        """Apne actions express karne ke liye (dab)!"""
        await self.action_command(ctx, None, "dab", "dab kar raha hai", "😎", False)

    @commands.hybrid_command(name="dance")
    async def dance(self, ctx):
        """Apne actions express karne ke liye (dance)!"""
        await self.action_command(ctx, None, "dance", "dance kar raha hai", "💃", False)

    @commands.hybrid_command(name="deredere")
    async def deredere(self, ctx):
        """Apne actions express karne ke liye (deredere)!"""
        await self.action_command(ctx, None, "deredere", "deredere mode me hai", "😍", False)

    @commands.hybrid_command(name="discord_memes")
    async def discord_memes(self, ctx):
        """Apne actions express karne ke liye (discord_memes)!"""
        await self.action_command(ctx, None, "discord_memes", "ne meme dekha", "😂", False)

    @commands.hybrid_command(name="facedesk")
    async def facedesk(self, ctx):
        """Apne actions express karne ke liye (facedesk)!"""
        await self.action_command(ctx, None, "facedesk", "ne facedesk kiya", "🤦‍♂️", False)

    @commands.hybrid_command(name="gaming")
    async def gaming(self, ctx):
        """Apne actions express karne ke liye (gaming)!"""
        await self.action_command(ctx, None, "gaming", "gaming kar raha hai", "🎮", False)

    @commands.hybrid_command(name="initial_d")
    async def initial_d(self, ctx):
        """Apne actions express karne ke liye (initial_d)!"""
        await self.action_command(ctx, None, "initial_d", "drifting kar raha hai", "🏎️", False)

    @commands.hybrid_command(name="jojo")
    async def jojo(self, ctx):
        """Apne actions express karne ke liye (jojo)!"""
        await self.action_command(ctx, None, "jojo", "jojo pose kar raha hai", "🧍‍♂️", False)

    @commands.hybrid_command(name="kemonomimi")
    async def kemonomimi(self, ctx):
        """Apne actions express karne ke liye (kemonomimi)!"""
        await self.action_command(ctx, None, "kemonomimi", "kemonomimi mode me hai", "🦊", False)

    @commands.hybrid_command(name="lewd")
    async def lewd(self, ctx):
        """Apne actions express karne ke liye (lewd)!"""
        await self.action_command(ctx, None, "lewd", "lewd soch raha hai", "🔞", False)

    @commands.hybrid_command(name="megumin")
    async def megumin(self, ctx):
        """Apne actions express karne ke liye (megumin)!"""
        await self.action_command(ctx, None, "megumin", "explosion magic kar raha hai", "💥", False)

    @commands.hybrid_command(name="nani")
    async def nani(self, ctx):
        """Apne actions express karne ke liye (nani)!"""
        await self.action_command(ctx, None, "nani", "nani?!", "😲", False)

    @commands.hybrid_command(name="neko")
    async def neko(self, ctx):
        """Apne actions express karne ke liye (neko)!"""
        await self.action_command(ctx, None, "neko", "neko pic dekh raha hai", "🐈", False)

    @commands.hybrid_command(name="otter")
    async def otter(self, ctx):
        """Apne actions express karne ke liye (otter)!"""
        await self.action_command(ctx, None, "otter", "ne otter pic dekhi", "🦦", False)

    @commands.hybrid_command(name="owo")
    async def owo(self, ctx):
        """Apne actions express karne ke liye (owo)!"""
        await self.action_command(ctx, None, "owo", "owo kar raha hai", "🥺", False)

    @commands.hybrid_command(name="poi")
    async def poi(self, ctx):
        """Apne actions express karne ke liye (poi)!"""
        await self.action_command(ctx, None, "poi", "poi kar raha hai", "⚓", False)

    @commands.hybrid_command(name="pout")
    async def pout(self, ctx):
        """Apne actions express karne ke liye (pout)!"""
        await self.action_command(ctx, None, "pout", "pout kar raha hai", "😡", False)

    @commands.hybrid_command(name="quokka")
    async def quokka(self, ctx):
        """Apne actions express karne ke liye (quokka)!"""
        await self.action_command(ctx, None, "quokka", "ne quokka dekha", "🐻", False)

    @commands.hybrid_command(name="rem")
    async def rem(self, ctx):
        """Apne actions express karne ke liye (rem)!"""
        await self.action_command(ctx, None, "rem", "rem mode me hai", "💙", False)

    @commands.hybrid_command(name="roll")
    async def roll(self, ctx):
        """Apne actions express karne ke liye (roll)!"""
        await self.action_command(ctx, None, "roll", "roll kar raha hai", "🔄", False)

    @commands.hybrid_command(name="shrug")
    async def shrug(self, ctx):
        """Apne actions express karne ke liye (shrug)!"""
        await self.action_command(ctx, None, "shrug", "shrug kar raha hai", "🤷", False)

    @commands.hybrid_command(name="sleepy")
    async def sleepy(self, ctx):
        """Apne actions express karne ke liye (sleepy)!"""
        await self.action_command(ctx, None, "sleepy", "sleepy feel kar raha hai", "😴", False)

    @commands.hybrid_command(name="smile")
    async def smile(self, ctx):
        """Apne actions express karne ke liye (smile)!"""
        await self.action_command(ctx, None, "smile", "smile kar raha hai", "😊", False)

    @commands.hybrid_command(name="smug")
    async def smug(self, ctx):
        """Apne actions express karne ke liye (smug)!"""
        await self.action_command(ctx, None, "smug", "smug face bana raha hai", "😏", False)

    @commands.hybrid_command(name="sumfuk")
    async def sumfuk(self, ctx):
        """Apne actions express karne ke liye (sumfuk)!"""
        await self.action_command(ctx, None, "sumfuk", "want sum fuk?", "🐦", False)

    @commands.hybrid_command(name="teehee")
    async def teehee(self, ctx):
        """Apne actions express karne ke liye (teehee)!"""
        await self.action_command(ctx, None, "teehee", "teehee kar raha hai", "🤭", False)

    @commands.hybrid_command(name="thinking")
    async def thinking(self, ctx):
        """Apne actions express karne ke liye (thinking)!"""
        await self.action_command(ctx, None, "thinking", "soch raha hai", "🤔", False)

    @commands.hybrid_command(name="thumbsup")
    async def thumbsup(self, ctx):
        """Apne actions express karne ke liye (thumbsup)!"""
        await self.action_command(ctx, None, "thumbsup", "thumbsup kar raha hai", "👍", False)

    @commands.hybrid_command(name="trap")
    async def trap(self, ctx):
        """Apne actions express karne ke liye (trap)!"""
        await self.action_command(ctx, None, "trap", "trap card activate kiya", "🃏", False)

    @commands.hybrid_command(name="triggered")
    async def triggered(self, ctx):
        """Apne actions express karne ke liye (triggered)!"""
        await self.action_command(ctx, None, "triggered", "triggered ho gaya", "💢", False)

    @commands.hybrid_command(name="wag")
    async def wag(self, ctx):
        """Apne actions express karne ke liye (wag)!"""
        await self.action_command(ctx, None, "wag", "apni tail wag kar raha hai", "🐕", False)

    @commands.hybrid_command(name="wasted")
    async def wasted(self, ctx):
        """Apne actions express karne ke liye (wasted)!"""
        await self.action_command(ctx, None, "wasted", "wasted ho gaya", "💀", False)

    @commands.hybrid_command(name="wombat")
    async def wombat(self, ctx):
        """Apne actions express karne ke liye (wombat)!"""
        await self.action_command(ctx, None, "wombat", "ne wombat dekha", "🦡", False)

    @commands.hybrid_command(name="nsfw")
    async def nsfw(self, ctx):
        """Apne actions express karne ke liye (nsfw)!"""
        await self.action_command(ctx, None, "nsfw", "ne nsfw pic dekhi", "🔞", False)

    # Error handling for targeted commands
    @bang.error
    @bite.error
    @cuddle.error
    @greet.error
    @handholding.error
    @highfive.error
    @hug.error
    @insult.error
    @kiss.error
    @lick.error
    @nom.error
    @pat.error
    @poke.error
    @punch.error
    @slap.error
    @spank.error
    @stare.error
    @tickle.error
    @waifu_insult.error
    @baka.error
    @delet_this.error
    async def action_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Kisko {ctx.command.name} karna hai bhai? `@user` mention karo!\n**Sahi tarika:** `{ctx.prefix}{ctx.command.name} @user`")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ Ye member mujhe server me nahi mila!")

async def setup(bot):
    await bot.add_cog(FunActions(bot))
