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

        # ---- CASE 1: Agar user ne sirf !help likha hai ----
        if not command_name:
            embed = discord.Embed(
                title=f"🤖 {self.bot.user.name} Help Menu",
                description=f"Mera prefix **`{prefix}`** hai. Kisi command ki detail dekhne ke liye `{prefix}help <command>` likhein.",
                color=discord.Color.blue()
            )
            
            owner_cmds = []
            mod_cmds = []
            utility_cmds = []  # Naya list utility ke liye
            general_cmds = []

            for cmd in self.bot.commands:
                if cmd.hidden and not await self.bot.is_owner(ctx.author):
                    continue
                
                if "owner" in cmd.cog_name.lower():
                    if await self.bot.is_owner(ctx.author):
                        owner_cmds.append(f"`{cmd.name}`")
                elif "mod" in cmd.cog_name.lower():
                    mod_cmds.append(f"`{cmd.name}`")
                elif "util" in cmd.cog_name.lower():  # Utility commands check
                    utility_cmds.append(f"`{cmd.name}`")
                else:
                    if not cmd.hidden:
                        general_cmds.append(f"`{cmd.name}`")

            if owner_cmds:
                embed.add_field(name="👑 Owner Only", value=", ".join(owner_cmds), inline=False)
            if mod_cmds:
                embed.add_field(name="🛡️ Moderation", value=", ".join(mod_cmds), inline=False)
            if utility_cmds:  # Utility category embed me jodi
                embed.add_field(name="⚙️ Utility", value=", ".join(utility_cmds), inline=False)
            if general_cmds:
                embed.add_field(name="⚙️ General", value=", ".join(general_cmds), inline=False)

            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
            return await ctx.send(embed=embed)

        # ---- CASE 2: Agar user ne !help <command> likha hai ----
        cmd = self.bot.get_command(command_name.lower())

        if not cmd:
            return await ctx.send(f"❌ Mujhe `{command_name}` naam ka koi command nahi mila!")

        if "owner" in cmd.cog_name.lower() and not await self.bot.is_owner(ctx.author):
            return await ctx.send("❌ Aapke paas is command ki details dekhne ki permission nahi hai!")

        description = "Koi description nahi di gayi."
        usage = f"`{prefix}{cmd.name}`"
        aliases = ", ".join([f"`{a}`" for a in cmd.aliases]) if cmd.aliases else "Koi alias nahi hai."
        
        # Category check up-to-date kiya
        category = "Moderation" if "mod" in cmd.cog_name.lower() else ("Owner Only" if "owner" in cmd.cog_name.lower() else ("Utility" if "util" in cmd.cog_name.lower() else "General"))

        # Commands ki custom details
        if cmd.name == "setstatus":
            description = "Bot ka status aur activity badalne ke liye."
            usage = f"**Basic:** `{prefix}setstatus <status>`\n**Advanced:** `{prefix}setstatus <status> <playing/watching/listening> <text>`"
            examples = f"`{prefix}setstatus dnd`\n`{prefix}setstatus online watching anime`"
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
            examples = f"`{prefix}mute @User 5s Spam` -> 5 seconds ke liye.\n`{prefix}mute @User 10m Abusing` -> 10 minutes ke liye.\n`{prefix}mute @User 1d Bad Words` -> 1 din ke liye."
        elif cmd.name == "unmute":
            description = "Kisi member ka timeout samay se pehle hatane ke liye."
            usage = f"`{prefix}unmute @user <reason>`"
            examples = f"`{prefix}unmute @User Galti se mute hua`"
        elif cmd.name == "invite":
            description = "Bot ko apne khud ke kisi server me add karne ke liye official invite link nikalne ke liye."
            usage = f"`{prefix}invite`"
            examples = f"`{prefix}invite` ya `{prefix}inv`"
        elif cmd.name == "serverinfo":
            description = "Jis server me aap hain uski poori details (Owner, Staff Roles aur Member counts) dekhne ke liye."
            usage = f"`{prefix}serverinfo`"
            examples = f"`{prefix}serverinfo` ya `{prefix}si`"
        elif cmd.name == "botinfo":
            description = "Bot ki live statistics (Total servers, monitored members aur tech specs) dekhne ke liye."
            usage = f"`{prefix}botinfo`"
            examples = f"`{prefix}botinfo` ya `{prefix}bi`"
        elif cmd.name == "afk":
            description = "Aapko AFK status par dalne ke liye taaki jab koi aapko ping kare toh bot use reason bataye."
            usage = f"`{prefix}afk <reason>`"
            examples = f"`{prefix}afk Khana kha raha hu`\n`{prefix}afk` -> Default reason ke sath."
        elif cmd.name == "purge":
            description = "Chat se normal messages, sirf bots ke messages, ya kisi specific user ke messages filter karke delete karne ke liye."
            usage = f"`{prefix}purge <amount>`\n`{prefix}purge bots <amount>`\n`{prefix}purge @user <amount>`"
            examples = f"`{prefix}purge 20` -> Pichle 20 normal messages hatayega.\n`{prefix}purge bots 50` -> Last 50 me se sirf bots ke messages udayega.\n`{prefix}purge @User 30` -> Last 30 me se sirf us user ke messages saaf karega."
        elif cmd.name == "kick":
            description = "Kisi member ko server ke rules todne par server se bahar nikalne ke liye (Banda wapas aa sakta hai)."
            usage = f"`{prefix}kick @user <reason>`"
            examples = f"`{prefix}kick @User Misbehave`"
        elif cmd.name == "ban":
            description = "Kisi member ko server se permanent ban karne ke liye (Banda bina unban hue wapas nahi aa payega)."
            usage = f"`{prefix}ban @user <reason>`"
            examples = f"`{prefix}ban @User Scam Link Sharing`"
        elif cmd.name == "unban":
            description = "Kisi banned user ka ban hatakar use server me wapas aane ki permission dene ke liye."
            usage = f"`{prefix}unban <User_ID_ya_Username>`"
            examples = f"`{prefix}unban 727718500663033897`\n`{prefix}unban monster119988`"
        elif cmd.name == "servers":
            description = "Sirf Bot Creator ke liye! Bot jin-jin servers me add hai, unki poori list aur owner ka naam dekhne ke liye."
            usage = f"`{prefix}servers`"
            examples = f"`{prefix}servers` ya `{prefix}guilds`"
        elif cmd.name == "slowmode":
            description = "Channel cooldown rate set karne ke liye."
            usage = f"`{prefix}slowmode <seconds>`"
            examples = f"`{prefix}slowmode 10`"
        elif cmd.name == "lock":
            description = "Channel ko explicit timer aur reason ke saath lock karne ke liye."
            usage = f"`{prefix}lock [#channel] [time] [reason]`"
            examples = f"`{prefix}lock #general 30m Spamming!`\n`{prefix}lock` -> Current channel ko hamesha ke liye lock karega."
        elif cmd.name == "unlock":
            description = "Kisi locked channel ko wapas open karne ke liye."
            usage = f"`{prefix}unlock [#channel]`"
            examples = f"`{prefix}unlock #general`"
        elif cmd.name == "lockdown":
            description = "🚨 EMERGENCY COMMAND: Poore server ke saare text channels ko ek baar me lock/unlock karne ke liye."
            usage = f"`{prefix}lockdown` -> Lockdown chalu karne ke liye.\n`{prefix}lockdown off` -> Lockdown hatane ke liye."
            examples = f"`{prefix}lockdown`\n`{prefix}lockdown off`"

        cmd_embed = discord.Embed(title=f"ℹ️ Command Detail: {cmd.name.upper()}", color=discord.Color.green())
        cmd_embed.add_field(name="📝 Description", value=description, inline=False)
        cmd_embed.add_field(name="⌨️ Usage", value=usage, inline=False)
        
        if cmd.name in ["setstatus", "warn", "warnings", "delwarn", "clearwarn", "mute", "unmute", "invite", "serverinfo", "botinfo", "afk", "purge", "kick", "ban", "unban"]:
            cmd_embed.add_field(name="💡 Examples", value=examples, inline=False)
            
        cmd_embed.add_field(name="🔀 Aliases (Shortforms)", value=aliases, inline=False)
        cmd_embed.add_field(name="📁 Category", value=category, inline=True)

        await ctx.send(embed=cmd_embed)

async def setup(bot):
    await bot.add_cog(Help(bot))