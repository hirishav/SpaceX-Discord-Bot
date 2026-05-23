# cogs/help.py
import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", aliases=["h"])
    async def help_command(self, ctx, *, command_name: str = None):
        """Bot ke saare commands ki list ya kisi specific command ki detail dikhata hai."""
        
        prefix = ctx.prefix

        # ---- CASE 1: Agar user ne sirf !help ya !!help likha hai ----
        if not command_name:
            embed = discord.Embed(
                title=f"🤖 {self.bot.user.name} Help Menu",
                description=f"Mera prefix **`{prefix}`** hai. Kisi command ki detail dekhne ke liye `{prefix}help <command>` likhein.",
                color=discord.Color.blue()
            )
            
            if await self.bot.is_owner(ctx.author):
                embed.add_field(name="👑 Owner Only", value="`servers`, `setstatus`, `addmoney`, `removemoney`, `maintenance`, `blacklist`", inline=False)
            
            mod_list = "`warn`, `warnings`, `delwarn`, `clearwarn`, `mute`, `unmute`, `kick`, `ban`, `unban`, `purge`, `slowmode`, `lock`, `unlock`, `lockdown`, `say`, `modlogs`, `poll`, `pin`, `unpin`, `setprefix`, `giveaway`"
            embed.add_field(name="🛡️ Moderation", value=mod_list, inline=False)
            
            eco_list = "`bal`, `work`, `slut`, `crime`, `rob`, `give`, `coinflip`, `roulette`, `blackjack`, `deposit`, `withdraw`, `leaderboard`"
            embed.add_field(name="💰 Economy & Gaming", value=eco_list, inline=False)
            
            util_list = "`serverinfo`, `botinfo`, `invite`, `avatar`"
            embed.add_field(name="⚙️ Utility", value=util_list, inline=False)
            
            general_list = "`afk`, `remindme`"
            embed.add_field(name="✨ General", value=general_list, inline=False)

            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
            return await ctx.send(embed=embed)

        # ---- CASE 2: Agar user ne !help <command> likha hai ----
        target_name = command_name.lower()
        cmd = self.bot.get_command(target_name)

        if not cmd:
            return await ctx.send(f"❌ Mujhe `{command_name}` naam ka koi command nahi mila!")

        if cmd.name in ["servers", "setstatus", "addmoney", "removemoney", "maintenance", "blacklist"] and not await self.bot.is_owner(ctx.author):
            return await ctx.send("❌ Aapke paas is command ki details dekhne ki permission nahi hai!")

        description = "Koi description nahi di gayi."
        usage = f"`{prefix}{cmd.name}`"
        aliases = ", ".join([f"`{a}`" for a in cmd.aliases]) if cmd.aliases else "Koi alias nahi hai."
        examples = f"`{prefix}{cmd.name}`"
        
        cog_name = cmd.cog.__class__.__name__.lower() if cmd.cog else ""
        
        if cmd.name in ["servers", "setstatus", "addmoney", "removemoney", "maintenance", "blacklist"]:
            category = "Owner Only"
        elif "mod" in cog_name or cmd.name in ["warn", "warnings", "delwarn", "clearwarn", "mute", "unmute", "kick", "ban", "unban", "purge", "slowmode", "lock", "unlock", "lockdown", "say", "modlogs", "poll", "pin", "unpin", "setprefix", "giveaway", "greroll", "reroll"]:
            category = "Moderation"
        elif "eco" in cog_name or cmd.name in ["balance", "bal", "money", "work", "job", "slut", "crime", "rob", "steal", "give", "share", "pay", "coinflip", "cf", "roulette", "rt", "blackjack", "bj", "deposit", "dep", "withdraw", "with", "leaderboard", "lb"]:
            category = "Economy & Gaming"
        elif "util" in cog_name or cmd.name in ["serverinfo", "botinfo", "invite", "avatar", "pfp", "av"]:
            category = "Utility"
        elif "gen" in cog_name or cmd.name in ["afk", "remindme", "rm"]:
            category = "General"
        else:
            category = "General"

        # ---- 📦 SAARE CUSTOM DESCRIPTIONS KA DATABASE ----
        if cmd.name == "blacklist":
            description = "🚨 Strictly for Bot Owner! Rules todne par kisi user ko globally bot se block karne ke liye."
            usage = f"`{prefix}blacklist @user/ID <duration> [reason]`\n👉 Blacklist hatane ke liye duration `0` daalein."
            examples = f"`{prefix}blacklist @User 30s Rules bypass`"
        elif cmd.name == "poll":
            description = "📊 Server me custom options ke sath official voting poll start karne ke liye (Requires Manage Messages Permission)."
            usage = f'`{prefix}poll "Question" "Option 1" "Option 2" ...`'
            examples = f'`{prefix}poll "SMR KTR or Home?" "SRM Chennai" "Ghar Jaana Hai"`'
        elif cmd.name == "pin":
            description = "📌 Server ke kisi bhi message ko ID ke zariye channel ke pinned messages me add karne ke liye."
            usage = f"`{prefix}pin <message_id>`"
            examples = f"`{prefix}pin 124357285194729481`"
        elif cmd.name == "unpin":
            description = "🔓 Channel ke kisi bhi pinned message ka pin hatane ke liye."
            usage = f"`{prefix}unpin <message_id>`"
            examples = f"`{prefix}unpin 124357285194729481`"
        elif cmd.name == "setstatus":
            description = "Bot ka status aur activity badalne ke liye."
            usage = f"**Basic:** `{prefix}setstatus <status>`\n**Advanced:** `{prefix}setstatus <status> <playing/watching/listening> <text>`"
            examples = f"`{prefix}setstatus dnd`"
        elif cmd.name == "addmoney":
            description = "Globally kisi bhi user ke wallet ya bank me coins add karne ke liye (Owner Command)."
            usage = f"`{prefix}addmoney @user/ID <wallet/bank> <amount>`"
            examples = f"`{prefix}addmoney @User bank 3e3`"
        elif cmd.name == "removemoney":
            description = "👑 Sirf Rishav bhai ke liye - Kisi bhi user ka paisa globally deduct, half ya completely clear karne ke liye."
            usage = f"`{prefix}removemoney @user/ID <amount/all/half>`"
            examples = f"`{prefix}removemoney @User 4e5`\n`{prefix}removemoney ID half`"
        elif cmd.name == "maintenance":
            description = "🚨 Global Bot Locking Engine! Pure bot commands block karne ke liye (Owner Only)."
            usage = f"`{prefix}maintenance <duration>`"
        elif cmd.name == "warn":
            description = "Kisi member ko officially warn karne ke liye."
            usage = f"`{prefix}warn @user <reason>`"
        elif cmd.name == "mute":
            description = "Kisi member ko specific samay ke liye timeout (mute) karne ke liye."
            usage = f"`{prefix}mute @user <duration><s/m/h/d> <reason>`"
        elif cmd.name == "unmute":
            description = "Kisi member ka timeout samay se pehle hatane ke liye."
            usage = f"`{prefix}unmute @user <reason>`"
        elif cmd.name == "purge":
            description = "Chat se messages filter karke delete karne ke liye (Normal, bots, ya specific user)."
            usage = f"`{prefix}purge <amount>`\n`{prefix}purge bots <amount>`"
        elif cmd.name in ["leaderboard", "lb"]:
            description = "🏆 Server ya Global level par top 10 sabse ameer players ki list dekhne ke liye."
            usage = f"`{prefix}lb server`\n`{prefix}lb global`"
        elif cmd.name in ["giveaway", "gstart"]:
            description = "🎉 Advance Interactive Button wala automatic giveaway start karne ke liye."
            usage = f"`{prefix}giveaway <time> <prize>`"
        elif cmd.name in ["avatar", "av", "pfp"]:
            description = "🖼️ Kisi bhi member ki high-resolution profile picture dekhne ke liye."
            usage = f"`{prefix}avatar [@user]`"
        elif cmd.name == "remindme":
            description = "⏰ Specific time ke baad kisi kaam ke liye ping karke yaad dilane ke liye."
            usage = f"`{prefix}remindme <time> <work>`"

        cmd_embed = discord.Embed(title=f"ℹ️ Command Detail: {cmd.name.upper()}", color=discord.Color.green())
        cmd_embed.add_field(name="📝 Description", value=description, inline=False)
        cmd_embed.add_field(name="⌨️ Usage", value=usage, inline=False)
        cmd_embed.add_field(name="💡 Examples", value=examples, inline=False)
        cmd_embed.add_field(name="🔀 Aliases (Shortforms)", value=aliases, inline=False)
        cmd_embed.add_field(name="📁 Category", value=category, inline=True)

        await ctx.send(embed=cmd_embed)

async def setup(bot):
    await bot.add_cog(Help(bot))