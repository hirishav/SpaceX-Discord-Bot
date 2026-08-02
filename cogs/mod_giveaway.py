# cogs/mod_giveaway.py
import discord
from discord.ext import commands, tasks
import asyncio
import random
import re
import datetime

ACTIVE_GIVEAWAYS = {}  
GIVEAWAY_COUNTER = 0

class GiveawayView(discord.ui.View):
    def __init__(self, required_role=None, prize_name="Something Sexy"):
        super().__init__(timeout=None) 
        self.entrants = set()
        self.required_role = None if str(required_role).lower() == "none" else required_role
        self.prize_name = prize_name

    @discord.ui.button(label="Join Giveaway! 🎉", style=discord.ButtonStyle.green, custom_id="join_giveaway_btn")
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        
        if self.required_role:
            if isinstance(self.required_role, discord.Role):
                if self.required_role not in user.roles:
                    return await interaction.response.send_message(f"❌ **Entry Denied:** Is giveaway me part lene ke liye aapke paas {self.required_role.mention} role hona zaroori hai bhai!", ephemeral=True)
            else:
                try:
                    role_id = int(self.required_role)
                    role_obj = interaction.guild.get_role(role_id)
                    if not role_obj or role_obj not in user.roles: raise Exception
                except Exception:
                    role_obj = discord.utils.get(user.roles, name=str(self.required_role))
                    if not role_obj:
                        return await interaction.response.send_message(f"❌ **Entry Denied:** Aapke paas required role (`{self.required_role}`) nahi hai!", ephemeral=True)

        if user.id in self.entrants:
            return await interaction.response.send_message("❌ Bhai, tum pehle se hi is giveaway me joined ho!", ephemeral=True)
        
        self.entrants.add(user.id)
        await interaction.response.send_message("🎉 **Mubarak ho!** Tumne giveaway kamyabi se join kar liya hai. Ek baar apna DM check karo!", ephemeral=True)
        
        try:
            dm_embed = discord.Embed(
                title="🎟️ Giveaway Entry Confirmed!",
                description=f"Hey {user.name}, aapne **{interaction.guild.name}** me **{self.prize_name}** ke giveaway me successfully participate kar liya hai! Good luck! 🌟",
                color=discord.Color.green()
            )
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            pass 

        try:
            embed = interaction.message.embeds[0]
            embed.set_field_at(2, name="📊 Total Entries", value=f"`{len(self.entrants)}` Players", inline=True)
            await interaction.message.edit(embed=embed)
        except Exception:
            pass

class ModGiveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_giveaways.start() # 🔥 Persistent loop checker checker engine start

    def cog_unload(self):
        self.check_giveaways.cancel()

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

    # 🔥 ACCURATE CONTINUOUS SCHEDULER: Har 10 second me active memory trace karta hai
    @tasks.loop(seconds=10.0)
    async def check_giveaways(self):
        now = datetime.datetime.now()
        for g_id, data in list(ACTIVE_GIVEAWAYS.items()):
            if not data["ended"] and now >= data["end_time"]:
                # Time target reached inside async loops matrix trigger
                await self.end_giveaway_logic(g_id, data["channel"])

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
            return await ctx.send(embed=embed_err)

        seconds = self.parse_time(duration_str)
        if not seconds: return await ctx.send("❌ Galat time format! Use `s`, `m`, `h`, ya `d`.")

        parsed_role = role_req
        if role_req.lower() != "none":
            try: parsed_role = await commands.RoleConverter().convert(ctx, role_req)
            except Exception: pass

        GIVEAWAY_COUNTER += 1
        current_g_id = GIVEAWAY_COUNTER

        end_datetime = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
        timestamp_str = f"<t:{int(end_datetime.timestamp())}:R>"

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

        view = GiveawayView(required_role=parsed_role, prize_name=prize)
        g_msg = await ctx.send(content="🎉 **GIVEAWAY LIVE** 🎉", embed=embed, view=view)

        # Config dictionary map registers end time directly
        ACTIVE_GIVEAWAYS[current_g_id] = {
            "message": g_msg,
            "view": view,
            "prize": prize,
            "ended": False,
            "end_time": end_datetime,
            "channel": ctx.channel
        }

        try: await ctx.message.delete()
        except Exception: pass

    async def end_giveaway_logic(self, giveaway_id, channel):
        if giveaway_id not in ACTIVE_GIVEAWAYS or ACTIVE_GIVEAWAYS[giveaway_id]["ended"]: return

        data = ACTIVE_GIVEAWAYS[giveaway_id]
        data["ended"] = True
        
        try: g_msg = await channel.fetch_message(data["message"].id)
        except Exception: return

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
        winner = channel.guild.get_member(winner_id)
        if not winner:
            try: winner = await channel.guild.fetch_member(winner_id)
            except Exception: winner = self.bot.get_user(winner_id)

        winner_mention = winner.mention if winner else f"<@{winner_id}>"

        embed_win = discord.Embed(
            title="🎉 GIVEAWAY WINNER! 🎉",
            description=f"### 🏆 Prize: **{prize}**\n\n👑 Winner: {winner_mention}\n📊 Total Participants: `{len(view.entrants)}`",
            color=discord.Color.green()
        )
        embed_win.set_footer(text="Mubarak ho bhai!")
        
        await g_msg.edit(content="🎉 **GIVEAWAY ENDED** 🎉", embed=embed_win, view=None)
        await channel.send(f"🥳 **Mubarak ho {winner_mention}!** Tumne **{prize}** ka giveaway jeet liya hai! {g_msg.jump_url}")
        
        if winner:
            try:
                win_dm = discord.Embed(
                    title="👑 YOU WON THE GIVEAWAY! 👑",
                    description=f"Congratulations! Aapne **{channel.guild.name}** me **{prize}** ka giveaway jeet liya hai! \n\n👉 Host se contact karke apna reward claim karein!",
                    color=discord.Color.gold()
                )
                await winner.send(embed=win_dm)
            except Exception: pass

    @commands.command(name="giveawayend", aliases=["gend"])
    @commands.has_permissions(manage_messages=True)
    async def giveaway_end(self, ctx, giveaway_id: int = None):
        """Chal rahe kisi bhi giveaway ko uski ID ke zariye instantly end karne ke liye."""
        if not giveaway_id: return await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}gend <id>`")
        if giveaway_id not in ACTIVE_GIVEAWAYS: return await ctx.send(f"❌ ID `#{giveaway_id}` active nahi hai!")
        await self.end_giveaway_logic(giveaway_id, ctx.channel)

    @commands.command(name="greroll", aliases=["reroll"])
    @commands.has_permissions(manage_messages=True)
    async def greroll(self, ctx, giveaway_id: int = None):
        """Khatam hue giveaway me se instantly naya winner roll karne ke liye."""
        if not giveaway_id or giveaway_id not in ACTIVE_GIVEAWAYS: return await ctx.send("❌ Galat ID!")
        view = ACTIVE_GIVEAWAYS[giveaway_id]["view"]
        prize = ACTIVE_GIVEAWAYS[giveaway_id]["prize"]
        if not view.entrants: return await ctx.send("❌ No entrants!")
        winner_id = random.choice(list(view.entrants))
        
        winner = ctx.guild.get_member(winner_id)
        if not winner:
            try: winner = await ctx.guild.fetch_member(winner_id)
            except Exception: winner = self.bot.get_user(winner_id)
            
        winner_mention = winner.mention if winner else f"<@{winner_id}>"
        await ctx.send(f"🎲 **Reroll Action:** {winner_mention} naye winner chune gaye hain **{prize}** ke liye! 🎉")

async def setup(bot):
    await bot.add_cog(ModGiveaway(bot))