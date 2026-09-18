import discord
from discord.ext import commands
import asyncio

class FunFake(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="fake", invoke_without_command=True)
    async def fake(self, ctx):
        """Fake moderation/utility commands group for fun."""
        await ctx.send("Available fake commands: ban, mute, kick, warn, delchannel, tic create, afk, role add, temprole, hide all, unhide all, slowmode", delete_after=10)
        try: await ctx.message.delete()
        except: pass

    @fake.command(name="ban")
    async def fake_ban(self, ctx, user: discord.Member, *, reason: str = "No reason provided"):
        embed = discord.Embed(
            description=f"✅ {user.mention} has been **banned** | {reason}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    @fake.command(name="mute")
    async def fake_mute(self, ctx, user: discord.Member, *, reason: str = "No reason provided"):
        embed = discord.Embed(
            description=f"✅ {user.mention} has been **muted** | {reason}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    @fake.command(name="kick")
    async def fake_kick(self, ctx, user: discord.Member, *, reason: str = "No reason provided"):
        embed = discord.Embed(
            description=f"✅ {user.mention} has been **kicked** | {reason}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    @fake.command(name="warn")
    async def fake_warn(self, ctx, user: discord.Member, *, reason: str = "No reason provided"):
        embed = discord.Embed(
            description=f"⚠️ {user.mention} has been **warned** | {reason}",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    @fake.command(name="delchannel")
    async def fake_delchannel(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        embed = discord.Embed(
            description=f"✅ {channel.mention} has been **deleted**.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    # 'fake tic' and 'fake tic create'
    @fake.group(name="tic", invoke_without_command=True)
    async def fake_tic(self, ctx):
        pass

    @fake_tic.command(name="create")
    async def fake_tic_create(self, ctx):
        embed = discord.Embed(
            description=f"✅ Ticket created successfully in <#{ctx.channel.id}>",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    @fake.command(name="afk")
    async def fake_afk(self, ctx, *, reason: str = "I'm AFK"):
        embed = discord.Embed(
            description=f"✅ {ctx.author.mention} your AFK is now set to: **{reason}**",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    # 'fake role' and 'fake role add'
    @fake.group(name="role", invoke_without_command=True)
    async def fake_role(self, ctx):
        pass

    @fake_role.command(name="add")
    async def fake_role_add(self, ctx, user: discord.Member, role_name: str = "Admin", *, reason: str = "No reason provided"):
        embed = discord.Embed(
            description=f"✅ Added role **{role_name}** to {user.mention} | {reason}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    @fake.command(name="temprole")
    async def fake_temprole(self, ctx, user: discord.Member, duration: str = "1h", role_name: str = "VIP"):
        embed = discord.Embed(
            description=f"✅ Added temp role **{role_name}** to {user.mention} for **{duration}**.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    # 'fake hide' and 'fake hide all'
    @fake.group(name="hide", invoke_without_command=True)
    async def fake_hide(self, ctx):
        pass

    @fake_hide.command(name="all")
    async def fake_hide_all(self, ctx):
        embed = discord.Embed(
            description="✅ All channels have been **hidden** from everyone.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    # 'fake unhide' and 'fake unhide all'
    @fake.group(name="unhide", invoke_without_command=True)
    async def fake_unhide(self, ctx):
        pass

    @fake_unhide.command(name="all")
    async def fake_unhide_all(self, ctx):
        embed = discord.Embed(
            description="✅ All channels have been **unhidden** for everyone.",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass

    @fake.command(name="slowmode")
    async def fake_slowmode(self, ctx, duration: str = "1h"):
        embed = discord.Embed(
            description=f"⏱️ Is channel me **{duration}** ka Slowmode laga diya gaya hai.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
        try: await ctx.message.delete()
        except: pass


async def setup(bot):
    await bot.add_cog(FunFake(bot))
