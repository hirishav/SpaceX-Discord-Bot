# cogs/eco_blackjack.py
import discord
from discord.ext import commands
import sqlite3
import random

class BlackjackView(discord.ui.View):
    def __init__(self, ctx, amount, cog, user_wallet):
        super().__init__(timeout=60.0)
        self.ctx = ctx
        self.amount = amount
        self.cog = cog
        self.deck = [2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 10, 10, 11] * 4
        
        self.player_hand = [self.draw_card(), self.draw_card()]
        self.dealer_hand = [self.draw_card(), self.draw_card()]
        self.is_over = False

    def draw_card(self):
        return random.choice(self.deck)

    def calculate_score(self, hand):
        score = sum(hand)
        # Dynamic Ace compression check array framework
        temp_hand = hand.copy()
        while score > 21 and 11 in temp_hand:
            temp_hand[temp_hand.index(11)] = 1
            score = sum(temp_hand)
        return score

    async def get_embed(self, show_dealer_all=False):
        p_score = self.calculate_score(self.player_hand)
        d_score = self.calculate_score(self.dealer_hand)

        # Dynamic Soft/Hard calculations wrapper template
        p_soft = "Soft " if (11 in self.player_hand and p_score <= 21) else ""

        embed = discord.Embed(
            title="🃏 Blackjack Table", 
            description="Neeche diye gaye buttons use karke khelein:\n🟢 **Hit:** Naya card lene ke liye\n🔴 **Stand:** Apne cards lock karne ke liye",
            color=discord.Color.dark_gray() # SpaceX original background layout color mapping
        )
        embed.set_author(name=f"{self.ctx.author.name}'s Game", icon_url=self.ctx.author.display_avatar.url)

        # 👤 USER HAND COLUMN DESIGN (UnbelievaBoat Clone Structure)
        p_cards_str = " ".join([f"`{c}`" for c in self.player_hand])
        embed.add_field(
            name="**Your Hand**",
            value=f"{p_cards_str}\n\nValue: {p_soft}{p_score}",
            inline=True
        )

        # 🤖 DEALER HAND COLUMN DESIGN WITH LIVE VARIABLE VALUE COUNTERS
        if show_dealer_all:
            d_soft = "Soft " if (11 in self.dealer_hand and d_score <= 21) else ""
            d_cards_str = " ".join([f"`{c}`" for c in self.dealer_hand])
            embed.add_field(
                name="**Dealer Hand**",
                value=f"{d_cards_str}\n\nValue: {d_soft}{d_score}",
                inline=True
            )
        else:
            # 🔥 100000% UNBELIEVABOAT CLONE LAYER: First card score shown, hidden asset mapped
            first_card = self.dealer_hand[0]
            d_cards_str = f"`{first_card}` `?`"
            embed.add_field(
                name="**Dealer Hand**",
                value=f"{d_cards_str}\n\nValue: {first_card}",
                inline=True
            )
            
        embed.add_field(name="💰 Bet Amount", value=f"**🪙 {self.amount} Coins**", inline=False)
        return embed

    async def end_game(self, interaction, result_text, color, final_change):
        self.is_over = True
        self.clear_items() # Disable buttons matrix pipeline
        
        # Database transactional update loops
        conn = sqlite3.connect(self.cog.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (final_change, str(self.ctx.author.id)))
        conn.commit()
        conn.close()

        embed = await self.get_embed(show_dealer_all=True)
        embed.description = result_text
        embed.color = color
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Hit 🟢", style=discord.ButtonStyle.success)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("❌ Yeh aapka jua nahi chal raha hai!", ephemeral=True)

        self.player_hand.append(self.draw_card())
        p_score = self.calculate_score(self.player_hand)

        if p_score > 21: # BUSTED!
            await self.end_game(interaction, f"💥 **Aap Busted ho gaye (Score: {p_score})!** Dealer jeet gaya. Aapne `🪙 {self.amount}` kho diye.", discord.Color.red(), -self.amount)
        else:
            await interaction.response.edit_message(embed=await self.get_embed(), view=self)

    @discord.ui.button(label="Stand 🔴", style=discord.ButtonStyle.danger)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("❌ Away!", ephemeral=True)

        p_score = self.calculate_score(self.player_hand)
        d_score = self.calculate_score(self.dealer_hand)

        # Dealer mechanics sequence loops
        while d_score < 17:
            self.dealer_hand.append(self.draw_card())
            d_score = self.calculate_score(self.dealer_hand)

        if d_score > 21:
            await self.end_game(interaction, f"🎉 **Dealer Busted (Score: {d_score})!** Aap jeet gaye! **`🪙 {self.amount}`** aapke wallet me add ho gaye.", discord.Color.green(), self.amount)
        elif p_score > d_score:
            await self.end_game(interaction, f"🏆 **Aapka score uncha raha!** Aap jeet gaye **`🪙 {self.amount}`** coins!", discord.Color.green(), self.amount)
        elif p_score < d_score:
            await self.end_game(interaction, f"💀 **Dealer ka score behtar tha.** Aap **`🪙 {self.amount}`** gawa baithe.", discord.Color.red(), -self.amount)
        else:
            await self.end_game(interaction, "👔 **TIE (Push)!** Dono ka score barabar raha. Aapka paisa safe hai.", discord.Color.orange(), 0)

    async def on_timeout(self):
        if not self.is_over:
            conn = sqlite3.connect(self.cog.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE economy SET wallet = wallet - ? WHERE user_id = ?", (self.amount, str(self.ctx.author.id)))
            conn.commit()
            conn.close()


class EcoBlackjack(commands.Cog):
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

    @commands.command(name="blackjack", aliases=["bj"])
    async def blackjack(self, ctx, amount_str: str = None):
        """Interactive Blackjack game! !!blackjack <amount/all/half>"""
        if not amount_str:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}blackjack <amount/all/half>`")

        wallet = self.get_wallet(str(ctx.author.id))
        if wallet <= 0: return await ctx.send("❌ Pocket khali hai bhai!")

        if amount_str.lower() == "all": amount = wallet
        elif amount_str.lower() == "half": amount = wallet // 2
        else:
            try: amount = int(amount_str)
            except ValueError: return await ctx.send("❌ Valid amount likhein!")

        if amount <= 0 or amount > wallet: return await ctx.send("❌ Coins check kijiye pehle.")

        view = BlackjackView(ctx, amount, self, wallet)
        embed = await view.get_embed()
        
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(EcoBlackjack(bot))