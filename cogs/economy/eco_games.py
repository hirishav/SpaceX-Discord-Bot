import discord
from discord.ext import commands
import random
import asyncio

class EcoGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['blackjack'])
    async def bj(self, ctx, amount: int = None):
        """Play blackjack with your cash."""
        if not amount or amount <= 0:
            return await ctx.send(f"❌ Usage: `{ctx.prefix}bj <amount>`")
            
        cursor = self.bot.db.cursor()
        cursor.execute("INSERT OR IGNORE INTO influencer_stats (user_id) VALUES (?)", (str(ctx.author.id),))
        self.bot.db.commit()
        
        cursor.execute("SELECT cash FROM influencer_stats WHERE user_id = ?", (str(ctx.author.id),))
        cash = cursor.fetchone()[0]
        
        if cash < amount:
            return await ctx.send(f"❌ You don't have enough cash. You only have `💵 {cash:,}`.")
            
        # Deduct bet
        cursor.execute("UPDATE influencer_stats SET cash = cash - ? WHERE user_id = ?", (amount, str(ctx.author.id)))
        self.bot.db.commit()
        
        # Simple blackjack logic
        player_total = random.randint(12, 21)
        dealer_total = random.randint(15, 22)
        
        if player_total == 21 and dealer_total != 21:
            win_amount = int(amount * 2.5)
            result = "Blackjack! You won!"
            color = discord.Color.green()
            cursor.execute("UPDATE influencer_stats SET cash = cash + ? WHERE user_id = ?", (win_amount, str(ctx.author.id)))
            self.bot.db.commit()
        elif dealer_total > 21 or player_total > dealer_total:
            win_amount = amount * 2
            result = "You won!"
            color = discord.Color.green()
            cursor.execute("UPDATE influencer_stats SET cash = cash + ? WHERE user_id = ?", (win_amount, str(ctx.author.id)))
            self.bot.db.commit()
        elif player_total == dealer_total:
            win_amount = amount
            result = "It's a tie! Bet returned."
            color = discord.Color.gold()
            cursor.execute("UPDATE influencer_stats SET cash = cash + ? WHERE user_id = ?", (win_amount, str(ctx.author.id)))
            self.bot.db.commit()
        else:
            result = "You lost!"
            color = discord.Color.red()
            
        embed = discord.Embed(title="🃏 Blackjack", color=color)
        embed.description = f"**Your total:** {player_total}\n**Dealer's total:** {dealer_total if dealer_total <= 21 else str(dealer_total) + ' (Bust)'}\n\n**{result}**"
        await ctx.send(embed=embed)

    @commands.command()
    async def roulette(self, ctx, amount: int = None, space: str = None):
        """Bet on roulette (red/black/green or specific number 0-36)."""
        if not amount or amount <= 0 or not space:
            return await ctx.send(f"❌ Usage: `{ctx.prefix}roulette <amount> <red/black/green/number>`")
            
        cursor = self.bot.db.cursor()
        cursor.execute("INSERT OR IGNORE INTO influencer_stats (user_id) VALUES (?)", (str(ctx.author.id),))
        self.bot.db.commit()
        
        cursor.execute("SELECT cash FROM influencer_stats WHERE user_id = ?", (str(ctx.author.id),))
        cash = cursor.fetchone()[0]
        
        if cash < amount:
            return await ctx.send(f"❌ You don't have enough cash. You only have `💵 {cash:,}`.")
            
        space = space.lower()
        valid_colors = ["red", "black", "green"]
        try:
            num_bet = int(space)
            if num_bet < 0 or num_bet > 36:
                return await ctx.send("❌ Number must be between 0 and 36.")
            is_num = True
        except ValueError:
            if space not in valid_colors:
                return await ctx.send("❌ You must bet on `red`, `black`, `green`, or a number (0-36).")
            is_num = False
            
        # Deduct bet
        cursor.execute("UPDATE influencer_stats SET cash = cash - ? WHERE user_id = ?", (amount, str(ctx.author.id)))
        self.bot.db.commit()
        
        roll = random.randint(0, 36)
        if roll == 0:
            roll_color = "green"
        elif roll % 2 == 0:
            roll_color = "black"
        else:
            roll_color = "red"
            
        won = False
        win_amount = 0
        if is_num and num_bet == roll:
            won = True
            win_amount = amount * 36
        elif not is_num and space == roll_color:
            won = True
            win_amount = amount * 2 if space != "green" else amount * 14
            
        embed = discord.Embed(title="🎰 Roulette", description=f"The ball landed on **{roll} ({roll_color})**!")
        if won:
            cursor.execute("UPDATE influencer_stats SET cash = cash + ? WHERE user_id = ?", (win_amount, str(ctx.author.id)))
            self.bot.db.commit()
            embed.color = discord.Color.green()
            embed.description += f"\n\n🎉 You won `💵 {win_amount:,}`!"
        else:
            embed.color = discord.Color.red()
            embed.description += f"\n\n💀 You lost your bet of `💵 {amount:,}`."
            
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EcoGames(bot))
