# cogs/eco_leaderboard.py
import discord
from discord.ext import commands
import sqlite3

class EcoLeaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="leaderboard", aliases=["lb"])
    async def leaderboard(self, ctx, mode: str = None):
        """Server ya Global level par top economy/gaming players dekhne ke liye."""
        
        # Validation: Agar mode nahi dala ya galat dala
        if not mode or mode.lower() not in ["server", "global"]:
            embed_err = discord.Embed(
                title="❌ Galat Format!",
                description=f"Sahi tarika:\n👉 `{ctx.prefix}lb server` - Current server ke top log\n👉 `{ctx.prefix}lb global` - Pure bot network ke top log",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed_err)

        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()

        # Database se saare users ka total balance (Wallet + Bank) high to low sort karke nikalna
        cursor.execute("SELECT user_id, (wallet + bank) as total_money FROM economy ORDER BY total_money DESC")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return await ctx.send("🪙 Abhi economy database khali hai! Thoda game khelo pehle.")

        embed = discord.Embed(color=discord.Color.gold())
        lb_text = ""
        rank = 1

        # --- MODE 1: SERVER LEADERBOARD ---
        if mode.lower() == "server":
            embed.title = f"🏆 {ctx.guild.name} - Economy Leaderboard"
            embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
            
            for row in rows:
                user_id = int(row[0])
                total_money = row[1]
                
                # Check karna ki user isi server me hai ya nahi
                member = ctx.guild.get_member(user_id)
                if member:
                    # Top 3 ko special medal emoji dene ke liye layout matrix
                    if rank == 1: emoji = "🥇"
                    elif rank == 2: emoji = "🥈"
                    elif rank == 3: emoji = "🥉"
                    else: emoji = f"`#{rank}`"
                    
                    lb_text += f"{emoji} **{member.name}** — 🪙 `{total_money:,}` coins\n"
                    rank += 1
                    
                if rank > 10: # Top 10 members hi dikhayenge screen space ke liye
                    break

        # --- MODE 2: GLOBAL LEADERBOARD ---
        elif mode.lower() == "global":
            embed.title = f"🌐 SpaceX Bot - Global Master Leaderboard"
            # Bot ki apni profile picture thumbnail me set
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
            
            for row in rows:
                user_id = int(row[0])
                total_money = row[1]
                
                # Global user object fetch karna (Jisse kisi bhi server ka banda ho, naam aa jaye)
                user = self.bot.get_user(user_id)
                if user:
                    if rank == 1: emoji = "🥇"
                    elif rank == 2: emoji = "🥈"
                    elif rank == 3: emoji = "🥉"
                    else: emoji = f"`#{rank}`"
                    
                    lb_text += f"{emoji} **{user.name}** — 🪙 `{total_money:,}` coins\n"
                    rank += 1
                    
                if rank > 10: # Global top 10 giants
                    break

        # Final layout building
        if not lb_text:
            embed.description = "*Is category me abhi koi data match nahi hua!*"
        else:
            embed.description = f"**Top 10 Rich Players Matrix:**\n\n{lb_text}"
            
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EcoLeaderboard(bot))