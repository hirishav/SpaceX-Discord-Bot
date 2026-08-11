import discord
from discord.ext import commands

class OwnerBadge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="badge")
    @commands.is_owner()
    async def add_badge(self, ctx, user: discord.User, *, badge: str):
        """Add a custom badge to a user's profile."""
        cursor = self.bot.db.cursor()
        try:
            cursor.execute("INSERT INTO user_badges (user_id, badge) VALUES (?, ?)", (str(user.id), badge))
            self.bot.db.commit()
            await ctx.send(f"<a:giveaway:686211362548088858> Added badge {badge} to **{user.name}**!")
        except Exception as e:
            await ctx.send(f"❌ Error adding badge (maybe they already have it?): {e}")

    @commands.hybrid_command(name="removebadge")
    @commands.is_owner()
    async def remove_badge(self, ctx, user: discord.User, *, badge: str):
        """Remove a custom badge from a user's profile."""
        cursor = self.bot.db.cursor()
        cursor.execute("DELETE FROM user_badges WHERE user_id = ? AND badge = ?", (str(user.id), badge))
        self.bot.db.commit()
        await ctx.send(f"<a:giveaway:686211362548088858> Removed badge {badge} from **{user.name}**!")

async def setup(bot):
    await bot.add_cog(OwnerBadge(bot))
