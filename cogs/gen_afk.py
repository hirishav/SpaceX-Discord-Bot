# cogs/gen_afk.py
import discord
from discord.ext import commands
import database as sqlite3
import time

class GenAFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.afk_cache = {}
        
        # Hydrate cache from DB on boot
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        cursor.execute("SELECT server_id, user_id, reason, timestamp FROM afk")
        for s_id, u_id, reason, ts in cursor.fetchall():
            self.afk_cache[(str(s_id), str(u_id))] = (reason, ts)
        conn.close()
        print(f"-> AFK Cache Hydrated: {len(self.afk_cache)} active AFKs loaded into RAM.")

    # Helper functions database handle karne ke liye
    def set_afk(self, server_id, user_id, reason):
        s_id = str(server_id)
        u_id = str(user_id)
        ts = int(time.time())
        
        # Update Cache
        self.afk_cache[(s_id, u_id)] = (reason, ts)
        
        # Update DB (Background operation)
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO afk (server_id, user_id, reason, timestamp) VALUES (?, ?, ?, ?)",
                       (s_id, u_id, reason, ts))
        conn.commit()
        conn.close()

    def remove_afk(self, server_id, user_id):
        s_id = str(server_id)
        u_id = str(user_id)
        
        # Update Cache
        self.afk_cache.pop((s_id, u_id), None)
        
        # Update DB
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM afk WHERE server_id = ? AND user_id = ?", (s_id, u_id))
        conn.commit()
        conn.close()

    def get_afk(self, server_id, user_id):
        # 1000x faster: Read directly from RAM cache instead of opening a database connection
        return self.afk_cache.get((str(server_id), str(user_id)))

    @commands.hybrid_command(name="afk")
    async def afk(self, ctx, *, reason: str = "I am currently away!"):
        """Aapko AFK status par set kar deta hai."""
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
            await message.channel.send(embed=embed, delete_after=5)

        # 2. CHECK PINGS: Agar koi kisi AFK bande ko ping karega
        if message.mentions:
            for member in message.mentions:
                if member.id == message.author.id:
                    continue
                
                member_afk = self.get_afk(message.guild.id, member.id)
                if member_afk:
                    reason, timestamp = member_afk
                    gone_since = int(time.time()) - timestamp
                    
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
                    break

async def setup(bot):
    await bot.add_cog(GenAFK(bot))