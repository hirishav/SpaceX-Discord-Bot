import discord
from discord.ext import commands

SHOP_ITEMS = {
    "mic": {"name": "🎙️ Blue Yeti Mic", "price": 1000, "desc": "Improves audio. +20% multiplier on streams."},
    "cam": {"name": "📷 4K Facecam", "price": 3000, "desc": "Crisp quality. +20% multiplier."},
    "rgb": {"name": "💡 RGB Ring Light", "price": 5000, "desc": "Perfect lighting. +20% multiplier."},
    "pc": {"name": "🖥️ RTX 5090 PC", "price": 15000, "desc": "Zero lag. +20% multiplier."},
    "studio": {"name": "🏠 Streaming Studio", "price": 50000, "desc": "Professional setup. +20% multiplier."}
}

class InfluencerShop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def shop(self, ctx):
        embed = discord.Embed(title="🛒 Creator Shop", description="Buy gear to increase your stream and video multipliers!", color=0x2b2d31)
        
        for item_id, item in SHOP_ITEMS.items():
            embed.add_field(name=f"{item['name']} — `${item['price']:,}`", value=f"ID: `{item_id}`\n{item['desc']}", inline=False)
            
        embed.set_footer(text="Use !buy <id> to purchase an item.")
        await ctx.send(embed=embed)

    @commands.command()
    async def buy(self, ctx, item_id: str = None):
        if not item_id or item_id.lower() not in SHOP_ITEMS:
            return await ctx.send("❌ Please provide a valid item ID. Use `!shop` to see items.")
            
        item_id = item_id.lower()
        item = SHOP_ITEMS[item_id]
        user_id = str(ctx.author.id)
        
        cursor = self.bot.db.cursor()
        cursor.execute("INSERT OR IGNORE INTO influencer_stats (user_id) VALUES (?)", (user_id,))
        
        cursor.execute("SELECT cash FROM influencer_stats WHERE user_id = ?", (user_id,))
        cash = cursor.fetchone()[0]
        
        if cash < item['price']:
            return await ctx.send(f"❌ You need `${item['price']:,}` to buy **{item['name']}**. You only have `${cash:,}`.")
            
        cursor.execute("SELECT 1 FROM influencer_gear WHERE user_id = ? AND item_id = ?", (user_id, item_id))
        if cursor.fetchone():
            return await ctx.send(f"❌ You already own **{item['name']}**!")
            
        # Deduct cash and add item
        cursor.execute("UPDATE influencer_stats SET cash = cash - ? WHERE user_id = ?", (item['price'], user_id))
        cursor.execute("INSERT INTO influencer_gear (user_id, item_id) VALUES (?, ?)", (user_id, item_id))
        self.bot.db.commit()
        
        await ctx.send(f"✅ You successfully bought **{item['name']}** for `${item['price']:,}`! Your multipliers have increased.")

async def setup(bot):
    await bot.add_cog(InfluencerShop(bot))
