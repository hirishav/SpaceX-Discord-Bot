# cogs/fun/fun_clan.py
import discord
from discord.ext import commands
import database as sqlite3
import discord
from discord.ext import commands
import database as sqlite3
import datetime
import random

class ClanInviteView(discord.ui.View):
    def __init__(self, inviter_id, invited_user, clan_id, clan_name):
        super().__init__(timeout=60.0)
        self.inviter_id = inviter_id
        self.invited_user = invited_user
        self.clan_id = clan_id
        self.clan_name = clan_name
        self.message = None

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green, custom_id="clan_yes")
    async def join_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.invited_user.id:
            return await interaction.response.send_message("❌ Ye invite aapke liye nahi hai!", ephemeral=True)
            
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT count(*) FROM clan_members WHERE clan_id = ?", (self.clan_id,))
        if cursor.fetchone()[0] >= 50:
            conn.close()
            return await interaction.response.send_message("❌ Ye clan ab full ho chuka hai!", ephemeral=True)
            
        cursor.execute("SELECT clan_id FROM clan_members WHERE user_id = ?", (str(interaction.user.id),))
        if cursor.fetchone():
            conn.close()
            return await interaction.response.send_message("❌ Aap pehle se hi ek clan me hain. Pehle use leave karein.", ephemeral=True)
            
        cursor.execute(
            "INSERT INTO clan_members (user_id, clan_id, role) VALUES (?, ?, ?)",
            (str(interaction.user.id), self.clan_id, "Member")
        )
        conn.commit()
        conn.close()
        
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content=f"✅ {interaction.user.mention} ne **{self.clan_name}** join kar liya hai!", embed=None, view=self)

    @discord.ui.button(label="No", style=discord.ButtonStyle.red, custom_id="clan_no")
    async def deny_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.invited_user.id:
            return await interaction.response.send_message("❌ Ye invite aapke liye nahi hai!", ephemeral=True)
            
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(content=f"❌ {interaction.user.mention} ne **{self.clan_name}** ka invite thukra diya.", embed=None, view=self)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            try:
                await self.message.edit(content="⏳ Invitation expire ho gaya hai.", view=self)
            except:
                pass

