# cogs/ticket.py
import discord
from discord.ext import commands
import database as sqlite3
import asyncio
import io
import time
from datetime import datetime, timezone

# ─────────────────────────────────────────────────────────────
# 🎨 TICKET UI COMPONENTS (PERSISTENT VIEWS)
# ─────────────────────────────────────────────────────────────

class TicketPanelView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Open Ticket", emoji="🎫", style=discord.ButtonStyle.primary, custom_id="spacex_ticket_open_btn")
    async def open_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("Ticket")
        if not cog:
            return await interaction.response.send_message("❌ Ticket system abhi load nahi hua hai!", ephemeral=True)
        await cog.open_ticket_logic(interaction)


class TicketControlView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Close Ticket", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="spacex_ticket_close_btn")
    async def close_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("Ticket")
        if not cog:
            return await interaction.response.send_message("❌ Ticket system not loaded!", ephemeral=True)
        await cog.close_ticket_logic(interaction)

    @discord.ui.button(label="Claim Ticket", emoji="🙋‍♂️", style=discord.ButtonStyle.success, custom_id="spacex_ticket_claim_btn")
    async def claim_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("Ticket")
        if not cog:
            return await interaction.response.send_message("❌ Ticket system not loaded!", ephemeral=True)
        await cog.claim_ticket_logic(interaction)

    @discord.ui.button(label="Delete Ticket", emoji="🗑️", style=discord.ButtonStyle.secondary, custom_id="spacex_ticket_delete_btn")
    async def delete_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("Ticket")
        if not cog:
            return await interaction.response.send_message("❌ Ticket system not loaded!", ephemeral=True)
        await cog.delete_ticket_logic(interaction)


class TicketClosedView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Reopen Ticket", emoji="🔓", style=discord.ButtonStyle.success, custom_id="spacex_ticket_reopen_btn")
    async def reopen_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("Ticket")
        if not cog:
            return await interaction.response.send_message("❌ Ticket system not loaded!", ephemeral=True)
        await cog.reopen_ticket_logic(interaction)

    @discord.ui.button(label="Delete Ticket", emoji="🗑️", style=discord.ButtonStyle.danger, custom_id="spacex_ticket_delete_closed_btn")
    async def delete_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("Ticket")
        if not cog:
            return await interaction.response.send_message("❌ Ticket system not loaded!", ephemeral=True)
        await cog.delete_ticket_logic(interaction)

    @discord.ui.button(label="Transcript", emoji="📜", style=discord.ButtonStyle.secondary, custom_id="spacex_ticket_transcript_btn")
    async def transcript_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = self.bot.get_cog("Ticket")
        if not cog:
            return await interaction.response.send_message("❌ Ticket system not loaded!", ephemeral=True)
        await cog.transcript_ticket_logic(interaction)


# ─────────────────────────────────────────────────────────────
# 🎫 TICKET COG
# ─────────────────────────────────────────────────────────────

