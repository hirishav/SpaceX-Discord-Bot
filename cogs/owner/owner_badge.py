import discord
from discord.ext import commands

class OwnerBadge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="badge", invoke_without_command=True)
    @commands.is_owner()
    async def badge_group(self, ctx, user: discord.User = None, *, badge: str = None):
        """Manage custom badges for a user's profile."""
        if user and badge:
            # Fallback for backwards compatibility if they type `!!badge @user 👑`
            await ctx.invoke(self.add_badge, user=user, badge=badge)
        else:
            await ctx.send(f"❌ Sahi format: `{ctx.prefix}badge add @user <badge>` ya `{ctx.prefix}badge remove @user <badge>`")

    @badge_group.command(name="add")
    @commands.is_owner()
    async def add_badge(self, ctx, user: discord.User, *, badge: str):
        """Add a custom badge to a user's profile."""
        cursor = self.bot.db.cursor()
        try:
            cursor.execute("INSERT INTO user_badges (user_id, badge) VALUES (?, ?)", (str(user.id), badge))
            self.bot.db.commit()
            await ctx.send(f"✅ Added badge {badge} to **{user.name}**!")
        except Exception as e:
            await ctx.send(f"❌ Error adding badge (maybe they already have it?): {e}")

    @badge_group.command(name="remove", aliases=["rm"])
    @commands.is_owner()
    async def remove_badge(self, ctx, user: discord.User, *, badge: str):
        """Remove a custom badge from a user's profile."""
        cursor = self.bot.db.cursor()
        cursor.execute("DELETE FROM user_badges WHERE user_id = ? AND badge = ?", (str(user.id), badge))
        self.bot.db.commit()
        await ctx.send(f"✅ Removed badge {badge} from **{user.name}**!")

async def setup(bot):
    await bot.add_cog(OwnerBadge(bot))
