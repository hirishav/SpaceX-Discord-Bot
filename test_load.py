import traceback
import sys
import discord
from discord.ext import commands
import asyncio

bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())

async def load():
    cogs = [
        'cogs.eco_work',
        'cogs.eco_crime',
        'cogs.eco_slut',
        'cogs.eco_rob',
        'cogs.eco_mine',
        'cogs.eco_daily',
        'cogs.eco_weekly'
    ]
    for ext in cogs:
        try:
            await bot.load_extension(ext)
            print(f'Loaded {ext}')
        except Exception as e:
            print(f'Failed {ext}: {e}')
            traceback.print_exc()

asyncio.run(load())
