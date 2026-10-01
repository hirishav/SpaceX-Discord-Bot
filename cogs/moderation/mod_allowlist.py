import discord
from discord.ext import commands
import time
import math

def is_manager_or_admin_check():
    async def predicate(ctx):
        if not ctx.guild:
            return False
        if ctx.author.id == ctx.guild.owner_id or ctx.author.id in ctx.bot.owner_ids:
            return True
        perms = getattr(ctx.author, 'guild_permissions', None)
        if perms and (perms.administrator or perms.manage_guild or perms.manage_roles):
            return True
        raise commands.CheckFailure("Yeh command sirf Server Managers aur Admins ke liye hai!")
    return commands.check(predicate)

class AllowListPaginationView(discord.ui.View):
    def __init__(self, ctx, entries, per_page=5):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.entries = entries
        self.per_page = per_page
        self.current_page = 0
        self.total_pages = max(1, math.ceil(len(entries) / per_page))
        self.message = None
        self.update_buttons()

    def update_buttons(self):
        self.prev_button.disabled = (self.current_page == 0)
        self.next_button.disabled = (self.current_page >= self.total_pages - 1)

    def create_embed(self):
        start = self.current_page * self.per_page
        end = start + self.per_page
        page_entries = self.entries[start:end]

        embed = discord.Embed(
            title="📋 Allowed Commands & Modules",
            description=f"Showing active allow overrides in **{self.ctx.guild.name}**.\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n",
            color=discord.Color.green()
        )

        for idx, item in enumerate(page_entries, start=start + 1):
            target_str = item["target_str"]
            cmd_mod = item["cmd_mod"]
            time_str = item["time_str"]
            reason = item["reason"]
            allowed_by_str = item["allowed_by_str"]

            embed.add_field(
                name=f"#{idx} • {cmd_mod.upper()}",
                value=(
                    f"**👤 Target:** {target_str}\n"
                    f"**⏳ Duration:** {time_str}\n"
                    f"**📝 Reason:** {reason}\n"
                    f"**🛡️ Allowed By:** {allowed_by_str}"
                ),
                inline=False
            )

        embed.set_footer(text=f"Page {self.current_page + 1}/{self.total_pages} • Total {len(self.entries)} Overrides | Requested by {self.ctx.author.name}")
        return embed

    @discord.ui.button(label="◀️ Prev", style=discord.ButtonStyle.secondary, custom_id="allowlist_prev")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("❌ Ye buttons sirf command chalane wale ke liye hain.", ephemeral=True)
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Next ▶️", style=discord.ButtonStyle.secondary, custom_id="allowlist_next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("❌ Ye buttons sirf command chalane wale ke liye hain.", ephemeral=True)
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass

class ModAllowList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="allowlist", aliases=["listallows", "allows", "allowedlist"])
    @is_manager_or_admin_check()
    async def allowlist_command(self, ctx):
        """Server me active allowed commands aur modules ki list dekhne ke liye (Managers & Admins)."""
        guild_id_int = ctx.guild.id
        current_time = int(time.time())
        cursor = self.bot.db.cursor()

        # Clean expired allows from DB
        cursor.execute("DELETE FROM command_allows WHERE guild_id = ? AND expires_at != -1 AND expires_at <= ?",
                       (str(guild_id_int), current_time))
        if cursor.rowcount > 0:
            self.bot.db.commit()

        # Clean expired allows from cache
        if hasattr(self.bot, 'allowed_commands_cache') and guild_id_int in self.bot.allowed_commands_cache:
            to_del_targets = []
            for t_id, items in self.bot.allowed_commands_cache[guild_id_int].items():
                expired_keys = [k for k, v in items.items() if v != -1 and current_time >= v]
                for k in expired_keys:
                    del items[k]
                if not items:
                    to_del_targets.append(t_id)
            for t_id in to_del_targets:
                del self.bot.allowed_commands_cache[guild_id_int][t_id]

        cursor.execute("SELECT target_id, command_or_module, expires_at, reason, allowed_by FROM command_allows WHERE guild_id = ? ORDER BY expires_at ASC",
                       (str(guild_id_int),))
        rows = cursor.fetchall()

        if not rows:
            embed = discord.Embed(
                title="📋 Allowed Commands List",
                description="❌ Is server me kisi bhi user ya role ke liye koi active **allow override** set nahi hai.",
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Requested by {ctx.author.name} | Staff Only")
            return await ctx.send(embed=embed)

        entries = []
        for t_id, cmd_mod, exp, reason, allowed_by in rows:
            t_id_int = int(t_id)
            if t_id_int == guild_id_int:
                target_str = "@everyone"
            else:
                role = ctx.guild.get_role(t_id_int)
                if role:
                    target_str = f"{role.mention} (`{role.name}`)"
                else:
                    member = ctx.guild.get_member(t_id_int)
                    if member:
                        target_str = f"{member.mention} (`{member.name}`)"
                    else:
                        target_str = f"<@{t_id_int}> (`ID: {t_id_int}`)"

            time_str = "Permanent ♾️" if exp == -1 else f"<t:{exp}:R> (<t:{exp}:f>)"
            allowed_by_str = f"<@{allowed_by}>" if allowed_by else "Unknown Staff"

            entries.append({
                "target_str": target_str,
                "cmd_mod": cmd_mod,
                "time_str": time_str,
                "reason": reason or "No reason provided",
                "allowed_by_str": allowed_by_str
            })

        if len(entries) <= 5:
            view = AllowListPaginationView(ctx, entries, per_page=5)
            embed = view.create_embed()
            await ctx.send(embed=embed)
        else:
            view = AllowListPaginationView(ctx, entries, per_page=5)
            msg = await ctx.send(embed=view.create_embed(), view=view)
            view.message = msg

async def setup(bot):
    await bot.add_cog(ModAllowList(bot))