class Ticket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "warnings.db"
        self.init_database()

    def get_connection(self):
        if hasattr(self.bot, 'db') and self.bot.db:
            return self.bot.db
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Config per guild
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ticket_config (
            guild_id TEXT PRIMARY KEY,
            category_id TEXT,
            support_role_id TEXT,
            log_channel_id TEXT,
            panel_channel_id TEXT,
            panel_message_id TEXT,
            ticket_counter INTEGER DEFAULT 0
        )
        """)

        # Active & historical tickets
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ticket_data (
            ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT,
            channel_id TEXT,
            user_id TEXT,
            claimed_by TEXT DEFAULT NULL,
            status TEXT DEFAULT 'open'
        )
        """)

        # Ticket logs table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ticket_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id TEXT,
            ticket_channel_id TEXT,
            user_id TEXT,
            action TEXT,
            reason TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()

    async def cog_load(self):
        self.bot.add_view(TicketPanelView(self.bot))
        self.bot.add_view(TicketControlView(self.bot))
        self.bot.add_view(TicketClosedView(self.bot))

    def get_config(self, guild_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT category_id, support_role_id, log_channel_id, panel_channel_id, panel_message_id, ticket_counter FROM ticket_config WHERE guild_id = ?", (str(guild_id),))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "category_id": int(row[0]) if row[0] else None,
            "support_role_id": int(row[1]) if row[1] else None,
            "log_channel_id": int(row[2]) if row[2] else None,
            "panel_channel_id": int(row[3]) if row[3] else None,
            "panel_message_id": int(row[4]) if row[4] else None,
            "ticket_counter": row[5] or 0
        }

    def update_config(self, guild_id: int, **kwargs):
        conn = self.get_connection()
        cursor = conn.cursor()
        current = self.get_config(guild_id)
        if not current:
            cursor.execute("INSERT INTO ticket_config (guild_id) VALUES (?)", (str(guild_id),))
            current = {
                "category_id": None, "support_role_id": None, "log_channel_id": None,
                "panel_channel_id": None, "panel_message_id": None, "ticket_counter": 0
            }

        for k, v in kwargs.items():
            current[k] = v

        cursor.execute("""
            UPDATE ticket_config
            SET category_id = ?, support_role_id = ?, log_channel_id = ?, panel_channel_id = ?, panel_message_id = ?, ticket_counter = ?
            WHERE guild_id = ?
        """, (
            str(current["category_id"]) if current["category_id"] else None,
            str(current["support_role_id"]) if current["support_role_id"] else None,
            str(current["log_channel_id"]) if current["log_channel_id"] else None,
            str(current["panel_channel_id"]) if current["panel_channel_id"] else None,
            str(current["panel_message_id"]) if current["panel_message_id"] else None,
            current["ticket_counter"],
            str(guild_id)
        ))
        conn.commit()

    async def log_action(self, guild: discord.Guild, channel_id: int, user_id: int, action: str, reason: str = "N/A"):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO ticket_logs (guild_id, ticket_channel_id, user_id, action, reason)
                VALUES (?, ?, ?, ?, ?)
            """, (str(guild.id), str(channel_id), str(user_id), action, reason))
            conn.commit()

            cfg = self.get_config(guild.id)
            if cfg and cfg.get("log_channel_id"):
                log_chan = guild.get_channel(cfg["log_channel_id"])
                if log_chan:
                    embed = discord.Embed(
                        title=f"📋 Ticket Action: {action}",
                        color=discord.Color.blue(),
                        timestamp=datetime.now(timezone.utc)
                    )
                    embed.add_field(name="🎫 Channel ID", value=f"`{channel_id}`", inline=True)
                    embed.add_field(name="👤 User", value=f"<@{user_id}>", inline=True)
                    embed.add_field(name="📝 Details", value=reason, inline=False)
                    embed.set_footer(text=f"SpaceX Ticket System • Guild ID: {guild.id}")
                    await log_chan.send(embed=embed)
        except Exception:
            pass

    def is_staff(self, member: discord.Member, cfg: dict) -> bool:
        if member.guild_permissions.administrator or member.guild_permissions.manage_guild or member.guild_permissions.manage_messages:
            return True
        if cfg and cfg.get("support_role_id"):
            role = member.guild.get_role(cfg["support_role_id"])
            if role and role in member.roles:
                return True
        return False

    # ─────────────────────────────────────────────────────────────
    # 🧠 SHARED LOGIC / INTERACTION CALLBACKS
    # ─────────────────────────────────────────────────────────────

    async def open_ticket_logic(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        cfg = self.get_config(guild.id)

        if not cfg or not cfg.get("category_id"):
            return await interaction.response.send_message(
                "❌ Bhai, is server me abhi ticket system setup nahi hua hai! Moderators se bolo `!!ticket setup` karne ko.",
                ephemeral=True
            )

        category = guild.get_channel(cfg["category_id"])
        if not category or not isinstance(category, discord.CategoryChannel):
            return await interaction.response.send_message(
                "❌ Configured ticket category channel delete ho chuka hai! Staff se check karne ko bole.",
                ephemeral=True
            )

        # Duplicate protection
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id FROM ticket_data WHERE guild_id = ? AND user_id = ? AND status = 'open'", (str(guild.id), str(user.id)))
        row = cursor.fetchone()
        if row:
            existing_chan = guild.get_channel(int(row[0]))
            if existing_chan:
                return await interaction.response.send_message(
                    f"❌ Bhai ticket already open hai 😂 Pehle apna purana ticket close karo: {existing_chan.mention}",
                    ephemeral=True
                )
            else:
                cursor.execute("DELETE FROM ticket_data WHERE channel_id = ?", (row[0],))
                conn.commit()

        counter = (cfg.get("ticket_counter") or 0) + 1
        self.update_config(guild.id, ticket_counter=counter)

        clean_name = ''.join(c for c in user.name.lower() if c.isalnum() or c in ['-', '_']) or "user"
        channel_name = f"ticket-{counter}-{clean_name[:10]}"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False, read_messages=False),
            user: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, attach_files=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, manage_channels=True, manage_messages=True, attach_files=True)
        }

        support_role = guild.get_role(cfg["support_role_id"]) if cfg.get("support_role_id") else None
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, attach_files=True, read_message_history=True)

        try:
            ticket_chan = await guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Ticket #{counter} | Created by {user.display_name} ({user.id})"
            )
        except discord.Forbidden:
            return await interaction.response.send_message("❌ Mere paas category me naya channel create karne ki permission nahi hai!", ephemeral=True)
        except Exception as e:
            return await interaction.response.send_message("❌ Channel create karte waqt error aayi. Please try again later.", ephemeral=True)

        cursor.execute("""
            INSERT INTO ticket_data (guild_id, channel_id, user_id, status)
            VALUES (?, ?, ?, 'open')
        """, (str(guild.id), str(ticket_chan.id), str(user.id)))
        conn.commit()

        embed = discord.Embed(
            title=f"🎫 Support Ticket #{counter}",
            description=(
                f"Namaste **{user.display_name}** bhai! Aapka support ticket open ho gaya hai. <a:giveaway:686211362548088858>\n\n"
                f"› Aapka jo bhi sawal ya problem hai, yahan detail me batayein.\n"
                f"› Staff jald hi aapse aakar baat karega.\n"
                f"› Jab kaam ho jaye toh neeche **Close Ticket** button dabayein."
            ),
            color=discord.Color.from_rgb(24, 26, 40)
        )
        embed.set_footer(text=f"SpaceX Ticket System • User ID: {user.id}")

        mention_str = user.mention
        if support_role:
            mention_str += f" | {support_role.mention}"

        await ticket_chan.send(content=mention_str, embed=embed, view=TicketControlView(self.bot))
        await self.log_action(guild, ticket_chan.id, user.id, "Ticket Created", f"Ticket #{counter} open kiya gaya.")

        await interaction.response.send_message(f"<a:giveaway:686211362548088858> Ticket successfully create ho gaya! Check karo: {ticket_chan.mention}", ephemeral=True)

    async def close_ticket_logic(self, interaction: discord.Interaction, reason: str = "Closed via button/command"):
        channel = interaction.channel
        user = interaction.user
        guild = interaction.guild

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, status FROM ticket_data WHERE guild_id = ? AND channel_id = ?", (str(guild.id), str(channel.id)))
        row = cursor.fetchone()
        if not row:
            return await interaction.response.send_message("❌ Bhai, ye channel koi active ticket channel nahi hai!", ephemeral=True)

        creator_id, status = row[0], row[1]
        if status == 'closed':
            return await interaction.response.send_message("❌ Ye ticket pehle se hi closed hai!", ephemeral=True)

        cfg = self.get_config(guild.id)
        if str(user.id) != creator_id and not self.is_staff(user, cfg):
            return await interaction.response.send_message("❌ Bhai, aap dusre ka ticket close nahi kar sakte!", ephemeral=True)

        cursor.execute("UPDATE ticket_data SET status = 'closed' WHERE channel_id = ?", (str(channel.id),))
        conn.commit()

        creator = guild.get_member(int(creator_id))
        if creator:
            try:
                await channel.set_permissions(creator, view_channel=True, send_messages=False, read_messages=True)
            except Exception:
                pass

        try:
            await channel.edit(name=f"closed-{channel.name}")
        except Exception:
            pass

        embed = discord.Embed(
            title="🔒 Ticket Closed",
            description=f"Ye ticket **{user.display_name}** dwara close kar diya गया hai.\n**Reason:** `{reason}`\n\nNeeche diye options se wapas open ya permanent delete kar sakte hain.",
            color=discord.Color.red()
        )
        await channel.send(embed=embed, view=TicketClosedView(self.bot))
        await self.log_action(guild, channel.id, user.id, "Ticket Closed", f"Reason: {reason}")
        if not interaction.response.is_done():
            await interaction.response.send_message("<a:giveaway:686211362548088858> Ticket close ho gaya hai.", ephemeral=True)

    async def reopen_ticket_logic(self, interaction: discord.Interaction):
        channel = interaction.channel
        user = interaction.user
        guild = interaction.guild

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, status FROM ticket_data WHERE guild_id = ? AND channel_id = ?", (str(guild.id), str(channel.id)))
        row = cursor.fetchone()
        if not row or row[1] != 'closed':
            return await interaction.response.send_message("❌ Ye ticket abhi closed status me nahi hai!", ephemeral=True)

        cfg = self.get_config(guild.id)
        if not self.is_staff(user, cfg):
            return await interaction.response.send_message("❌ Ye command sirf moderators/staff use kar sakte hain.", ephemeral=True)

        cursor.execute("UPDATE ticket_data SET status = 'open' WHERE channel_id = ?", (str(channel.id),))
        conn.commit()

        creator = guild.get_member(int(row[0]))
        if creator:
            try:
                await channel.set_permissions(creator, view_channel=True, send_messages=True, read_messages=True)
            except Exception:
                pass

        try:
            if channel.name.startswith("closed-"):
                await channel.edit(name=channel.name[7:])
        except Exception:
            pass

        embed = discord.Embed(
            title="🔓 Ticket Reopened",
            description=f"Is ticket ko **{user.display_name}** ne wapas reopen kar diya hai! Ab aap message bhej sakte hain.",
            color=discord.Color.green()
        )
        await channel.send(embed=embed, view=TicketControlView(self.bot))
        await self.log_action(guild, channel.id, user.id, "Ticket Reopened", "Ticket was reopened by staff.")
        if not interaction.response.is_done():
            await interaction.response.send_message("<a:giveaway:686211362548088858> Ticket reopen ho gaya hai.", ephemeral=True)

    async def delete_ticket_logic(self, interaction: discord.Interaction):
        channel = interaction.channel
        user = interaction.user
        guild = interaction.guild

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM ticket_data WHERE guild_id = ? AND channel_id = ?", (str(guild.id), str(channel.id)))
        row = cursor.fetchone()
        if not row:
            return await interaction.response.send_message("❌ Bhai, ye koi registered ticket channel nahi hai!", ephemeral=True)

        cfg = self.get_config(guild.id)
        if not self.is_staff(user, cfg):
            return await interaction.response.send_message("❌ Ye command sirf moderators use kar sakte hain.", ephemeral=True)

        await interaction.response.send_message("🗑️ **Ye ticket channel 5 seconds me hamesha ke liye delete ho jayega...**")
        await self.log_action(guild, channel.id, user.id, "Ticket Deleted", f"Channel #{channel.name} was deleted by {user.name}.")

        cursor.execute("DELETE FROM ticket_data WHERE channel_id = ?", (str(channel.id),))
        conn.commit()

        await asyncio.sleep(5)
        try:
            await channel.delete(reason=f"Ticket deleted by {user.name}")
        except Exception:
            pass

    async def claim_ticket_logic(self, interaction: discord.Interaction):
        channel = interaction.channel
        user = interaction.user
        guild = interaction.guild

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT claimed_by FROM ticket_data WHERE guild_id = ? AND channel_id = ?", (str(guild.id), str(channel.id)))
        row = cursor.fetchone()
        if not row:
            return await interaction.response.send_message("❌ Ye channel ticket channel nahi hai!", ephemeral=True)

        cfg = self.get_config(guild.id)
        if not self.is_staff(user, cfg):
            return await interaction.response.send_message("❌ Ye command sirf moderators aur staff use kar sakte hain.", ephemeral=True)

        if row[0]:
            claimer = guild.get_member(int(row[0]))
            claimer_name = claimer.display_name if claimer else f"ID: {row[0]}"
            return await interaction.response.send_message(f"❌ Ye ticket pehle hi **{claimer_name}** ne claim kar rakha hai!", ephemeral=True)

        cursor.execute("UPDATE ticket_data SET claimed_by = ? WHERE channel_id = ?", (str(user.id), str(channel.id)))
        conn.commit()

        embed = discord.Embed(
            title="🙋‍♂️ Ticket Claimed",
            description=f"Is ticket ko {user.mention} (**{user.display_name}**) ne claim kar liya hai!\nAb wahi aapki problem handle karenge.",
            color=discord.Color.green()
        )
        await channel.send(embed=embed)
        await self.log_action(guild, channel.id, user.id, "Ticket Claimed", f"Claimed by {user.name}")
        if not interaction.response.is_done():
            await interaction.response.send_message("<a:giveaway:686211362548088858> Aapne ye ticket claim kar liya hai.", ephemeral=True)

    async def transcript_ticket_logic(self, interaction: discord.Interaction):
        channel = interaction.channel
        user = interaction.user
        guild = interaction.guild

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM ticket_data WHERE guild_id = ? AND channel_id = ?", (str(guild.id), str(channel.id)))
        row = cursor.fetchone()
        if not row:
            return await interaction.response.send_message("❌ Ye ticket channel nahi hai!", ephemeral=True)

        await interaction.response.send_message("📜 **Ticket transcript generate ho raha hai...**", ephemeral=True)

        transcript_text = f"=== 🎫 TICKET TRANSCRIPT : #{channel.name} ===\n"
        transcript_text += f"Server: {guild.name} ({guild.id})\n"
        transcript_text += f"Generated At: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        transcript_text += "=" * 55 + "\n\n"

        messages = [msg async for msg in channel.history(limit=500, oldest_first=True)]
        for msg in messages:
            ts = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            author_tag = f"{msg.author.name} ({msg.author.id})"
            transcript_text += f"[{ts}] {author_tag}: {msg.content}\n"
            if msg.attachments:
                for att in msg.attachments:
                    transcript_text += f"    [Attachment: {att.url}]\n"

        file_bytes = io.BytesIO(transcript_text.encode("utf-8"))
        file = discord.File(file_bytes, filename=f"transcript-{channel.name}.txt")

        embed = discord.Embed(
            title="📜 Ticket Transcript",
            description=f"Is ticket (**#{channel.name}**) ki complete chat log attached file me hai.",
            color=discord.Color.blue()
        )
        await channel.send(embed=embed, file=file)
        await self.log_action(guild, channel.id, user.id, "Transcript Generated", f"Generated by {user.name}")

    # ─────────────────────────────────────────────────────────────
    # ⌨️ TICKET COMMANDS (GROUP & SUBCOMMANDS)
    # ─────────────────────────────────────────────────────────────

    @commands.hybrid_group(name="ticket", invoke_without_command=True)
    async def ticket(self, ctx):
        """SpaceX Ticket System — Support tickets create aur manage karne ke liye commands."""
        embed = discord.Embed(
            title="🎫 SpaceX Ticket System",
            description="Server me support tickets create aur manage karne ke saare commands:",
            color=discord.Color.from_rgb(24, 26, 40)
        )
        prefix = ctx.prefix
        embed.add_field(name="⚙️ Admin / Setup", value=(
            f"`{prefix}ticket setup <category> <support_role> [log_channel]` — Ticket system configure karein\n"
            f"`{prefix}ticket panel` — Interactive ticket panel channel me bhejein\n"
            f"`{prefix}ticket logs` — Server ke recent ticket activity logs dekhein"
        ), inline=False)
        embed.add_field(name="🎟️ User Commands", value=(
            f"`{prefix}ticket create` — Naya ticket open karein\n"
            f"`{prefix}ticket close [reason]` — Current ticket close karein\n"
            f"`{prefix}ticket reopen` — Closed ticket ko wapas open karein\n"
            f"`{prefix}ticket delete` — Ticket channel delete karein"
        ), inline=False)
        embed.add_field(name="🛡️ Staff Commands", value=(
            f"`{prefix}ticket claim` — Ticket claim karein\n"
            f"`{prefix}ticket unclaim` — Ticket ka claim hatayein\n"
            f"`{prefix}ticket add @user` — Member ko ticket me add karein\n"
            f"`{prefix}ticket remove @user` — Member ko ticket se harayein\n"
            f"`{prefix}ticket rename <name>` — Ticket channel ka naam badlein\n"
            f"`{prefix}ticket transcript` — Ticket chat ka text transcript download karein"
        ), inline=False)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @ticket.command(name="setup")
    @commands.has_permissions(manage_guild=True)
    async def setup(self, ctx, category: discord.CategoryChannel, support_role: discord.Role, log_channel: discord.TextChannel = None):
        """Ticket system configure karne ke liye (Category, Support Role, Log Channel)."""
        self.update_config(
            ctx.guild.id,
            category_id=category.id,
            support_role_id=support_role.id,
            log_channel_id=log_channel.id if log_channel else None
        )
        embed = discord.Embed(
            title="<a:giveaway:686211362548088858> Ticket System Setup Done!",
            description="Is server ke liye SpaceX Ticket System successfully configure ho gaya hai.",
            color=discord.Color.green()
        )
        embed.add_field(name="📁 Category", value=category.name, inline=True)
        embed.add_field(name="🛡️ Support Role", value=support_role.mention, inline=True)
        embed.add_field(name="📋 Log Channel", value=log_channel.mention if log_channel else "Not Configured", inline=True)
        embed.set_footer(text="Ab aap `!!ticket panel` command use karke ticket button bhej sakte hain!")
        await ctx.send(embed=embed)

    @ticket.command(name="panel")
    @commands.has_permissions(manage_guild=True)
    async def panel(self, ctx):
        """Server me attractive open ticket panel embed aur button bhejne ke liye."""
        cfg = self.get_config(ctx.guild.id)
        if not cfg or not cfg.get("category_id"):
            return await ctx.send(f"❌ Bhai, pehle ticket setup toh karo! Example: `{ctx.prefix}ticket setup #category @SupportRole`")

        embed = discord.Embed(
            title="🎫 Server Support Desk",
            description=(
                f"**{ctx.guild.name}** ke support system me aapka swagat hai!\n\n"
                f"Agar aapko koi problem hai, staff se help chahiye, ya inquiry karni hai, "
                f"toh neeche diye gaye **`Open Ticket`** button par click karein.\n\n"
                f"⚠️ *Kripya faltu ya fake tickets open na karein.*"
            ),
            color=discord.Color.from_rgb(24, 26, 40)
        )
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text="SpaceX Ticket System • One Click Support", icon_url=self.bot.user.display_avatar.url)

        view = TicketPanelView(self.bot)
        msg = await ctx.send(embed=embed, view=view)
        self.update_config(ctx.guild.id, panel_channel_id=ctx.channel.id, panel_message_id=msg.id)

    @ticket.command(name="create", aliases=["open"])
    async def create(self, ctx):
        """Naya ticket open karne ke liye command."""
        cfg = self.get_config(ctx.guild.id)
        if not cfg or not cfg.get("category_id"):
            return await ctx.send("❌ Bhai, is server me abhi ticket system setup nahi hua hai!")

        category = ctx.guild.get_channel(cfg["category_id"])
        if not category or not isinstance(category, discord.CategoryChannel):
            return await ctx.send("❌ Configured ticket category channel delete ho chuka hai!")

        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id FROM ticket_data WHERE guild_id = ? AND user_id = ? AND status = 'open'", (str(ctx.guild.id), str(ctx.author.id)))
        row = cursor.fetchone()
        if row:
            existing_chan = ctx.guild.get_channel(int(row[0]))
            if existing_chan:
                return await ctx.send(f"❌ Bhai ticket already open hai 😂 Pehle apna purana ticket close karo: {existing_chan.mention}")
            else:
                cursor.execute("DELETE FROM ticket_data WHERE channel_id = ?", (row[0],))
                conn.commit()

        counter = (cfg.get("ticket_counter") or 0) + 1
        self.update_config(ctx.guild.id, ticket_counter=counter)

        clean_name = ''.join(c for c in ctx.author.name.lower() if c.isalnum() or c in ['-', '_']) or "user"
        channel_name = f"ticket-{counter}-{clean_name[:10]}"

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False, read_messages=False),
            ctx.author: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, attach_files=True, read_message_history=True),
            ctx.guild.me: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, manage_channels=True, manage_messages=True, attach_files=True)
        }

        support_role = ctx.guild.get_role(cfg["support_role_id"]) if cfg.get("support_role_id") else None
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, attach_files=True, read_message_history=True)

        try:
            ticket_chan = await ctx.guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites,
                topic=f"Ticket #{counter} | Created by {ctx.author.display_name} ({ctx.author.id})"
            )
        except discord.Forbidden:
            return await ctx.send("❌ Mere paas category me channel create karne ki permission nahi hai!")

        cursor.execute("""
            INSERT INTO ticket_data (guild_id, channel_id, user_id, status)
            VALUES (?, ?, ?, 'open')
        """, (str(ctx.guild.id), str(ticket_chan.id), str(ctx.author.id)))
        conn.commit()

        embed = discord.Embed(
            title=f"🎫 Support Ticket #{counter}",
            description=(
                f"Namaste **{ctx.author.display_name}** bhai! Aapka support ticket open ho gaya hai. <a:giveaway:686211362548088858>\n\n"
                f"› Aapka jo bhi sawal ya problem hai, yahan detail me batayein.\n"
                f"› Staff jald hi aapse aakar baat karega.\n"
                f"› Jab kaam ho jaye toh neeche **Close Ticket** button dabayein."
            ),
            color=discord.Color.from_rgb(24, 26, 40)
        )
        embed.set_footer(text=f"SpaceX Ticket System • User ID: {ctx.author.id}")

        mention_str = ctx.author.mention
        if support_role:
            mention_str += f" | {support_role.mention}"

        await ticket_chan.send(content=mention_str, embed=embed, view=TicketControlView(self.bot))
        await self.log_action(ctx.guild, ticket_chan.id, ctx.author.id, "Ticket Created", f"Ticket #{counter} open kiya gaya.")
        await ctx.send(f"<a:giveaway:686211362548088858> Ticket successfully create ho gaya! Check karo: {ticket_chan.mention}")

    @ticket.command(name="close")
    async def close(self, ctx, *, reason: str = "Closed via command"):
        """Current open ticket ko close karne ke liye."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, status FROM ticket_data WHERE guild_id = ? AND channel_id = ?", (str(ctx.guild.id), str(ctx.channel.id)))
        row = cursor.fetchone()
        if not row:
            return await ctx.send("❌ Bhai, ye channel koi ticket channel nahi hai!")

        creator_id, status = row[0], row[1]
        if status == 'closed':
            return await ctx.send("❌ Ye ticket pehle se hi closed hai!")

        cfg = self.get_config(ctx.guild.id)
        if str(ctx.author.id) != creator_id and not self.is_staff(ctx.author, cfg):
            return await ctx.send("❌ Bhai, aap dusre ka ticket close nahi kar sakte!")

        cursor.execute("UPDATE ticket_data SET status = 'closed' WHERE channel_id = ?", (str(ctx.channel.id),))
        conn.commit()

        creator = ctx.guild.get_member(int(creator_id))
        if creator:
            try:
                await ctx.channel.set_permissions(creator, view_channel=True, send_messages=False, read_messages=True)
            except Exception:
                pass

        try:
            await ctx.channel.edit(name=f"closed-{ctx.channel.name}")
        except Exception:
            pass

        embed = discord.Embed(
            title="🔒 Ticket Closed",
            description=f"Ye ticket **{ctx.author.display_name}** dwara close kar diya gaya hai.\n**Reason:** `{reason}`\n\nNeeche diye options se wapas open ya permanent delete kar sakte hain.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, view=TicketClosedView(self.bot))
        await self.log_action(ctx.guild, ctx.channel.id, ctx.author.id, "Ticket Closed", f"Reason: {reason}")

    @ticket.command(name="reopen")
    async def reopen(self, ctx):
        """Closed ticket ko wapas open karne ke liye."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, status FROM ticket_data WHERE guild_id = ? AND channel_id = ?", (str(ctx.guild.id), str(ctx.channel.id)))
        row = cursor.fetchone()
        if not row or row[1] != 'closed':
            return await ctx.send("❌ Ye ticket abhi closed status me nahi hai!")

        cfg = self.get_config(ctx.guild.id)
        if not self.is_staff(ctx.author, cfg):
            return await ctx.send("❌ Ye command sirf moderators aur staff use kar sakte hain.")

        cursor.execute("UPDATE ticket_data SET status = 'open' WHERE channel_id = ?", (str(ctx.channel.id),))
        conn.commit()

        creator = ctx.guild.get_member(int(row[0]))
        if creator:
            try:
                await ctx.channel.set_permissions(creator, view_channel=True, send_messages=True, read_messages=True)
            except Exception:
                pass

        try:
            if ctx.channel.name.startswith("closed-"):
                await ctx.channel.edit(name=ctx.channel.name[7:])
        except Exception:
            pass

        embed = discord.Embed(
            title="🔓 Ticket Reopened",
            description=f"Is ticket ko **{ctx.author.display_name}** ne wapas reopen kar diya hai! Ab aap message bhej sakte hain.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed, view=TicketControlView(self.bot))
        await self.log_action(ctx.guild, ctx.channel.id, ctx.author.id, "Ticket Reopened", "Reopened via command.")

    @ticket.command(name="delete")
    async def delete(self, ctx):
        """Current ticket channel ko hamesha ke liye delete karne ke liye."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM ticket_data WHERE guild_id = ? AND channel_id = ?", (str(ctx.guild.id), str(ctx.channel.id)))
        row = cursor.fetchone()
        if not row:
            return await ctx.send("❌ Bhai, ye koi ticket channel nahi hai!")

        cfg = self.get_config(ctx.guild.id)
        if not self.is_staff(ctx.author, cfg):
            return await ctx.send("❌ Ye command sirf moderators use kar sakte hain.")

        await ctx.send("🗑️ **Ye ticket channel 5 seconds me hamesha ke liye delete ho jayega...**")
        await self.log_action(ctx.guild, ctx.channel.id, ctx.author.id, "Ticket Deleted", f"Deleted by {ctx.author.name}")

        cursor.execute("DELETE FROM ticket_data WHERE channel_id = ?", (str(ctx.channel.id),))
        conn.commit()

        await asyncio.sleep(5)
        try:
            await ctx.channel.delete(reason=f"Ticket deleted by {ctx.author.name}")
        except Exception:
            pass

    @ticket.command(name="claim")
    async def claim(self, ctx):
        """Staff member dwara ticket claim karne ke liye."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT claimed_by FROM ticket_data WHERE guild_id = ? AND channel_id = ?", (str(ctx.guild.id), str(ctx.channel.id)))
        row = cursor.fetchone()
        if not row:
            return await ctx.send("❌ Ye channel ticket channel nahi hai!")

        cfg = self.get_config(ctx.guild.id)
        if not self.is_staff(ctx.author, cfg):
            return await ctx.send("❌ Ye command sirf moderators aur staff use kar sakte hain.")

        if row[0]:
            claimer = ctx.guild.get_member(int(row[0]))
            claimer_name = claimer.display_name if claimer else f"ID: {row[0]}"
            return await ctx.send(f"❌ Ye ticket pehle hi **{claimer_name}** ne claim kar rakha hai!")

        cursor.execute("UPDATE ticket_data SET claimed_by = ? WHERE channel_id = ?", (str(ctx.author.id), str(ctx.channel.id)))
        conn.commit()

        embed = discord.Embed(
            title="🙋‍♂️ Ticket Claimed",
            description=f"Is ticket ko {ctx.author.mention} (**{ctx.author.display_name}**) ne claim kar liya hai!\nAb wahi aapki problem handle karenge.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        await self.log_action(ctx.guild, ctx.channel.id, ctx.author.id, "Ticket Claimed", f"Claimed by {ctx.author.name}")

    @ticket.command(name="unclaim")
    async def unclaim(self, ctx):
        """Claim kiye hue ticket ka claim hatane ke liye."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT claimed_by FROM ticket_data WHERE guild_id = ? AND channel_id = ?", (str(ctx.guild.id), str(ctx.channel.id)))
        row = cursor.fetchone()
        if not row:
            return await ctx.send("❌ Ye channel ticket channel nahi hai!")

        cfg = self.get_config(ctx.guild.id)
        if not self.is_staff(ctx.author, cfg):
            return await ctx.send("❌ Ye command sirf moderators aur staff use kar sakte hain.")

        if not row[0]:
            return await ctx.send("❌ Ye ticket kisi ne claim nahi kiya hai!")

        if str(ctx.author.id) != row[0] and not ctx.author.guild_permissions.administrator:
            return await ctx.send("❌ Aap kisi aur staff member ka claim nahi hata sakte!")

        cursor.execute("UPDATE ticket_data SET claimed_by = NULL WHERE channel_id = ?", (str(ctx.channel.id),))
        conn.commit()

        embed = discord.Embed(
            title="🔓 Ticket Unclaimed",
            description="Is ticket se staff claim hata diya gaya hai. Ab koi bhi staff member help kar sakta hai.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        await self.log_action(ctx.guild, ctx.channel.id, ctx.author.id, "Ticket Unclaimed", f"Unclaimed by {ctx.author.name}")

    @ticket.command(name="add")
    async def add_member(self, ctx, member: discord.Member):
        """Ticket channel me kisi member/user ko add karne ke liye."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM ticket_data WHERE guild_id = ? AND channel_id = ?", (str(ctx.guild.id), str(ctx.channel.id)))
        row = cursor.fetchone()
        if not row:
            return await ctx.send("❌ Ye channel ticket channel nahi hai!")

        cfg = self.get_config(ctx.guild.id)
        if str(ctx.author.id) != row[0] and not self.is_staff(ctx.author, cfg):
            return await ctx.send("❌ Sirf ticket creator ya staff kisi ko add kar sakte hain!")

        try:
            await ctx.channel.set_permissions(member, view_channel=True, read_messages=True, send_messages=True)
            await ctx.send(f"<a:giveaway:686211362548088858> **{member.display_name}** ({member.mention}) ko is ticket me add kar diya gaya hai!")
            await self.log_action(ctx.guild, ctx.channel.id, ctx.author.id, "User Added", f"Added member: {member.name} ({member.id})")
        except discord.Forbidden:
            await ctx.send("❌ Mere paas permissions modify karne ka power nahi hai!")

    @ticket.command(name="remove")
    async def remove_member(self, ctx, member: discord.Member):
        """Ticket channel se kisi member/user ko remove karne ke liye."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM ticket_data WHERE guild_id = ? AND channel_id = ?", (str(ctx.guild.id), str(ctx.channel.id)))
        row = cursor.fetchone()
        if not row:
            return await ctx.send("❌ Ye channel ticket channel nahi hai!")

        cfg = self.get_config(ctx.guild.id)
        if str(ctx.author.id) != row[0] and not self.is_staff(ctx.author, cfg):
            return await ctx.send("❌ Sirf ticket creator ya staff kisi ko remove kar sakte hain!")

        if str(member.id) == row[0]:
            return await ctx.send("❌ Ticket creator ko hi remove nahi kar sakte bhai!")

        try:
            await ctx.channel.set_permissions(member, overwrite=None)
            await ctx.send(f"🚫 **{member.display_name}** ko is ticket se remove kar diya gaya hai.")
            await self.log_action(ctx.guild, ctx.channel.id, ctx.author.id, "User Removed", f"Removed member: {member.name} ({member.id})")
        except discord.Forbidden:
            await ctx.send("❌ Mere paas permissions modify karne ka power nahi hai!")

    @ticket.command(name="rename")
    async def rename(self, ctx, *, new_name: str):
        """Current ticket channel ka naam badalne ke liye."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM ticket_data WHERE guild_id = ? AND channel_id = ?", (str(ctx.guild.id), str(ctx.channel.id)))
        row = cursor.fetchone()
        if not row:
            return await ctx.send("❌ Ye channel ticket channel nahi hai!")

        cfg = self.get_config(ctx.guild.id)
        if not self.is_staff(ctx.author, cfg) and str(ctx.author.id) != row[0]:
            return await ctx.send("❌ Sirf staff ya ticket creator naam badal sakte hain!")

        clean_name = ''.join(c for c in new_name.lower() if c.isalnum() or c in ['-', '_']) or "ticket"
        try:
            await ctx.channel.edit(name=clean_name)
            await ctx.send(f"✏️ Ticket ka naam badalkar **`{clean_name}`** kar diya gaya hai!")
            await self.log_action(ctx.guild, ctx.channel.id, ctx.author.id, "Ticket Renamed", f"Renamed to {clean_name}")
        except discord.Forbidden:
            await ctx.send("❌ Mere paas channel rename karne ki permission nahi hai!")

    @ticket.command(name="transcript")
    async def transcript(self, ctx):
        """Current ticket ki complete text transcript download karne ke liye."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM ticket_data WHERE guild_id = ? AND channel_id = ?", (str(ctx.guild.id), str(ctx.channel.id)))
        row = cursor.fetchone()
        if not row:
            return await ctx.send("❌ Ye channel ticket channel nahi hai!")

        await ctx.send("📜 **Ticket transcript generate ho raha hai...**")

        transcript_text = f"=== 🎫 TICKET TRANSCRIPT : #{ctx.channel.name} ===\n"
        transcript_text += f"Server: {ctx.guild.name} ({ctx.guild.id})\n"
        transcript_text += f"Generated At: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
        transcript_text += "=" * 55 + "\n\n"

        messages = [msg async for msg in ctx.channel.history(limit=500, oldest_first=True)]
        for msg in messages:
            ts = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
            author_tag = f"{msg.author.name} ({msg.author.id})"
            transcript_text += f"[{ts}] {author_tag}: {msg.content}\n"
            if msg.attachments:
                for att in msg.attachments:
                    transcript_text += f"    [Attachment: {att.url}]\n"

        file_bytes = io.BytesIO(transcript_text.encode("utf-8"))
        file = discord.File(file_bytes, filename=f"transcript-{ctx.channel.name}.txt")

        embed = discord.Embed(
            title="📜 Ticket Transcript",
            description=f"Is ticket (**#{ctx.channel.name}**) ki complete chat log attached file me hai.",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed, file=file)
        await self.log_action(ctx.guild, ctx.channel.id, ctx.author.id, "Transcript Generated", f"Generated by {ctx.author.name}")

    @ticket.command(name="logs")
    @commands.has_permissions(manage_messages=True)
    async def logs(self, ctx, limit: int = 10):
        """Server ke recent ticket actions aur logs dekhne ke liye."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ticket_channel_id, user_id, action, reason, timestamp
            FROM ticket_logs
            WHERE guild_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (str(ctx.guild.id), min(limit, 25)))
        rows = cursor.fetchall()

        if not rows:
            return await ctx.send("<a:giveaway:686211362548088858> Is server me abhi tak koi ticket log record nahi hai.")

        embed = discord.Embed(
            title="📋 Server Ticket Logs",
            description=f"Pichle **{len(rows)}** ticket actions ki list:",
            color=discord.Color.blue()
        )
        for chan_id, u_id, action, reason, ts in rows:
            embed.add_field(
                name=f"➡️ {action} • {ts}",
                value=f"**User:** <@{u_id}> | **Channel:** `<#{chan_id}>`\n**Details:** `{reason}`",
                inline=False
            )
        embed.set_footer(text=f"SpaceX Ticket System • Server ID: {ctx.guild.id}")
        await ctx.send(embed=embed)

    @setup.error
    @panel.error
    @logs.error
    async def ticket_mod_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Ye command sirf moderators use kar sakte hain.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}ticket setup #category @SupportRole [#log_channel]`")


async def setup(bot):
    await bot.add_cog(Ticket(bot))
