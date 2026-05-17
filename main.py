# main.py
import discord
from discord.ext import commands
import os
import config
import sqlite3

# NAYA JADU: Web Server ke liye imports (Render par 24/7 chalane ke liye)
from flask import Flask
from threading import Thread

# Flask App setup
app = Flask('')

@app.route('/')
def home():
    return "SpaceX Bot Is Alive & Running 24/7! 🚀"

def run_server():
    # Render hamesha port 8080 ya dynamic port dhoondhta hai
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

bot = commands.Bot(command_prefix=get_prefix, intents=intents, owner_ids={config.OWNER_ID})
bot.remove_command('help')

@bot.event
async def on_ready():
    print("---------------------------------------")
    print(f'Mubarak ho! Bot ka naam hai: {bot.user.name}')
    
    # DATABASE SETUP
    conn = sqlite3.connect("warnings.db")
    cursor = conn.cursor()
    
    # Warnings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS warnings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        server_id TEXT,
        user_id TEXT,
        reason TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # AFK Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS afk (
        server_id TEXT,
        user_id TEXT,
        reason TEXT,
        timestamp INTEGER,
        PRIMARY KEY (server_id, user_id)
    )
    """)
    
    conn.commit()
    conn.close()
    print("-> Database Connected & AFK Table Ready!")
    
    print('Modules load ho rahe hain...')
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f'-> Successfully Loaded: {filename}')
            
    print('Bot successfully online aa gaya hai! 🎉')
    print("---------------------------------------")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user.mentioned_in(message) and len(message.content.strip().split()) == 1:
        embed = discord.Embed(
            title=f"Hello {message.author.name}! 👋",
            description=f"Mera current prefix **`!!`** hai.\nAap commands ko **`!!help`** ya mujhe ping karke **`{bot.user.mention} help`** tarike se use kar sakte hain!",
            color=discord.Color.blue()
        )
        return await message.channel.send(embed=embed)

    await bot.process_commands(message)

if __name__ == '__main__':
    # NAYA: Bot run hone se thik pehle Web Server ko background me chalu karega
    keep_alive()
    print("-> Background Web Server Started!")
    
    bot.run(config.BOT_TOKEN)