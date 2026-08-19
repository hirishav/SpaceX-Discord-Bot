# cogs/help.py
import discord
from discord.ext import commands

try:
    import config
except ImportError:
    config = None

# ─────────────────────────────────────────────────────────────
# 🎨 THEME
# ─────────────────────────────────────────────────────────────
EMBED_COLOR = discord.Color(0x2b2d31)  # Discord invisible dark — sleek & modern
BOT_INVITE_URL = "https://discord.com/oauth2/authorize?client_id=1505527456155570196&permissions=7707175400501110&integration_type=0&scope=bot+applications.commands"


def _cfg(name: str, default: str = "") -> str:
    """Config.py se safely value nikalta hai, warna default deta hai."""
    return getattr(config, name, default) if config else default


# ─────────────────────────────────────────────────────────────
# 📂 CATEGORY DEFINITIONS
# Category ka pata cog ke class-name prefix se dynamically chalta hai,
# isliye naya cog add karne par bas iski file "Mod_/Eco_/Fun_/Gen_/Owner_"
# naming convention follow kare toh help menu apne aap update ho jaata hai.
# ─────────────────────────────────────────────────────────────
CATEGORY_ORDER = ["moderation", "economy", "fun", "utility", "general", "owner"]

CATEGORY_META = {
    "moderation": {
        "emoji": "🛠️",
        "label": "Moderation",
        "aliases": ["mod", "mods", "moderation", "modding"],
        "blurb": "Server ko control aur safe rakhne ke liye saare moderation tools.",
    },
    "economy": {
        "emoji": "💰",
        "label": "Economy & Gaming",
        "aliases": ["eco", "economy", "gaming", "casino", "money", "stocks", "stock"],
        "blurb": "Wallet, casino games aur live stock market — sab kuch ek jagah.",
    },
    "fun": {
        "emoji": "🎮",
        "label": "Fun & Comedy",
        "aliases": ["fun", "comedy", "meme", "memes"],
        "blurb": "Masti-mazak aur entertainment ke liye commands.",
    },
    "utility": {
        "emoji": "🧰",
        "label": "Utility",
        "aliases": ["util", "utils", "utility", "tools", "info"],
        "blurb": "Bot, server aur account se juri useful jaankari.",
    },
    "general": {
        "emoji": "✨",
        "label": "General",
        "aliases": ["gen", "general", "core", "misc"],
        "blurb": "Roz kaam aane wale general-purpose commands.",
    },
    "owner": {
        "emoji": "👑",
        "label": "Owner Only",
        "aliases": ["owner", "admin", "dev", "creator"],
        "blurb": "Sirf bot creator ke liye — restricted control system.",
    },
}


def resolve_category(cmd: commands.Command) -> str:
    """Kisi bhi command ka category key nikalta hai — cog class-name prefix ke basis par."""
    cog_name = cmd.cog.__class__.__name__ if cmd.cog else ""

    # ownerinfo is PUBLIC info about the bot creator, not an owner-locked command —
    # its cog just happens to be named "OwnerInfo".
    if cog_name == "OwnerInfo":
        return "utility"

    # Hidden / owner-locked commands hamesha Owner category me jaayenge,
    # chahe unka cog file kisi bhi naam se shuru hota ho (e.g. mod_blacklist.py).
    if cmd.hidden or cog_name.startswith("Owner") or cmd.name in {"blacklist"}:
        return "owner"
    if cog_name.startswith("Mod"):
        return "moderation"
    if cog_name.startswith("Eco") or cog_name.startswith("Stocks"):
        return "economy"
    if cog_name.startswith("Fun"):
        return "fun"
    if cog_name.startswith("Gen"):
        return "general"
    return "utility"  # BotInfo, Invite, ServerInfo, OwnerInfo (public), UtilAvatar, etc.


def get_commands_by_category(bot: commands.Bot, category_key: str):
    seen = set()
    result = []
    for cmd in bot.commands:
        if cmd.name == "help" or cmd.name in seen:
            continue
        if resolve_category(cmd) != category_key:
            continue
        seen.add(cmd.name)
        result.append(cmd)
    result.sort(key=lambda c: c.name)
    return result


