import asyncio
import discord
from discord.ext import commands
import os

class MockMessage:
    def __init__(self, content):
        self.content = content
        self.author = type('Author', (object,), {'id': 123, 'bot': False})()
        self.channel = type('Channel', (object,), {'id': 456, 'send': self.mock_send})()
        self.guild = type('Guild', (object,), {'id': 789})()
        
    async def mock_send(self, *args, **kwargs):
        print(f"MOCK MESSAGE SEND: args={args} kwargs={kwargs}")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!!', intents=intents)

@bot.event
async def on_command_error(ctx, error):
    print(f"ON COMMAND ERROR: {type(error)}: {error}")

async def main():
    await bot.load_extension('cogs.eco_work')
    await bot.load_extension('cogs.eco_daily')
    msg = MockMessage('!!work')
    ctx = await bot.get_context(msg)
    print(f"CTX COMMAND: {ctx.command}")
    await bot.invoke(ctx)
    print("DONE INVOKING")

asyncio.run(main())
