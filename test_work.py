import asyncio, discord
from discord.ext import commands

bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())
bot.remove_command('help')

class MockContext:
    def __init__(self):
        class Author:
            id = 123
            mention = "<@123>"
        self.author = Author()
    
    async def send(self, **kwargs):
        print("MOCK SEND:", kwargs)

async def main():
    await bot.load_extension('cogs.eco_work')
    cmd = bot.get_command('work')
    ctx = MockContext()
    await cmd.callback(cmd.cog, ctx)

asyncio.run(main())
