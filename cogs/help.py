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
                title=f"✨ {self.bot.user.name} Premium Help Menu ✨",
                description=f"Mera current prefix **`{prefix}`** hai.\n`Kisi specific command ki details ke liye likhein:` **`{prefix}help <command>`**\n\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬",
                color=discord.Color.from_rgb(47, 49, 54) # Sleek Dark Aesthetic Charcoal Color
            )
            
            # --- 👑 OWNER ONLY CATEGORY ---
            if await self.bot.is_owner(ctx.author):
                embed.add_field(
                    name="👑 OWNER ONLY CONTROL SYSTEM", 
                    value="> `servers`, `setstatus`, `addmoney`, `removemoney`, `seeconfess`, `maintenance`, `blacklist`, `ownerportfolio`, `addstock`, `setshares`, `spam`, `addprefixless`, `removeprefixless`, `listprefixless`", 
                    inline=False
                )
            
            # --- 🛡️ MODERATION CATEGORY ---
            mod_list = "> `warn`, `warnings`, `delwarn`, `clearwarn`, `mute`, `unmute`, `kick`, `ban`, `unban`, `purge`, `slowmode`, `lock`, `unlock`, `lockdown`, `say`, `modlogs`, `poll`, `pin`, `unpin`, `setprefix`, `giveaway`, `staffstats`, `roleaudit`, `lookup`"
            embed.add_field(name="🛡️ MODERATION ENGINE", value=mod_list, inline=False)
            
            # --- 💰 ECONOMY, CASINO & STOCKS Subcategory Nested System ---
            eco_nested = (
                "💳 **Routine Wallet Cash Engine**\n"
                "> `bal`, `work`, `slut`, `crime`, `rob`, `give`, `deposit`, `withdraw`, `leaderboard`\n\n"
                "🎲 **Casino Gambling Hub**\n"
                "> `coinflip`, `roulette`, `blackjack`\n\n"
                "📈 **Stocks & Market**\n"
                "> `stocks`, `buystock`, `sellstock`, `portfolio`, `marketnews`"
            )
            embed.add_field(name="💰 ECONOMY & GAMING", value=eco_nested, inline=False)

            # --- 🎭 FUN CATEGORY ---
            fun_list = "> `roast`, `confess`, `match`, `dm`"
            embed.add_field(name="🎭 COMEDY & FUN", value=fun_list, inline=False)
            
            # --- 🎵 MUSIC ENGINE ---
            music_list = "> `play`, `playnext`, `pause`, `resume`, `skip`, `previous`, `stop`, `leave`, `queue`, `nowplaying`, `volume`, `vmute`, `autoplay`, `loop`, `shuffle`, `clear`, `remove`, `move`, `history`"
            embed.add_field(name="🎵 MUSIC ENGINE", value=music_list, inline=False)
            
            # --- ⚙️ UTILITY CATEGORY ---
            util_list = "> `serverinfo`, `botinfo`, `invite`, `avatar`"
            embed.add_field(name="⚙️ UTILITIES", value=util_list, inline=False)
            
            # --- ✨ GENERAL CATEGORY ---
            general_list = "> `afk`, `remindme`"
            embed.add_field(name="✨ CORE GENERAL", value=general_list, inline=False)

            embed.add_field(name="​", value="▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", inline=False)
            embed.set_footer(text=f"Requested by {ctx.author.name} | SpaceX Bot!", icon_url=ctx.author.display_avatar.url)
            return await ctx.send(embed=embed)

        # ---- CASE 2: Agar user ne !help <command> likha hai ----
        target_name = command_name.lower().strip()
        
        # Exact command fetch template matrix
        cmd = self.bot.get_command(target_name)

        if not cmd:
            return await ctx.send(f"❌ Mujhe `{command_name}` naam ka koi command nahi mila!")

        # 🔒 Security firewall on owner parameters
        owner_cmds = ["servers", "setstatus", "addmoney", "removemoney", "seeconfess", "maintenance", "blacklist", "ownerportfolio", "addstock", "setshares", "spam", "addprefixless", "removeprefixless", "listprefixless"]
        if cmd.name in owner_cmds and not await self.bot.is_owner(ctx.author):
            return await ctx.send("❌ Aapke paas is command ki details dekhne ki permission nahi hai!")

        # Raw declarations parameters template
        description = "Koi description nahi di gayi."
        usage = f"`{prefix}{cmd.name}`"
        aliases = ", ".join([f"`{a}`" for a in cmd.aliases]) if cmd.aliases else "Koi alias nahi hai."
        examples = f"`{prefix}{cmd.name}`"
        category = "General"

        # Explicit hardcoded manual categories structure blocks
        if cmd.name in owner_cmds:
            category = "Owner Only"
        elif cmd.name in ["warn", "warnings", "delwarn", "clearwarn", "mute", "unmute", "kick", "ban", "unban", "purge", "slowmode", "lock", "unlock", "lockdown", "say", "modlogs", "poll", "pin", "unpin", "setprefix", "giveaway", "staffstats", "roleaudit", "lookup"]:
            category = "Moderation"
        elif cmd.name in ["balance", "bal", "money", "work", "job", "slut", "crime", "rob", "steal", "give", "share", "pay", "coinflip", "cf", "roulette", "rt", "blackjack", "bj", "deposit", "dep", "withdraw", "with", "leaderboard", "lb", "stocks", "buystock", "sellstock", "portfolio", "marketnews"]:
            category = "Economy & Gaming"
        elif cmd.name in ["roast", "confess", "match", "dm"]:
            category = "Fun"
        elif cmd.name in ["serverinfo", "botinfo", "invite", "avatar", "pfp", "av"]:
            category = "Utility"
        elif cmd.name in ["afk", "remindme"]:
            category = "General"
        elif cmd.name in ["join", "play", "playnext", "pause", "resume", "skip", "previous", "stop", "leave", "queue", "nowplaying", "volume", "vmute", "autoplay", "loop", "shuffle", "clear", "remove", "move", "history", "p", "pn", "prev", "dc", "q", "np", "ap", "rm"]:
            category = "Music"

        # ---- 📦 SAARE CUSTOM DESCRIPTIONS KA BACCHAFULL EXTENDED DATABASE ----
        if cmd.name == "blacklist":
            description = "🚨 Strictly for Bot Owner! Rules todne par kisi user ko globally bot se block karne ke liye."
            usage = f"`{prefix}blacklist @user/ID <duration> [reason]`"
            examples = f"`{prefix}blacklist @User 30s Rules bypass`"
            
        elif cmd.name == "poll":
            description = "📊 Server me custom options ke sath official voting poll start karne ke liye (Requires Manage Messages Permission)."
            usage = f'{prefix}poll "Question" "Option 1" "Option 2" ...'
            examples = f'{prefix}poll "SMR KTR or Home?" "SRM Chennai" "Ghar Jaana Hai"'
            
        elif cmd.name == "pin":
            description = "📌 Server ke kisi bhi message ko ID ke zariye channel ke pinned messages me add karne ke liye."
            usage = f"`{prefix}pin <message_id>`"
            examples = f"`{prefix}pin 124357285194729481`"
            
        elif cmd.name == "unpin":
            description = "🔓 Channel ke kisi bhi pinned message ka pin hatane ke liye."
            usage = f"`{prefix}unpin <message_id>`"
            examples = f"`{prefix}unpin 124357285194729481`"
            
        elif cmd.name == "setstatus":
            description = "Bot ka status aur activity badalne ke liye (Owner Command)."
            usage = f"`{prefix}setstatus <status> [playing/watching/listening] [text]`"
            examples = f"`{prefix}setstatus dnd watching anime`"
            
        elif cmd.name == "addmoney":
            description = "👑 Sirf Rishav bhai ke liye - Globally kisi ke wallet ya bank me coins add karne ke liye."
            usage = f"`{prefix}addmoney @user/ID <wallet/bank> <amount>`"
            examples = f"`{prefix}addmoney @User bank 3e3`"
            
        elif cmd.name == "removemoney":
            description = "👑 Sirf Rishav bhai ke liye - Kisi bhi user ka paisa globally deduct, half ya completely clear karne ke liye."
            usage = f"`{prefix}removemoney @user/ID <amount/all/half>`"
            examples = f"`{prefix}removemoney @User 4e5`\n`{prefix}removemoney ID half`"
            
        elif cmd.name == "maintenance":
            description = "🚨 Global Bot Locking Engine! Pure bot commands block karne ke liye (Owner Only)."
            usage = f"`{prefix}maintenance <duration>`\n👉 Unlock karne ke liye duration `off` daalein."
            examples = f"`{prefix}maintenance 1h`"
            
        elif cmd.name == "warn":
            description = "Kisi member ko officially warn karne ke liye aur unke DM me notice bhejne ke liye."
            usage = f"`{prefix}warn @user <reason>`"
            examples = f"`{prefix}warn @User Chat Rules Bypass`"
            
        elif cmd.name == "warnings":
            description = "Kisi member ki purani saari warnings ki list dekhne ke liye."
            usage = f"`{prefix}warnings @user`"
            examples = f"`{prefix}warnings @User`"
            
        elif cmd.name == "delwarn":
            description = "Kisi user ki koi ek specific warning number delete karne ke liye."
            usage = f"`{prefix}delwarn @user <warning_number>`"
            examples = f"`{prefix}delwarn @User 2`"
            
        elif cmd.name == "clearwarn":
            description = "Kisi member ki saari warnings ek baar me poori tarah saaf karne ke liye."
            usage = f"`{prefix}clearwarn @user`"
            examples = f"`{prefix}clearwarn @User`"
            
        elif cmd.name == "mute":
            description = "Kisi member ko specific samay ke liye timeout (mute) karne ke liye."
            usage = f"`{prefix}mute @user <duration><s/m/h/d> <reason>`"
            examples = f"`{prefix}mute @User 10m Spamming`"
            
        elif cmd.name == "unmute":
            description = "Kisi member ka active timeout samay se pehle hatane ke liye."
            usage = f"`{prefix}unmute @user [reason]`"
            examples = f"`{prefix}unmute @User Gussa Thanda Hogya`"
            
        elif cmd.name == "kick":
            description = "Kisi member ko server se bahar nikalne ke liye."
            usage = f"`{prefix}kick @user [reason]`"
            examples = f"`{prefix}kick @User Bad Behaviour`"
            
        elif cmd.name == "ban":
            description = "Kisi member ko server se permanent ban karne ke liye."
            usage = f"`{prefix}ban @user [reason]`"
            examples = f"`{prefix}ban @User Raid Attempt`"
            
        elif cmd.name == "unban":
            description = "Kisi banned user ka ban hatakar use wapas aane dene ke liye."
            usage = f"`{prefix}unban <User_ID>`"
            examples = f"`{prefix}unban 727718500663033897`"
            
        elif cmd.name == "purge":
            description = "Chat se hard constraints ke sath selective criteria filter par messages saaf karne ke liye."
            usage = f"`{prefix}purge <amount>`\n`{prefix}purge links <amount>`\n`{prefix}purge images <amount>`\n`{prefix}purge word <\"keyword\"> <amount>`"
            examples = f"`{prefix}purge links 50`\n`{prefix}purge word \"spam\" 20`"
            
        elif cmd.name == "slowmode":
            description = "Current text channel ka message sending cooldown cooldown timer change karne ke liye."
            usage = f"`{prefix}slowmode <seconds>`"
            examples = f"`{prefix}slowmode 5`"
            
        elif cmd.name == "lock":
            description = "Channel ko explicit timer aur reason ke saath lock karne ke liye."
            usage = f"`{prefix}lock [#channel] [time] [reason]`"
            examples = f"`{prefix}lock #general 30m Raid Control`"
            
        elif cmd.name == "unlock":
            description = "Kisi locked channel ko wapas open karne ke liye."
            usage = f"`{prefix}unlock [#channel]`"
            examples = f"`{prefix}unlock #general`"
            
        elif cmd.name == "lockdown":
            description = "🚨 EMERGENCY: Poore server ke saare text channels ko ek baar me check ya bypass karke lock ya wapas unlock karne ke liye."
            usage = f"`{prefix}lockdown <on/off>`"
            examples = f"`{prefix}lockdown on`"
            
        elif cmd.name == "say":
            description = "📢 Bot ke zariye chat me apni marzi ka message thukwane ke liye."
            usage = f"`{prefix}say <message>`"
            examples = f"`{prefix}say Hello Guys`"
            
        elif cmd.name == "modlogs":
            description = "📊 Server me kisi user ke upar chalaaye gaye saare mod action stats aur history ki details."
            usage = f"`{prefix}modlogs @user/ID`"
            examples = f"`{prefix}modlogs @User`"
            
        elif cmd.name in ["balance", "bal"]:
            description = "Aapka wallet aur bank balance check karne ke liye."
            usage = f"`{prefix}bal`"
            examples = f"`{prefix}bal`"
            
        elif cmd.name == "work":
            description = "Mehnat ka kaam karke safe coins kamane ke liye (30s Cooldown)."
            usage = f"`{prefix}work`"
            examples = f"`{prefix}work`"
            
        elif cmd.name == "slut":
            description = "Risky tareeqon se paise kamane ke liye! Fine lagne ka khatra rehta hai."
            usage = f"`{prefix}slut`"
            examples = f"`{prefix}slut`"
            
        elif cmd.name == "crime":
            description = "High-risk, High-reward illegal kaam karke paise chhapne ke liye."
            usage = f"`{prefix}crime`"
            examples = f"`{prefix}crime`"
            
        elif cmd.name == "rob":
            description = "Kisi doosre user ke wallet se cash cash churane ke liye."
            usage = f"`{prefix}rob @user`"
            examples = f"`{prefix}rob @User`"
            
        elif cmd.name == "give":
            description = "Apne wallet se kisi doosre user ko coins transfer karne ke liye."
            usage = f"`{prefix}give @user <amount>`"
            examples = f"`{prefix}give @User 5000`"
            
        elif cmd.name in ["coinflip", "cf"]:
            description = "Heads ya Tails par jua khelne ke liye! Double cash jackpot reward."
            usage = f"`{prefix}coinflip <amount> <heads/tails>`"
            examples = f"`{prefix}coinflip 1000 heads`"
            
        elif cmd.name in ["roulette", "rt"]:
            description = "Casino Roulette game! Red/Black par 2x aur Green par direct 14x cash payout."
            usage = f"`{prefix}roulette <amount> <red/black/green>`"
            examples = f"`{prefix}roulette 500 red`"
            
        elif cmd.name in ["blackjack", "bj"]:
            description = "Real interactive buttons (Hit/Stand) wala genuine Blackjack card game!"
            usage = f"`{prefix}blackjack <amount>`"
            examples = f"`{prefix}blackjack 2000`"
            
        elif cmd.name in ["deposit", "dep"]:
            description = "Wallet se cash nikal kar safe bank locker me deposit karne ke liye."
            usage = f"`{prefix}deposit <amount/all/half>`"
            examples = f"`{prefix}deposit all`"
            
        elif cmd.name in ["withdraw", "with"]:
            description = "Bank account se paise nikal kar wapas cash wallet me lane ke liye."
            usage = f"`{prefix}withdraw <amount/all/half>`"
            examples = f"`{prefix}withdraw 5000`"
            
        elif cmd.name == "invite":
            description = "Bot ko doosre server me add karne ke liye official invite link nikalne ke liye."
            usage = f"`{prefix}invite`"
            examples = f"`{prefix}invite`"
            
        elif cmd.name == "serverinfo":
            description = "Jis server me aap hain uski poori details aur statistics dekhne ke liye."
            usage = f"`{prefix}serverinfo`"
            examples = f"`{prefix}serverinfo`"
            
        elif cmd.name == "botinfo":
            description = "Bot ki live statistics, uptime aur network performance data dekhne ke liye."
            usage = f"`{prefix}botinfo`"
            examples = f"`{prefix}botinfo`"
            
        elif cmd.name == "afk":
            description = "Aapko AFK status par dalne ke liye taaki ping karne par bot notify kare."
            usage = f"`{prefix}afk [reason]`"
            examples = f"`{prefix}afk Khana Kha Raha Hun`"
            
        elif cmd.name == "remindme":
            description = "⏰ Specific time ke baad kisi kaam ke liye ping karke yaad dilane ke liye."
            usage = f"`{prefix}remindme <time><s/m/h> <work>`"
            examples = f"`{prefix}remindme 10m Exams Ki Taiyari`"
            
        elif cmd.name == "servers":
            description = "Sirf Bot Creator ke liye active servers ki list tracking map (Owner Only)."
            usage = f"`{prefix}servers`"
            examples = f"`{prefix}servers`"
            
        elif cmd.name == "setprefix":
            description = "⚙️ Server ka default custom bot prefix badalne ke liye (Requires Manage Server Permission)."
            usage = f"`{prefix}setprefix <new_prefix>`"
            examples = f"`{prefix}setprefix $`"
            
        elif cmd.name in ["leaderboard", "lb"]:
            description = "🏆 Server ya Global level par top 10 sabse ameer players ki list dekhne ke liye."
            usage = f"`{prefix}lb server`\n`{prefix}lb global`"
            examples = f"`{prefix}lb server`"
            
        elif cmd.name in ["giveaway", "gstart"]:
            description = "🎉 Advance Interactive Button wala automatic giveaway engine framework toggle karne ke liye."
            usage = f'`{prefix}gstart <time> "<requirements_text>" <@role/none> <prize>`'
            examples = f'`{prefix}gstart 10m "Must have Fans role" @Fans Spotify`'
            
        elif cmd.name in ["avatar", "av", "pfp"]:
            description = "🖼️ Kisi bhi member ki high-resolution display picture fetch karke show karne ke liye."
            usage = f"`{prefix}avatar [@user/ID]`"
            examples = f"`{prefix}avatar @Rishav`"

        elif cmd.name == "roast":
            description = "🔥 Kisi member ki dosto ke beech shandaar witty roasts ke sath taang kheenchna."
            usage = f"`{prefix}roast [@user]`"
            examples = f"`{prefix}roast @User`"

        elif cmd.name == "confess":
            description = "🤫 Mentioned channel me anonymous embed message bhejta hai aur back-end tracking table me save karta hai."
            usage = f"`{prefix}confess <#channel> <message>`"
            examples = f"`{prefix}confess #confessions I Love You Kriti`"

        elif cmd.name == "match":
            description = "❤️ Do logo ke beech ka fun love/friendship percentage matrix calculator."
            usage = f"`{prefix}match @user1 @user2`"
            examples = f"`{prefix}match @User1 @User2`"

        elif cmd.name == "dm":
            description = "📩 Bot ke zariye kisi user ko private DM bhejkar logs embed screen par dikhana."
            usage = f"`{prefix}dm @user/ID <message>`"
            examples = f"`{prefix}dm @User Kaise ho bhai?`"

        elif cmd.name == "seeconfess":
            description = "👑 Sirf Rishav bhai ke liye - Saare anonymous confessions track karne ya kisi specific user ka data nikalne ke liye."
            usage = f"`{prefix}seeconfess`\n`{prefix}seeconfess @user/ID`"

        elif cmd.name == "stocks":
            description = "📈 Live Top 200 Real-life Stocks (Samsung, NIFTY 50, SilverBees) ke rates aur remaining available limits page-wise check karne ke liye."
            usage = f"`{prefix}stocks [page_number]`"
            examples = f"`{prefix}stocks 2`"
            
        elif cmd.name == "buystock":
            description = "🛒 Wallet coins ko use karke 10,000 limited share inventory pool se real assets instantly purchase karne ke liye."
            usage = f"`{prefix}buystock <TICKER> <quantity>`"
            examples = f"`{prefix}buystock NIFTY 5`"
            
        elif cmd.name == "sellstock":
            description = "💰 Owned portfolio shares ko current live market value pricing par profit ya loss ke sath instant wallet liquid cash me swap karne ke liye."
            usage = f"`{prefix}sellstock <TICKER> <quantity>`"
            examples = f"`{prefix}sellstock SMSNG 2`"
            
        elif cmd.name == "portfolio":
            description = "💼 Aapka dynamic holdings asset value show karta hai. Isme aap security visibility status controls manage kar sakte ho."
            usage = f"`{prefix}portfolio [@user]`\n`{prefix}portfolio set <public/private>`"
            examples = f"`{prefix}portfolio set private`\n`{prefix}portfolio @User`"
            
        elif cmd.name == "ownerportfolio":
            description = "👑 (Admin Override Command) Server ke kisi bhi private account ka portfolio securely bypass karke analytics dekhne ke liye."
            usage = f"`{prefix}ownerportfolio @user`"
            
        elif cmd.name == "addstock":
            description = "👑 Live market database registries me instantly manually custom real ticker inject karne ke liye."
            usage = f"`{prefix}addstock <TICKER> <Full Name> <Initial Cost Price>`"
            examples = f"`{prefix}addstock COFFEE \"Starbucks Capital\" 250`"
            
        elif cmd.name == "setshares":
            description = "👑 Kisi active ticker ke total 10,000 baseline pool bache hue available inventory shares force-rewrite karne ke liye."
            usage = f"`{prefix}setshares <TICKER> <quantity>`"
            examples = f"`{prefix}setshares RELI 5000`"

        elif cmd.name in ["marketnews", "news"]:
            description = "📻 Live share market me dynamic global sectors (Tech, Bluechips, Crypto) ke boom aur crash alerts check karne ke liye."
            usage = f"`{prefix}marketnews`"
            examples = f"`{prefix}marketnews`"

        elif cmd.name == "staffstats":
            description = "📊 Server staff aur administrative profiles ke continuous actions frequency aur punishment tracking reports dekhne ke liye."
            usage = f"`{prefix}staffstats` ya `{prefix}staffstats @user`"
            examples = f"`{prefix}staffstats`\n`{prefix}staffstats @Rishav`"

        elif cmd.name == "roleaudit":
            description = "🛡️ Server security matrix audit. Dangerous administrative permissions (Administrator, Manage Roles) wale logo ki tracking dashboard screen par lane ke liye."
            usage = f"`{prefix}roleaudit`"
            examples = f"`{prefix}roleaudit`"

        elif cmd.name == "lookup":
            description = "🕵️ User Profile Forensics Matrix. Kisi bhi member ka deep timeline creation aur safety check permissions report dekhne ke liye."
            usage = f"`{prefix}lookup` ya `{prefix}lookup @user`"
            examples = f"`{prefix}lookup @Rishav`"

        elif cmd.name == "spam":
            description = "👑 MAXIMUM DESTRUCTIVE COMMAND (Owner Only): Server ke kisi bhi text channel me target text sequence ko multiple times loop me spam karne ke liye."
            usage = f"`{prefix}spam #channel <amount> <message_content>`"
            examples = f"`{prefix}spam #general 100 Hello @User`"

        # 🔥 --- NO PREFIX PROTOCOLS REGISTRY ---
        elif cmd.name == "addprefixless":
            description = "👑 Owner-Only: Server ke kisi trusted member ko bina prefix execution route ke bot use karne ka premium access dene ke liye."
            usage = f"`{prefix}addprefixless @user`"
            examples = f"`{prefix}addprefixless @User`"

        elif category == "Music":
            description = cmd.help if cmd.help else "Music playback and control engine command."
            usage = f"`{prefix}{cmd.name}`"
            examples = f"`{prefix}{cmd.name}`"

        cmd_embed = discord.Embed(title=f"ℹ️ Command Detail: {cmd.name.upper()}", color=discord.Color.green())
        cmd_embed.add_field(name="📝 Description", value=description, inline=False)
        cmd_embed.add_field(name="⌨️ Usage", value=usage, inline=False)
        cmd_embed.add_field(name="💡 Examples", value=examples, inline=False)
        cmd_embed.add_field(name="🔀 Aliases (Shortforms)", value=aliases, inline=False)
        cmd_embed.add_field(name="📁 Category", value=category, inline=True)

        await ctx.send(embed=cmd_embed)

async def setup(bot):
    await bot.add_cog(Help(bot))