import discord
from discord.ext import commands

class OwnerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ownerinfo", aliases=["owner"], help="Displays information about the bot creator Rishav.")
    async def owner_details(self, ctx): # Cogs me 'self' zaroori hai
        # Apni explicit public details yahan set karo
        owner_username = "phrenic_rishav" 
        owner_id = "727718500663033897" # Apni real numeric ID yahan daal dena
        github_link = "https://github.com/hirishav" # Apni profile link lagao
        
        embed = discord.Embed(
            title="✨ Rishav Das | The Mastermind Behind the Blocks",
            description=(
                "> *\"I don't just write code; I engineer digital ecosystems.\"*\n\n"
                "Building custom Minecraft experiences end-to-end — from optimized plugins "
                "and APIs to high-quality resource packs and complex server setups."
            ),
            color=0x5ea2e8 # Aesthetic Blue matching the portfolio
        )
        
        # --- ROW 1: Identity & Links ---
        embed.add_field(
            name="👑 Developer", 
            value=f"**{owner_username}**\n`{owner_id}`", 
            inline=True
        )
        embed.add_field(
            name="🌐 Connections", 
            value=f"✦ [Portfolio](https://mcdevs.netlify.app/)\n✦ [GitHub]({github_link})", 
            inline=True
        )
        embed.add_field(
            name="📫 Contact", 
            value="✦ `phrenic_rishav`\n✦ [Email](mailto:rishavproductions@gmail.com)", 
            inline=True
        )

        # --- ROW 2: Stats & Roles ---
        embed.add_field(
            name="📈 Track Record", 
            value="> 🏆 ` 4+ ` **Years Exp.**\n> 🚀 `50+ ` **Projects**\n> 🤝 `200+` **Clients**", 
            inline=True
        )
        embed.add_field(
            name="🎯 Core Specialties", 
            value="> ✦ Plugin Developer\n> ✦ Resource Pack Creator\n> ✦ Full Stack Engineer", 
            inline=True
        )
        embed.add_field(name="\u200b", value="\u200b", inline=True) # Invisible spacer for clean 3-column layout

        # --- ROW 3: Tech Stack (YAML Codeblock for aesthetic) ---
        embed.add_field(
            name="💻 Tech Arsenal", 
            value=(
                "```yaml\n"
                "Languages  :: Java, Python, C/C++, TS/JS, HTML/CSS\n"
                "Databases  :: MySQL, MongoDB, PostgreSQL, Redis, SQLite\n"
                "Frameworks :: Spigot/Paper, React, Next.js, Node.js\n"
                "Tools      :: Git, Docker, Linux, LLMs, AI Integration\n"
                "```"
            ),
            inline=False
        )
        
        # --- ROW 4: Academics ---
        embed.add_field(
            name="🎓 Academics & Interests", 
            value="**B.Tech CSE** (2025-2029) | Coding, Gaming, AI Research, Music", 
            inline=False
        )
        
        # Discord avatar fetch karne ke liye (Cog format)
        try:
            user = await self.bot.fetch_user(int(owner_id))
            if user.avatar:
                embed.set_thumbnail(url=user.avatar.url)
        except Exception:
            pass

        embed.set_footer(text="SpaceX Official Support • Secure & Verified Application")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OwnerInfo(bot))