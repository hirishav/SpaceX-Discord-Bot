import re
import time
import datetime
import typing
import discord
from discord.ext import commands
import database as sqlite3

async def send_mod_log(bot, guild, log_type, embed, files=None):
    """
    Helper function to send a log embed to the configured channel for a specific log type.
    Valid log_types: 'mod', 'msg_delete', 'msg_edit'
    """
    try:
        conn = sqlite3.connect("warnings.db")
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id FROM log_channels WHERE server_id = ? AND log_type = ?", (str(guild.id), log_type))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            channel_id = int(row[0])
            channel = guild.get_channel(channel_id)
            if channel:
                kwargs = {'embed': embed}
                if files:
                    kwargs['files'] = files
                await channel.send(**kwargs)
    except Exception as e:
        print(f"Error sending mod log: {e}")

# ==========================================
# UNIFIED DURATION & TIME PARSING UTILITIES
# ==========================================

TIME_REGEX = re.compile(
    r'(\d+)\s*(months?|mo|minutes?|mins?|min|m|seconds?|secs?|sec|s|hours?|hrs?|hr|h|days?|day|d|weeks?|wks?|wk|w|years?|yrs?|yr|y)',
    re.IGNORECASE
)

def parse_time_to_seconds(time_str: str) -> typing.Optional[int]:
    """
    Converts a time/duration string to total seconds.
    Supports:
    - s, sec, secs, second, seconds
    - m, min, mins, minute, minutes
    - h, hr, hrs, hour, hours
    - d, day, days
    - w, wk, wks, week, weeks
    - mo, month, months (30 days)
    - y, yr, yrs, year, years (365 days)
    - permanent, perm, forever, always, unlimited, -1, infinite, infinity -> returns -1
    - raw numbers e.g. "60" -> 60 seconds
    Returns:
    - int seconds (>0)
    - -1 for permanent / unlimited
    - None if invalid format
    """
    if not time_str:
        return None

    s = str(time_str).strip().lower()

    if s in ["permanent", "perm", "-1", "forever", "always", "infinite", "infinity", "unlimited"]:
        return -1

    if s.isdigit():
        return int(s)

    matches = TIME_REGEX.findall(s)
    if not matches:
        return None

    # Verify there are no unrelated stray words
    matched_text = "".join(m[0] + m[1] for m in matches)
    cleaned_original = re.sub(r'[\s,\-_]+', '', s)
    if matched_text.lower() != cleaned_original.lower():
        return None

    total_seconds = 0
    for amount_str, unit in matches:
        amt = int(amount_str)
        u = unit.lower()
        if u in ['s', 'sec', 'secs', 'second', 'seconds']:
            total_seconds += amt
        elif u in ['m', 'min', 'mins', 'minute', 'minutes']:
            total_seconds += amt * 60
        elif u in ['h', 'hr', 'hrs', 'hour', 'hours']:
            total_seconds += amt * 3600
        elif u in ['d', 'day', 'days']:
            total_seconds += amt * 86400
        elif u in ['w', 'wk', 'wks', 'week', 'weeks']:
            total_seconds += amt * 604800
        elif u in ['mo', 'month', 'months']:
            total_seconds += amt * 2592000
        elif u in ['y', 'yr', 'yrs', 'year', 'years']:
            total_seconds += amt * 31536000

    return total_seconds

def parse_duration_to_timestamp(time_str: str) -> typing.Optional[int]:
    """
    Returns future UNIX timestamp in seconds, or -1 for permanent, or None if invalid.
    """
    secs = parse_time_to_seconds(time_str)
    if secs is None:
        return None
    if secs == -1:
        return -1
    return int(time.time()) + secs

def parse_duration_to_timedelta(time_str: str) -> typing.Optional[datetime.timedelta]:
    """
    Returns datetime.timedelta object, or None if invalid or permanent.
    """
    secs = parse_time_to_seconds(time_str)
    if secs is None or secs < 0:
        return None
    return datetime.timedelta(seconds=secs)

