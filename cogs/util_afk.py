# cogs/util_afk.py
import discord
from discord.ext import commands
import sqlite3
import time

class UtilAFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Helper functions database handle karne ke liye
    def set_afk(self, server_id, user_id, reason):
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO afk (server_id, user_id, reason, timestamp) VALUES (?, ?, ?, ?)",
                       (str(server_id), str(user_id), reason, int(time.time())))
        conn.commit()
        conn.close()

    def remove_afk(self, server_id, user_id):
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM afk WHERE server_id = ? AND user_id = ?", (str(server_id), str(user_id)))
        conn.commit()
        conn.close()

    def get_afk(self, server_id, user_id):
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        cursor.execute("SELECT reason, timestamp FROM afk WHERE server_id = ? AND user_id = ?", (str(server_id), str(user_id)))
        row = cursor.fetchone()
        conn.close()
        return row

    @commands.command(name="afk")
    async def afk(self, ctx, *, reason: str = "I am currently away!"):
        """Aapko AFK status par set kar deta hai."""
        # Member ka nick badal kar [AFK] lagane ka try karna (Optional)
        try:
            if not ctx.author.display_name.startswith("[AFK]"):
                await ctx.author.edit(nick=f"[AFK] {ctx.author.display_name}")
        except Exception:
            pass

        self.set_afk(ctx.guild.id, ctx.author.id, reason)
        
        embed = discord.Embed(
            description=f"💤 {ctx.author.mention}, ab aap AFK hain: **{reason}**",
            color=discord.Color.yellow()
        )
        await ctx.send(embed=embed)

    # NAYA JADU: Listener jo pings aur wapas aane wale logo ko detect karega
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        # 1. CHECK WELCOME BACK: Agar koi AFK banda khud message karega toh AFK hatega
        afk_data = self.get_afk(message.guild.id, message.author.id)
        if afk_data:
            self.remove_afk(message.guild.id, message.author.id)
            try:
                if message.author.display_name.startswith("[AFK]"):
                    new_nick = message.author.display_name.replace("[AFK] ", "", 1)
                    await message.author.edit(nick=new_nick)
            except Exception:
                pass
            
            embed = discord.Embed(
                description=f"👋 Welcome back {message.author.mention}! Aapka AFK status hata diya gaya hai.",
                color=discord.Color.green()
            )
            await message.channel.send(embed=embed, delete_after=5) # 5 second me gayab ho jayega

        # 2. CHECK PINGS: Agar koi kisi AFK bande ko ping karega
        if message.mentions:
            for member in message.mentions:
                if member.id == message.author.id:
                    continue # Agar khud ko ping kiya toh ignore
                
                member_afk = self.get_afk(message.guild.id, member.id)
                if member_afk:
                    reason, timestamp = member_afk
                    gone_since = int(time.time()) - timestamp
                    
                    # Time format set karna (e.g., 5m ago)
                    if gone_since < 60:
                        time_str = f"{gone_since}s pehle"
                    elif gone_since < 3600:
                        time_str = f"{gone_since // 60}m pehle"
                    else:
                        time_str = f"{gone_since // 3600}h pehle"

                    embed = discord.Embed(
                        description=f"💤 **{member.name}** abhi AFK hain ({time_str})\n📝 **Reason:** {reason}",
                        color=discord.Color.orange()
                    )
                    await message.channel.send(embed=embed)
                    break # Ek baar me ek hi alert kaafi hai

async def setup(bot):
    await bot.add_cog(UtilAFK(bot))