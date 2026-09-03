# cogs/moderation/mod_snipe.py
import discord
from discord.ext import commands
import datetime

class ModSnipe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Dictionary to store deleted messages per channel
        # Format: {channel_id: [{"content": "msg", "author": User, "time": datetime, "attachment": url}]}
        self.sniped_messages = {}

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        # Ignore bot messages
        if message.author.bot:
            return
            
        channel_id = message.channel.id
        
        # Initialize list for this channel if not exists
        if channel_id not in self.sniped_messages:
            self.sniped_messages[channel_id] = []
            
        # Get attachment if any
        attachment_url = message.attachments[0].url if message.attachments else None
        
        # Store message data
        message_data = {
            "content": message.content,
            "author": message.author,
            "time": datetime.datetime.now(datetime.timezone.utc),
            "attachment": attachment_url
        }
        
        # Add to the beginning of the list (newest first)
        self.sniped_messages[channel_id].insert(0, message_data)
        
        # Keep only the last 3 deleted messages
        if len(self.sniped_messages[channel_id]) > 3:
            self.sniped_messages[channel_id].pop()

    @commands.hybrid_command(name="snipe", aliases=["s"])
    @commands.has_permissions(manage_messages=True)
    async def snipe(self, ctx):
        """Shows the last 3 deleted messages in this channel."""
        channel_id = ctx.channel.id
        
        if channel_id not in self.sniped_messages or not self.sniped_messages[channel_id]:
            embed = discord.Embed(
                description="❌ There's nothing to snipe here!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed, ephemeral=True)
            
        messages = self.sniped_messages[channel_id]
        
        embed = discord.Embed(
            title="🔫 Sniped Messages",
            color=discord.Color.purple()
        )
        
        for i, msg in enumerate(messages):
            author = msg["author"]
            content = msg["content"] or "*No text content*"
            time = msg["time"]
            attachment = msg["attachment"]
            
            # Format time relative
            time_str = f"<t:{int(time.timestamp())}:R>"
            
            field_value = f"{content}\n\n*🕒 {time_str}*"
            if attachment:
                if content == "*No text content*":
                    field_value = f"[Attachment Link]({attachment})\n\n*🕒 {time_str}*"
                else:
                    field_value = f"{content}\n[Attachment Link]({attachment})\n\n*🕒 {time_str}*"
                
            embed.add_field(
                name=f"{i+1}. {author.name}",
                value=field_value,
                inline=False
            )
            
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ModSnipe(bot))
