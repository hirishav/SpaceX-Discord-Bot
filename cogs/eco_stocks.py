# cogs/eco_stocks.py
import discord
from discord.ext import commands, tasks
import random
import database as sqlite3
from cogs.eco_stocks_core import get_db, init_stocks_db, get_stock_cap

# --- 🔢 MODAL POPUP FOR "GO TO PAGE" BUTTON ---
class GoToPageModal(discord.ui.Modal, title="Jump to Stock Page"):
    page_input = discord.ui.TextInput(
        label="Page Number", 
        placeholder="E.g., 5", 
        min_length=1, 
        max_length=3,
        required=True
    )

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            target_page = int(self.page_input.value)
            if target_page < 1 or target_page > self.view.total_pages:
                return await interaction.response.send_message(f"❌ Invalid page! Please enter between 1 and {self.view.total_pages}.", ephemeral=True)
            
            self.view.current_page = target_page
            await self.view.update_message(interaction)
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number bhai!", ephemeral=True)

# --- 🎛️ PERSISTENT PAGINATION BUTTONS VIEW ---
class StockPaginationView(discord.ui.View):
    def __init__(self, ctx, rows, start_page=1, items_per_page=7, sort_mode=None):
        super().__init__(timeout=120.0) 
        self.ctx = ctx
        self.items_per_page = items_per_page
        self.sort_mode = sort_mode
        self.rows = self.sort_rows(rows, sort_mode)
        self.total_pages = (len(self.rows) + items_per_page - 1) // items_per_page
        
        # Safe boundary clamp for initial startup page configuration
        self.current_page = max(1, min(start_page, self.total_pages))
        
    def sort_rows(self, rows, mode):
        if not mode:
            return rows
        if mode == "price_asc":
            return sorted(rows, key=lambda x: x[2])
        elif mode == "price_desc":
            return sorted(rows, key=lambda x: x[2], reverse=True)
        elif mode == "perf_asc":
            return sorted(rows, key=lambda x: float(x[3].replace('%', '').replace('+', '')))
        elif mode == "perf_desc":
            return sorted(rows, key=lambda x: float(x[3].replace('%', '').replace('+', '')), reverse=True)
        return rows

    async def update_message(self, interaction: discord.Interaction):
        # Dynamically evaluate the button status matrices
        self.btn_first.disabled = self.current_page == 1
        self.btn_prev.disabled = self.current_page == 1
        self.btn_next.disabled = self.current_page == self.total_pages
        self.btn_last.disabled = self.current_page == self.total_pages

        embed = self.generate_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    def generate_embed(self):
        start = (self.current_page - 1) * self.items_per_page
        end = start + self.items_per_page

        embed = discord.Embed(title="📈 SpaceX Live 24/7 Global Stock Exchange 📉", color=discord.Color.dark_green())
        embed.description = f"### Market Pool Status (Page {self.current_page}/{self.total_pages})\nUse buttons below to navigate quickly!\n\n"

        for ticker, name, price, change, available in self.rows[start:end]:
            emoji = "🔺" if "+" in change else "🔻"
            embed.add_field(
                name=f"🏢 {name} (`{ticker}`)",
                value=f"👉 Current Price: **{price} Specie**\n📊 Change Vector: `{change}` {emoji}\n📦 Available Supply: `{available}/10000` Shares Left",
                inline=False
            )
        embed.set_footer(text=f"Use {self.ctx.prefix}buystock to invest! | Active User: {self.ctx.author.name}")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ Yeh trading session aapka nahi hai bhai! Apna khud ka board kholne ke liye `!!stocks` likhein.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except Exception:
            pass

    # --- BUTTON COMMAND PATHS ---
    @discord.ui.button(label="⏮️ First", style=discord.ButtonStyle.secondary, custom_id="stk_first")
    async def btn_first(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 1
        await self.update_message(interaction)

    @discord.ui.button(label="◀️ Prev", style=discord.ButtonStyle.primary, custom_id="stk_prev")
    async def btn_prev(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 1:
            self.current_page -= 1
            await self.update_message(interaction)

    @discord.ui.button(label="Jump", style=discord.ButtonStyle.blurple, custom_id="stk_goto")
    async def btn_goto(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(GoToPageModal(self))

    @discord.ui.button(label="Next ➡️", style=discord.ButtonStyle.secondary, custom_id="stk_next")
    async def btn_next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        await self.update_message(interaction)

    @discord.ui.button(label="Last ⏭️", style=discord.ButtonStyle.danger, custom_id="stk_last")
    async def btn_last(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = self.total_pages
        await self.update_message(interaction)

    @discord.ui.button(label="💲 Sort Price", style=discord.ButtonStyle.secondary, custom_id="stk_sort_price", row=1)
    async def btn_sort_price(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.sort_mode == "price_desc":
            self.sort_mode = "price_asc"
            button.label = "💲 Price (Asc)"
        else:
            self.sort_mode = "price_desc"
            button.label = "💲 Price (Desc)"
            
        self.rows = self.sort_rows(self.rows, self.sort_mode)
        self.current_page = 1
        await self.update_message(interaction)

    @discord.ui.button(label="📈 Sort Perf", style=discord.ButtonStyle.secondary, custom_id="stk_sort_perf", row=1)
    async def btn_sort_perf(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.sort_mode == "perf_desc":
            self.sort_mode = "perf_asc"
            button.label = "📉 Perf (Asc)"
        else:
            self.sort_mode = "perf_desc"
            button.label = "📈 Perf (Desc)"
            
        self.rows = self.sort_rows(self.rows, self.sort_mode)
        self.current_page = 1
        await self.update_message(interaction)


# --- MAIN COG CLASSIFIER MATRIX ---
class EcoStocks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_stocks_db()
        self.market_fluctuation.start()

    def cog_unload(self):
        self.market_fluctuation.cancel()

    @tasks.loop(minutes=5.0)
    async def market_fluctuation(self):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT ticker, current_price FROM stocks")
        all_stocks = cursor.fetchall()

        for ticker, price in all_stocks:
            change = random.randint(-15, 18)
            if change == 0: change = 3
            
            factor = 1 + (change / 100)
            new_price = max(10, int(price * factor)) 
            
            cap = get_stock_cap(ticker)
            if new_price > cap:
                new_price = cap
            
            sign = "+" if change > 0 else ""
            change_str = f"{sign}{change}%"
            
            cursor.execute("UPDATE stocks SET current_price = ?, last_change = ? WHERE ticker = ?", (new_price, change_str, ticker))
            
        conn.commit()
        conn.close()

    @commands.hybrid_command(name="stocks", aliases=["market", "sharemarket"])
    async def view_market(self, ctx, page: int = 1):
        """Top 200 Real-life stocks aur unki capacity interactive buttons ke sath dekhne ke liye."""
        if page < 1: page = 1

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT ticker, company_name, current_price, last_change, available_shares FROM stocks")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return await ctx.send("❌ Market Database load nahi ho paya! Kripya bot restart karein.")

        # Sync the structural layout views with custom input fallback definitions
        view = StockPaginationView(ctx, rows, start_page=page, items_per_page=7)
        
        # Initial compilation setup state evaluation
        view.btn_first.disabled = view.current_page == 1
        view.btn_prev.disabled = view.current_page == 1
        view.btn_next.disabled = view.current_page == view.total_pages
        view.btn_last.disabled = view.current_page == view.total_pages

        initial_embed = view.generate_embed()
        view.message = await ctx.send(embed=initial_embed, view=view)

async def setup(bot):
    init_stocks_db()
    await bot.add_cog(EcoStocks(bot))
