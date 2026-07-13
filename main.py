# main.py
import discord
from discord.ext import commands
import os
import sqlite3
import time
import asyncio
import aiohttp
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Environment Variable aur Config setup
try:
    import config
    OWNER_ID = config.OWNER_ID
    BOT_TOKEN = config.BOT_TOKEN
except (ImportError, AttributeError):
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

# ⚙️ DYNAMIC CUSTOM PREFIX FETCH ENGINE (OPTIMIZED)
def get_prefix(bot, message):
    if not message.guild:
        return '!!'
    
    # ⚡ Cache se instantly uthao (0.000ms Latency)
    if hasattr(bot, 'prefix_cache') and message.guild.id in bot.prefix_cache:
        return bot.prefix_cache[message.guild.id]
        
    return '!!'

# Discord Bot Setup - Optimized for 512MB RAM
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
# Presences disabled to save MASSIVE amounts of RAM

class SpaceXBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=get_prefix, intents=intents, owner_ids={OWNER_ID, 1061268825913438358}, chunk_guilds_at_startup=False)
        self.remove_command('help')
        
        # 🔥 MAINTENANCE GLOBALS
        self.maintenance_mode = False
        self.maintenance_end = 0
        self.interrupted_users = {} # Format: {user_id: channel_id}
        
        self.prefix_cache = {}
        self.prefixless_cache = set()
        self.blacklist_cache = {}
        self.premium_cache = set()

    async def setup_hook(self):
        # ⚡ PERSISTENT CONNECTION MATRIX
        # Initialize Database connection once safely
        self.db = sqlite3.connect("warnings.db", check_same_thread=False)
        cursor = self.db.cursor()

        # 🔥 SQLITE PERFORMANCE PRAGMAS (Ultra-Speed Tweaks)
        cursor.execute("PRAGMA journal_mode=WAL;")  # Write-Ahead Logging for concurrency
        cursor.execute("PRAGMA synchronous=NORMAL;") # Fast disk writing bounds
        cursor.execute("PRAGMA cache_size=-8000;")  # 8MB cache optimization memory allocation (down from 64MB to save RAM)

        # SERVER CUSTOM PREFIX TABLE
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS server_prefixes (
            server_id TEXT PRIMARY KEY,
            prefix TEXT
        )
        """)

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

        # PREFIXLESS USERS LEAF MATRIX TABLE
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS prefixless_users (
            user_id TEXT PRIMARY KEY
        )
        """)

        # PREMIUM SERVERS TABLE
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS premium_servers (
            server_id TEXT PRIMARY KEY
        )
        """)
        
        self.db.commit()
        
        # 🧠 WARM UP CACHE ENGINE: Memory hydration on startup
        print("-> Hydrating runtime memory cache arrays...")
        
        cursor.execute("SELECT server_id, prefix FROM server_prefixes")
        for s_id, pref in cursor.fetchall():
            self.prefix_cache[int(s_id)] = pref
            
        cursor.execute("SELECT user_id FROM prefixless_users")
        for (u_id,) in cursor.fetchall():
            self.prefixless_cache.add(int(u_id))

        cursor.execute("SELECT user_id, expires_at, reason FROM blacklist")
        for u_id, exp_at, reason in cursor.fetchall():
            self.blacklist_cache[int(u_id)] = (exp_at, reason)

        cursor.execute("SELECT server_id FROM premium_servers")
        for (s_id,) in cursor.fetchall():
            self.premium_cache.add(int(s_id))
            
        print("-> Database Connected & Speed Cache Engines Synchronized!")
        
        print('Modules load ho rahe hain...')
        if os.path.exists('./cogs'):
            for filename in os.listdir('./cogs'):
                if filename.endswith('.py'):
                    if filename in ['stocks_core.py', 'eco_stocks_list.py']:
                        print(f'-> Skipped Non-Cog Utility File: {filename}')
                        continue
                        
                    try:
                        await self.load_extension(f'cogs.{filename[:-3]}')
                        print(f'-> Successfully Loaded: {filename}')
                    except Exception as e:
                        print(f'💥 Failed to Load Extension {filename}: {e}')

bot = SpaceXBot()

@bot.event
async def on_ready():
    print("---------------------------------------")
    print(f'Mubarak ho! Bot ka naam hai: {bot.user.name}')
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
    if message.author.bot or not message.guild:
        return

    # Cache optimized fast lookup
    current_prefix = get_prefix(bot, message)

    # 🚨 STEP A: PREFIXLESS ROUTING LAYER ENGINE (FAST LOOKUP)
    is_whitelisted = False
    if message.author.id in bot.owner_ids or message.author.id in bot.prefixless_cache:
        is_whitelisted = True

    # Agar banda whitelist hai aur message bina command prefix ke aaya hai
    if is_whitelisted and not message.content.startswith(current_prefix):
        tokens = message.content.split()
        if tokens:
            first_word = tokens[0].lower()
            all_commands = [cmd.name for cmd in bot.commands]
            for cmd in bot.commands:
                all_commands.extend(cmd.aliases)
            
            if first_word in all_commands:
                message.content = f"{current_prefix}" + message.content

    # 1. 🔥 MAINTENANCE SYSTEM PEHRA
    is_owner = message.author.id in bot.owner_ids
    if bot.maintenance_mode and not is_owner:
        if int(time.time()) >= bot.maintenance_end:
            bot.maintenance_mode = False
        else:
            bot.interrupted_users[message.author.id] = message.channel.id
            time_left = get_remaining_time_str(bot.maintenance_end)
            
            if message.content.startswith(current_prefix):
                embed = discord.Embed(
                    title="⚙️ Bot Under Maintenance",
                    description=f"🤖 Sorry buddy, I am under maintenance right now.\n\n⏳ **I will be back just after:** `{time_left}`",
                    color=discord.Color.red()
                )
                return await message.channel.send(embed=embed)
            return

    # 2. 🚨 GLOBAL BLACKLIST CHECKER (Zero DB Queries - Ultra Fast)
    current_time = int(time.time())
    
    if message.author.id in bot.blacklist_cache:
        expires_at, reason = bot.blacklist_cache[message.author.id]
        
        # Check if the blacklist is still active (-1 is permanent)
        if expires_at == -1 or current_time < expires_at:
            # Allow them to check their blacklist status ONLY
            if message.content.startswith(f"{current_prefix}blacklist") or message.content.startswith(f"{current_prefix}bl"):
                pass
            else:
                return # Block command execution completely
        elif current_time >= expires_at:
            # Blacklist expired: Remove from cache and database
            del bot.blacklist_cache[message.author.id]
            cursor = bot.db.cursor()
            cursor.execute("DELETE FROM blacklist WHERE user_id = ?", (str(message.author.id),))
            bot.db.commit()

    # Dynamic ping response handler using current prefix
    if bot.user.mentioned_in(message) and len(message.content.strip().split()) == 1:
        embed = discord.Embed(
            title=f"Hello {message.author.name}! 👋",
            description=f"Is server me mera current prefix **``{current_prefix}``** hai.\nAap commands ko **`{current_prefix}help`** tarike se use kar sakte hain!",
            color=discord.Color.blue()
        )
        return await message.channel.send(embed=embed)

    await bot.process_commands(message)

if __name__ == '__main__':
    keep_alive()
    print("-> Background Web Server Started!")
    if BOT_TOKEN:
        bot.run(BOT_TOKEN)
    else:
        print("💥 BOT_TOKEN is missing! Please configure config.py or environment variables.")