def format_duration(seconds: int) -> str:
    """
    Formats seconds into a clean human-readable Hindi/English duration string.
    """
    if seconds == -1:
        return "Permanent ♾️"
    if seconds <= 0:
        return "0 seconds"

    parts = []
    years, rem = divmod(seconds, 31536000)
    months, rem = divmod(rem, 2592000)
    weeks, rem = divmod(rem, 604800)
    days, rem = divmod(rem, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, rem = divmod(rem, 60)
    secs = rem

    if years > 0:
        parts.append(f"{years} {'year' if years == 1 else 'years'}")
    if months > 0:
        parts.append(f"{months} {'month' if months == 1 else 'months'}")
    if weeks > 0:
        parts.append(f"{weeks} {'week' if weeks == 1 else 'weeks'}")
    if days > 0:
        parts.append(f"{days} {'day' if days == 1 else 'days'}")
    if hours > 0:
        parts.append(f"{hours} {'hour' if hours == 1 else 'hours'}")
    if minutes > 0:
        parts.append(f"{minutes} {'min' if minutes == 1 else 'mins'}")
    if secs > 0 and not parts:
        parts.append(f"{secs} {'sec' if secs == 1 else 'secs'}")

    return ", ".join(parts[:2]) if parts else "0 seconds"

# ==========================================
# SMART ROLE & TARGET RESOLUTION UTILITIES
# ==========================================

class SmartRoleConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str) -> discord.Role:
        """
        Custom Role Converter that:
        1. Tries exact match for ID or Mention.
        2. Tries exact match for role name (case-insensitive).
        3. Tries substring match on role names.
        4. Tries cleaned alphanumeric match (handles decorative symbols like [✦Creator✦]).
        5. If multiple roles match, prompts the user via a UI View to select the intended one.
        """
        if not argument or not ctx.guild:
            raise commands.BadArgument("❌ Invalid role argument.")

        arg_clean = argument.strip()

        # 1. Try exact match for ID or Mention
        id_match = re.match(r'^<@&(\d+)>$|^(\d+)$', arg_clean)
        if id_match:
            role_id = int(id_match.group(1) or id_match.group(2))
            role = ctx.guild.get_role(role_id)
            if role:
                return role
            try:
                role = await commands.RoleConverter().convert(ctx, arg_clean)
                return role
            except commands.RoleNotFound:
                pass

        guild_roles = [r for r in ctx.guild.roles if r.id != ctx.guild.id]
        arg_lower = arg_clean.lower()

        # 2. Try exact name match (case-insensitive)
        exact_matches = [r for r in guild_roles if r.name.lower() == arg_lower]
        if exact_matches:
            return exact_matches[0]

        # 3. Try partial/fuzzy match for names (substring)
        matched_roles = [r for r in guild_roles if arg_lower in r.name.lower()]

        # 4. Fallback: alphanumeric cleaned match (e.g. "creator" matching "[✦Creator✦]")
        if not matched_roles:
            clean_query = re.sub(r'[^a-zA-Z0-9]', '', arg_lower)
            if clean_query:
                matched_roles = [
                    r for r in guild_roles 
                    if clean_query in re.sub(r'[^a-zA-Z0-9]', '', r.name.lower())
                ]

        if len(matched_roles) == 0:
            raise commands.BadArgument(f"❌ Role `{argument}` server me nahi mila.")
        
        elif len(matched_roles) == 1:
            return matched_roles[0]
            
        else:
            # 5. Multiple matches, prompt user with Select Menu
            options = []
            for r in matched_roles[:25]: # Max 25 limit for SelectMenu
                options.append(discord.SelectOption(
                    label=r.name[:100], 
                    value=str(r.id), 
                    description=f"ID: {r.id}"
                ))
                
            class RoleSelect(discord.ui.Select):
                def __init__(self):
                    super().__init__(placeholder="Kripya ek role select karein...", min_values=1, max_values=1, options=options)
                    
                async def callback(self, interaction: discord.Interaction):
                    if interaction.user.id != ctx.author.id:
                        return await interaction.response.send_message("❌ Ye action sirf command chalane wale ke liye hai!", ephemeral=True)
                        
                    self.view.selected_role = ctx.guild.get_role(int(self.values[0]))
                    self.view.stop()
                    try:
                        await interaction.message.delete()
                    except Exception:
                        pass
                        
            class RoleSelectView(discord.ui.View):
                def __init__(self):
                    super().__init__(timeout=60)
                    self.selected_role = None
                    self.add_item(RoleSelect())
                    
                async def on_timeout(self):
                    try:
                        await self.message.delete()
                    except Exception:
                        pass
                        
            view = RoleSelectView()
            msg = await ctx.send(
                f"⚠️ **{len(matched_roles)}** roles mile `{argument}` ke naam se. Kripya niche se sahi role select karein:", 
                view=view
            )
            view.message = msg
            
            await view.wait()
            
            if view.selected_role:
                return view.selected_role
            else:
                raise commands.BadArgument("Role selection cancel ho gaya ya time out ho gaya.")

