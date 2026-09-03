import discord
from discord.ext import commands
import database

class ModJoinRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)
    async def joinrole(self, ctx, *, role: discord.Role = None):
        """
        Configure the join role for the server.
        Usage:
        `!!joinrole on` - Enable join role
        `!!joinrole off` - Disable join role
        `!!joinrole @role` - Set the join role
        """
        if role is not None:
            db = database.connect()
            cursor = db.cursor()
            cursor.execute("""
            INSERT INTO joinrole_config (server_id, role_id, is_enabled)
            VALUES (?, ?, 1)
            ON CONFLICT(server_id) DO UPDATE SET role_id=excluded.role_id, is_enabled=1
            """, (str(ctx.guild.id), str(role.id)))
            db.commit()
            db.close()
            await ctx.send(f"✅ **Join Role** has been set to {role.mention} and enabled.\n*(Note: This role is now **sticky**! Members who leave and rejoin will get their previous roles back automatically.)*")
        else:
            await ctx.send_help(ctx.command)

    @joinrole.command(name="on")
    @commands.has_permissions(manage_roles=True)
    async def joinrole_on(self, ctx):
        """Enable the join role feature."""
        db = database.connect()
        cursor = db.cursor()
        cursor.execute("SELECT role_id FROM joinrole_config WHERE server_id = ?", (str(ctx.guild.id),))
        row = cursor.fetchone()
        
        if row and row[0]:
            cursor.execute("UPDATE joinrole_config SET is_enabled = 1 WHERE server_id = ?", (str(ctx.guild.id),))
            db.commit()
            await ctx.send("✅ **Join Role** feature is now **enabled**.")
        else:
            await ctx.send("❌ You haven't set a join role yet. Use `!!joinrole @role` to set one first.")
        db.close()

    @joinrole.command(name="off")
    @commands.has_permissions(manage_roles=True)
    async def joinrole_off(self, ctx):
        """Disable the join role feature."""
        db = database.connect()
        cursor = db.cursor()
        cursor.execute("UPDATE joinrole_config SET is_enabled = 0 WHERE server_id = ?", (str(ctx.guild.id),))
        db.commit()
        db.close()
        await ctx.send("✅ **Join Role** feature is now **disabled**.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        roles_to_add = []
        
        db = database.connect()
        cursor = db.cursor()
        
        # 1. Check for sticky roles
        cursor.execute("SELECT roles FROM sticky_roles WHERE server_id = ? AND user_id = ?", (str(guild.id), str(member.id)))
        sticky_row = cursor.fetchone()
        
        if sticky_row and sticky_row[0]:
            saved_role_ids = sticky_row[0].split(',')
            for role_id_str in saved_role_ids:
                if role_id_str:
                    try:
                        role = guild.get_role(int(role_id_str))
                        if role and role < guild.me.top_role and role.id != guild.id:
                            roles_to_add.append(role)
                    except ValueError:
                        pass
        
        # 2. Check for join role
        cursor.execute("SELECT role_id, is_enabled FROM joinrole_config WHERE server_id = ?", (str(guild.id),))
        join_row = cursor.fetchone()
        
        if join_row and join_row[1] == 1 and join_row[0]:
            join_role = guild.get_role(int(join_row[0]))
            if join_role and join_role < guild.me.top_role and join_role not in roles_to_add:
                roles_to_add.append(join_role)
                
        db.close()
        
        if roles_to_add:
            try:
                await member.add_roles(*roles_to_add, reason="Sticky Roles / Join Role Assignment")
            except discord.Forbidden:
                pass
            except discord.HTTPException:
                pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        guild = member.guild
        # Get all roles except @everyone and roles that are higher than bot's top role
        # Actually just filtering out everyone role is fine, can't add back higher roles later anyway.
        roles = [str(r.id) for r in member.roles if r.id != guild.id]
        
        if not roles:
            return
            
        roles_str = ",".join(roles)
        
        db = database.connect()
        cursor = db.cursor()
        cursor.execute("""
        INSERT INTO sticky_roles (server_id, user_id, roles)
        VALUES (?, ?, ?)
        ON CONFLICT(server_id, user_id) DO UPDATE SET roles=excluded.roles
        """, (str(guild.id), str(member.id), roles_str))
        db.commit()
        db.close()

async def setup(bot):
    await bot.add_cog(ModJoinRole(bot))
