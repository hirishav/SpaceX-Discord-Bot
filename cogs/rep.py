# cogs/rep.py
import discord
from discord.ext import commands
import database as sqlite3

class RepSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def fetch_user(self, ctx, user_str):
        try:
            member = await commands.MemberConverter().convert(ctx, user_str)
            return str(member.id), member.name
        except Exception:
            try:
                user = await self.bot.fetch_user(int(user_str))
                return str(user.id), user.name
            except Exception:
                return None, None

    @commands.hybrid_group(name="rep", invoke_without_command=True)
    async def rep(self, ctx, user_str: str = None):
        """Check yours or someone else's rep points!"""
        if ctx.invoked_subcommand is None:
            member = None
            if user_str:
                user_id, username = await self.fetch_user(ctx, user_str)
                if not user_id:
                    return await ctx.send("❌ User not found!")
                
                try:
                    member = await commands.MemberConverter().convert(ctx, user_str)
                except:
                    pass
            else:
                user_id = str(ctx.author.id)
                username = ctx.author.name
                member = ctx.author

            conn = sqlite3.connect("warnings.db")
            cursor = conn.cursor()
            cursor.execute("SELECT rep_points FROM reps WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            conn.close()

            points = result[0] if result else 0
            
            embed = discord.Embed(title=f"⭐ {username}'s Rep Profile", color=discord.Color.gold())
            embed.description = f"**Total Rep Points:** `{points}`\n\n*Vote on Top.gg to earn more rep points!*"
            
            if member:
                embed.set_thumbnail(url=member.display_avatar.url)

            await ctx.send(embed=embed)

    @rep.command(name="lb")
    async def rep_lb(self, ctx, scope: str = "global"):
        """Leaderboard for rep points. Usage: !!rep lb global or !!rep lb server"""
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        
        if scope.lower() in ["server", "local", "guild"]:
            if not ctx.guild:
                conn.close()
                return await ctx.send("❌ This command can only be used in a server!")
            
            query = "SELECT user_id, rep_points FROM reps WHERE rep_points > 0 ORDER BY rep_points DESC"
            cursor.execute(query)
            all_reps = cursor.fetchall()
            
            results = []
            for user_id, points in all_reps:
                member = ctx.guild.get_member(int(user_id))
                if not member:
                    try:
                        member = await ctx.guild.fetch_member(int(user_id))
                    except discord.NotFound:
                        pass
                
                if member:
                    results.append((user_id, points))
                
                if len(results) == 10:
                    break
            
            title = f"🏆 Server Rep Leaderboard - {ctx.guild.name}"
        else:
            query = "SELECT user_id, rep_points FROM reps WHERE rep_points > 0 ORDER BY rep_points DESC LIMIT 10"
            cursor.execute(query)
            results = cursor.fetchall()
            title = "🏆 Global Rep Leaderboard"
            
        conn.close()
        
        if not results:
            return await ctx.send("❌ No rep points found!")
            
        embed = discord.Embed(title=title, color=discord.Color.gold())
        
        desc = ""
        for i, (user_id, points) in enumerate(results, 1):
            desc += f"**{i}.** <@{user_id}> - `{points}` Reps\n"
            
        embed.description = desc
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RepSystem(bot))
