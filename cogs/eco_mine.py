import discord
from discord.ext import commands
import database as sqlite3
import random
import math

def comb(n, k):
    if k < 0 or k > n:
        return 0
    return math.factorial(n) // (math.factorial(k) * math.factorial(n - k))

def calculate_multiplier(mines: int, revealed: int, total_tiles: int = 9):
    if revealed == 0:
        return 1.0
    safe_tiles = total_tiles - mines
    if revealed > safe_tiles:
        return 0.0
    
    # Using backward compatible comb
    combinations_safe = comb(safe_tiles, revealed)
    combinations_total = comb(total_tiles, revealed)
    
    if combinations_safe == 0:
        return 0.0
        
    probability = combinations_safe / combinations_total
    multiplier = (1 / probability) * 0.95
    return round(multiplier, 2)

class MineButton(discord.ui.Button):
    def __init__(self, index: int, is_mine: bool, row: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=row, custom_id=f"mine_{index}")
        self.index = index
        self.is_mine = is_mine
        self.is_revealed = False

    async def callback(self, interaction: discord.Interaction):
        try:
            view: EcoMineView = self.view
            if interaction.user.id != view.user.id:
                return await interaction.response.send_message("❌ Yeh game aapka nahi hai!", ephemeral=True)
                
            if self.is_revealed or view.is_finished:
                return await interaction.response.defer()

            self.is_revealed = True
            self.disabled = True

            if self.is_mine:
                self.style = discord.ButtonStyle.danger
                self.emoji = "💥"
                self.label = ""
                await view.game_over(interaction, won=False)
            else:
                self.style = discord.ButtonStyle.success
                self.emoji = "💎"
                self.label = ""
                view.revealed_count += 1
                await view.update_game(interaction)
        except Exception as e:
            await interaction.channel.send(f"⚠️ Debug Mine Error: {e}")
            import traceback
            traceback.print_exc()

class CashOutButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.success, label="Cash Out", row=3, emoji="💸", disabled=True)

    async def callback(self, interaction: discord.Interaction):
        view: EcoMineView = self.view
        if interaction.user.id != view.user.id:
            return await interaction.response.send_message("❌ Yeh game aapka nahi hai!", ephemeral=True)
            
        if view.is_finished:
            return await interaction.response.defer()
            
        await view.game_over(interaction, won=True)

