import discord
from discord.ext import commands
import database as sqlite3
import random
import asyncio

class EcoMineView(discord.ui.View):
    def __init__(self, user_id, bet_amount, mines_count, db_path):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.bet_amount = bet_amount
        self.mines_count = mines_count
        self.db_path = db_path
        self.clicked_tiles = 0
        self.max_safe_tiles = 25 - mines_count
        self.multiplier = 1.0
        self.is_cashed_out = False
        self.mine_positions = random.sample(range(25), mines_count)
        self.buttons = []
        
        # Add 25 buttons (5x5 grid)
        for i in range(25):
            btn = discord.ui.Button(
                style=discord.ButtonStyle.secondary,
                label="\u200b", # Zero-width space
                custom_id=f"mine_btn_{i}",
                row=i // 5
            )
            btn.callback = self.create_callback(i)
            self.buttons.append(btn)
            self.add_item(btn)
            
        # Add Cashout button
        self.cashout_btn = discord.ui.Button(
            style=discord.ButtonStyle.success,
            label="💵 Cashout",
            custom_id="cashout_btn",
            row=4 # Putting it on the last row might not look perfect, maybe 5x5 + 1 button?
        )
        self.cashout_btn.callback = self.cashout_callback
        self.add_item(self.cashout_btn)

    def create_callback(self, index):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                return await interaction.response.send_message("❌ Yeh aapki game nahi hai!", ephemeral=True)
            
            if self.is_cashed_out:
                return

            btn = self.buttons[index]
            
            # If mine hit
            if index in self.mine_positions:
                btn.style = discord.ButtonStyle.danger
                btn.emoji = "💣"
                btn.disabled = True
                await self.end_game(interaction, won=False)
            else:
                # Safe tile hit
                btn.style = discord.ButtonStyle.primary
                btn.emoji = "💎"
                btn.disabled = True
                self.clicked_tiles += 1
                
                # Calculate multiplier (simplified version)
                # Multiplier increases faster with more mines
                increment = (0.05 * self.mines_count) * (1 + (self.clicked_tiles * 0.1))
                self.multiplier += increment
                
                embed = interaction.message.embeds[0]
                embed.description = f"**Bet:** 💠 {self.bet_amount}\n**Mines:** {self.mines_count}\n**Multiplier:** {self.multiplier:.2f}x\n**Current Value:** 💠 {int(self.bet_amount * self.multiplier)}"
                
                if self.clicked_tiles >= self.max_safe_tiles:
                    await self.end_game(interaction, won=True)
                else:
                    await interaction.response.edit_message(embed=embed, view=self)

        return callback
        
    async def cashout_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Yeh aapki game nahi hai!", ephemeral=True)
            
        if self.clicked_tiles == 0:
            return await interaction.response.send_message("⚠️ Kam se kam 1 tile toh kholo!", ephemeral=True)
            
        await self.end_game(interaction, won=True)

    async def end_game(self, interaction: discord.Interaction, won: bool):
        self.is_cashed_out = True
        
        # Reveal all tiles
        for i, btn in enumerate(self.buttons):
            btn.disabled = True
            if i in self.mine_positions:
                if btn.style != discord.ButtonStyle.danger: # If not the one that exploded
                    btn.emoji = "💣"
                    btn.style = discord.ButtonStyle.secondary
            else:
                if btn.style == discord.ButtonStyle.secondary:
                    btn.emoji = "💎"
                    
        self.cashout_btn.disabled = True
        
        embed = interaction.message.embeds[0]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if won:
            winnings = int(self.bet_amount * self.multiplier)
            embed.title = "🎉 Cashout Successful!"
            embed.color = discord.Color.green()
            embed.description = f"Aapne safely cashout kar liya!\n\n**Bet:** 💠 {self.bet_amount}\n**Multiplier:** {self.multiplier:.2f}x\n**Won:** 💠 {winnings}"
            
            # Add winnings
            cursor.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (winnings, str(self.user_id)))
            conn.commit()
            conn.close()
            
        else:
            embed.title = "💥 BOOM! Game Over"
            embed.color = discord.Color.red()
            embed.description = f"Aapne mine pe step kar diya!\n\n**Lost:** 💠 {self.bet_amount}"
            conn.close() # Loss was already deducted at start
            
        await interaction.response.edit_message(embed=embed, view=self)
        
    async def on_timeout(self):
        if not self.is_cashed_out:
            self.is_cashed_out = True
            for btn in self.buttons:
                btn.disabled = True
            self.cashout_btn.disabled = True
            # We don't have interaction object here, so we just let it timeout.
            # Loss was already deducted at start.

class EcoMine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "warnings.db"
        
    def check_balance(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT wallet FROM economy WHERE user_id = ?", (str(user_id),))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else 0

    @commands.hybrid_command(name="mine")
    async def mine(self, ctx, amount: int, mines_count: int = 3):
        """Khatarnak mines game khelo aur Specie multiply karo!"""
        
        if amount <= 0:
            return await ctx.send("⚠️ Bet amount 0 ya negative nahi ho sakti!")
            
        if mines_count < 1 or mines_count > 24:
            return await ctx.send("⚠️ Mines 1 se 24 ke beech me honi chahiye!")
            
        balance = self.check_balance(ctx.author.id)
        if balance < amount:
            return await ctx.send(f"❌ Aapke paas itne Specie nahi hain! Current balance: **💠 {balance}**")
            
        # Deduct bet amount upfront
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (amount, str(ctx.author.id)))
        conn.commit()
        conn.close()
        
        view = EcoMineView(user_id=ctx.author.id, bet_amount=amount, mines_count=mines_count, db_path=self.db_path)
        
        embed = discord.Embed(
            title="💣 Mines Game",
            description=f"**Bet:** 💠 {amount}\n**Mines:** {mines_count}\n**Multiplier:** 1.00x\n**Current Value:** 💠 {amount}",
            color=discord.Color.gold()
        )
        
        await ctx.send(embed=embed, view=view)

    @mine.error
    async def mine_error(self, ctx, error):
        await ctx.send(f"⚠️ Debug Mine Error: {error}")
        import traceback
        traceback.print_exc()

async def setup(bot):
    await bot.add_cog(EcoMine(bot))