def chunk_command_lines(cmds, prefix, limit: int = 950):
    """Command list ko Discord ke 1024-char field limit ke andar multiple chunks me todta hai."""
    lines = []
    for cmd in cmds:
        raw_desc = (cmd.help or "No description provided.").strip().split("\n")[0]
        if len(raw_desc) > 55:
            raw_desc = raw_desc[:52] + "..."
        lines.append(f"**` {prefix}{cmd.name} `** ╰ {raw_desc}")

    chunks, current = [], ""
    for line in lines:
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) > limit:
            chunks.append(current)
            current = line
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks or ["> *Is category me abhi koi command nahi hai.*"]


# ─────────────────────────────────────────────────────────────
# 🖱️ INTERACTIVE COMPONENTS
# ─────────────────────────────────────────────────────────────
class CategorySelect(discord.ui.Select):
    def __init__(self, cog: "Help", ctx: commands.Context, is_owner: bool, current: str = "home"):
        options = [
            discord.SelectOption(
                label="Home",
                description="Main menu par wapas jao",
                emoji="🏠",
                value="home",
                default=(current == "home"),
            )
        ]
        for key in CATEGORY_ORDER:
            if key == "owner" and not is_owner:
                continue
            meta = CATEGORY_META[key]
            options.append(
                discord.SelectOption(
                    label=meta["label"],
                    description=meta["blurb"][:95],
                    emoji=meta["emoji"],
                    value=key,
                    default=(current == key),
                )
            )
        super().__init__(
            placeholder="📂 Ek category chuno...",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )
        self.cog = cog
        self.ctx = ctx
        self.is_owner = is_owner

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message(
                "❌ Ye help menu tumhare liye nahi hai! Apna khud ka help command chalao.",
                ephemeral=True,
            )

        value = self.values[0]
        if value == "owner" and not self.is_owner:
            return await interaction.response.send_message(
                "❌ Ye category sirf bot owner ke liye hai!", ephemeral=True
            )

        if value == "home":
            embed = self.cog.build_home_embed(self.ctx, self.is_owner)
        else:
            embed = self.cog.build_category_embed(self.ctx, value)

        view = HelpView(self.cog, self.ctx, self.is_owner, current=value)
        view.message = interaction.message
        await interaction.response.edit_message(embed=embed, view=view)


class HelpView(discord.ui.View):
    def __init__(self, cog: "Help", ctx: commands.Context, is_owner: bool, current: str = "home", timeout: int = 150):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.message = None

        self.add_item(CategorySelect(cog, ctx, is_owner, current=current))

        # 🔗 Quick-access link buttons — footers can't hold clickable links on Discord,
        # so these live here instead (this is the "premium footer" replacement).
        vote_url = _cfg("TOPGG_VOTE_URL") or f"https://top.gg/bot/{ctx.bot.user.id}/vote"
        self.add_item(
            discord.ui.Button(label="Vote on Top.gg", emoji="🚀", url=vote_url, style=discord.ButtonStyle.link, row=1)
        )
        self.add_item(
            discord.ui.Button(label="Invite Bot", emoji="✨", url=BOT_INVITE_URL, style=discord.ButtonStyle.link, row=1)
        )
        support_url = _cfg("SUPPORT_SERVER_URL") or f"https://discord.gg/xgHkpePc9J"
        if support_url and support_url.startswith("http"):
            self.add_item(
                discord.ui.Button(label="Support Server", emoji="🛠️", url=support_url, style=discord.ButtonStyle.link, row=1)
            )

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


