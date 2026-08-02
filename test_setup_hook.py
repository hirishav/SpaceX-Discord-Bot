import asyncio
from main import SpaceXBot
import os

async def test_setup():
    bot = SpaceXBot()
    try:
        await bot.setup_hook()
        print("Setup hook finished successfully!")
        print("Commands:", [c.name for c in bot.commands])
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(test_setup())
