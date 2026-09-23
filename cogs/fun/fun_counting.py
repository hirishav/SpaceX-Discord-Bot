import discord
from discord.ext import commands
import database
import time
import random
import asyncio
import datetime

ROASTS = [
    "You should repeat class 2 to learn counting! 😂",
    "Bro forgot how numbers work after 5... 💀",
    "Math left the chat. Get a calculator next time! 🧮",
    "Bhai, bachpan me maths class bunk ki thi kya? 🤣",
    "Aap Mumbai nahi aa sakte, aapko ginti nahi aati! 🚶‍♂️",
    "Are you counting in another dimension? That's not the next number! 🌌",
    "Even my dog counts better than that by barking! 🐶",
    "Itni weak maths? Beta tumse na ho payega! 🤦‍♂️",
    "You just ruined the streak! The whole squad is disappointed. 🤡",
    "Back to kindergarten for you! 🏫"
]

class FunCounting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def counting(self, ctx, channel: discord.TextChannel = None):
        """
        Set up a counting channel.
        Usage: `!!counting #channel`
        """
        channel = channel or ctx.channel
        
        db = database.connect()
        cursor = db.cursor()
        # Ensure it's tracked in DB (reset to 1)
        cursor.execute("""
        INSERT INTO counting_config (server_id, channel_id, current_number, last_user_id)
        VALUES (?, ?, 1, NULL)
        ON CONFLICT(channel_id) DO UPDATE SET current_number=1, last_user_id=NULL
        """, (str(ctx.guild.id), str(channel.id)))
        db.commit()
        db.close()
        
        embed = discord.Embed(
            title="Counting Game Started!",
            description="Start counting from **1** here! 🚀\n\n**Rules:**\n- No skipping numbers.\n- You can't count twice in a row.\n- Any wrong message will ruin the streak!",
            color=discord.Color.green()
        )
        await channel.send(embed=embed)
        if channel != ctx.channel:
            await ctx.send(f"✅ Counting game setup successfully in {channel.mention}.")

    @commands.command()
    async def seecounting(self, ctx):
        """
        Shows the current counting number for the server.
        Usage: `!!seecounting`
        """
        db = database.connect()
        cursor = db.cursor()
        cursor.execute("SELECT current_number, channel_id FROM counting_config WHERE server_id = ?", (str(ctx.guild.id),))
        row = cursor.fetchone()
        
        # Fallback if server_id is missing or incorrect due to legacy data
        if not row:
            cursor.execute("SELECT current_number, channel_id FROM counting_config WHERE channel_id = ?", (str(ctx.channel.id),))
            row = cursor.fetchone()
            if row:
                cursor.execute("UPDATE counting_config SET server_id = ? WHERE channel_id = ?", (str(ctx.guild.id), str(ctx.channel.id)))
                db.commit()
                
        # Second fallback: check all text channels in guild
        if not row:
            channel_ids = [str(c.id) for c in ctx.guild.text_channels]
            cursor.execute("SELECT current_number, channel_id FROM counting_config WHERE server_id IS NULL OR server_id = ''")
            for num, cid in cursor.fetchall():
                if cid in channel_ids:
                    row = (num, cid)
                    cursor.execute("UPDATE counting_config SET server_id = ? WHERE channel_id = ?", (str(ctx.guild.id), cid))
                    db.commit()
                    break

        db.close()
        
        if row:
            await ctx.send(f"The next number to count in <#{row[1]}> is **{row[0]}**")
        else:
            await ctx.send("Counting is not set up in this server.")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setcounting(self, ctx, number: int):
        """
        Set the starting number for the counting game.
        Usage: `!!setcounting <number>`
        """
        if number < 1:
            return await ctx.send("❌ Number kam se kam 1 hona chahiye.")
            
        db = database.connect()
        cursor = db.cursor()
        
        # Check if counting channel exists for this server
        cursor.execute("SELECT channel_id FROM counting_config WHERE server_id = ?", (str(ctx.guild.id),))
        row = cursor.fetchone()
        
        if not row:
            db.close()
            return await ctx.send("❌ Is server mein counting setup nahi hai. Pehle `!!counting <#channel>` run karein.")
            
        cursor.execute("""
        UPDATE counting_config 
        SET current_number = ?, last_user_id = NULL 
        WHERE server_id = ?
        """, (number, str(ctx.guild.id)))
        db.commit()
        db.close()
        
        await ctx.send(f"✅ Counting game ka number update ho gaya hai! Ab <#{row[0]}> mein agla number **{number}** se shuru hoga.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        db = database.connect()
        cursor = db.cursor()
        
        # Check if channel is counting channel
        cursor.execute("SELECT current_number, last_user_id FROM counting_config WHERE channel_id = ?", (str(message.channel.id),))
        row = cursor.fetchone()
        
        if not row:
            db.close()
            return
            
        current_number = row[0]
        last_user_id = row[1]
        
        # Validate message
        content = message.content.strip()
        
        # Try to parse number
        is_valid = False
        is_double_count = False
        try:
            num = int(content)
            if num == current_number:
                if str(message.author.id) != last_user_id:
                    is_valid = True
                else:
                    is_double_count = True
        except ValueError:
            is_valid = False

        if is_valid:
            # Success
            await message.add_reaction("✅")
            cursor.execute("""
            UPDATE counting_config 
            SET current_number = current_number + 1, last_user_id = ? 
            WHERE channel_id = ?
            """, (str(message.author.id), str(message.channel.id)))
            db.commit()
        else:
            # Failure
            await message.add_reaction("❌")
            if is_double_count:
                roast = "You cannot count one after another! 🚫"
            else:
                roast = random.choice(ROASTS)
            
            # Reset counter
            cursor.execute("""
            UPDATE counting_config 
            SET current_number = 1, last_user_id = NULL 
            WHERE channel_id = ?
            """, (str(message.channel.id),))
            
            # Track faults
            cursor.execute("SELECT faults FROM counting_faults WHERE user_id = ?", (str(message.author.id),))
            f_row = cursor.fetchone()
            faults = (f_row[0] + 1) if f_row else 1
            
            cursor.execute("""
            INSERT INTO counting_faults (user_id, faults)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET faults=excluded.faults
            """, (str(message.author.id), faults))
            db.commit()
            
            if faults == 1:
                punishment_str = "*Warning: First warn! No timeout this time. Count has been reset to **1**.*"
            elif faults == 2:
                punishment_str = "*Warning: Last warn! Next mistake will result in a timeout. Count has been reset to **1**.*"
            else:
                timeout_seconds = 30
                try:
                    duration = datetime.timedelta(seconds=timeout_seconds)
                    await message.author.timeout(duration, reason="Counting mistake: 3rd+ fault")
                    punishment_str = f"*You are timed out for {timeout_seconds} seconds. The count has been reset to **1**.*"
                except discord.Forbidden:
                    punishment_str = "*(Failed to mute: Missing Permissions). The count has been reset to **1**.*"
                
            fail_embed = discord.Embed(
                title="❌ Streak Ruined!",
                description=f"{message.author.mention} messed up! The next number was supposed to be **{current_number}**.\n\n**{roast}**\n\n{punishment_str}",
                color=discord.Color.red()
            )
            await message.channel.send(embed=fail_embed)
            
        db.close()

async def setup(bot):
    await bot.add_cog(FunCounting(bot))
