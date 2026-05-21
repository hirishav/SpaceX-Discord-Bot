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
            
            # --- 👑 OWNER ONLY CATEGORY (Sirf aapko hi poori list dikhegi) ---
            if await self.bot.is_owner(ctx.author):
                embed.add_field(name="👑 Owner Only", value="`servers`, `setstatus`, `add-money`, `reset-money`", inline=False)
            
            # --- 🛡️ MODERATION CATEGORY ---
            mod_list = "`warn`, `warnings`, `delwarn`, `clearwarn`, `mute`, `unmute`, `kick`, `ban`, `unban`, `purge`, `slowmode`, `lock`, `unlock`, `lockdown`, `say`"
            embed.add_field(name="🛡️ Moderation", value=mod_list, inline=False)
            
            # --- 💰 ECONOMY & GAMING (OwO Global Style) ---
            eco_list = "`bal`, `work`, `slut`, `crime`, `rob`, `give`, `coinflip`, `roulette`, `blackjack`, `dep`, `with`"
            embed.add_field(name="💰 Economy & Gaming", value=eco_list, inline=False)
            
            # --- ⚙️ UTILITY CATEGORY ---
            util_list = "`serverinfo`, `botinfo`, `invite`"
            embed.add_field(name="⚙️ Utility", value=util_list, inline=False)
            
            # --- ✨ GENERAL CATEGORY ---
            general_list = "`afk`"
            embed.add_field(name="✨ General", value=general_list, inline=False)

            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
            return await ctx.send(embed=embed)

        # ---- CASE 2: Agar user ne !help <command> likha hai ----
        cmd = self.bot.get_command(command_name.lower())

        if not cmd:
            return await ctx.send(f"❌ Mujhe `{command_name}` naam ka koi command nahi mila!")

        # 🔒 STRICT SECURITY CHECK: Owner commands par strict pehra
        if cmd.name in ["servers", "setstatus", "add-money", "reset-money"] and not await self.bot.is_owner(ctx.author):
            return await ctx.send("❌ Aapke paas is command ki details dekhne ki permission nahi hai!")

        description = "Koi description nahi di gayi."
        usage = f"`{prefix}{cmd.name}`"
        aliases = ", ".join([f"`{a}`" for a in cmd.aliases]) if cmd.aliases else "Koi alias nahi hai."
        examples = f"`{prefix}{cmd.name}`"
        
        # Category Mapping
        cog_name = cmd.cog.__class__.__name__.lower() if cmd.cog else ""
        
        if cmd.name in ["servers", "setstatus", "add-money", "reset-money"]:
            category = "Owner Only"
        elif cmd.name in ["warn", "warnings", "delwarn", "clearwarn", "mute", "unmute", "kick", "ban", "unban", "purge", "slowmode", "lock", "unlock", "lockdown", "say"]:
            category = "Moderation"
        elif "eco" in cog_name or cmd.name in ["balance", "bal", "money", "work", "job", "slut", "crime", "rob", "steal", "give", "share", "pay", "coinflip", "cf", "roulette", "rt", "blackjack", "bj", "deposit", "dep", "withdraw", "with"]:
            category = "Economy & Gaming"
        elif cmd.name in ["serverinfo", "botinfo", "invite"]:
            category = "Utility"
        else:
            category = "General"

        # Commands ki custom details
        if cmd.name == "setstatus":
            description = "Bot ka status aur activity badalne ke liye."
            usage = f"**Basic:** `{prefix}setstatus <status>`\n**Advanced:** `{prefix}setstatus <status> <playing/watching/listening> <text>`"
            examples = f"`{prefix}setstatus dnd`\n`{prefix}setstatus online watching anime`"
        elif cmd.name == "add-money":
            description = "Globally kisi bhi user ke wallet me coins add karne ke liye (Owner Command)."
            usage = f"`{prefix}add-money @user/ID <amount>`"
            examples = f"`{prefix}add-money @Rishav 50000`\n`{prefix}add-money 727718500663033897 100000`"
        elif cmd.name == "reset-money":
            description = "Globally kisi bhi user ka bank aur wallet balance completely zero karne ke liye (Owner Command)."
            usage = f"`{prefix}reset-money @user/ID`"
            examples = f"`{prefix}reset-money @User`"
        elif cmd.name == "warn":
            description = "Kisi member ko officially warn karne ke liye aur unke DM me message bhejne ke liye."
            usage = f"`{prefix}warn @user <reason>`"
            examples = f"`{prefix}warn @User Playing Odd Songs`"
        elif cmd.name == "warnings":
            description = "Kisi member ki purani saari warnings ki list dekhne ke liye."
            usage = f"`{prefix}warnings @user`"
            examples = f"`{prefix}warnings @User`"
        elif cmd.name == "delwarn":
            description = "Kisi user ki koi ek specific warning number delete karne ke liye."
            usage = f"`{prefix}delwarn @user <warning_number>`"
            examples = f"`{prefix}delwarn @User 1` -> Pehli warning delete karega."
        elif cmd.name == "clearwarn":
            description = "Kisi member ki saari warnings ek baar me poori tarah saaf karne ke liye."
            usage = f"`{prefix}clearwarn @user`"
            examples = f"`{prefix}clearwarn @User`"
        elif cmd.name == "mute":
            description = "Kisi member ko specific samay (seconds, minutes, hours, days) ke liye timeout (mute) karne ke liye."
            usage = f"`{prefix}mute @user <duration><s/m/h/d> <reason>`"
            examples = f"`{prefix}mute @User 10m Abusing` -> 10 minutes ke liye."
        elif cmd.name == "unmute":
            description = "Kisi member ka timeout samay se pehle hatane ke liye."
            usage = f"`{prefix}unmute @user <reason>`"
            examples = f"`{prefix}unmute @User Galti se mute hua`"
        elif cmd.name == "invite":
            description = "Bot ko apne khud ke kisi server me add karne ke liye official invite link nikalne ke liye."
            usage = f"`{prefix}invite`"
            examples = f"`{prefix}invite`"
        elif cmd.name == "serverinfo":
            description = "Jis server me aap hain uski poori details (Owner, Staff Roles aur Member counts) dekhne ke liye."
            usage = f"`{prefix}serverinfo`"
            examples = f"`{prefix}serverinfo`"
        elif cmd.name == "botinfo":
            description = "Bot ki live statistics (Total servers, monitored members aur tech specs) dekhne ke liye."
            usage = f"`{prefix}botinfo`"
            examples = f"`{prefix}botinfo`"
        elif cmd.name == "afk":
            description = "Aapko AFK status par dalne ke liye taaki jab koi aapko ping kare toh bot use reason bataye."
            usage = f"`{prefix}afk <reason>`"
            examples = f"`{prefix}afk Khana kha raha hu`"
        elif cmd.name == "purge":
            description = "Chat se normal messages, sirf bots ke messages, ya kisi specific user ke messages filter karke delete karne ke liye."
            usage = f"`{prefix}purge <amount>`\n`{prefix}purge bots <amount>`\n`{prefix}purge @user <amount>`"
            examples = f"`{prefix}purge 20` -> 20 normal msgs."
        elif cmd.name == "kick":
            description = "Kisi member ko server ke rules todne par server se bahar nikalne ke liye."
            usage = f"`{prefix}kick @user <reason>`"
            examples = f"`{prefix}kick @User Misbehave`"
        elif cmd.name == "ban":
            description = "Kisi member ko server se permanent ban karne ke liye."
            usage = f"`{prefix}ban @user <reason>`"
            examples = f"`{prefix}ban @User Scam Link Sharing`"
        elif cmd.name == "unban":
            description = "Kisi banned user ka ban hatakar use server me wapas aane ki permission dene ke liye."
            usage = f"`{prefix}unban <User_ID>`"
            examples = f"`{prefix}unban 727718500663033897`"
        elif cmd.name == "servers":
            description = "Sirf Bot Creator ke liye! Bot jin-jin servers me add hai, unki poori list aur owner ka naam dekhne ke liye."
            usage = f"`{prefix}servers`"
            examples = f"`{prefix}servers`"
        elif cmd.name == "slowmode":
            description = "Channel cooldown rate set karne ke liye taaki log ruk kar chat karein."
            usage = f"`{prefix}slowmode <seconds>`"
            examples = f"`{prefix}slowmode 10` -> 10s cooldown."
        elif cmd.name == "lock":
            description = "Channel ko explicit timer aur reason ke saath lock karne ke liye."
            usage = f"`{prefix}lock [#channel] [time] [reason]`"
            examples = f"`{prefix}lock #general 30m Spamming!`"
        elif cmd.name == "unlock":
            description = "Kisi locked channel ko wapas open karne ke liye."
            usage = f"`{prefix}unlock [#channel]`"
            examples = f"`{prefix}unlock #general`"
        elif cmd.name == "lockdown":
            description = "🚨 EMERGENCY COMMAND: Poore server ke saare text channels ko ek baar me lock/unlock karne ke liye."
            usage = f"`{prefix}lockdown` -> Lockdown chalu.\n`{prefix}lockdown off` -> Lockdown hatane ke liye."
            examples = f"`{prefix}lockdown`\n`{prefix}lockdown off`"
        elif cmd.name == "say":
            description = "📢 Bot ke zariye chat me apni marzi ka message bhejne ya kisi user ko target karke ping karwane ke liye."
            usage = f"`{prefix}say <message>`\n`{prefix}say @user <message>`"
            examples = f"`{prefix}say Hello Rishav~`"
        elif cmd.name in ["balance", "bal"]:
            description = "Aapka ya kisi dusre member ka cash wallet aur bank balance check karne ke liye."
            usage = f"`{prefix}bal`\n`{prefix}bal @user`"
            examples = f"`{prefix}bal`\n`{prefix}bal @Rishav`"
        elif cmd.name == "work":
            description = "Mehnat ka kaam karke bina kisi risk ke safe coins kamane ke liye. (Cooldown: 30s Countdown)"
            usage = f"`{prefix}work`"
            examples = f"`{prefix}work`"
        elif cmd.name == "slut":
            description = "Risky tareeqon se paise kamane ke liye! Jeetne ka chance zyada hai par harne par fine lagega. (Cooldown: 30s Countdown)"
            usage = f"`{prefix}slut`"
            examples = f"`{prefix}slut`"
        elif cmd.name == "crime":
            description = "High-risk, High-reward illegal kaam! Jeetne par mota paisa, pakde jaane par bhaari fine. (Cooldown: 30s Countdown)"
            usage = f"`{prefix}crime`"
            examples = f"`{prefix}crime`"
        elif cmd.name == "rob":
            description = "Kisi doosre user ke wallet (cash) se chori karne ke liye. Target ke paas jitna zyada cash hoga, fail hone ka chance utna hi badhega! (Cooldown: 30s Countdown)"
            usage = f"`{prefix}rob @user`"
            examples = f"`{prefix}rob @Rishav`"
        elif cmd.name == "give":
            description = "Apne wallet se kisi doosre user ko coins transfer karne ke liye."
            usage = f"`{prefix}give @user <amount/all/half>`"
            examples = f"`{prefix}give @Rishav 5000`\n`{prefix}give @User all`"
        elif cmd.name in ["coinflip", "cf"]:
            description = "Heads ya Tails par jua khelne ke liye! Sahi andaze par lagaya hua paisa direct double."
            usage = f"`{prefix}coinflip <amount/all/half> <heads/tails>`"
            examples = f"`{prefix}coinflip 1000 heads`\n`{prefix}coinflip all tails`"
        elif cmd.name in ["roulette", "rt"]:
            description = "Casino Roulette game! Red/Black par lagane se 2x aur Green (0) par lagane se seedhe 14x cash multiplier milega!"
            usage = f"`{prefix}roulette <amount/all/half> <red/black/green>`"
            examples = f"`{prefix}roulette 500 red`\n`{prefix}roulette half green`"
        elif cmd.name in ["blackjack", "bj"]:
            description = "Real interactive buttons (Hit/Stand) wala genuine Blackjack card game!"
            usage = f"`{prefix}blackjack <amount/all/half>`"
            examples = f"`{prefix}blackjack 2000`\n`{prefix}blackjack all`"
        elif cmd.name in ["deposit", "dep"]:
            description = "Wallet se cash nikal kar safe bank me deposit karne ke liye taaki koi rob na kar paye."
            usage = f"`{prefix}dep <amount/all/half>`"
            examples = f"`{prefix}dep 2000`\n`{prefix}dep all`"
        elif cmd.name in ["withdraw", "with"]:
            description = "Bank account se paise nikal kar wapas cash wallet me lane ke liye."
            usage = f"`{prefix}with <amount/all/half>`"
            examples = f"`{prefix}with 5000`\n`{prefix}with half`"

        cmd_embed = discord.Embed(title=f"ℹ️ Command Detail: {cmd.name.upper()}", color=discord.Color.green())
        cmd_embed.add_field(name="📝 Description", value=description, inline=False)
        cmd_embed.add_field(name="⌨️ Usage", value=usage, inline=False)
        cmd_embed.add_field(name="💡 Examples", value=examples, inline=False)
        cmd_embed.add_field(name="🔀 Aliases (Shortforms)", value=aliases, inline=False)
        cmd_embed.add_field(name="📁 Category", value=category, inline=True)

        await ctx.send(embed=cmd_embed)

async def setup(bot):
    await bot.add_cog(Help(bot))