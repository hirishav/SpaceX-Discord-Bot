# cogs/mod_temprole.py
import discord
from discord.ext import commands, tasks
import datetime
import re
import asyncio
import time
from discord.ext.commands import Converter, BadArgument
from utils import SmartRoleConverter

class ModTemprole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_temproles.start()

    def cog_unload(self):
        self.check_temproles.cancel()

    # Helper function to parse duration strings like 10m, 1h
    def parse_duration(self, time_str: str):
        time_match = re.match(r"(\d+)([smhd])", time_str.lower())
        if not time_match:
            return None
        
        amount = int(time_match.group(1))
        unit = time_match.group(2)
        
        if unit == 's':
            return datetime.timedelta(seconds=amount)
        elif unit == 'm':
            return datetime.timedelta(minutes=amount)
        elif unit == 'h':
            return datetime.timedelta(hours=amount)
        elif unit == 'd':
            return datetime.timedelta(days=amount)
        return None

    @commands.hybrid_command(name="temprole")
    @commands.has_guild_permissions(manage_roles=True)
    async def temprole(self, ctx, member: discord.Member, duration_str: str, *, role_and_reason: str):
        """Kisi user ko limited time ke liye ek specific role assign karne ke liye."""
        
        # Split by comma if possible, mimicking Dyno's syntax
        if "," in role_and_reason:
            parts = role_and_reason.split(",", 1)
            role_arg = parts[0].strip()
            reason = parts[1].strip()
        else:
            role_arg = role_and_reason.strip()
            reason = "No reason provided"

        # Try to convert the first part to a Role using SmartRoleConverter
        try:
            role = await SmartRoleConverter().convert(ctx, role_arg)
        except commands.BadArgument as e:
            return await ctx.send(str(e))

        if role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("❌ Aap apne se baray ya barabar ke role ko kisi ko de nahi sakte!")
            
        if role >= ctx.guild.me.top_role:
            return await ctx.send("❌ Main yeh role nahi de sakta kyunki yeh mere top role se upar hai!")

        duration = self.parse_duration(duration_str)
        if not duration:
            return await ctx.send("❌ Galat time format! Use karein: `s`, `m`, `h`, ya `d`. (Example: `10m`, `1d`)")

        expires_at = int(time.time() + duration.total_seconds())

        try:
            await member.add_roles(role, reason=f"Temprole by {ctx.author.name} | Reason: {reason}")
            
            # Save to database
            cursor = self.bot.db.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO temproles (guild_id, user_id, role_id, expires_at) VALUES (?, ?, ?, ?)",
                (str(ctx.guild.id), str(member.id), str(role.id), expires_at)
            )
            self.bot.db.commit()

            embed = discord.Embed(
                title="✅ Role Added Temporarily",
                description=f"{member.mention} ko **{role.name}** role de diya gaya hai.",
                color=discord.Color.green(),
                timestamp=datetime.datetime.now(datetime.timezone.utc)
            )
            embed.add_field(name="👤 Target", value=f"{member.name} ({member.id})", inline=True)
            embed.add_field(name="⏳ Duration", value=f"`{duration_str}`", inline=True)
            embed.add_field(name="🛡️ Staff", value=ctx.author.mention, inline=True)
            embed.add_field(name="📝 Reason", value=reason, inline=False)
            
            await ctx.send(embed=embed)

            try:
                await ctx.message.delete()
            except Exception:
                pass

        except discord.Forbidden:
            await ctx.send("❌ Main is member ko role nahi de sakta! Permissions check karein.")
        except Exception as e:
            await ctx.send(f"❌ Kuch gadbad hui: {e}")

    @temprole.error
    async def temprole_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            pass
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}temprole @user <time> <role>, [reason]`\nExample: `{ctx.prefix}temprole @user 10m @VIP, Good behaviour`")

    @tasks.loop(seconds=30)
    async def check_temproles(self):
        await self.bot.wait_until_ready()
        
        current_time = int(time.time())
        try:
            cursor = self.bot.db.cursor()
            cursor.execute("SELECT guild_id, user_id, role_id FROM temproles WHERE expires_at <= ?", (current_time,))
            expired_roles = cursor.fetchall()
            
            for guild_id, user_id, role_id in expired_roles:
                try:
                    guild = self.bot.get_guild(int(guild_id)) or await self.bot.fetch_guild(int(guild_id))
                    if guild:
                        member = guild.get_member(int(user_id))
                        if not member:
                            try:
                                member = await guild.fetch_member(int(user_id))
                            except discord.NotFound:
                                member = None

                        if member:
                            role = guild.get_role(int(role_id))
                            if role:
                                await member.remove_roles(role, reason="Temprole expired")
                except Exception as e:
                    print(f"Failed to remove expired temprole (Guild: {guild_id}, User: {user_id}, Role: {role_id}): {e}")
                
                # Finally delete from DB regardless of whether the user/role still exists
                cursor.execute(
                    "DELETE FROM temproles WHERE guild_id = ? AND user_id = ? AND role_id = ?", 
                    (guild_id, user_id, role_id)
                )
            
            if expired_roles:
                self.bot.db.commit()
                
        except Exception as e:
            print(f"Error in temprole loop: {e}")

async def setup(bot):
    await bot.add_cog(ModTemprole(bot))
