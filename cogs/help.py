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
            
            # --- 👑 OWNER ONLY CATEGORY (Blacklist Ab Safe Hai) ---
            if await self.bot.is_owner(ctx.author):
                embed.add_field(name="👑 Owner Only", value="`servers`, `setstatus`, `add-money`, `reset-money`, `maintenance`, `blacklist`", inline=False)
            
            # --- 🛡️ MODERATION CATEGORY (Poll Added, Blacklist Removed!) ---
            mod_list = "`warn`, `warnings`, `delwarn`, `clearwarn`, `mute`, `unmute`, `kick`, `ban`, `unban`, `purge`, `slowmode`, `lock`, `unlock`, `lockdown`, `say`, `modlogs`, `poll`, `pin`"
            embed.add_field(name="🛡️ Moderation", value=mod_list, inline=False)
            
            # --- 💰 ECONOMY & GAMING ---
            eco_list = "`bal`, `work`, `slut`, `crime`, `rob`, `give`, `coinflip`, `roulette`, `blackjack`, `deposit`, `withdraw`"
            embed.add_field(name="💰 Economy & Gaming", value=eco_list, inline=False)
            
            # --- ⚙️ UTILITY CATEGORY ---
            util_list = "`serverinfo`, `botinfo`, `invite`"
            embed.add_field(name="⚙️ Utility", value=util_list, inline=False)
            
            # --- ✨ GENERAL CATEGORY ---
            general_list = "`afk`, `remindme`"
            embed.add_field(name="✨ General", value=general_list, inline=False)

            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
            return await ctx.send(embed=embed)

        # ---- CASE 2: Agar user ne !help <command> likha hai ----
        cmd = self.bot.get_command(command_name.lower())

        if not cmd:
            return await ctx.send(f"❌ Mujhe `{command_name}` naam ka koi command nahi mila!")

        # 🔒 OWNER COMMAND SECURITY CHECK
        if cmd.name in ["servers", "setstatus", "add-money", "reset-money", "maintenance", "blacklist"] and not await self.bot.is_owner(ctx.author):
            return await ctx.send("❌ Aapke paas is command ki details dekhne ki permission nahi hai!")

        description = "Koi description nahi di gayi."
        usage = f"`{prefix}{cmd.name}`"
        aliases = ", ".join([f"`{a}`" for a in cmd.aliases]) if cmd.aliases else "Koi alias nahi hai."
        examples = f"`{prefix}{cmd.name}`"
        
        # Category Mapping Matrix
        cog_name = cmd.cog.__class__.__name__.lower() if cmd.cog else ""
        
        if cmd.name in ["servers", "setstatus", "add-money", "reset-money", "maintenance", "blacklist"]:
            category = "Owner Only"
        elif "modpoll" in cog_name or cmd.name in ["warn", "warnings", "delwarn", "clearwarn", "mute", "unmute", "kick", "ban", "unban", "purge", "slowmode", "lock", "unlock", "lockdown", "say", "modlogs", "poll", "pin"]:
            category = "Moderation"
        elif "eco" in cog_name or cmd.name in ["balance", "bal", "money", "work", "job", "slut", "crime", "rob", "steal", "give", "share", "pay", "coinflip", "cf", "roulette", "rt", "blackjack", "bj", "deposit", "dep", "withdraw", "with"]:
            category = "Economy & Gaming"
        elif cmd.name in ["serverinfo", "botinfo", "invite"]:
            category = "Utility"
        elif "genafk" in cog_name or "genremindme" in cog_name or cmd.name in ["afk", "remindme", "rm"]:
            category = "General"
        else:
            category = "General"

        # Custom details mapping cache
        if cmd.name == "blacklist":
            description = "🚨 Strictly for Bot Owner! Rules todne par kisi user ko globally bot se block karne ke liye."
            usage = f"`{prefix}blacklist @user/ID <duration> [reason]`\n👉 Blacklist hatane ke liye duration `0` daalein."
            examples = f"`{prefix}blacklist @User 30s Rules bypass`"
        elif cmd.name == "poll":
            description = "📊 Server me custom options ke sath official voting poll start karne ke liye (Requires Manage Messages Permission)."
            usage = f'`{prefix}poll "Question" "Option 1" "Option 2"`'
            examples = f'`{prefix}poll "SMR KTR or Home?" "SRM Chennai" "Ghar Jaana Hai"`'
        elif cmd.name == "setstatus":
            description = "Bot ka status aur activity badalne ke liye."
            usage = f"**Basic:** `{prefix}setstatus <status>`\n**Advanced:** `{prefix}setstatus <status> <playing/watching/listening> <text>`"
            examples = f"`{prefix}setstatus dnd`"
        elif cmd.name == "add-money":
            description = "Globally kisi bhi user ke wallet me coins add karne ke liye (Owner Command)."
            usage = f"`{prefix}add-money @user/ID <amount>`"
        elif cmd.name == "reset-money":
            description = "Globally kisi bhi user ka bank aur wallet balance completely zero karne ke liye (Owner Command)."
            usage = f"`{prefix}reset-money @user/ID`"
        elif cmd.name == "maintenance":
            description = "🚨 Global Bot Locking Engine! Pure bot commands block karne ke liye (Owner Only)."
            usage = f"`{prefix}maintenance <duration>`\n👉 Unlock karne ke liye: `{prefix}maintenance off`"
        elif cmd.name == "warn":
            description = "Kisi member ko officially warn karne ke liye aur unke DM me message bhejne ke liye."
            usage = f"`{prefix}warn @user <reason>`"
        elif cmd.name == "warnings":
            description = "Kisi member ki purani saari warnings ki list dekhne ke liye."
            usage = f"`{prefix}warnings @user`"
        elif cmd.name == "delwarn":
            description = "Kisi user ki koi ek specific warning number delete karne ke liye."
            usage = f"`{prefix}delwarn @user <warning_number>`"
        elif cmd.name == "clearwarn":
            description = "Kisi member ki saari warnings ek baar me poori tarah saaf karne ke liye."
            usage = f"`{prefix}clearwarn @user`"
        elif cmd.name == "mute":
            description = "Kisi member ko specific samay ke liye timeout (mute) karne ke liye."
            usage = f"`{prefix}mute @user <duration><s/m/h/d> <reason>`"
        elif cmd.name == "unmute":
            description = "Kisi member ka timeout samay se pehle hatane ke liye."
            usage = f"`{prefix}unmute @user <reason>`"
        elif cmd.name == "kick":
            description = "Kisi member ko server se bahar nikalne ke liye."
            usage = f"`{prefix}kick @user <reason>`"
        elif cmd.name == "ban":
            description = "Kisi member ko server se permanent ban karne ke liye."
            usage = f"`{prefix}ban @user <reason>`"
        elif cmd.name == "unban":
            description = "Kisi banned user ka ban hatakar use wapas aane dene ke liye."
            usage = f"`{prefix}unban <User_ID>`"
        elif cmd.name == "purge":
            description = "Chat se specific amount me messages delete karne ke liye."
            usage = f"`{prefix}purge <amount>`"
        elif cmd.name == "slowmode":
            description = "Channel cooldown rate set karne ke liye."
            usage = f"`{prefix}slowmode <seconds>`"
        elif cmd.name == "lock":
            description = "Channel ko explicit timer aur reason ke saath lock karne ke liye."
            usage = f"`{prefix}lock [#channel] [time] [reason]`"
        elif cmd.name == "unlock":
            description = "Kisi locked channel ko wapas open karne ke liye."
            usage = f"`{prefix}unlock [#channel]`"
        elif cmd.name == "lockdown":
            description = "🚨 EMERGENCY COMMAND: Poore server ke saare text channels ko ek baar me lock/unlock karne ke liye."
            usage = f"`{prefix}lockdown`"
        elif cmd.name == "say":
            description = "📢 Bot ke zariye chat me apni marzi ka message bhejne ke liye."
            usage = f"`{prefix}say <message>`"
        elif cmd.name == "modlogs":
            description = "📊 Server me kisi user ke upar chalaaye gaye saare moderation action stats aur history dekhne ke liye."
            usage = f"`{prefix}modlogs @user/ID`"
        elif cmd.name in ["balance", "bal"]:
            description = "Aapka wallet aur bank balance check karne ke liye."
            usage = f"`{prefix}bal`"
        elif cmd.name == "work":
            description = "Mehnat ka kaam karke safe coins kamane ke liye. (30s Cooldown)"
            usage = f"`{prefix}work`"
        elif cmd.name == "slut":
            description = "Risky tareeqon se paise kamane ke liye! Harne par fine lag sakta hai."
            usage = f"`{prefix}slut`"
        elif cmd.name == "crime":
            description = "High-risk, High-reward illegal kaam! (30s Cooldown)"
            usage = f"`{prefix}crime`"
        elif cmd.name == "rob":
            description = "Kisi doosre user ke wallet se cash churaane ke liye."
            usage = f"`{prefix}rob @user`"
        elif cmd.name == "give":
            description = "Apne wallet se kisi doosre user ko coins transfer karne ke liye."
            usage = f"`{prefix}give @user <amount>`"
        elif cmd.name in ["coinflip", "cf"]:
            description = "Heads ya Tails par jua khelne ke liye! Double cash jackpot."
            usage = f"`{prefix}coinflip <amount> <heads/tails>`"
        elif cmd.name in ["roulette", "rt"]:
            description = "Casino Roulette game! Red/Black par 2x aur Green par direct 14x cash!"
            usage = f"`{prefix}roulette <amount> <red/black/green>`"
        elif cmd.name in ["blackjack", "bj"]:
            description = "Real interactive buttons (Hit/Stand) wala genuine Blackjack card game!"
            usage = f"`{prefix}blackjack <amount>`"
        elif cmd.name in ["deposit", "dep"]:
            description = "Wallet se cash nikal kar safe bank me deposit karne ke liye."
            usage = f"`{prefix}deposit <amount/all/half>`"
        elif cmd.name in ["withdraw", "with"]:
            description = "Bank account se paise nikal kar wapas cash wallet me lane ke liye."
            usage = f"`{prefix}withdraw <amount/all/half>`"
        elif cmd.name == "invite":
            description = "Bot ko apne khud ke kisi server me add karne ke liye official invite link nikalne ke liye."
            usage = f"`{prefix}invite`"
        elif cmd.name == "serverinfo":
            description = "Jis server me aap hain uski poori details dekhne ke liye."
            usage = f"`{prefix}serverinfo`"
        elif cmd.name == "botinfo":
            description = "Bot ki live statistics dekhne ke liye."
            usage = f"`{prefix}botinfo`"
        elif cmd.name == "afk":
            description = "Aapko AFK status par dalne ke liye taaki jab koi aapko ping kare toh bot use reason bataye."
            usage = f"`{prefix}afk <reason>`"
        elif cmd.name == "remindme":
            description = "⏰ Aapko aur baki users ko specific time ke baad kisi kaam ke liye ping karke yaad dilane ke liye."
            usage = f"`{prefix}remindme <time><s/m/h> <work>`"
        elif cmd.name == "servers":
            description = "Sirf Bot Creator ke liye servers ki list dekhne ke liye (Owner Command)."
            usage = f"`{prefix}servers`"
        elif cmd.name == "pin":
         description = "📌 Server ke kisi bhi message ko ID ke zariye channel ke pinned messages me add karne ke liye."
         usage = f"`{prefix}pin <message_id>`"
         examples = f"`{prefix}pin 124357285194729481`"

        cmd_embed = discord.Embed(title=f"ℹ️ Command Detail: {cmd.name.upper()}", color=discord.Color.green())
        cmd_embed.add_field(name="📝 Description", value=description, inline=False)
        cmd_embed.add_field(name="⌨️ Usage", value=usage, inline=False)
        cmd_embed.add_field(name="💡 Examples", value=examples, inline=False)
        cmd_embed.add_field(name="🔀 Aliases (Shortforms)", value=aliases, inline=False)
        cmd_embed.add_field(name="📁 Category", value=category, inline=True)

        await ctx.send(embed=cmd_embed)

async def setup(bot):
    await bot.add_cog(Help(bot))