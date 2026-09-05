import discord
from discord.ext import commands

SHOP_ITEMS = {
    # PROCESSORS
    "i3": {"category": "Processors", "name": "Intel Core i3", "price": 500, "multiplier": 0.05, "desc": "Basic streaming processor. +5% multiplier."},
    "i5": {"category": "Processors", "name": "Intel Core i5", "price": 1200, "multiplier": 0.10, "desc": "Mid-tier processor. +10% multiplier."},
    "i7": {"category": "Processors", "name": "Intel Core i7", "price": 3000, "multiplier": 0.20, "desc": "High-end processor. +20% multiplier."},
    "i9": {"category": "Processors", "name": "Intel Core i9", "price": 6000, "multiplier": 0.30, "desc": "Enthusiast processor. +30% multiplier."},
    "ryzen3": {"category": "Processors", "name": "AMD Ryzen 3", "price": 500, "multiplier": 0.05, "desc": "Budget AMD processor. +5% multiplier."},
    "ryzen5": {"category": "Processors", "name": "AMD Ryzen 5", "price": 1200, "multiplier": 0.10, "desc": "Solid AMD processor. +10% multiplier."},
    "ryzen7": {"category": "Processors", "name": "AMD Ryzen 7", "price": 3000, "multiplier": 0.20, "desc": "Great for multitasking. +20% multiplier."},
    "ryzen9": {"category": "Processors", "name": "AMD Ryzen 9", "price": 6000, "multiplier": 0.30, "desc": "Top tier AMD processor. +30% multiplier."},
    "threadripper": {"category": "Processors", "name": "AMD Threadripper", "price": 15000, "multiplier": 0.50, "desc": "God tier processor. +50% multiplier."},
    
    # RAM
    "ram2": {"category": "RAM", "name": "2GB RAM", "price": 50, "multiplier": 0.01, "desc": "Can barely open Chrome. +1% multiplier."},
    "ram4": {"category": "RAM", "name": "4GB RAM", "price": 100, "multiplier": 0.02, "desc": "Struggles with OBS. +2% multiplier."},
    "ram8": {"category": "RAM", "name": "8GB RAM", "price": 300, "multiplier": 0.05, "desc": "Minimum for streaming. +5% multiplier."},
    "ram16": {"category": "RAM", "name": "16GB RAM", "price": 700, "multiplier": 0.10, "desc": "Standard setup. +10% multiplier."},
    "ram32": {"category": "RAM", "name": "32GB RAM", "price": 1500, "multiplier": 0.20, "desc": "Comfortable multitasking. +20% multiplier."},
    "ram64": {"category": "RAM", "name": "64GB RAM", "price": 3500, "multiplier": 0.35, "desc": "Overkill for most. +35% multiplier."},
    "ram128": {"category": "RAM", "name": "128GB RAM", "price": 8000, "multiplier": 0.50, "desc": "You are running NASA. +50% multiplier."},
    
    # PERIPHERALS
    "mouse": {"category": "Peripherals", "name": "Gaming Mouse", "price": 200, "multiplier": 0.05, "desc": "RGB enabled. +5% multiplier."},
    "keyboard": {"category": "Peripherals", "name": "Mechanical Keyboard", "price": 400, "multiplier": 0.05, "desc": "Click clack sounds. +5% multiplier."},
    "controller": {"category": "Peripherals", "name": "Pro Controller", "price": 500, "multiplier": 0.05, "desc": "For controller players. +5% multiplier."},
    "ringlight": {"category": "Peripherals", "name": "RGB Ring Light", "price": 800, "multiplier": 0.10, "desc": "Perfect lighting. +10% multiplier."},
    "greenscreen": {"category": "Peripherals", "name": "Green Screen", "price": 1200, "multiplier": 0.15, "desc": "Professional background. +15% multiplier."},
    "streamdeck": {"category": "Peripherals", "name": "Elgato Stream Deck", "price": 2000, "multiplier": 0.20, "desc": "Easy transitions. +20% multiplier."},
    
    # MICS & CAMS
    "mic_cheap": {"category": "A/V Gear", "name": "Headset Mic", "price": 100, "multiplier": 0.02, "desc": "Sounds like a toaster. +2% multiplier."},
    "mic_yeti": {"category": "A/V Gear", "name": "Blue Yeti Mic", "price": 1500, "multiplier": 0.15, "desc": "The streamer standard. +15% multiplier."},
    "mic_shure": {"category": "A/V Gear", "name": "Shure SM7B", "price": 5000, "multiplier": 0.30, "desc": "Podcast quality audio. +30% multiplier."},
    "cam_cheap": {"category": "A/V Gear", "name": "720p Webcam", "price": 300, "multiplier": 0.05, "desc": "A bit blurry. +5% multiplier."},
    "cam_4k": {"category": "A/V Gear", "name": "4K Facecam", "price": 2500, "multiplier": 0.20, "desc": "Crisp quality. +20% multiplier."},
    "dslr": {"category": "A/V Gear", "name": "Sony A7S III DSLR", "price": 10000, "multiplier": 0.40, "desc": "Cinematic quality. +40% multiplier."},
    
    # CONSOLES
    "ps4": {"category": "Consoles", "name": "PlayStation 4", "price": 2000, "multiplier": 0.10, "desc": "Last gen console. +10% multiplier."},
    "ps5": {"category": "Consoles", "name": "PlayStation 5", "price": 5000, "multiplier": 0.25, "desc": "Current gen console. +25% multiplier."},
    "xbox": {"category": "Consoles", "name": "Xbox Series X", "price": 5000, "multiplier": 0.25, "desc": "Current gen console. +25% multiplier."},
    "switch": {"category": "Consoles", "name": "Nintendo Switch", "price": 3000, "multiplier": 0.15, "desc": "For the Nintendo fanboys. +15% multiplier."}
}