class EcoMineView(discord.ui.View):
    def __init__(self, user: discord.Member, bet_amount: int, mines_count: int, db_path: str):
        super().__init__(timeout=120)
        self.user = user
        self.bet_amount = bet_amount
        self.mines_count = mines_count
        self.db_path = db_path
        self.revealed_count = 0
        self.total_tiles = 9
        self.multiplier = 1.0
        self.is_finished = False
        self.message = None
        
        # Setup board
        mine_indices = set(random.sample(range(self.total_tiles), self.mines_count))
        self.mine_buttons = []
        for i in range(self.total_tiles):
            row = i // 3
            btn = MineButton(index=i, is_mine=(i in mine_indices), row=row)
            self.mine_buttons.append(btn)
            self.add_item(btn)
            
        self.cash_out_btn = CashOutButton()
        self.add_item(self.cash_out_btn)

    async def on_timeout(self):
        if not self.is_finished and self.message:
            self.is_finished = True
            for btn in self.mine_buttons:
                btn.disabled = True
            self.cash_out_btn.disabled = True
            
            embed = self.build_embed(game_over=True, won=False, timeout=True)
            try:
                await self.message.edit(embed=embed, view=self)
            except discord.HTTPException:
                pass

    def build_embed(self, won: bool = None, game_over: bool = False, timeout: bool = False):
        winnings = int(self.bet_amount * self.multiplier)
        next_multiplier = calculate_multiplier(self.mines_count, self.revealed_count + 1, self.total_tiles)
        
        embed = discord.Embed(color=0x2b2d31) # Dark discord color
        
        if timeout:
            embed.set_author(name=f"{self.user.name} timed out!", icon_url=self.user.display_avatar.url)
        elif game_over:
            if won:
                embed.set_author(name=f"{self.user.name} cashed out!", icon_url=self.user.display_avatar.url)
            else:
                embed.set_author(name=f"{self.user.name} hit a mine!", icon_url=self.user.display_avatar.url)
        else:
            embed.set_author(name=f"{self.user.name}'s mines game", icon_url=self.user.display_avatar.url)

        desc = f"**Bet:** {self.bet_amount:,}  **Mines:** {self.mines_count}\n"
        
        if game_over and not won:
            desc += f"~~**Winnings:** {winnings:,} ({self.multiplier}x)~~\n"
        else:
            desc += f"**Winnings:** {winnings:,} ({self.multiplier}x)\n"
            
        if next_multiplier > 0:
            next_winnings = int(self.bet_amount * next_multiplier)
            if game_over:
                desc += f"~~**Next:** {next_winnings:,} ({next_multiplier}x)~~"
            else:
                desc += f"**Next:** {next_winnings:,} ({next_multiplier}x)"
                
        embed.description = desc
        return embed

    async def update_game(self, interaction: discord.Interaction):
        self.multiplier = calculate_multiplier(self.mines_count, self.revealed_count, self.total_tiles)
        
        self.cash_out_btn.disabled = False
        
        if self.revealed_count == self.total_tiles - self.mines_count:
            await self.game_over(interaction, won=True)
            return

        embed = self.build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def game_over(self, interaction: discord.Interaction, won: bool):
        self.is_finished = True
        for btn in self.mine_buttons:
            btn.disabled = True
            if btn.is_mine and not btn.is_revealed:
                btn.emoji = "💥"
                btn.style = discord.ButtonStyle.secondary
                btn.label = ""
        self.cash_out_btn.disabled = True
        
        embed = self.build_embed(won=won, game_over=True)
        
        if won:
            winnings = int(self.bet_amount * self.multiplier)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (winnings, str(self.user.id)))
            conn.commit()
            conn.close()
            
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

class EcoMine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "warnings.db"

    def get_wallet(self, user_id: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT wallet FROM economy WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0

    @commands.hybrid_command(name="mine", aliases=["mines"])
    async def mine(self, ctx, amount_str: str = None, mines_str: str = "3"):
        """Mine khelo aur double profit kamao! !!mine <amount/all/half> <mines:1-8>"""
        if not amount_str:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}mine <amount/all/half> [mines: 1-8]`\nDefault mines = 3")

        wallet = self.get_wallet(str(ctx.author.id))
        if wallet <= 0:
            return await ctx.send("❌ Aapke paas jua khelne ke liye ek Specie bhi nahi hai!")

        if amount_str.lower() == "all": amount = wallet
        elif amount_str.lower() == "half": amount = wallet // 2
        else:
            try: amount = int(amount_str)
            except ValueError: return await ctx.send("❌ Amount thik se likho!")

        if amount > 250000:
            amount = 250000

        if amount <= 0 or amount > wallet:
            return await ctx.send("❌ Galat amount! Check kijiye aapke pass kitne Specie hain.")
            
        try:
            mines_count = int(mines_str)
            if mines_count < 1 or mines_count > 8:
                return await ctx.send("❌ Mines ki sankhya 1 se 8 ke beech honi chahiye!")
        except ValueError:
            return await ctx.send("❌ Mines ko ek number hona chahiye (1-8)!")

        # Deduct bet amount upfront
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (amount, str(ctx.author.id)))
        conn.commit()
        conn.close()

        view = EcoMineView(user=ctx.author, bet_amount=amount, mines_count=mines_count, db_path=self.db_path)
        embed = view.build_embed()
        
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    @mine.error
    async def mine_error(self, ctx, error):
        await ctx.send(f"⚠️ Debug Mine Error: {error}")
        import traceback
        traceback.print_exc()

async def setup(bot):
    await bot.add_cog(EcoMine(bot))
