import traceback
import sys
import discord
from discord.ext import commands
import asyncio
import os

bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())

async def load():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            if filename in ['eco_stocks_core.py', 'eco_stocks_list.py']:
                print(f'-> Skipped: {filename}')
                continue
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'-> Loaded: {filename}')
            except Exception as e:
                print(f'-> Failed {filename}: {e}')

asyncio.run(load())
