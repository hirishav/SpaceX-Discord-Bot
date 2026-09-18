import discord
from discord.ext import commands
import sqlite3
import os

try:
    import config
except ImportError:
    config = None

class OwnerAddOwner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._init_db()
        self._load_owners()

    def _init_db(self):
        cursor = self.bot.db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trusted_owners (
                user_id TEXT PRIMARY KEY
            )
        ''')
        self.bot.db.commit()

    def _load_owners(self):
        cursor = self.bot.db.cursor()
        cursor.execute("SELECT user_id FROM trusted_owners")
        rows = cursor.fetchall()
        for row in rows:
            try:
                self.bot.owner_ids.add(int(row[0]))
            except ValueError:
                pass
        cursor.close()

    @commands.command(aliases=['ao'], hidden=True)
    @commands.is_owner()
    async def addowner(self, ctx, user: discord.User = None):
        if not user:
            embed = discord.Embed(
                title="❌ Error",
                description="Please mention a user or provide their ID.\nUsage: `!!addowner @user`",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        user_id_str = str(user.id)
        
        cursor = self.bot.db.cursor()
        cursor.execute("SELECT user_id FROM trusted_owners WHERE user_id = ?", (user_id_str,))
        if cursor.fetchone():
            embed = discord.Embed(
                title="⚠️ Already Owner",
                description=f"{user.mention} is already a trusted owner.",
                color=discord.Color.orange()
            )
            return await ctx.send(embed=embed)

        cursor.execute("INSERT INTO trusted_owners (user_id) VALUES (?)", (user_id_str,))
        self.bot.db.commit()
        cursor.close()

        self.bot.owner_ids.add(user.id)

        embed = discord.Embed(
            title="✅ Owner Added",
            description=f"Successfully granted owner permissions to {user.mention}.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=['ro'], hidden=True)
    @commands.is_owner()
    async def removeowner(self, ctx, user: discord.User = None):
        if not user:
            embed = discord.Embed(
                title="❌ Error",
                description="Please mention a user or provide their ID.\nUsage: `!!removeowner @user`",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        main_owner_id = getattr(config, 'OWNER_ID', 727718500663033897) if config else int(os.environ.get('OWNER_ID', 727718500663033897))
        if user.id == main_owner_id:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You cannot remove the main bot owner!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)

        user_id_str = str(user.id)
        
        cursor = self.bot.db.cursor()
        cursor.execute("SELECT user_id FROM trusted_owners WHERE user_id = ?", (user_id_str,))
        if not cursor.fetchone():
            embed = discord.Embed(
                title="⚠️ Not an Owner",
                description=f"{user.mention} is not a trusted owner.",
                color=discord.Color.orange()
            )
            return await ctx.send(embed=embed)

        cursor.execute("DELETE FROM trusted_owners WHERE user_id = ?", (user_id_str,))
        self.bot.db.commit()
        cursor.close()

        if user.id in self.bot.owner_ids:
            self.bot.owner_ids.remove(user.id)

        embed = discord.Embed(
            title="✅ Owner Removed",
            description=f"Successfully revoked owner permissions from {user.mention}.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(OwnerAddOwner(bot))
