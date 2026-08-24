# cogs/mod_roleuser.py
import discord
from discord.ext import commands

class ModRoleUser(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="roleuser", aliases=["roleusers", "inrole"])
    @commands.has_guild_permissions(manage_roles=True)
    async def roleuser(self, ctx, *, role: discord.Role):
        """Kisi specific role ke members ki list dekhne ke liye."""
        
        # Ensure guild members are fully cached
        if not ctx.guild.chunked:
            await ctx.guild.chunk()
            
        members = role.members
        if not members:
            embed = discord.Embed(
                title=f"👥 Members with {role.name}",
                description="❌ Is role me koi member nahi hai.",
                color=role.color if role.color.value != 0 else discord.Color.blue()
            )
            await ctx.send(embed=embed)
            try:
                await ctx.message.delete()
            except Exception:
                pass
            return

        # Format member list: 1. Username (ID)
        lines = []
        for index, member in enumerate(members, start=1):
            lines.append(f"`{index}.` {member.mention} - `{member.name}`")

        # Join and split if it exceeds Discord's description limits (4096 chars)
        description = "\n".join(lines)
        
        if len(description) <= 4000:
            embed = discord.Embed(
                title=f"👥 Members with {role.name} ({len(members)})",
                description=description,
                color=role.color if role.color.value != 0 else discord.Color.blue()
            )
            await ctx.send(embed=embed)
        else:
            # Chunking the list if it's too long
            chunks = []
            current_chunk = ""
            for line in lines:
                if len(current_chunk) + len(line) + 1 > 4000:
                    chunks.append(current_chunk)
                    current_chunk = line + "\n"
                else:
                    current_chunk += line + "\n"
            if current_chunk:
                chunks.append(current_chunk)

            for i, chunk in enumerate(chunks, start=1):
                embed = discord.Embed(
                    title=f"👥 Members with {role.name} ({len(members)}) - Part {i}/{len(chunks)}",
                    description=chunk,
                    color=role.color if role.color.value != 0 else discord.Color.blue()
                )
                await ctx.send(embed=embed)

        try:
            await ctx.message.delete()
        except Exception:
            pass

    @roleuser.error
    async def roleuser_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Aapke paas is command ko use karne ki permission nahi hai!")
        elif isinstance(error, commands.RoleNotFound):
            await ctx.send("❌ Role nahi mila! Kripya sahi role mention karein ya ID daalein.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Sahi tarika: `{ctx.prefix}roleuser @role`")
        else:
            await ctx.send(f"❌ Kuch gadbad hui: {error}")

async def setup(bot):
    await bot.add_cog(ModRoleUser(bot))
