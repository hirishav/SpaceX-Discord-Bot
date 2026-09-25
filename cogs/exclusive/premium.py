import discord
from discord.ext import commands

class ExclusivePremium(commands.Cog):
    """
    Premium exclusive features for SpaceX.
    """
    def __init__(self, bot):
        self.bot = bot

    def is_premium_server(self, guild_id: int) -> bool:
        return guild_id in getattr(self.bot, "premium_cache", set())

    @commands.group(name="premium", aliases=["p"], invoke_without_command=True)
    async def premium(self, ctx):
        """💎 View Premium details, perks, and payment methods."""
        is_prem = self.is_premium_server(ctx.guild.id)
        
        status_text = "✅ **PREMIUM ACTIVE**" if is_prem else "❌ **NOT PREMIUM**"
        color = 0xffd700 if is_prem else 0x2b2d31
        
        embed = discord.Embed(
            title="💎 SpaceX Premium Dashboard",
            description=f"Server Status: {status_text}\n\nUpgrade to Premium and unlock exclusive aesthetic features for your server!",
            color=color
        )
        embed.add_field(
            name="✨ Premium Perks",
            value=(
                "**1.** **Prefixless Commands**\n"
                "└ Use `!!p ap @role` to allow roles to use prefixless commands.\n"
                "**2.** **Aesthetic UI**\n"
                "└ Enjoy beautiful, premium-themed command responses.\n"
                "**3.** **More Limits & Features**\n"
                "└ Unlock higher limits for automod, giveaways, and more."
            ),
            inline=False
        )
        embed.add_field(
            name="💳 Payment Methods",
            value=(
                "**UPI ID:** `your_upi_id@ybl`\n"
                "**PayPal:** [paypal.me/yourlink](https://paypal.me/)\n"
                "**Stripe:** [Click Here to Pay](https://stripe.com/)"
            ),
            inline=False
        )
        embed.set_footer(text="Scan the QR below to pay via UPI!", icon_url=ctx.author.display_avatar.url)
        embed.set_image(url="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=your_upi_id@ybl")
        
        view = discord.ui.View()
        
        # QR Code button
        qr_btn = discord.ui.Button(label="Show QR Code", style=discord.ButtonStyle.secondary, emoji="📷")
        async def qr_callback(interaction):
            qr_embed = discord.Embed(title="UPI QR Code", color=0xffd700)
            qr_embed.set_image(url="https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=your_upi_id@ybl")
            await interaction.response.send_message(embed=qr_embed, ephemeral=True)
        qr_btn.callback = qr_callback
        view.add_item(qr_btn)
        
        # External links
        view.add_item(discord.ui.Button(label="UPI ID", style=discord.ButtonStyle.secondary, emoji="🏦", custom_id="upi_id_show"))
        view.add_item(discord.ui.Button(label="PayPal", url="https://paypal.me/", emoji="💳"))
        view.add_item(discord.ui.Button(label="Stripe", url="https://stripe.com/", emoji="🔗"))
        
        msg = await ctx.send(embed=embed, view=view)
        
        # Intercept the UPI ID button
        async def upi_callback(interaction):
            await interaction.response.send_message("UPI ID: `your_upi_id@ybl`", ephemeral=True)
            
        for child in view.children:
            if getattr(child, "custom_id", None) == "upi_id_show":
                child.callback = upi_callback
        
        await msg.edit(view=view)

    @premium.command(name="addprefixless", aliases=["ap"])
    @commands.has_permissions(administrator=True)
    async def add_prefixless(self, ctx, role: discord.Role = None):
        """💎 (Admin) Add prefixless permission for a specific role or everyone."""
        if not self.is_premium_server(ctx.guild.id):
            return await ctx.send("❌ **Premium Required!**\nThis server needs SpaceX Premium to use Prefixless features.\nType `!!premium` to see how to upgrade!")
            
        target_id = role.id if role else ctx.guild.default_role.id
        target_name = role.name if role else "@everyone"
        
        target_id_str = str(target_id)
        
        if target_id in getattr(self.bot, 'prefixless_cache', set()):
            return await ctx.send(f"⚠️ `{target_name}` already has prefixless permissions!")
            
        try:
            cursor = self.bot.db.cursor()
            cursor.execute("INSERT INTO prefixless_users (user_id) VALUES (?)", (target_id_str,))
            self.bot.db.commit()
            if hasattr(self.bot, 'prefixless_cache'):
                self.bot.prefixless_cache.add(target_id)
                
            embed = discord.Embed(
                title="✨ Prefixless Access Granted",
                description=f"Successfully granted prefixless command permissions to **{target_name}**.",
                color=0xffd700
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

    @premium.command(name="removeprefixless", aliases=["rp"])
    @commands.has_permissions(administrator=True)
    async def remove_prefixless(self, ctx, role: discord.Role = None):
        """💎 (Admin) Remove prefixless permission from a specific role or everyone."""
        if not self.is_premium_server(ctx.guild.id):
            return await ctx.send("❌ **Premium Required!**\nThis server needs SpaceX Premium to use Prefixless features.")
            
        target_id = role.id if role else ctx.guild.default_role.id
        target_name = role.name if role else "@everyone"
        
        target_id_str = str(target_id)
        
        if target_id not in getattr(self.bot, 'prefixless_cache', set()):
            return await ctx.send(f"⚠️ `{target_name}` does not have prefixless permissions!")
            
        try:
            cursor = self.bot.db.cursor()
            cursor.execute("DELETE FROM prefixless_users WHERE user_id = ?", (target_id_str,))
            self.bot.db.commit()
            if hasattr(self.bot, 'prefixless_cache'):
                self.bot.prefixless_cache.discard(target_id)
                
            embed = discord.Embed(
                title="🛑 Prefixless Access Revoked",
                description=f"Successfully removed prefixless command permissions from **{target_name}**.",
                color=0xff5555
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")


async def setup(bot):
    await bot.add_cog(ExclusivePremium(bot))
