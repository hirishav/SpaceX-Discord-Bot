# cogs/mod_giveaway.py
import discord
from discord.ext import commands
import asyncio
import random
import re
import datetime

# --- ACTIVE GLOBAL DATA STORAGE MATRIX ---
ACTIVE_GIVEAWAYS = {}  # Format: {giveaway_id: {"message": msg_obj, "view": view_obj, "prize": str, "ended": bool, "task": asyncio.Task}}
GIVEAWAY_COUNTER = 0

class GiveawayView(discord.ui.View):
    def __init__(self, required_role=None):
        super().__init__(timeout=None)
        self.entrants = set()
        self.required_role = None if str(required_role).lower() == "none" else required_role

    @discord.ui.button(label="Join Giveaway! 🎉", style=discord.ButtonStyle.green, custom_id="join_giveaway_btn")
    async def join_button(self, interaction: discord.Interaction):
        user = interaction.user
        
        # 🛡️ ROLE REQUIREMENT CHECK (AIRTIGHT FILTER)
        if self.required_role:
            if isinstance(self.required_role, discord.Role):
                if self.required_role not in user.roles:
                    return await interaction.response.send_message(f"❌ **Entry Denied:** Is giveaway me part lene ke liye aapke paas {self.required_role.mention} role hona zaroori hai bhai!", ephemeral=True)
            else:
                try:
                    role_id = int(self.required_role)
                    role_obj = interaction.guild.get_role(role_id)
                    if not role_obj or role_obj not in user.roles:
                        raise Exception
                except Exception:
                    role_obj = discord.utils.get(user.roles, name=str(self.required_role))
                    if not role_obj:
                        return await interaction.response.send_message(f"❌ **Entry Denied:** Aapke paas required role (`{self.required_role}`) nahi hai!", ephemeral=True)

        if user.id in self.entrants:
            return await interaction.response.send_message("❌ Bhai, tum pehle se hi is giveaway me joined ho!", ephemeral=True)
        
        self.entrants.add(user.id)
        
        # 🔥 FIX: Embed counter update aur instant ephemeral reply ek sath single hit me delivery matrix
        try:
            embed = interaction.message.embeds[0]
            embed.set_field_at(2, name="📊 Total Entries", value=f"`{len(self.entrants)}` Players", inline=True)
            
            # Instant respond with update and text combined to eliminate delay
            await interaction.response.edit_message(embed=embed)
            await interaction.followup.send("🎉 **Mubarak ho!** Tumne giveaway kamyabi se join kar liya hai.", ephemeral=True)
        except Exception:
            # Fallback agar message update block ho jaye
            try:
                await interaction.response.send_message("🎉 **Mubarak ho!** Tumne giveaway kamyabi se join kar liya hai.", ephemeral=True)
            except Exception:
                pass


class ModGiveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def parse_time(self, time_str: str):
        match = re.match(r"(\d+)([smhd])", time_str.lower())
        if not match: return None
        amount = int(match.group(1))
        unit = match.group(2)
        if unit == 's': return amount
        if unit == 'm': return amount * 60
        if unit == 'h': return amount * 3600
        if unit == 'd': return amount * 86400
        return None

    @commands.command(name="giveaway", aliases=["gstart"])
    @commands.has_permissions(manage_messages=True)
    async def giveaway(self, ctx, duration_str: str = None, requirement_statement: str = None, role_req: str = None, *, prize: str = None):
        """Advanced customizable parameters ke saath giveaway start karne ke liye."""
        global GIVEAWAY_COUNTER
        
        if not duration_str or not requirement_statement or not role_req or not prize:
            embed_err = discord.Embed(
                title="❌ Advance Format Error!",
                description=f"**Sahi Tarika:**\n`{ctx.prefix}gstart <time> \"<requirements_text>\" <@role/none> <prize>`",
                color=discord.Color.red()
            )
            embed_err.add_field(
                name="💡 Example Usages",
                value=f'👉 `{ctx.prefix}gstart 10m "Must have Mod role" @Mod Spotify Premium`\n👉 `{ctx.prefix}gstart 30s "No special rules" none Nitro Classic`',
                inline=False
            )
            return await ctx.send(embed=embed_err)

        seconds = self.parse_time(duration_str)
        if not seconds:
            return await ctx.send("❌ Galat time format! Use `s`, `m`, `h`, ya `d`.")

        parsed_role = role_req
        if role_req.lower() != "none":
            try:
                parsed_role = await commands.RoleConverter().convert(ctx, role_req)
            except Exception:
                pass

        GIVEAWAY_COUNTER += 1
        current_g_id = GIVEAWAY_COUNTER

        end_time = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        timestamp_str = f"<t:{int(end_time.timestamp())}:R>"

        embed = discord.Embed(
            title=f"🎁 GIVEAWAY LIVE [ID: #{current_g_id}] 🎁",
            description=f"### 🏆 Prize: **{prize}**\n\n📌 **Requirements:** {requirement_statement}",
            color=discord.Color.blurple()
        )
        embed.add_field(name="⏳ Ends In", value=timestamp_str, inline=True)
        role_mention_text = parsed_role.mention if isinstance(parsed_role, discord.Role) else f"`{parsed_role.upper()}`"
        embed.add_field(name="🛡️ Role Required", value=role_mention_text, inline=True)
        embed.add_field(name="📊 Total Entries", value="`0` Players", inline=True)
        embed.add_field(name="👑 Host", value=ctx.author.mention, inline=False)
        embed.set_footer(text="Niche diye gaye button par click karke join karein!")

        view = GiveawayView(required_role=parsed_role)
        g_msg = await ctx.send(content="🎉 **GIVEAWAY LIVE** 🎉", embed=embed, view=view)

        loop_task = asyncio.create_task(self.giveaway_countdown_waiter(seconds, current_g_id, ctx.channel))

        ACTIVE_GIVEAWAYS[current_g_id] = {
            "message": g_msg,
            "view": view,
            "prize": prize,
            "ended": False,
            "task": loop_task
        }

        try:
            await ctx.message.delete()
        except Exception:
            pass

    async def giveaway_countdown_waiter(self, seconds, giveaway_id, channel):
        await asyncio.sleep(seconds)
        await self.end_giveaway_logic(giveaway_id, channel)

    async def end_giveaway_logic(self, giveaway_id, channel):
        if giveaway_id not in ACTIVE_GIVEAWAYS or ACTIVE_GIVEAWAYS[giveaway_id]["ended"]:
            return

        data = ACTIVE_GIVEAWAYS[giveaway_id]
        data["ended"] = True
        
        if not data["task"].done():
            data["task"].cancel()
        
        try:
            g_msg = await channel.fetch_message(data["message"].id)
        except Exception:
            return

        view = data["view"]
        prize = data["prize"]

        if not view.entrants:
            embed_end = discord.Embed(
                title=f"🛑 Giveaway Ended [ID: #{giveaway_id}]",
                description=f"### 🏆 Prize: **{prize}**\n\n❌ Kisi ne parameters check criteria clear karke join nahi kiya!",
                color=discord.Color.red()
            )
            await g_msg.edit(content="🛑 **GIVEAWAY ENDED** 🛑", embed=embed_end, view=None)
            return

        winner_id = random.choice(list(view.entrants))
        winner = self.bot.get_user(winner_id)

        embed_win = discord.Embed(
            title="🎉 GIVEAWAY WINNER! 🎉",
            description=f"### 🏆 Prize: **{prize}**\n\n👑 Winner: {winner.mention if winner else f'ID: {winner_id}'}\n📊 Total Participants: `{len(view.entrants)}`",
            color=discord.Color.green()
        )
        embed_win.set_footer(text="Mubarak ho bhai!")
        
        await g_msg.edit(content="🎉 **GIVEAWAY ENDED** 🎉", embed=embed_win, view=None)
        await channel.send(f"🥳 **Mubarak ho {winner.mention}!** Tumne **{prize}** ka giveaway jeet liya hai! {g_msg.jump_url}")

    @commands.command(name="giveawayend", aliases=["gend"])
    @commands.has_permissions(manage_messages=True)
    async def giveaway_end(self, ctx, giveaway_id: int = None):
        """Chal rahe kisi bhi giveaway ko uski ID ke zariye instantly end karne ke liye."""
        if not giveaway_id:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}gend <giveaway_no_integer>`")

        if giveaway_id not in ACTIVE_GIVEAWAYS:
            return await ctx.send(f"❌ Mujhe ID `#{giveaway_id}` ka koi active giveaway nahi mila!")
            
        if ACTIVE_GIVEAWAYS[giveaway_id]["ended"]:
            return await ctx.send("❌ Yeh giveaway pehle se hi khatam ho chuka hai!")

        await ctx.send(f"⏱️ ID `#{giveaway_id}` ke giveaway ko instantly end kiya jaa raha hai...")
        await self.end_giveaway_logic(giveaway_id, ctx.channel)

    @commands.command(name="greroll", aliases=["reroll"])
    @commands.has_permissions(manage_messages=True)
    async def greroll(self, ctx, giveaway_id: int = None):
        """Khatam hue giveaway me se instantly naya winner roll karne ke liye."""
        if not giveaway_id:
            return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}reroll <giveaway_id_no>`")

        if giveaway_id not in ACTIVE_GIVEAWAYS:
            return await ctx.send("❌ Is giveaway ID ka cache data memory me nahi hai!")

        view = ACTIVE_GIVEAWAYS[giveaway_id]["view"]
        prize = ACTIVE_GIVEAWAYS[giveaway_id]["prize"]

        if not view.entrants:
            return await ctx.send("❌ Is giveaway me koi entrants hi nahi the, reroll nahi ho sakta!")

        winner_id = random.choice(list(view.entrants))
        winner = self.bot.get_user(winner_id)

        await ctx.send(f"🎲 **Reroll Action:** {winner.mention} naye winner chune gaye hain **{prize}** ke liye! 🎉")

    @giveaway.error
    @giveaway_end.error
    @greroll.error
    async def giveaway_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ **Permission Denied:** Is command ke liye aapke paas `Manage Messages` perms honi chahiye!")
        else:
            await ctx.send(f"❌ **Error:** Format check karein bhai! Sawaal aur values string context matrix double quotes `\" \"` me hona zaroori hai.")

async def setup(bot):
    await bot.add_cog(ModGiveaway(bot))