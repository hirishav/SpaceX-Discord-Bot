# main.py
import discord
from discord.ext import commands
import os
import sqlite3
import time
import asyncio

# Environment Variable aur Config setup
try:
    import config
    OWNER_ID = config.OWNER_ID
    BOT_TOKEN = config.BOT_TOKEN
except ImportError:
    OWNER_ID = 727718500663033897  # Aapki asli Discord ID permanent backup
    BOT_TOKEN = os.getenv("BOT_TOKEN")

# Web Server ke liye imports (For Render 24/7)
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "SpaceX Bot Is Alive & Running 24/7! 🚀"

def run_server():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_server)
    t.start()

# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True 

def get_prefix(bot, message):
    prefixes = ['!!']
    return commands.when_mentioned_or(*prefixes)(bot, message)

bot = commands.Bot(command_prefix=get_prefix, intents=intents, owner_ids={OWNER_ID})
bot.remove_command('help')

# 🔥 MAINTENANCE GLOBALS
bot.maintenance_mode = False
bot.maintenance_end = 0
bot.interrupted_users = {} # Format: {user_id: channel_id}

@bot.event
async def on_ready():
    print("---------------------------------------")
    print(f'Mubarak ho! Bot ka naam hai: {bot.user.name}')
    
    # DATABASE SETUP
    conn = sqlite3.connect("warnings.db")
    cursor = conn.cursor()

    # CENTRAL MODERATION LOGS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mod_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        server_id TEXT,
        user_id TEXT,
        action TEXT,
        moderator_id TEXT,
        reason TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Moderation & AFK Tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS warnings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        server_id TEXT,
        user_id TEXT,
        reason TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS afk (
        server_id TEXT,
        user_id TEXT,
        reason TEXT,
        timestamp INTEGER,
        PRIMARY KEY (server_id, user_id)
    )
    """)
    
    # GLOBAL ECONOMY TABLE (OwO Style)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS economy (
        user_id TEXT PRIMARY KEY,
        wallet INTEGER DEFAULT 0,
        bank INTEGER DEFAULT 0
    )
    """)
    
    # GLOBAL BLACKLIST TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS blacklist (
        user_id TEXT PRIMARY KEY,
        expires_at INTEGER,
        reason TEXT
    )
    """)
    
    conn.commit()
    conn.close()
    print("-> Database Connected & All Clean Tables Ready!")
    
    print('Modules load ho rahe hain...')
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f'-> Successfully Loaded: {filename}')
            
    print('Bot successfully online aa gaya hai! 🎉')
    print("---------------------------------------")

def get_remaining_time_str(expires_at):
    remaining = expires_at - int(time.time())
    if remaining <= 0:
        return "kuch hi seconds"
    
    hours = remaining // 3600
    minutes = (remaining % 3600) // 60
    seconds = remaining % 60
    
    time_str = ""
    if hours > 0:
        time_str += f"{hours}h "
    if minutes > 0:
        time_str += f"{minutes}m "
    time_str += f"{seconds}s"
    return time_str.strip()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 1. 🔥 MAINTENANCE SYSTEM PEHRA
    is_owner = message.author.id in bot.owner_ids
    if bot.maintenance_mode and not is_owner:
        if int(time.time()) >= bot.maintenance_end:
            # Loop check safety filter background check failsafe trigger
            bot.maintenance_mode = False
        else:
            # User ko alert list queue me safe karo ping ke liye
            bot.interrupted_users[message.author.id] = message.channel.id
            
            # Dynamic countdown calculations
            time_left = get_remaining_time_str(bot.maintenance_end)
            
            # Check agar command register tha tabhi error popup dein
            if message.content.startswith('!!'):
                embed = discord.Embed(
                    title="⚙️ Bot Under Maintenance",
                    description=f"🤖 Sorry buddy, I am under maintenance right now.\n\n⏳ **I will be back just after:** `{time_left}`",
                    color=discord.Color.red()
                )
                return await message.channel.send(embed=embed)
            return

    # 2. 🚨 GLOBAL BLACKLIST CHECKER
    current_time = int(time.time())
    conn = sqlite3.connect("warnings.db")
    cursor = conn.cursor()
    cursor.execute("SELECT expires_at, reason FROM blacklist WHERE user_id = ?", (str(message.author.id),))
    row = cursor.fetchone()
    conn.close()

    if row:
        expires_at, reason = row[0], row[1]
        if expires_at == -1 or current_time < expires_at:
            if message.content.startswith("!!blacklist") or message.content.startswith("!!bl"):
                pass
            else:
                return
        elif current_time >= expires_at:
            conn = sqlite3.connect("warnings.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM blacklist WHERE user_id = ?", (str(message.author.id),))
            conn.commit()
            conn.close()

    if bot.user.mentioned_in(message) and len(message.content.strip().split()) == 1:
        embed = discord.Embed(
            title=f"Hello {message.author.name}! 👋",
            description=f"Mera current prefix **``!!``** hai.\nAap commands ko **`!!help`** tarike se use kar sakte hain!",
            color=discord.Color.blue()
        )
        return await message.channel.send(embed=embed)

    await bot.process_commands(message)

if __name__ == '__main__':
    keep_alive()
    print("-> Background Web Server Started!")
    bot.run(BOT_TOKEN)