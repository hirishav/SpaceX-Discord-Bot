import discord
from discord.ext import commands

class ModHide(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="hide")
    @commands.has_permissions(manage_channels=True)
    async def hide(self, ctx, *, target: str = None):
        """Channel ko sabse hide karne ke liye (!!hide, !!hide all, !!hide off)."""
        target = target.lower().strip() if target else None

        if target == "off":
            return await self.unhide_channel(ctx, ctx.channel)
        elif target == "off all":
            return await self.unhide_all_channels(ctx)
        elif target == "all":
            return await self.hide_all_channels(ctx)
        else:
            return await self.hide_channel(ctx, ctx.channel)

    @commands.hybrid_command(name="unhide")
    @commands.has_permissions(manage_channels=True)
    async def unhide(self, ctx, *, target: str = None):
        """Hidden channel ko wapas dikhane aur purani permissions restore karne ke liye."""
        target = target.lower().strip() if target else None

        if target == "all":
            return await self.unhide_all_channels(ctx)
        else:
            return await self.unhide_channel(ctx, ctx.channel)

    async def hide_channel(self, ctx, channel):
        # We only hide regular guild channels
        if not isinstance(channel, discord.abc.GuildChannel):
            return await ctx.send("❌ You can only hide server channels!")

        cursor = self.bot.db.cursor()
        cursor.execute("SELECT previous_view_channel FROM hidden_channels WHERE channel_id = ?", (str(channel.id),))
        row = cursor.fetchone()
        
        if row is not None:
            return await ctx.send("❌ This channel is already tracked as hidden!")

        # Save previous state
        current_val = channel.overwrites_for(ctx.guild.default_role).view_channel
        val_str = str(current_val)

        cursor.execute("INSERT INTO hidden_channels (channel_id, previous_view_channel) VALUES (?, ?)", (str(channel.id), val_str))
        self.bot.db.commit()

        # Hide it
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Hidden by {ctx.author}")
        
        await ctx.send(f"✅ {channel.mention} has been hidden from everyone.")

    async def unhide_channel(self, ctx, channel):
        if not isinstance(channel, discord.abc.GuildChannel):
            return await ctx.send("❌ You can only unhide server channels!")

        cursor = self.bot.db.cursor()
        cursor.execute("SELECT previous_view_channel FROM hidden_channels WHERE channel_id = ?", (str(channel.id),))
        row = cursor.fetchone()

        if row is None:
            return await ctx.send("❌ This channel is not hidden in the database! Or maybe its permissions weren't tracked.")

        val_str = row[0]
        if val_str == "True":
            new_val = True
        elif val_str == "False":
            new_val = False
        else:
            new_val = None

        cursor.execute("DELETE FROM hidden_channels WHERE channel_id = ?", (str(channel.id),))
        self.bot.db.commit()

        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = new_val
        if overwrite.is_empty():
            await channel.set_permissions(ctx.guild.default_role, overwrite=None, reason=f"Unhidden by {ctx.author}")
        else:
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Unhidden by {ctx.author}")

        await ctx.send(f"✅ {channel.mention} has been unhidden. Restored original permissions.")

    async def hide_all_channels(self, ctx):
        msg = await ctx.send("🔄 Hiding all text and voice channels... Please wait, this might take a while.")
        cursor = self.bot.db.cursor()
        count = 0
        
        # Only target TextChannels and VoiceChannels (skip Categories to avoid double sync issues)
        channels = [c for c in ctx.guild.channels if isinstance(c, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel))]
        
        for channel in channels:
            cursor.execute("SELECT previous_view_channel FROM hidden_channels WHERE channel_id = ?", (str(channel.id),))
            if cursor.fetchone() is not None:
                continue
                
            current_val = channel.overwrites_for(ctx.guild.default_role).view_channel
            
            val_str = str(current_val)
            cursor.execute("INSERT INTO hidden_channels (channel_id, previous_view_channel) VALUES (?, ?)", (str(channel.id), val_str))
            
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.view_channel = False
            try:
                await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Mass hidden by {ctx.author}")
                count += 1
            except discord.Forbidden:
                pass # skip channels bot can't edit

        self.bot.db.commit()
        await msg.edit(content=f"✅ Successfully hidden **{count}** channels.")

    async def unhide_all_channels(self, ctx):
        msg = await ctx.send("🔄 Unhiding all tracked channels... Please wait.")
        cursor = self.bot.db.cursor()
        
        channels = [c for c in ctx.guild.channels if isinstance(c, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel))]
        hidden_ids = [str(c.id) for c in channels]
            
        if not hidden_ids:
            return await msg.edit(content="✅ No channels to unhide.")

        placeholders = ','.join('?' for _ in hidden_ids)
        cursor.execute(f"SELECT channel_id, previous_view_channel FROM hidden_channels WHERE channel_id IN ({placeholders})", hidden_ids)
        rows = cursor.fetchall()
        
        count = 0
        for channel_id_str, val_str in rows:
            channel = ctx.guild.get_channel(int(channel_id_str))
            if not channel:
                continue
                
            if val_str == "True":
                new_val = True
            elif val_str == "False":
                new_val = False
            else:
                new_val = None
                
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.view_channel = new_val
            
            try:
                if overwrite.is_empty():
                    await channel.set_permissions(ctx.guild.default_role, overwrite=None, reason=f"Mass unhidden by {ctx.author}")
                else:
                    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Mass unhidden by {ctx.author}")
                
                cursor.execute("DELETE FROM hidden_channels WHERE channel_id = ?", (channel_id_str,))
                count += 1
            except discord.Forbidden:
                pass
            
        self.bot.db.commit()
        await msg.edit(content=f"✅ Successfully unhidden **{count}** channels and restored original permissions.")

async def setup(bot):
    await bot.add_cog(ModHide(bot))
