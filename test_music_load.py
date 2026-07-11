import asyncio
import os
import discord
from discord.ext import commands

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

async def test_load():
    try:
        await bot.load_extension("cogs.music")
        print("Successfully loaded cogs.music")
        print("Commands:", [c.name for c in bot.commands])
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(test_load())