# ─────────────────────────────────────────────────────────────
# 📖 HELP COG
# ─────────────────────────────────────────────────────────────
class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------- EMBED BUILDERS ----------
    def build_home_embed(self, ctx: commands.Context, is_owner: bool) -> discord.Embed:
        prefix = ctx.prefix
        bot = self.bot
        total_cmds = len({c.name for c in bot.commands if c.name != "help"})

        embed = discord.Embed(
            title=f"✦ {bot.user.name} Command Center ✦",
            description=(
                f"Swagat hai **{ctx.author.display_name}** bhai! Main hoon **{bot.user.name}**, tera all-in-one assistant.\n\n"
                f"**Kaise use karein:**\n"
                f"> 📂 Niche diye gaye menu se ek module select karo.\n"
                f"> 🔍 Ya fir kisi command ke baare me janne ke liye `{prefix}help <command>` likho.\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=EMBED_COLOR,
        )
        embed.set_thumbnail(url=bot.user.display_avatar.url)

        for key in CATEGORY_ORDER:
            if key == "owner" and not is_owner:
                continue
            cmds = get_commands_by_category(bot, key)
            if not cmds:
                continue
            meta = CATEGORY_META[key]
            
            preview = " • ".join(f"`{c.name}`" for c in cmds[:5])
            if len(cmds) > 5:
                preview += f" *(+{len(cmds) - 5} more)*"
                
            embed.add_field(
                name=f"{meta['emoji']} **{meta['label']}**",
                value=f"> {preview}\n",
                inline=False,
            )

        embed.set_footer(
            text=f"Modules Loaded: {len(CATEGORY_ORDER)}  |  Total Commands: {total_cmds}",
            icon_url=ctx.author.display_avatar.url,
        )
        return embed

    def build_category_embed(self, ctx: commands.Context, key: str) -> discord.Embed:
        meta = CATEGORY_META[key]
        cmds = get_commands_by_category(self.bot, key)

        embed = discord.Embed(
            title=f"{meta['emoji']} {meta['label']} Module",
            description=(
                f"> {meta['blurb']}\n\n"
                f"💡 *Tip: Use `{ctx.prefix}help <command>` for detailed usage.*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=EMBED_COLOR,
        )
        for i, chunk in enumerate(chunk_command_lines(cmds, ctx.prefix)):
            embed.add_field(name=" " if i == 0 else "\u200b", value=chunk, inline=False)

        embed.set_footer(
            text=f"Module Commands: {len(cmds)}  |  Requested by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url,
        )
        return embed

    # ---------- MAIN COMMAND ----------
    @commands.hybrid_command(name="help", aliases=["h", "commands"])
    async def help_command(self, ctx, *, query: str = None):
        """Bot ke saare commands ki list aur kisi specific command ki details."""

        prefix = ctx.prefix
        is_owner = await self.bot.is_owner(ctx.author)

        # ---- CASE 1: !!help ----
        if not query:
            embed = self.build_home_embed(ctx, is_owner)
            view = HelpView(self, ctx, is_owner, current="home")
            msg = await ctx.send(embed=embed, view=view)
            view.message = msg
            return

        target = query.lower().strip()

        # ---- CASE 2: !!help <category> ----
        matched_key = None
        for key, meta in CATEGORY_META.items():
            if target in meta["aliases"]:
                matched_key = key
                break

        if matched_key:
            if matched_key == "owner" and not is_owner:
                return await ctx.send("❌ Ye category sirf bot owner ke liye hai!")
            embed = self.build_category_embed(ctx, matched_key)
            view = HelpView(self, ctx, is_owner, current=matched_key)
            msg = await ctx.send(embed=embed, view=view)
            view.message = msg
            return

        # ---- CASE 3: !!help <command> ----
        cmd = self.bot.get_command(target)

        if not cmd:
            return await ctx.send(f"❌ Mujhe `{query}` naam ka koi command ya category nahi mila!")

        cmd_category = resolve_category(cmd)
        if cmd_category == "owner" and not is_owner:
            return await ctx.send("❌ Aapke paas is command ki details dekhne ki permission nahi hai!")

        # Raw declarations parameters template
        description = "Koi description nahi di gayi."
        usage = f"`{prefix}{cmd.name}`"
        aliases = ", ".join([f"`{a}`" for a in cmd.aliases]) if cmd.aliases else "Koi alias nahi hai."
        examples = f"`{prefix}{cmd.name}`"
        category = CATEGORY_META[cmd_category]["label"]

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
            description = "🚨 Global/Server Bot Locking Engine! Pure bot ya specific server me commands block karne ke liye (Owner Only)."
            usage = f"`{prefix}maintenance <duration> [server_id/name]`\n👉 Unlock karne ke liye duration `off` daalein."
            examples = f"`{prefix}maintenance 1h`\n`{prefix}maintenance 2h 1234567890`"

        elif cmd.name in ["restorebackup", "loadbackup"]:
            description = "🔄 Cloud se manually backup load karke live database update karne ke liye bina bot restart kiye (Owner Only)."
            usage = f"`{prefix}restorebackup`"
            examples = f"`{prefix}restorebackup`"

        elif cmd.name == "badge":
            description = "🏅 Kisi user ke profile me custom badge add karne ke liye (Owner Only)."
            usage = f"`{prefix}badge @user <badge_text_or_emoji>`"
            examples = f"`{prefix}badge @User 💎 VIP`"

        elif cmd.name == "removebadge":
            description = "🚫 Kisi user ke profile se custom badge hatane ke liye (Owner Only)."
            usage = f"`{prefix}removebadge @user <badge_text_or_emoji>`"
            examples = f"`{prefix}removebadge @User 💎 VIP`"

        elif cmd.name == "cleanspace":
            description = "🧹 Un sabhi servers se bot ko nikalne ke liye jinme members kam hain (Owner Only)."
            usage = f"`{prefix}cleanspace [min_members]`"
            examples = f"`{prefix}cleanspace 10`"

        elif cmd.name == "blacklistserver":
            description = "🚫 Kisi toxic/raid server ko blacklist karna taaki bot waha se leave ho jaye aur future me join na kare (Owner Only)."
            usage = f"`{prefix}blacklistserver <server_id>`"
            examples = f"`{prefix}blacklistserver 1234567890`"

        elif cmd.name == "whitelistserver":
            description = "✅ Kisi server ko blacklist se hatane ke liye (Owner Only)."
            usage = f"`{prefix}whitelistserver <server_id>`"
            examples = f"`{prefix}whitelistserver 1234567890`"

        elif cmd.name == "sudo":
            description = "👨‍💻 Kisi aur user ke naam se (as them) koi command run karne ke liye (Owner Only)."
            usage = f"`{prefix}sudo @user <command_string>`"
            examples = f"`{prefix}sudo @User bal`"

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

        elif cmd.name == "forceban":
            description = "Kisi user ko uske ID se permanent ban karne ke liye (chahe wo server me na ho)."
            usage = f"`{prefix}forceban <User_ID> [reason]`"
            examples = f"`{prefix}forceban 727718500663033897 Raid`"

        elif cmd.name == "unban":
            description = "Kisi banned user ka ban hatakar use wapas aane dene ke liye."
            usage = f"`{prefix}unban <User_ID>`"
            examples = f"`{prefix}unban 727718500663033897`"

        elif cmd.name == "purge":
            description = "Chat se specific constraints filter lagakar bulk messages saaf karne ke liye advanced toolkit."
            usage = (
                f"`{prefix}purge <amount>`\n"
                f"`{prefix}purge text <amount>`\n"
                f"`{prefix}purge humans <amount>`\n"
                f"`{prefix}purge bots <amount>`\n"
                f"`{prefix}purge user @user <amount>`\n"
                f"`{prefix}purge images <amount>`\n"
                f"`{prefix}purge links <amount>`\n"
                f"`{prefix}purge startswith <word> <amount>`\n"
                f"`{prefix}purge endswith <word> <amount>`\n"
                f"`{prefix}purge match <word> <amount>`"
            )
            examples = f"`{prefix}purge match ball 50`\n`{prefix}purge bots 100`\n`{prefix}purge user @User 20`"

        elif cmd.name == "slowmode":
            description = "Current text channel ka message sending cooldown timer change karne ke liye."
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
            description = "🚨 EMERGENCY: Poore server ke saare text channels ko ek baar me lock ya wapas unlock karne ke liye."
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

        elif cmd.name in ["profile", "userinfo", "pr"]:
            description = "👤 Kisi user ki puri profile (badges, net worth, warnings aur account age) dekhne ke liye."
            usage = f"`{prefix}profile [@user]`"
            examples = f"`{prefix}profile`\n`{prefix}profile @User`"

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
            description = "Kisi doosre user ke wallet se cash churane ke liye."
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
            description = "✅ Advance Interactive Button wala automatic giveaway engine framework toggle karne ke liye."
            usage = f'`{prefix}gstart <time> "<requirements_text>" <@role/none> <prize>`'
            examples = f'`{prefix}gstart 10m "Must have Fans role" @Fans Spotify`'

        elif cmd.name in ["giveawayend", "gend"]:
            description = "🏁 Kisi chal rahe giveaway ko manually turant khatam karke winner announce karne ke liye."
            usage = f"`{prefix}gend <message_id>`"
            examples = f"`{prefix}gend 124357285194729481`"

        elif cmd.name in ["greroll", "reroll"]:
            description = "🔁 Ended giveaway ka naya winner dobara pick karne ke liye."
            usage = f"`{prefix}greroll <message_id>`"
            examples = f"`{prefix}greroll 124357285194729481`"

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
            description = "🛒 Wallet coins ko use karke limited share inventory pool se real assets instantly purchase karne ke liye."
            usage = f"`{prefix}buystock <TICKER> <quantity>`"
            examples = f"`{prefix}buystock NIFTY 5`"

        elif cmd.name == "sellstock":
            description = "💰 Owned portfolio shares ko current live market value pricing par profit/loss ke sath instant wallet cash me swap karne ke liye."
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
            examples = f'`{prefix}addstock COFFEE "Starbucks Capital" 250`'

        elif cmd.name == "setshares":
            description = "👑 Kisi active ticker ke total baseline pool bache hue available inventory shares force-rewrite karne ke liye."
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

        elif cmd.name == "role":
            description = "🛡️ Kisi user ko server me role assign ya unse role remove karne ke liye."
            usage = f"`{prefix}role @user <role>`"
            examples = f"`{prefix}role @User @Mod`"

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

        elif cmd.name == "addprefixless":
            description = "👑 Owner-Only: Server ke kisi trusted member ko bina prefix execution route ke bot use karne ka premium access dene ke liye."
            usage = f"`{prefix}addprefixless @user`"
            examples = f"`{prefix}addprefixless @User`"

        elif cmd.name == "removeprefixless":
            description = "👑 Owner-Only: Kisi member ka bina-prefix access wapas revoke karne ke liye."
            usage = f"`{prefix}removeprefixless @user`"
            examples = f"`{prefix}removeprefixless @User`"

        elif cmd.name == "listprefixless":
            description = "👑 Owner-Only: Un sabhi members ki list dekhne ke liye jinke paas bina-prefix access hai."
            usage = f"`{prefix}listprefixless`"
            examples = f"`{prefix}listprefixless`"

        elif cmd.name in ["addpremium", "apremium"]:
            description = "👑 Owner-Only: Kisi server/user ko premium perks grant karne ke liye."
            usage = f"`{prefix}addpremium <ID>`"
            examples = f"`{prefix}addpremium 727718500663033897`"

        elif cmd.name in ["removepremium", "rpremium"]:
            description = "👑 Owner-Only: Kisi server/user ka premium access revoke karne ke liye."
            usage = f"`{prefix}removepremium <ID>`"
            examples = f"`{prefix}removepremium 727718500663033897`"

        elif cmd.name in ["ownerinfo", "owner"]:
            description = "🚀 Bot creator ke public details aur tech stack dekhne ke liye."
            usage = f"`{prefix}ownerinfo`"
            examples = f"`{prefix}ownerinfo`"

        elif cmd.name in ["vote", "topgg", "support"]:
            description = "🚀 Top.gg par bot ko vote karke support karne ke liye link deta hai."
            usage = f"`{prefix}vote`"
            examples = f"`{prefix}vote`"

        elif cmd.name in ["updatetopgg", "topggupdate", "poststats"]:
            description = "👑 Owner-Only: Top.gg website par direct live server count post karne aur API status verify karne ke liye."
            usage = f"`{prefix}updatetopgg`"
            examples = f"`{prefix}updatetopgg`"

        elif cmd.name == "ping":
            description = "🏓 Bot ki current response latency check karne ke liye."
            usage = f"`{prefix}ping`"
            examples = f"`{prefix}ping`"

        elif cmd.name == "ticket":
            description = "🎫 Server support tickets create aur manage karne ke liye complete system."
            usage = (
                f"`{prefix}ticket auto-setup`\n"
                f"`{prefix}ticket setup #category #logs @SupportRole`\n"
                f"`{prefix}ticket panel`\n"
                f"`{prefix}ticket claim` / `{prefix}ticket unclaim`\n"
                f"`{prefix}ticket add @user` / `{prefix}ticket remove @user`\n"
                f"`{prefix}ticket transfer @user`\n"
                f"`{prefix}ticket rename <name>` / `{prefix}ticket topic <desc>`\n"
                f"`{prefix}ticket close` / `{prefix}ticket force-close`\n"
                f"`{prefix}ticket transcript`"
            )
            examples = f"`{prefix}ticket auto-setup`\n`{prefix}ticket panel`"

        elif cmd.name == "welcome":
            description = "👋 Server me naye members ka custom swagat aur join messages configure karne ke liye."
            usage = f"`{prefix}welcome setchannel #channel`\n`{prefix}welcome setmessage <msg>`\n`{prefix}welcome mention <on/off>`\n`{prefix}welcome test`"
            examples = f"`{prefix}welcome setchannel #welcome`\n`{prefix}welcome setmessage Welcome {{user}} to {{server}}! ✅`"

        elif cmd.name in ["kiss", "hug", "slap", "spank", "tickle"]:
            action = cmd.name
            description = f"🎭 Kisi member ko {action} karne ke liye ek anime reaction GIF ke saath!"
            usage = f"`{prefix}{action} @user`"
            examples = f"`{prefix}{action} @User`"

        elif cmd.name == "rep":
            description = "⭐ Apna ya kisi doosre user ka rep points check karne aur leaderboard dekhne ke liye."
            usage = f"`{prefix}rep [@user]`\n`{prefix}rep lb global`\n`{prefix}rep lb server`"
            examples = f"`{prefix}rep @User`\n`{prefix}rep lb server`"

        elif cmd.name == "addrep":
            description = "👑 Owner-Only: Kisi user ko instantly globally rep points grant karne ke liye."
            usage = f"`{prefix}addrep @user <amount>`"
            examples = f"`{prefix}addrep @User 10`"

        elif cmd.name == "removerep":
            description = "👑 Owner-Only: Kisi user ke rep points hatane ya reset karne ke liye."
            usage = f"`{prefix}removerep @user <amount/all>`"
            examples = f"`{prefix}removerep @User all`"

        elif cmd.name == "disable":
            description = "🚫 Server ya specific channel me kisi command ya poore module (jaise economy, fun) ko band (disable) karne ke liye."
            usage = f"`{prefix}disable module <name> [#channel]`\n`{prefix}disable command <name> [#channel]`"
            examples = f"`{prefix}disable module economy`\n`{prefix}disable command ban #general`"

        elif cmd.name == "enable":
            description = "✅ Kisi disabled command ya module ko wapas chalu (enable) karne ke liye."
            usage = f"`{prefix}enable module <name> [#channel]`\n`{prefix}enable command <name> [#channel]`"
            examples = f"`{prefix}enable module economy`\n`{prefix}enable command ban #general`"

        elif cmd.name == "help":
            description = "📖 Bot ke saare commands ki premium, category-wise list dikhata hai."
            usage = f"`{prefix}help`\n`{prefix}help <category>`\n`{prefix}help <command>`"
            examples = f"`{prefix}help moderation`\n`{prefix}help ban`"

        cmd_embed = discord.Embed(
            title=f"✦ Command: {cmd.name.capitalize()} ✦",
            description=f"> {description}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            color=EMBED_COLOR,
        )
        cmd_embed.add_field(name="⌨️ Usage", value=f"{usage}", inline=False)
        cmd_embed.add_field(name="💡 Example", value=f"{examples}", inline=False)
        cmd_embed.add_field(name="🔀 Aliases", value=aliases, inline=True)
        cmd_embed.add_field(name="📂 Category", value=category, inline=True)
        cmd_embed.set_footer(
            text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url
        )

        view = HelpView(self, ctx, is_owner, current=cmd_category)
        msg = await ctx.send(embed=cmd_embed, view=view)
        view.message = msg


async def setup(bot):
    await bot.add_cog(Help(bot))
