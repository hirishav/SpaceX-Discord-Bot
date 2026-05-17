# main.py
import discord
from discord.ext import commands
import os
import sqlite3
from flask import Flask
from threading import Thread

# Environment aur Config handle karna
try:
    import config
    OWNER_ID = config.OWNER_ID
    BOT_TOKEN = config.BOT_TOKEN
except ImportError:
    OWNER_ID = 727718500663033897  
    BOT_TOKEN = os.getenv("BOT_TOKEN")

# Flask Web Server Setup (For 24/7 Render)
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

# Bot instance (Hybrid command support ke sath)
bot = commands.Bot(command_prefix=get_prefix, intents=intents, owner_ids={OWNER_ID})
bot.remove_command('help')

@bot.event
async def on_ready():
    print("---------------------------------------")
    print(f'Mubarak ho! Bot ka naam hai: {bot.user.name}')
    
    # DATABASE SETUP
    conn = sqlite3.connect("warnings.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS warnings (id INTEGER PRIMARY KEY AUTOINCREMENT, server_id TEXT, user_id TEXT, reason TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)")
    cursor.execute("CREATE TABLE IF NOT EXISTS afk (server_id TEXT, user_id TEXT, reason TEXT, timestamp INTEGER, PRIMARY KEY (server_id, user_id))")
    conn.commit()
    conn.close()
    
    print('Modules load ho rahe hain...')
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f'-> Successfully Loaded: {filename}')
            
    print('Bot successfully online aa gaya hai! 🎉')
    print("---------------------------------------")

# NAYA JADU: Owner Only Sync Command (Slash commands register karne ke liye)
@bot.command(name="sync", hidden=True)
@commands.is_owner()
async def sync(ctx):
    """Is command se saare slash commands Discord par register ho jayenge."""
    await ctx.send("🔄 Slash commands ko Sync kiya jaa raha hai, thoda sabr rakhein...")
    try:
        synced = await bot.tree.sync()
        await ctx.send(f"✅ Kamyabi se **{len(synced)}** Slash Commands pure Discord par sync ho gaye hain! Ab `/` daba kar check karein.")
    except Exception as e:
        await ctx.send(f"❌ Sync fail ho gaya: {e}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user.mentioned_in(message) and len(message.content.strip().split()) == 1:
        embed = discord.Embed(
            title=f"Hello {message.author.name}! 👋",
            description=f"Mera current prefix **`!!`** hai.\nAap commands ko **`!!help`**, `/help` ya mujhe ping karke **`{bot.user.mention} help`** tarike se use kar sakte hain!",
            color=discord.Color.blue()
        )
        return await message.channel.send(embed=embed)

    await bot.process_commands(message)

if __name__ == '__main__':
    keep_alive()
    bot.run(BOT_TOKEN)