class ShopPagination(discord.ui.View):
    def __init__(self, pages, prefix):
        super().__init__(timeout=120)
        self.pages = pages
        self.current_page = 0
        self.prefix = prefix
        self.update_buttons()

    def update_buttons(self):
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == len(self.pages) - 1

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, custom_id="shop_prev")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary, custom_id="shop_next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)


class InfluencerShop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def shop(self, ctx):
        categories = {}
        for item_id, item in SHOP_ITEMS.items():
            cat = item["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((item_id, item))

        pages = []
        for cat, items in categories.items():
            embed = discord.Embed(title=f"🛒 Creator Shop - {cat}", description="Buy gear to increase your stream and video multipliers!", color=0x2b2d31)
            for item_id, item in items:
                embed.add_field(name=f"{item['name']} — `💵 {item['price']:,}`", value=f"ID: `{item_id}`\n{item['desc']}", inline=False)
            embed.set_footer(text=f"Page {len(pages) + 1}/{len(categories)} | Use {ctx.prefix}buy <id> to purchase")
            pages.append(embed)

        view = ShopPagination(pages, ctx.prefix)
        await ctx.send(embed=pages[0], view=view)

    @commands.command()
    async def buy(self, ctx, item_id: str = None):
        if not item_id or item_id.lower() not in SHOP_ITEMS:
            return await ctx.send(f"❌ Please provide a valid item ID. Use `{ctx.prefix}shop` to see items.")
            
        item_id = item_id.lower()
        item = SHOP_ITEMS[item_id]
        user_id = str(ctx.author.id)
        
        cursor = self.bot.db.cursor()
        cursor.execute("INSERT OR IGNORE INTO influencer_stats (user_id) VALUES (?)", (user_id,))
        
        cursor.execute("SELECT cash FROM influencer_stats WHERE user_id = ?", (user_id,))
        cash_row = cursor.fetchone()
        cash = cash_row[0] if cash_row else 0
        
        if cash < item['price']:
            return await ctx.send(f"❌ You need `💵 {item['price']:,}` to buy **{item['name']}**. You only have `💵 {cash:,}`.")
            
        cursor.execute("SELECT 1 FROM influencer_gear WHERE user_id = ? AND item_id = ?", (user_id, item_id))
        if cursor.fetchone():
            return await ctx.send(f"❌ You already own **{item['name']}**!")
            
        # Deduct cash and add item
        cursor.execute("UPDATE influencer_stats SET cash = cash - ? WHERE user_id = ?", (item['price'], user_id))
        cursor.execute("INSERT INTO influencer_gear (user_id, item_id) VALUES (?, ?)", (user_id, item_id))
        self.bot.db.commit()
        
        await ctx.send(f"✅ You successfully bought **{item['name']}** for `💵 {item['price']:,}`! Your multipliers have increased.")

async def setup(bot):
    await bot.add_cog(InfluencerShop(bot))
