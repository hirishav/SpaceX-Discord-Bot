# main.py
import discord
from discord.ext import commands, tasks
import os
import database as sqlite3
import time
import asyncio
from pathlib import Path

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

import aiohttp
import topgg
import shutil
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from web_server import app, setup_web_server
import hypercorn.asyncio
from hypercorn.config import Config as HyperConfig

# Environment Variable aur Config setup
try:
    import config
    OWNER_ID = getattr(config, 'OWNER_ID', 727718500663033897)
    BOT_TOKEN = getattr(config, 'BOT_TOKEN', os.getenv("BOT_TOKEN"))
    TOPGG_TOKEN = getattr(config, 'TOPGG_TOKEN', os.getenv("TOPGG_TOKEN"))
    BACKUP_CHANNEL_ID = getattr(config, 'BACKUP_CHANNEL_ID', os.getenv("BACKUP_CHANNEL_ID"))
except (ImportError, AttributeError):
    OWNER_ID = 727718500663033897  # Permanent backup
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    TOPGG_TOKEN = os.getenv("TOPGG_TOKEN")
    BACKUP_CHANNEL_ID = os.getenv("BACKUP_CHANNEL_ID")

# Web Server is now handled by web_server.py

# ⚙️ DYNAMIC CUSTOM PREFIX FETCH ENGINE (OPTIMIZED)
def get_prefix(bot, message):
    base_prefix = '!!'
    if not message.guild:
        return base_prefix
    
    # ⚡ Cache se instantly uthao (0.000ms Latency)
    if hasattr(bot, 'prefix_cache') and message.guild.id in bot.prefix_cache:
        base_prefix = bot.prefix_cache[message.guild.id]
        
    is_whitelisted = False
    if message.author.id in bot.owner_ids or (hasattr(bot, 'prefixless_cache') and message.author.id in bot.prefixless_cache):
        is_whitelisted = True
    elif hasattr(bot, 'prefixless_servers_cache') and message.guild.id in bot.prefixless_servers_cache:
        expires_at = bot.prefixless_servers_cache[message.guild.id]
        if expires_at == -1 or int(time.time()) < expires_at:
            is_whitelisted = True

    if is_whitelisted and message.content:
        tokens = message.content.split()
        if tokens:
            first_word = tokens[0].lower()
            if first_word in bot.all_commands:
                return (base_prefix, "")
                
    return base_prefix

# Discord Bot Setup - Optimized for 512MB RAM
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
# Presences disabled to save MASSIVE amounts of RAM

class SpaceXBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=get_prefix,
            intents=intents,
            owner_ids={OWNER_ID, 1061268825913438358},
            chunk_guilds_at_startup=False,
            case_insensitive=True
        )
        self.remove_command('help')
        
        # 🔥 MAINTENANCE GLOBALS
        self.maintenance_mode = False
        self.maintenance_end = 0
        self.server_maintenance = {} # Format: {server_id: end_time}
        self.interrupted_users = {} # Format: {user_id: channel_id}
        
        self.prefix_cache = {}
        self.prefixless_cache = set()
        self.prefixless_servers_cache = {}
        self.blacklist_cache = {}
        self.premium_cache = set()
        
        # Disable configs cache
        self.disabled_commands_cache = {} # server_id -> set of commands
        self.disabled_commands_channel_cache = {} # channel_id -> set of commands
        self.enabled_commands_channel_cache = {} # channel_id -> set of commands
        self.disabled_modules_server_cache = {} # server_id -> set of modules
        self.disabled_modules_channel_cache = {} # channel_id -> set of modules
        self.enabled_modules_channel_cache = {} # channel_id -> set of modules
        
        self.topgg_client = None
        self.add_check(self.check_disabled_commands)
        self.tree.interaction_check = self.tree_interaction_check

    def _resolve_module(self, cmd) -> str:
        cog_name = getattr(cmd, 'cog_name', None) or (cmd.cog.__class__.__name__ if getattr(cmd, 'cog', None) else "")
        if cog_name == "OwnerInfo": return "utility"
        if getattr(cmd, 'hidden', False) or cog_name.startswith("Owner") or cmd.name in {"blacklist"}: return "owner"
        if cog_name.startswith("Mod"): return "moderation"
        if cog_name.startswith("Eco") or cog_name.startswith("Stocks"): return "economy"
        if cog_name.startswith("Fun"): return "fun"
        if cog_name.startswith("Gen"): return "general"
        return "utility"

    async def tree_interaction_check(self, interaction: discord.Interaction):
        if not interaction.guild or not interaction.command:
            return True
            
        command_name = interaction.command.name
        
        if command_name in {"disable", "enable"}: 
            return True
            
        guild_id = interaction.guild.id
        channel_id = interaction.channel_id
        module_name = self._resolve_module(interaction.command)
        
        disabled_reason = None
        
        is_cmd_enabled_channel = channel_id in self.enabled_commands_channel_cache and command_name in self.enabled_commands_channel_cache[channel_id]
        is_mod_enabled_channel = channel_id in self.enabled_modules_channel_cache and module_name in self.enabled_modules_channel_cache[channel_id]
        
        if channel_id in self.disabled_commands_channel_cache and command_name in self.disabled_commands_channel_cache[channel_id]:
            disabled_reason = True
        elif not is_cmd_enabled_channel and guild_id in self.disabled_commands_cache and command_name in self.disabled_commands_cache[guild_id]:
            disabled_reason = True
        elif channel_id in self.disabled_modules_channel_cache and module_name in self.disabled_modules_channel_cache[channel_id]:
            disabled_reason = True
        elif not is_mod_enabled_channel and not is_cmd_enabled_channel and guild_id in self.disabled_modules_server_cache and module_name in self.disabled_modules_server_cache[guild_id]:
            disabled_reason = True
            
        if disabled_reason:
            return False
            
        return True

    async def check_disabled_commands(self, ctx):
        if getattr(ctx, 'is_sudo', False):
            return True
        if not ctx.guild or not ctx.command:
            return True
        if ctx.command.name in {"disable", "enable"}:
            return True
            
        guild_id = ctx.guild.id
        channel_id = ctx.channel.id
        command_name = ctx.command.name
        module_name = self._resolve_module(ctx.command)
        
        disabled_reason = None
        
        is_cmd_enabled_channel = channel_id in self.enabled_commands_channel_cache and command_name in self.enabled_commands_channel_cache[channel_id]
        is_mod_enabled_channel = channel_id in self.enabled_modules_channel_cache and module_name in self.enabled_modules_channel_cache[channel_id]
        
        if channel_id in self.disabled_commands_channel_cache and command_name in self.disabled_commands_channel_cache[channel_id]:
            disabled_reason = True
        elif not is_cmd_enabled_channel and guild_id in self.disabled_commands_cache and command_name in self.disabled_commands_cache[guild_id]:
            disabled_reason = True
        elif channel_id in self.disabled_modules_channel_cache and module_name in self.disabled_modules_channel_cache[channel_id]:
            disabled_reason = True
        elif not is_mod_enabled_channel and not is_cmd_enabled_channel and guild_id in self.disabled_modules_server_cache and module_name in self.disabled_modules_server_cache[guild_id]:
            disabled_reason = True
            
        if disabled_reason:
            return False
            
        return True

    async def post_topgg_stats(self):
        """Top.gg API me direct live server count post karta hai (zero dependency on topgg-py)."""
        if not TOPGG_TOKEN or not self.user:
            return False, "TOPGG_TOKEN missing ya Bot abhi ready nahi hai."

        url = f"https://top.gg/api/bots/{self.user.id}/stats"
        headers = {
            "Authorization": TOPGG_TOKEN,
            "Content-Type": "application/json"
        }
        payload = {
            "server_count": len(self.guilds)
        }
        if self.shard_count and self.shard_count > 1:
            payload["shard_count"] = self.shard_count

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        print(f"-> Successfully posted {len(self.guilds)} servers to Top.gg!")
                        return True, f"Successfully posted {len(self.guilds)} servers to Top.gg! (Status 200)"
                    else:
                        text = await resp.text()
                        print(f"⚠️ Top.gg API returned status {resp.status}: {text}")
                        return False, f"Status {resp.status}: {text}"
        except Exception as e:
            print(f"⚠️ Top.gg stats posting failed: {e}")
            return False, str(e)

    @tasks.loop(minutes=30)
    async def topgg_autopost_task(self):
        await self.wait_until_ready()
        await self.post_topgg_stats()

    @tasks.loop(minutes=60)
    async def backup_db_task(self):
        await self.wait_until_ready()
        if not BACKUP_CHANNEL_ID:
            return
            
        try:
            channel = self.get_channel(int(BACKUP_CHANNEL_ID)) or await self.fetch_channel(int(BACKUP_CHANNEL_ID))
            if channel:
                # Use SQLite backup API to safely flush WAL and snapshot the DB
                import sqlite3
                backup_conn = sqlite3.connect("warnings_backup.db")
                with backup_conn:
                    self.db.backup(backup_conn)
                backup_conn.close()
                
                file = discord.File("warnings_backup.db", filename="warnings.db")
                await channel.send(content=f"Database Backup at <t:{int(time.time())}:F>", file=file)
                os.remove("warnings_backup.db")
                print("-> ✅ DB Backup successfully uploaded to Discord!")
        except Exception as e:
            print(f"⚠️ Failed to upload DB backup: {e}")

    async def download_db_backup(self):
        if not BACKUP_CHANNEL_ID:
            print("⚠️ BACKUP_CHANNEL_ID not set. Skipping DB backup download.")
            return
            
        if os.path.exists("warnings.db") and os.path.getsize("warnings.db") > 0:
            print("-> Local warnings.db already exists and is not empty. Skipping cloud backup download to prevent data loss.")
            print("-> Note: Use !!restorebackup command if you really want to force load the cloud backup.")
            return
            
        print("-> Checking for DB backups in the cloud channel...")
        try:
            url = f"https://discord.com/api/v10/channels/{BACKUP_CHANNEL_ID}/messages?limit=10"
            headers = {"Authorization": f"Bot {BOT_TOKEN}"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    if resp.status == 200:
                        messages = await resp.json()
                        for msg in messages:
                            if msg.get("attachments"):
                                for att in msg["attachments"]:
                                    if att["filename"] == "warnings.db":
                                        print(f"-> Found warnings.db backup! Downloading...")
                                        async with session.get(att["url"]) as file_resp:
                                            if file_resp.status == 200:
                                                with open("warnings.db", "wb") as f:
                                                    f.write(await file_resp.read())
                                                print("-> ✅ Successfully restored warnings.db from the cloud!")
                                                return
                    else:
                        print(f"⚠️ Failed to fetch backups. Status: {resp.status}")
        except Exception as e:
            print(f"⚠️ Error downloading DB backup: {e}")

    async def setup_hook(self):
        # 🚀 START WEB SERVER
        setup_web_server(self)
        config = HyperConfig()
        config.bind = ["0.0.0.0:8080"]
        self.loop.create_task(hypercorn.asyncio.serve(app, config))
        print("-> Background Web Server Started via Hypercorn!")

        # ⚡ RESTORE CLOUD DATABASE FIRST
        await self.download_db_backup()

        # ⚡ PERSISTENT CONNECTION MATRIX
        self.db = sqlite3.connect("warnings.db", check_same_thread=False, isolation_level=None)
        cursor = self.db.cursor()

        # 🔥 SQLITE PERFORMANCE PRAGMAS (Ultra-Speed Tweaks)
        cursor.execute("PRAGMA journal_mode=WAL;")  # Write-Ahead Logging for concurrency
        cursor.execute("PRAGMA synchronous=NORMAL;") # Fast disk writing bounds
        cursor.execute("PRAGMA cache_size=-8000;")  # 8MB cache optimization memory allocation

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
        
        # GLOBAL ECONOMY TABLE
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

        # GLOBAL REPS TABLE
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reps (
            user_id TEXT PRIMARY KEY,
            rep_points INTEGER DEFAULT 0
        )
        """)

        # PREFIXLESS USERS LEAF MATRIX TABLE
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS prefixless_users (
            user_id TEXT PRIMARY KEY
        )
        """)

        # PREFIXLESS SERVERS TABLE
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS prefixless_servers (
            server_id TEXT PRIMARY KEY,
            expires_at INTEGER
        )
        """)

        # USER BADGES TABLE
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_badges (
            user_id TEXT,
            badge TEXT,
            PRIMARY KEY (user_id, badge)
        )
        """)

        # BLACKLISTED SERVERS TABLE
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS blacklisted_servers (
            server_id TEXT PRIMARY KEY
        )
        """)

        # PREMIUM SERVERS TABLE
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS premium_servers (
            server_id TEXT PRIMARY KEY
        )
        """)
        
        # DISABLED COMMANDS TABLE
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS disabled_commands (
            server_id TEXT,
            command_name TEXT,
            PRIMARY KEY (server_id, command_name)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS disabled_commands_channel (
            channel_id TEXT,
            command_name TEXT,
            PRIMARY KEY (channel_id, command_name)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS disabled_modules_server (
            server_id TEXT,
            module_name TEXT,
            PRIMARY KEY (server_id, module_name)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS disabled_modules_channel (
            channel_id TEXT,
            module_name TEXT,
            PRIMARY KEY (channel_id, module_name)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS enabled_commands_channel (
            channel_id TEXT,
            command_name TEXT,
            PRIMARY KEY (channel_id, command_name)
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS enabled_modules_channel (
            channel_id TEXT,
            module_name TEXT,
            PRIMARY KEY (channel_id, module_name)
        )
        """)

        # TEMPORARY ROLES TABLE
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS temproles (
            guild_id TEXT,
            user_id TEXT,
            role_id TEXT,
            expires_at INTEGER,
            PRIMARY KEY (guild_id, user_id, role_id)
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

        cursor.execute("SELECT server_id, expires_at FROM prefixless_servers")
        for s_id, exp_at in cursor.fetchall():
            self.prefixless_servers_cache[int(s_id)] = exp_at

        cursor.execute("SELECT user_id, expires_at, reason FROM blacklist")
        for u_id, exp_at, reason in cursor.fetchall():
            self.blacklist_cache[int(u_id)] = (exp_at, reason)

        cursor.execute("SELECT server_id FROM premium_servers")
        for (s_id,) in cursor.fetchall():
            self.premium_cache.add(int(s_id))
            
        cursor.execute("SELECT server_id, command_name FROM disabled_commands")
        for s_id, cmd_name in cursor.fetchall():
            s_id_int = int(s_id)
            if s_id_int not in self.disabled_commands_cache:
                self.disabled_commands_cache[s_id_int] = set()
            self.disabled_commands_cache[s_id_int].add(cmd_name)
            
        cursor.execute("SELECT channel_id, command_name FROM disabled_commands_channel")
        for c_id, cmd_name in cursor.fetchall():
            c_id_int = int(c_id)
            if c_id_int not in self.disabled_commands_channel_cache:
                self.disabled_commands_channel_cache[c_id_int] = set()
            self.disabled_commands_channel_cache[c_id_int].add(cmd_name)

        cursor.execute("SELECT server_id, module_name FROM disabled_modules_server")
        for s_id, mod_name in cursor.fetchall():
            s_id_int = int(s_id)
            if s_id_int not in self.disabled_modules_server_cache:
                self.disabled_modules_server_cache[s_id_int] = set()
            self.disabled_modules_server_cache[s_id_int].add(mod_name)

        cursor.execute("SELECT channel_id, module_name FROM disabled_modules_channel")
        for c_id, mod_name in cursor.fetchall():
            c_id_int = int(c_id)
            if c_id_int not in self.disabled_modules_channel_cache:
                self.disabled_modules_channel_cache[c_id_int] = set()
            self.disabled_modules_channel_cache[c_id_int].add(mod_name)

        cursor.execute("SELECT channel_id, command_name FROM enabled_commands_channel")
        for c_id, cmd_name in cursor.fetchall():
            c_id_int = int(c_id)
            if c_id_int not in self.enabled_commands_channel_cache:
                self.enabled_commands_channel_cache[c_id_int] = set()
            self.enabled_commands_channel_cache[c_id_int].add(cmd_name)

        cursor.execute("SELECT channel_id, module_name FROM enabled_modules_channel")
        for c_id, mod_name in cursor.fetchall():
            c_id_int = int(c_id)
            if c_id_int not in self.enabled_modules_channel_cache:
                self.enabled_modules_channel_cache[c_id_int] = set()
            self.enabled_modules_channel_cache[c_id_int].add(mod_name)

        cursor.close()    
        print("-> Database Connected & Speed Cache Engines Synchronized!")
        
        # 🚀 TOP.GG API INTEGRATION MATRIX (DIRECT HTTP POST)
        if TOPGG_TOKEN:
            try:
                self.topgg_autopost_task.start()
                print("-> Top.gg Direct AutoPost task started (30m interval)!")
            except Exception as e:
                print(f"⚠️ Top.gg task start failed: {e}")
        else:
            print("⚠️ TOPGG_TOKEN missing. Top.gg stats posting is disabled.")

        # 🚀 START BACKUP TASK
        if BACKUP_CHANNEL_ID:
            self.backup_db_task.start()
            print("-> DB Cloud Backup task started (60m interval)!")

        print('Modules load ho rahe hain...')
        if os.path.exists('./cogs'):
            for path in Path('./cogs').rglob('*.py'):
                filename = path.name
                if filename in ['eco_stocks_core.py', 'eco_stocks_list.py']:
                    print(f'-> Skipped Non-Cog Utility File: {filename}')
                    continue
                    
                # Extract parts without '.py'
                module_path = '.'.join(path.parts)[:-3]
                
                try:
                    await self.load_extension(module_path)
                    print(f'-> Successfully Loaded: {module_path}')
                except Exception as e:
                    print(f'-> Failed to Load Extension {module_path}: {e}')

        print('Syncing slash commands...')
        try:
            synced = await self.tree.sync()
            print(f"-> Synced {len(synced)} slash commands globally!")
        except Exception as e:
            print(f"⚠️ Failed to sync slash commands: {e}")

bot = SpaceXBot()

@bot.event
async def on_ready():
    print("---------------------------------------")
    print(f'Mubarak ho! Bot ka naam hai: {bot.user.name}')
    print('Bot successfully online aa gaya hai! ✅')
    print("---------------------------------------")
    
    # 📈 TOP.GG GUILD COUNT POSTING (DIRECT)
    await bot.post_topgg_stats()

@bot.event
async def on_guild_join(guild):
    # Check if blacklisted
    cursor = bot.db.cursor()
    cursor.execute("SELECT server_id FROM blacklisted_servers WHERE server_id = ?", (str(guild.id),))
    row = cursor.fetchone()
    cursor.close()
    if row:
        print(f"-> Left blacklisted server automatically: {guild.name}")
        await guild.leave()
        return

    print(f"-> Joined new server: {guild.name} (Total: {len(bot.guilds)})")
    await bot.post_topgg_stats()

@bot.event
async def on_guild_remove(guild):
    print(f"-> Left server: {guild.name} (Total: {len(bot.guilds)})")
    await bot.post_topgg_stats()

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
    display_prefix = current_prefix[0] if isinstance(current_prefix, tuple) else current_prefix

    # 🚨 STEP A: PREFIXLESS ROUTING LAYER ENGINE (FAST LOOKUP)
    is_whitelisted = False
    if message.author.id in bot.owner_ids or message.author.id in bot.prefixless_cache:
        is_whitelisted = True
    elif message.guild and message.guild.id in bot.prefixless_servers_cache:
        expires_at = bot.prefixless_servers_cache[message.guild.id]
        if expires_at == -1 or int(time.time()) < expires_at:
            is_whitelisted = True
        else:
            del bot.prefixless_servers_cache[message.guild.id]
            cursor = bot.db.cursor()
            cursor.execute("DELETE FROM prefixless_servers WHERE server_id = ?", (str(message.guild.id),))
            bot.db.commit()

    # 1. 🔥 MAINTENANCE SYSTEM PEHRA
    is_owner = message.author.id in bot.owner_ids
    if not is_owner:
        is_maintenance = False
        end_time = 0
        guild_id = message.guild.id if message.guild else None
        
        # Check global maintenance
        if bot.maintenance_mode:
            if int(time.time()) >= bot.maintenance_end:
                bot.maintenance_mode = False
            else:
                is_maintenance = True
                end_time = bot.maintenance_end
                
        # Check server maintenance
        if not is_maintenance and guild_id and hasattr(bot, 'server_maintenance') and guild_id in bot.server_maintenance:
            if int(time.time()) >= bot.server_maintenance[guild_id]:
                del bot.server_maintenance[guild_id]
            else:
                is_maintenance = True
                end_time = bot.server_maintenance[guild_id]

        if is_maintenance:
            bot.interrupted_users[message.author.id] = message.channel.id
            time_left = get_remaining_time_str(end_time)
            
            if message.content.startswith(current_prefix):
                embed = discord.Embed(
                    title="⚙️ Bot Under Maintenance",
                    description=f"🤖 Sorry bhai, abhi thoda maintenance ka kaam chal raha hai mere andar.\n\n⏳ **Bas itni der mein wapas aata hoon:** `{time_left}`",
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
            description=f"Is server me mera current prefix **``{display_prefix}``** hai.\nAap commands ko **`{display_prefix}help`** tarike se use kar sakte hain!",
            color=discord.Color.blue()
        )
        return await message.channel.send(embed=embed)

    await bot.process_commands(message)

if __name__ == '__main__':
    if BOT_TOKEN:
        bot.run(BOT_TOKEN)
    else:
        print("💥 BOT_TOKEN is missing! Please configure config.py or environment variables.")
