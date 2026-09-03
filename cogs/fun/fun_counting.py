import discord
from discord.ext import commands
import database
import time
import random
import asyncio

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
    @commands.has_permissions(manage_channels=True)
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
        
        # Check if user is blacklisted
        cursor.execute("SELECT expires_at FROM counting_blacklist WHERE user_id = ?", (str(message.author.id),))
        bl_row = cursor.fetchone()
        if bl_row:
            if time.time() < bl_row[0]:
                await message.delete()
                # Silently delete or send a temporary warning? Let's just delete to keep channel clean.
                db.close()
                return
            else:
                # Blacklist expired, remove from DB
                cursor.execute("DELETE FROM counting_blacklist WHERE user_id = ?", (str(message.author.id),))
                db.commit()
                
        # Validate message
        content = message.content.strip()
        
        # Try to parse number
        is_valid = False
        try:
            num = int(content)
            if num == current_number and str(message.author.id) != last_user_id:
                is_valid = True
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
            roast = random.choice(ROASTS)
            
            # Reset counter
            cursor.execute("""
            UPDATE counting_config 
            SET current_number = 1, last_user_id = NULL 
            WHERE channel_id = ?
            """, (str(message.channel.id),))
            
            # Blacklist for 10 minutes (600 seconds)
            expires_at = int(time.time()) + 600
            cursor.execute("""
            INSERT INTO counting_blacklist (user_id, expires_at)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET expires_at=excluded.expires_at
            """, (str(message.author.id), expires_at))
            db.commit()
            
            fail_embed = discord.Embed(
                title="❌ Streak Ruined!",
                description=f"{message.author.mention} messed up! The next number was supposed to be **{current_number}**.\n\n**{roast}**\n\n*You are blacklisted from counting for 10 minutes. The count has been reset to **1**.*",
                color=discord.Color.red()
            )
            await message.channel.send(embed=fail_embed)
            
        db.close()

async def setup(bot):
    await bot.add_cog(FunCounting(bot))
