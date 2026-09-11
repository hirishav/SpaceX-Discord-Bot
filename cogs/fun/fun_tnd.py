import discord
from discord.ext import commands, tasks
import random
import database
from .tnd_data import MORE_TRUTHS, MORE_DARES

TRUTHS = [
    "What's a secret you've never told anyone?",
    "What is the most embarrassing thing you've done in front of a crush?",
    "Have you ever lied to get out of trouble? What was the lie?",
    "What is your biggest fear?",
    "If you could be invisible for a day, what would you do?",
    "What's the worst trouble you've ever been in?",
    "Who was your first and last crush?",
    "What's the most childish thing you still do?",
    "What is a habit you have that you think is completely gross?",
    "What's the longest you've gone without showering?",
    "Have you ever broken something and blamed someone else?",
    "If you had to kiss one person in this server, who would it be?",
    "What's the most embarrassing message you've accidentally sent to the wrong person?",
    "Have you ever been caught picking your nose?",
    "What is your weirdest flex?"
]

TRUTHS.extend(MORE_TRUTHS)

DARES = [
    "Join a Voice Channel, turn on your camera, and make a funny face for 10 seconds.",
    "Screen share and show us your YouTube homepage recommendations.",
    "Send a voice message singing the 'Happy Birthday' song to a random server member.",
    "Change your Discord nickname to 'Discord Kitten' for the next hour.",
    "Turn on your camera in a Voice Channel and balance a spoon on your nose.",
    "Screen share your Discord DMs list (without opening any messages!).",
    "Join a VC and whisper everything you say for the next 5 minutes.",
    "Send a selfie in the chat with the weirdest object in your room right now.",
    "Screen share and type out a random Wikipedia article for 1 minute.",
    "Turn on your camera in VC and do 10 jumping jacks while counting loudly.",
    "Change your profile picture to the oldest photo in your gallery for 24 hours.",
    "Join a VC and speak with a fake British accent for the next 5 minutes.",
    "Send a voice message in chat barking like a dog.",
    "Screen share your Google search history from the past 24 hours.",
    "Go to the general chat and type 'I am a certified clown 🤡'."
]

DARES.extend(MORE_DARES)

class TNDView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    async def check_if_enabled(self, interaction: discord.Interaction) -> bool:
        db = database.connect()
        cursor = db.cursor()
        cursor.execute("SELECT is_enabled FROM tnd_config WHERE server_id = ? AND channel_id = ?", (str(interaction.guild.id), str(interaction.channel.id)))
        row = cursor.fetchone()
        db.close()
        
        if row and row[0] == 1:
            return True
        return False

    @discord.ui.button(label="Truth", style=discord.ButtonStyle.primary, custom_id="tnd_truth", emoji="💬")
    async def truth_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_if_enabled(interaction):
            await interaction.response.send_message("Truth and Dare is not enabled in this channel anymore.", ephemeral=True)
            return
            
        question = random.choice(TRUTHS)
        embed = discord.Embed(
            title="Truth!",
            description=f"{interaction.user.mention}, your truth is:\n**{question}**",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="Dare", style=discord.ButtonStyle.danger, custom_id="tnd_dare", emoji="😈")
    async def dare_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_if_enabled(interaction):
            await interaction.response.send_message("Truth and Dare is not enabled in this channel anymore.", ephemeral=True)
            return
            
        question = random.choice(DARES)
        embed = discord.Embed(
            title="Dare!",
            description=f"{interaction.user.mention}, your dare is:\n**{question}**",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)


class FunTND(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_channels = set()
        self.tnd_loop.start()

    def cog_unload(self):
        self.tnd_loop.cancel()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        
        # Check if channel is TND enabled
        db = database.connect()
        cursor = db.cursor()
        cursor.execute("SELECT is_enabled FROM tnd_config WHERE channel_id = ?", (str(message.channel.id),))
        row = cursor.fetchone()
        db.close()
        
        if row and row[0] == 1:
            self.active_channels.add(message.channel.id)

    @tasks.loop(seconds=30)
    async def tnd_loop(self):
        await self.bot.wait_until_ready()
        
        channels_to_process = list(self.active_channels)
        self.active_channels.clear()
        
        for channel_id in channels_to_process:
            channel = self.bot.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    title="Truth or Dare",
                    description="Are you brave enough? Choose Truth or Dare by clicking the buttons below!\nBe prepared for spicy questions or wild dares! 🔥",
                    color=discord.Color.purple()
                )
                embed.set_footer(text="Click a button below to get your prompt!")
                
                try:
                    await channel.send(embed=embed, view=TNDView())
                except discord.Forbidden:
                    pass

    @commands.group(invoke_without_command=True)
    async def tnd(self, ctx):
        """
        Configure Truth and Dare for a channel.
        Usage:
        `!!tnd on #channel` - Enable Truth and Dare in a channel
        `!!tnd off #channel` - Disable Truth and Dare in a channel
        """
        await ctx.send_help(ctx.command)

    @tnd.command(name="on")
    async def tnd_on(self, ctx, channel: discord.TextChannel = None):
        """Enable Truth and Dare in the specified channel."""
        channel = channel or ctx.channel
        
        db = database.connect()
        cursor = db.cursor()
        cursor.execute("""
        INSERT INTO tnd_config (server_id, channel_id, is_enabled)
        VALUES (?, ?, 1)
        ON CONFLICT(channel_id) DO UPDATE SET is_enabled=1
        """, (str(ctx.guild.id), str(channel.id)))
        db.commit()
        db.close()
        
        embed = discord.Embed(
            title="Truth or Dare",
            description="Are you brave enough? Choose Truth or Dare by clicking the buttons below!\nBe prepared for spicy questions or wild dares! 🔥",
            color=discord.Color.purple()
        )
        embed.set_footer(text="Click a button below to get your prompt!")
        
        await channel.send(embed=embed, view=TNDView())
        if channel != ctx.channel:
            await ctx.send(f"✅ Truth and Dare has been enabled in {channel.mention}.")

    @tnd.command(name="off")
    async def tnd_off(self, ctx, channel: discord.TextChannel = None):
        """Disable Truth and Dare in the specified channel."""
        channel = channel or ctx.channel
        
        db = database.connect()
        cursor = db.cursor()
        cursor.execute("UPDATE tnd_config SET is_enabled = 0 WHERE server_id = ? AND channel_id = ?", (str(ctx.guild.id), str(channel.id)))
        db.commit()
        db.close()
        
        await ctx.send(f"✅ Truth and Dare has been disabled in {channel.mention}.")


async def setup(bot):
    bot.add_view(TNDView())
    await bot.add_cog(FunTND(bot))