async def resolve_target(ctx: commands.Context, target: typing.Union[discord.Member, discord.Role, str], allow_everyone: bool = True):
    """
    Intelligent target resolver:
    Resolves targets for commands like allow, disallow, resetallow.
    Supports:
    - @everyone / everyone
    - Member (mention, ID, exact username, display name, partial match)
    - Role (mention, ID, exact name, fuzzy substring with UI dropdown if multiple)
    Returns:
    (target_obj, target_id, target_mention, is_everyone, is_role)
    """
    if target is None:
        raise commands.BadArgument("❌ Target missing.")

    if isinstance(target, discord.Role):
        is_everyone = (target.id == ctx.guild.id)
        return target, target.id, "@everyone" if is_everyone else target.mention, is_everyone, True

    if isinstance(target, (discord.Member, discord.User)):
        return target, target.id, target.mention, False, False

    target_str = str(target).strip()

    # 1. Check everyone
    if target_str.lower() in ["everyone", "@everyone"]:
        if allow_everyone:
            return ctx.guild.default_role, ctx.guild.id, "@everyone", True, True
        else:
            raise commands.BadArgument("❌ `@everyone` yaha allowed nahi hai.")

    # 2. Check role mention <@&id>
    role_mention_match = re.match(r'^<@&(\d+)>$', target_str)
    if role_mention_match:
        role = ctx.guild.get_role(int(role_mention_match.group(1)))
        if role:
            return role, role.id, role.mention, (role.id == ctx.guild.id), True

    # 3. Check user mention <@!id> or <@id>
    user_mention_match = re.match(r'^<@!?(\d+)>$', target_str)
    if user_mention_match:
        member = ctx.guild.get_member(int(user_mention_match.group(1)))
        if not member:
            try:
                member = await ctx.guild.fetch_member(int(user_mention_match.group(1)))
            except Exception:
                pass
        if member:
            return member, member.id, member.mention, False, False

    # 4. Check raw numerical ID
    if target_str.isdigit():
        target_id_int = int(target_str)
        role = ctx.guild.get_role(target_id_int)
        if role:
            return role, role.id, role.mention, (role.id == ctx.guild.id), True
        member = ctx.guild.get_member(target_id_int)
        if not member:
            try:
                member = await ctx.guild.fetch_member(target_id_int)
            except Exception:
                pass
        if member:
            return member, member.id, member.mention, False, False

    # 5. Check if it matches a role via SmartRoleConverter (handles fuzzy e.g. "creator" -> "[✦Creator✦]")
    try:
        role = await SmartRoleConverter().convert(ctx, target_str)
        return role, role.id, role.mention, (role.id == ctx.guild.id), True
    except commands.BadArgument:
        pass

    # 6. Check if it matches a member
    try:
        member = await commands.MemberConverter().convert(ctx, target_str)
        return member, member.id, member.mention, False, False
    except commands.BadArgument:
        pass

    # 7. Check partial member match by name or nick
    t_lower = target_str.lower()
    matched_members = [m for m in ctx.guild.members if t_lower in m.display_name.lower() or t_lower in m.name.lower()]
    if len(matched_members) == 1:
        m = matched_members[0]
        return m, m.id, m.mention, False, False

    raise commands.BadArgument(f"❌ Target `{target_str}` na toh koi user hai, na role, aur na hi 'everyone'.")
