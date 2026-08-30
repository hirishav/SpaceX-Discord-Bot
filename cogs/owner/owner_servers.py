# cogs/owner_servers.py
import discord
from discord.ext import commands

class OwnerServers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="servers", aliases=["guilds", "serverlist"], hidden=True)
    @commands.is_owner()
    async def servers_list(self, ctx):
        """👑 Sirf Bot Owner ke liye - Saare servers ki list nikalne ke liye jahan bot add hai."""
        
        # Async framework check for guilds tracking array matrix
        if not self.bot.guilds:
            return await ctx.send("❌ Bot abhi tak kisi bhi server me add nahi hua hai!")

        # Dynamic loop execution setup parameters
        guilds_data = []
        for index, guild in enumerate(self.bot.guilds, start=1):
            server_name = guild.name
            server_id = guild.id
            member_count = guild.member_count
            
            # 🔥 API GATEWAY BYPASS FIX: Cache issues se bachne ke liye direct safe checking block
            if guild.owner:
                server_owner = f"{guild.owner.name} (Mention: {guild.owner.mention})"
            else:
                # Agar cache fail ho toh temporary text override lagao
                server_owner = "`Fetch Failed (Cache Boundary Exception)`"
            
            guild_string = f"**{index}. {server_name}**\n🆔 ID: `{server_id}`\n👑 Owner: {server_owner}\n👥 Members: `{member_count:,}`\n"
            guilds_data.append(guild_string)

        # 📦 FIELD CONSTRAINT FIX: String manipulation chunk matrix setup
        # Agar text bohot bada ho toh text flow description block ke andar setup karenge
        full_description = "\n".join(guilds_data)
        
        # Discord validation: description blocks limit is 4096 characters max
        if len(full_description) > 4000:
            # Agar bot bohot bade metrics par hai, text file compile karke dm thoko
            import io
            with io.StringIO(full_description.replace("**", "").replace("`", "")) as server_file:
                file_payload = discord.File(fp=server_file, filename="spacex_servers_ledger.txt")
                try:
                    await ctx.author.send(content="🏰 Rishav bhai, server list bohot badi thi isliye text asset ledger file send kar raha hoon:", file=file_payload)
                    return await ctx.send("📥 Server limits exceed hone ke karan data dashboard **Personal DM** me file form me bhej diya gaya hai!")
                except discord.Forbidden:
                    return await ctx.send("❌ Rishav bhai apna DM settings open karo, file delivery block ho rahi hai!")

        # Standard Premium Dark Aesthetic Panel
        embed = discord.Embed(
            title="🏰 SpaceX Bot - Global Server Expansion Blueprint",
            description=f"Mubarak ho Rishav bhai! Aapka bot abhi total **{len(self.bot.guilds)}** servers me deploy ho chuka hai.\n\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n\n{full_description}\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
            color=discord.Color.gold()
        )
        embed.set_footer(text=f"Owner Admin Overrides Activated | Queried by: {ctx.author.name}", icon_url=ctx.author.display_avatar.url)

        try:
            await ctx.author.send(embed=embed)
            await ctx.send("📥 Rishav bhai, security aur privacy parameters ke liye maine saare servers ki list aapke **Personal DM** me flash kar di hai!")
        except discord.Forbidden:
            # Alternate pathway if DM configurations are sealed shut
            await ctx.send("⚠️ Aapka DM locked hai bhai, validation details yahin override kar raha hoon:", embed=embed)

    @commands.command(name="addpremium", aliases=["apremium"], hidden=True)
    @commands.is_owner()
    async def add_premium(self, ctx, server_id: int):
        """👑 Sirf Bot Owner ke liye - Kisi server ko premium status dene ke liye."""
        if server_id in self.bot.premium_cache:
            return await ctx.send(f"❌ Server `{server_id}` pehle se hi premium hai!")
        
        try:
            cursor = self.bot.db.cursor()
            cursor.execute("INSERT INTO premium_servers (server_id) VALUES (?)", (str(server_id),))
            self.bot.db.commit()
            self.bot.premium_cache.add(server_id)
            await ctx.send(f"✅ Server `{server_id}` ko successfully **Premium** access de diya gaya hai!")
        except Exception as e:
            await ctx.send(f"❌ Error while adding premium: {e}")

    @commands.command(name="removepremium", aliases=["rpremium"], hidden=True)
    @commands.is_owner()
    async def remove_premium(self, ctx, server_id: int):
        """👑 Sirf Bot Owner ke liye - Kisi server ka premium status hatane ke liye."""
        if server_id not in self.bot.premium_cache:
            return await ctx.send(f"❌ Server `{server_id}` premium nahi hai!")
        
        try:
            cursor = self.bot.db.cursor()
            cursor.execute("DELETE FROM premium_servers WHERE server_id = ?", (str(server_id),))
            self.bot.db.commit()
            self.bot.premium_cache.remove(server_id)
            await ctx.send(f"✅ Server `{server_id}` ka **Premium** access remove kar diya gaya hai!")
        except Exception as e:
            await ctx.send(f"❌ Error while removing premium: {e}")

async def setup(bot):
    await bot.add_cog(OwnerServers(bot))