class FunClan(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True, name="clan", aliases=["clans"])
    async def clan_cmd(self, ctx):
        """Clan module commands. Use help clan for details."""
        await ctx.send(f"❌ Valid subcommands: `create`, `info`, `join`, `leave`, `disband`, `edit`, `leaderboard`, `list`, `war`, `transfer`, `admin`, `invite`, `raid`\nExample: `{ctx.prefix}clan info`")

    @clan_cmd.command(name="create")
    async def clan_create(self, ctx, *, name: str = None):
        """Creates a new clan."""
        if not name:
            return await ctx.send(f"❌ Kripya clan ka naam likhiye! Example: `{ctx.prefix}clan create SpaceX Warriors`")
        if len(name) > 30:
            return await ctx.send("❌ Clan ka naam 30 characters se lamba nahi ho sakta.")
            
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        
        # Check if user already in a clan
        cursor.execute("SELECT clan_id FROM clan_members WHERE user_id = ?", (str(ctx.author.id),))
        if cursor.fetchone():
            conn.close()
            return await ctx.send("❌ Aap pehle se hi ek clan me hain. Pehle use `leave` karein.")
            
        # Check if name exists
        cursor.execute("SELECT clan_id FROM clans WHERE name = ?", (name,))
        if cursor.fetchone():
            conn.close()
            return await ctx.send("❌ Ye clan name pehle se kisi ne le liya hai. Koi naya naam sochein.")
            
        cursor.execute(
            "INSERT INTO clans (name, leader_id) VALUES (?, ?)", 
            (name, str(ctx.author.id))
        )
        # PostgreSQL bridge doesn't always support lastrowid, fetch by name
        cursor.execute("SELECT clan_id FROM clans WHERE name = ?", (name,))
        clan_row = cursor.fetchone()
        if not clan_row:
            conn.close()
            return await ctx.send("❌ Clan create karne mein error aayi.")
            
        clan_id = clan_row[0]
            
        cursor.execute(
            "INSERT INTO clan_members (user_id, clan_id, role) VALUES (?, ?, ?)",
            (str(ctx.author.id), clan_id, "Leader")
        )
        conn.commit()
        conn.close()
        
        await ctx.send(f"✅ **{name}** clan successfully ban gaya hai! Aap iske Leader hain. 🎉")

    @clan_cmd.command(name="info")
    async def clan_info(self, ctx, *, name: str = None):
        """Shows clan information."""
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        
        if not name:
            cursor.execute("SELECT clan_id FROM clan_members WHERE user_id = ?", (str(ctx.author.id),))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return await ctx.send(f"❌ Aap kisi clan me nahi hain! Kripya kisi clan ka naam likhein (e.g. `{ctx.prefix}clan info <name>`) ya apna clan banayein.")
            clan_id = row[0]
            cursor.execute("SELECT * FROM clans WHERE clan_id = ?", (clan_id,))
        else:
            cursor.execute("SELECT * FROM clans WHERE name = ?", (name,))
            
        clan = cursor.fetchone()
        if not clan:
            conn.close()
            return await ctx.send("❌ Ye clan nahi mila!")
            
        clan_id, clan_name, desc, leader_id, points, created_at = clan
        
        cursor.execute("SELECT count(*) FROM clan_members WHERE clan_id = ?", (clan_id,))
        member_count = cursor.fetchone()[0]
        
        # Calculate Rank
        cursor.execute("SELECT clan_id FROM clans ORDER BY points DESC")
        leaderboard = cursor.fetchall()
        rank = 0
        for i, (cid,) in enumerate(leaderboard):
            if cid == clan_id:
                rank = i + 1
                break
                
        conn.close()
        
        embed = discord.Embed(
            title=f"🛡️ Clan: {clan_name}",
            description=f"**Description:** {desc}",
            color=discord.Color.gold()
        )
        embed.add_field(name="👑 Leader", value=f"<@{leader_id}>")
        embed.add_field(name="🏆 Points", value=f"{points:,}")
        embed.add_field(name="🏅 Global Rank", value=f"#{rank}")
        embed.add_field(name="👥 Members", value=f"{member_count}/50")
        
        if created_at:
            created_at_date = str(created_at).split()[0]
            embed.add_field(name="📅 Created", value=created_at_date)
        
        await ctx.send(embed=embed)

    @clan_cmd.command(name="join")
    async def clan_join(self, ctx, *, name: str):
        """Join a clan."""
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT clan_id FROM clan_members WHERE user_id = ?", (str(ctx.author.id),))
        if cursor.fetchone():
            conn.close()
            return await ctx.send("❌ Aap pehle se hi ek clan me hain. Pehle use `leave` karein.")
            
        cursor.execute("SELECT clan_id FROM clans WHERE name = ?", (name,))
        clan = cursor.fetchone()
        if not clan:
            conn.close()
            return await ctx.send("❌ Ye clan nahi mila!")
            
        clan_id = clan[0]
        cursor.execute("SELECT count(*) FROM clan_members WHERE clan_id = ?", (clan_id,))
        if cursor.fetchone()[0] >= 50:
            conn.close()
            return await ctx.send("❌ Ye clan full ho chuka hai! (Max 50 members)")
            
        cursor.execute(
            "INSERT INTO clan_members (user_id, clan_id, role) VALUES (?, ?, ?)",
            (str(ctx.author.id), clan_id, "Member")
        )
        conn.commit()
        conn.close()
        await ctx.send(f"✅ Aapne **{name}** clan join kar liya hai! 🎉")

    @clan_cmd.command(name="leave")
    async def clan_leave(self, ctx):
        """Leave your current clan."""
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT clan_id, role FROM clan_members WHERE user_id = ?", (str(ctx.author.id),))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return await ctx.send("❌ Aap kisi clan me nahi hain.")
            
        clan_id, role = row
        if role == "Leader":
            conn.close()
            return await ctx.send(f"❌ Aap clan ke Leader hain! Leave karne ke liye pehle kisi aur ko Leader banayein, ya fir `{ctx.prefix}clan disband` use karein.")
            
        cursor.execute("DELETE FROM clan_members WHERE user_id = ?", (str(ctx.author.id),))
        conn.commit()
        conn.close()
        await ctx.send("✅ Aapne clan chhod diya hai.")

    @clan_cmd.command(name="disband")
    async def clan_disband(self, ctx):
        """Disbands (deletes) the clan. Leader only."""
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT clan_id, role FROM clan_members WHERE user_id = ?", (str(ctx.author.id),))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return await ctx.send("❌ Aap kisi clan me nahi hain.")
            
        clan_id, role = row
        if role != "Leader":
            conn.close()
            return await ctx.send("❌ Sirf clan ka Leader hi clan ko disband kar sakta hai!")
            
        cursor.execute("DELETE FROM clan_members WHERE clan_id = ?", (clan_id,))
        cursor.execute("DELETE FROM clans WHERE clan_id = ?", (clan_id,))
        cursor.execute("DELETE FROM clan_wars WHERE challenger_id = ? OR defender_id = ?", (clan_id, clan_id))
        conn.commit()
        conn.close()
        await ctx.send("💥 Aapka clan hamesha ke liye delete (disband) kar diya gaya hai.")

    @clan_cmd.command(name="leaderboard", aliases=["lb", "top"])
    async def clan_leaderboard(self, ctx):
        """Shows the top clans by points."""
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, points FROM clans ORDER BY points DESC LIMIT 10")
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return await ctx.send("❌ Abhi tak koi clans nahi bane hain.")
            
        embed = discord.Embed(title="🏆 Global Clan Leaderboard", color=discord.Color.gold())
        for i, (name, points) in enumerate(rows):
            embed.add_field(name=f"#{i+1} {name}", value=f"Points: **{points:,}**", inline=False)
            
        await ctx.send(embed=embed)

    @clan_cmd.command(name="edit")
    async def clan_edit(self, ctx, *, description: str):
        """Edit clan description (Leaders/Co-leaders)."""
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT clan_id, role FROM clan_members WHERE user_id = ?", (str(ctx.author.id),))
        row = cursor.fetchone()
        if not row or row[1] not in ["Leader", "Co-Leader"]:
            conn.close()
            return await ctx.send("❌ Aapke paas ye karne ki permission nahi hai (Only Leader/Co-Leader).")
            
        cursor.execute("UPDATE clans SET description = ? WHERE clan_id = ?", (description[:150], row[0]))
        conn.commit()
        conn.close()
        await ctx.send("✅ Clan description successfully update ho gaya hai!")

    @clan_cmd.command(name="war")
    async def clan_war(self, ctx, *, target_clan: str):
        """Declare a war against another clan! (Leaders/Co-leaders only)"""
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        
        # Check if caller is leader
        cursor.execute("SELECT clan_id, role FROM clan_members WHERE user_id = ?", (str(ctx.author.id),))
        caller = cursor.fetchone()
        if not caller or caller[1] not in ["Leader", "Co-Leader"]:
            conn.close()
            return await ctx.send("❌ Sirf Leader ya Co-Leader hi war declare kar sakte hain!")
            
        challenger_id = caller[0]
        
        # Check target clan
        cursor.execute("SELECT clan_id, name FROM clans WHERE name = ?", (target_clan,))
        target = cursor.fetchone()
        if not target:
            conn.close()
            return await ctx.send("❌ Target clan nahi mila! Sahi naam likhein.")
            
        defender_id = target[0]
        defender_name = target[1]
        
        if challenger_id == defender_id:
            conn.close()
            return await ctx.send("❌ Aap apne hi clan pe war declare nahi kar sakte!")
            
        # Check if already in war
        cursor.execute("SELECT war_id FROM clan_wars WHERE status = 'Pending' AND ((challenger_id = ? AND defender_id = ?) OR (challenger_id = ? AND defender_id = ?))", (challenger_id, defender_id, defender_id, challenger_id))
        if cursor.fetchone():
            conn.close()
            return await ctx.send(f"❌ Aapka clan already **{defender_name}** ke khilaf war me hai (Pending)!")
            
        cursor.execute(
            "INSERT INTO clan_wars (challenger_id, defender_id, status) VALUES (?, ?, ?)",
            (challenger_id, defender_id, "Pending")
        )
        conn.commit()
        conn.close()
        
        await ctx.send(f"⚔️ **WAR DECLARED!** Aapne **{defender_name}** ke khilaf war declare kar di hai! Abhi status 'Pending' hai (Admins can resolve it or it will be resolved based on points gathered during the war period).")

    @clan_cmd.command(name="transfer")
    async def clan_transfer(self, ctx, member: discord.Member):
        """Transfers the ownership (Leader role) to another clan member."""
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT clan_id, role FROM clan_members WHERE user_id = ?", (str(ctx.author.id),))
        caller = cursor.fetchone()
        if not caller or caller[1] != "Leader":
            conn.close()
            return await ctx.send("❌ Sirf clan ka Leader hi ownership transfer kar sakta hai!")
            
        clan_id = caller[0]
        
        cursor.execute("SELECT role FROM clan_members WHERE user_id = ? AND clan_id = ?", (str(member.id), clan_id))
        target = cursor.fetchone()
        if not target:
            conn.close()
            return await ctx.send(f"❌ {member.mention} aapke clan me nahi hai!")
            
        if member.id == ctx.author.id:
            conn.close()
            return await ctx.send("❌ Aap khudko hi transfer nahi kar sakte!")
            
        # Update roles
        cursor.execute("UPDATE clan_members SET role = 'Admin' WHERE user_id = ?", (str(ctx.author.id),))
        cursor.execute("UPDATE clan_members SET role = 'Leader' WHERE user_id = ?", (str(member.id),))
        cursor.execute("UPDATE clans SET leader_id = ? WHERE clan_id = ?", (str(member.id), clan_id))
        
        conn.commit()
        conn.close()
        await ctx.send(f"👑 Clan ki ownership successfully {member.mention} ko transfer kar di gayi hai! Ab woh naye Leader hain.")

    @clan_cmd.command(name="admin")
    async def clan_admin(self, ctx, member: discord.Member):
        """Promote a member to Admin."""
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT clan_id, role FROM clan_members WHERE user_id = ?", (str(ctx.author.id),))
        caller = cursor.fetchone()
        if not caller or caller[1] != "Leader":
            conn.close()
            return await ctx.send("❌ Sirf clan ka Leader hi kisi ko Admin bana sakta hai!")
            
        clan_id = caller[0]
        
        cursor.execute("SELECT role FROM clan_members WHERE user_id = ? AND clan_id = ?", (str(member.id), clan_id))
        target = cursor.fetchone()
        if not target:
            conn.close()
            return await ctx.send(f"❌ {member.mention} aapke clan me nahi hai!")
            
        if target[0] == "Leader":
            conn.close()
            return await ctx.send("❌ Ye pehle se hi Leader hai!")
            
        if target[0] == "Admin":
            conn.close()
            return await ctx.send(f"❌ {member.mention} pehle se hi Admin hai!")
            
        cursor.execute("UPDATE clan_members SET role = 'Admin' WHERE user_id = ?", (str(member.id),))
        conn.commit()
        conn.close()
        await ctx.send(f"🛡️ {member.mention} ko clan ka **Admin** bana diya gaya hai!")

    @clan_cmd.command(name="invite")
    async def clan_invite(self, ctx, member: discord.Member):
        """Invite a user to your clan."""
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT clan_id, role FROM clan_members WHERE user_id = ?", (str(ctx.author.id),))
        caller = cursor.fetchone()
        if not caller:
            conn.close()
            return await ctx.send("❌ Aap kisi clan me nahi hain.")
            
        if caller[1] not in ["Leader", "Admin", "Co-Leader"]:
            conn.close()
            return await ctx.send("❌ Sirf Leader ya Admin hi invite kar sakte hain.")
            
        cursor.execute("SELECT name, clan_id FROM clans WHERE clan_id = ?", (caller[0],))
        clan_data = cursor.fetchone()
        clan_name = clan_data[0]
        clan_id = clan_data[1]
            
        cursor.execute("SELECT clan_id FROM clan_members WHERE user_id = ?", (str(member.id),))
        if cursor.fetchone():
            conn.close()
            return await ctx.send(f"❌ {member.display_name} pehle se hi kisi clan me hai.")
            
        conn.close()
        
        embed = discord.Embed(
            title="💌 Clan Invitation",
            description=f"{ctx.author.mention} ne aapko **{clan_name}** clan me invite kiya hai!\n\nJoin karne ke liye niche `Yes` par click karein.",
            color=discord.Color.blue()
        )
        
        view = ClanInviteView(ctx.author.id, member, clan_id, clan_name)
        msg = await ctx.send(content=member.mention, embed=embed, view=view)
        view.message = msg

    @clan_cmd.command(name="list")
    async def clan_list(self, ctx):
        """List all clans globally."""
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, points FROM clans ORDER BY created_at ASC")
        clans = cursor.fetchall()
        conn.close()
        
        if not clans:
            return await ctx.send("❌ Abhi tak koi clans nahi bane hain.")
            
        embed = discord.Embed(title="🌍 Global Clan List", color=discord.Color.blurple())
        desc = ""
        for i, (name, points) in enumerate(clans[:25]): # Cap at 25 for embed limits
            desc += f"**{i+1}.** {name} *(Points: {points:,})*\n"
            
        if len(clans) > 25:
            desc += f"\n*...aur {len(clans) - 25} clans.*"
            
        embed.description = desc
        await ctx.send(embed=embed)

    @clan_cmd.command(name="raid")
    @commands.cooldown(1, 7200, commands.BucketType.guild)
    async def clan_raid(self, ctx, *, target_clan: str):
        """Raid another clan to steal their points!"""
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT clan_id, role FROM clan_members WHERE user_id = ?", (str(ctx.author.id),))
        caller = cursor.fetchone()
        if not caller:
            conn.close()
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ Aap kisi clan me nahi hain.")
            
        if caller[1] not in ["Leader", "Admin", "Co-Leader"]:
            conn.close()
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ Sirf Leader ya Admin hi raid initiate kar sakte hain.")
            
        challenger_id = caller[0]
        
        cursor.execute("SELECT name, points FROM clans WHERE clan_id = ?", (challenger_id,))
        attacker = cursor.fetchone()
        attacker_name = attacker[0]
        
        cursor.execute("SELECT clan_id, name, points FROM clans WHERE name = ?", (target_clan,))
        target = cursor.fetchone()
        if not target:
            conn.close()
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ Target clan nahi mila! Sahi naam likhein.")
            
        defender_id = target[0]
        defender_name = target[1]
        defender_points = target[2]
        
        if challenger_id == defender_id:
            conn.close()
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("❌ Aap apne hi clan pe raid nahi kar sakte!")
            
        if defender_points <= 0:
            conn.close()
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(f"❌ **{defender_name}** ke paas lootne ke liye points hi nahi hain (0 points).")
            
        # 50% chance to win
        success = random.choice([True, False])
        
        if success:
            # Steal 5% to 15% of their points
            steal_percentage = random.randint(5, 15) / 100
            stolen_points = int(defender_points * steal_percentage)
            if stolen_points == 0:
                stolen_points = 1
                
            cursor.execute("UPDATE clans SET points = points + ? WHERE clan_id = ?", (stolen_points, challenger_id))
            cursor.execute("UPDATE clans SET points = MAX(0, points - ?) WHERE clan_id = ?", (stolen_points, defender_id))
            conn.commit()
            
            embed = discord.Embed(
                title="🔥 RAID SUCCESSFUL! 🔥",
                description=f"**{attacker_name}** ne **{defender_name}** par achanak hamla kar diya!\n\nTarget ko sambhalne ka mauka hi nahi mila aur aapne unke **{stolen_points:,}** points loot liye!",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            # Attacker loses some points
            attacker_points = attacker[1]
            lose_percentage = random.randint(5, 10) / 100
            lost_points = int(attacker_points * lose_percentage)
            if lost_points == 0:
                lost_points = 1
                
            cursor.execute("UPDATE clans SET points = MAX(0, points - ?) WHERE clan_id = ?", (lost_points, challenger_id))
            conn.commit()
            
            embed = discord.Embed(
                title="🛡️ RAID FAILED! 🛡️",
                description=f"**{attacker_name}** ne **{defender_name}** par hamla kiya, lekin unke guards alert the!\n\nRaid fail ho gayi aur aapko **{lost_points:,}** points ka nuksan uthana pada bhagte waqt.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            
        conn.close()

    # ------------------ OWNER BYPASS COMMANDS ------------------
    @commands.command(name="clan_force_delete", hidden=True)
    @commands.is_owner()
    async def clan_force_delete(self, ctx, *, name: str):
        """👑 Owner Only: Force delete any clan."""
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        cursor.execute("SELECT clan_id FROM clans WHERE name = ?", (name,))
        clan = cursor.fetchone()
        if not clan:
            conn.close()
            return await ctx.send("❌ Ye clan nahi mila!")
        clan_id = clan[0]
        cursor.execute("DELETE FROM clan_members WHERE clan_id = ?", (clan_id,))
        cursor.execute("DELETE FROM clans WHERE clan_id = ?", (clan_id,))
        cursor.execute("DELETE FROM clan_wars WHERE challenger_id = ? OR defender_id = ?", (clan_id, clan_id))
        conn.commit()
        conn.close()
        await ctx.send(f"👑 Force deleted clan **{name}**.")

    @commands.command(name="clan_add_points", hidden=True)
    @commands.is_owner()
    async def clan_add_points(self, ctx, points: int, *, name: str):
        """👑 Owner Only: Add points to a clan."""
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE clans SET points = points + ? WHERE name = ?", (points, name))
        conn.commit()
        conn.close()
        await ctx.send(f"👑 Added {points} points to clan **{name}**.")
        
    @commands.command(name="clan_force_join", hidden=True)
    @commands.is_owner()
    async def clan_force_join(self, ctx, member: discord.Member, *, clan_name: str):
        """👑 Owner Only: Force a user into a clan."""
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT clan_id FROM clans WHERE name = ?", (clan_name,))
        clan = cursor.fetchone()
        if not clan:
            conn.close()
            return await ctx.send("❌ Clan not found!")
            
        clan_id = clan[0]
        # Remove user from old clan if any
        cursor.execute("DELETE FROM clan_members WHERE user_id = ?", (str(member.id),))
        
        cursor.execute(
            "INSERT INTO clan_members (user_id, clan_id, role) VALUES (?, ?, ?)",
            (str(member.id), clan_id, "Member")
        )
        conn.commit()
        conn.close()
        await ctx.send(f"👑 Forced {member.mention} to join clan **{clan_name}**.")
        
    @commands.Cog.listener()
    async def on_message(self, message):
        """Automatically give points to clans when their members chat."""
        if message.author.bot or not message.guild:
            return
            
        # Basic 1 point per message
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        cursor.execute("SELECT clan_id FROM clan_members WHERE user_id = ?", (str(message.author.id),))
        row = cursor.fetchone()
        if row:
            cursor.execute("UPDATE clans SET points = points + 1 WHERE clan_id = ?", (row[0],))
            conn.commit()
        conn.close()

async def setup(bot):
    await bot.add_cog(FunClan(bot))
