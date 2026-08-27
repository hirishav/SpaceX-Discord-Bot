import os
import time
import asyncio
from quart import Quart, request, jsonify, redirect, session, url_for
from quart_cors import cors
import aiohttp
import discord
import database as sqlite3

app = Quart(__name__)
app.config['JSON_SORT_KEYS'] = False
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'spacex-super-secret-key-123')

# Define FRONTEND_URL dynamically (use localhost for testing, Netlify for prod)
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')

# Enable CORS for the frontend server
app = cors(app, allow_origin=[FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"], allow_credentials=True)

# Discord OAuth2 configuration
CLIENT_ID = os.getenv("OAUTH_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:5173/api/auth/callback")
DISCORD_API_ENDPOINT = "https://discord.com/api/v10"

# This will hold a reference to the bot
bot_instance = None

def setup_web_server(bot):
    global bot_instance
    bot_instance = bot

@app.route('/')
async def home():
    return "SpaceX Bot API Is Alive & Running 24/7! 🚀"

# ----------------- TOP.GG WEBHOOK -----------------
@app.route('/topgg_webhook', methods=['POST'])
async def topgg_webhook():
    data = await request.json
    if data and 'user' in data:
        user_id = str(data['user'])
        
        # Connect to database
        db = sqlite3.connect("warnings.db", check_same_thread=False, isolation_level=None)
        cursor = db.cursor()
        cursor.execute("INSERT OR IGNORE INTO reps (user_id, rep_points) VALUES (?, 0)", (user_id,))
        cursor.execute("INSERT OR IGNORE INTO economy (user_id, wallet, bank) VALUES (?, 0, 0)", (user_id,))
        
        # Determine rep points: e.g., 1 point for normal and weekend votes
        rep_amount = 1
        specie_reward = 5000
        
        cursor.execute("UPDATE reps SET rep_points = rep_points + ? WHERE user_id = ?", (rep_amount, user_id))
        cursor.execute("UPDATE economy SET wallet = wallet + ? WHERE user_id = ?", (specie_reward, user_id))
        
        cursor.execute("SELECT rep_points FROM reps WHERE user_id = ?", (user_id,))
        total_rep = cursor.fetchone()[0]
        db.commit()
        db.close()
        
        # Send DM asynchronously
        try:
            user_id_int = int(user_id)
            async def send_dm():
                try:
                    user = bot_instance.get_user(user_id_int) or await bot_instance.fetch_user(user_id_int)
                    if user:
                        embed = discord.Embed(
                            title="✅ Vote ke liye Sukriya! ✅",
                            description=f"Aapke vote ke liye bahut bahut dhanyawad! ❤️\n\nIske inaam mein aapko mila hai **{rep_amount} Rep Point** aur **💠 {specie_reward:,} Specie**! ✨\n**Total Rep Points:** `{total_rep}`\n\nAise hi support karte rahiye aur aur bhi inaam kamate rahiye! 🚀",
                            color=discord.Color.brand_green()
                        )
                        embed.set_footer(text="SpaceX Bot Team")
                        if bot_instance.user.display_avatar:
                            embed.set_thumbnail(url=bot_instance.user.display_avatar.url)
                        await user.send(embed=embed)
                except Exception as e:
                    print(f"Failed to send DM for vote: {e}")

            if bot_instance and bot_instance.loop and bot_instance.is_ready():
                bot_instance.loop.create_task(send_dm())
        except Exception as e:
            print(f"Error preparing DM for vote: {e}")
        
        return jsonify({"status": "success", "user": user_id, "reps_added": rep_amount}), 200
        
    return jsonify({"status": "error", "message": "Invalid payload"}), 400

# ----------------- AUTHENTICATION -----------------
@app.route('/api/auth/login')
async def login():
    if not CLIENT_ID:
        return jsonify({"error": "OAuth2 not configured"}), 500
    
    # Discord OAuth2 URL
    discord_auth_url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
        f"&response_type=code&scope=identify%20guilds"
    )
    return redirect(discord_auth_url)

@app.route('/api/auth/callback')
async def callback():
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "No code provided"}), 400
        
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    async with aiohttp.ClientSession() as aio_session:
        async with aio_session.post(f"{DISCORD_API_ENDPOINT}/oauth2/token", data=data, headers=headers) as resp:
            token_response = await resp.json()
            
            if 'access_token' not in token_response:
                return jsonify({"error": "Failed to get access token", "details": token_response}), 400
                
            session['access_token'] = token_response['access_token']
            session['refresh_token'] = token_response['refresh_token']
            
    # Redirect back to frontend dashboard
    return redirect(f"{FRONTEND_URL}/dashboard")

@app.route('/api/auth/logout')
async def logout():
    session.pop('access_token', None)
    session.pop('refresh_token', None)
    return jsonify({"status": "success"})

# ----------------- API ENDPOINTS -----------------
@app.route('/api/client_id')
async def get_client_id():
    return jsonify({'client_id': CLIENT_ID})

@app.route('/api/commands')
async def get_commands():
    # Fetch all commands that are not hidden and not owner-only
    commands = []
    for cmd in bot_instance.commands:
        if not getattr(cmd, 'hidden', False) and not cmd.cog_name == "Owner":
            commands.append(cmd.name)
    commands.sort()
    return jsonify({'commands': commands})

@app.route('/api/users/@me')
async def get_user():
    token = session.get('access_token')
    if not token:
        return jsonify({"error": "Unauthorized"}), 401
        
    headers = {"Authorization": f"Bearer {token}"}
    async with aiohttp.ClientSession() as aio_session:
        async with aio_session.get(f"{DISCORD_API_ENDPOINT}/users/@me", headers=headers) as resp:
            if resp.status != 200:
                return jsonify({"error": "Failed to fetch user"}), resp.status
            user_data = await resp.json()
            return jsonify(user_data)

@app.route('/api/users/@me/guilds')
async def get_user_guilds():
    token = session.get('access_token')
    if not token:
        return jsonify({"error": "Unauthorized"}), 401
        
    headers = {"Authorization": f"Bearer {token}"}
    async with aiohttp.ClientSession() as aio_session:
        async with aio_session.get(f"{DISCORD_API_ENDPOINT}/users/@me/guilds", headers=headers) as resp:
            if resp.status != 200:
                return jsonify({"error": "Failed to fetch guilds"}), resp.status
            guilds = await resp.json()
            
            # Filter guilds where user has MANAGE_GUILD (0x20) or ADMINISTRATOR (0x8)
            manageable_guilds = []
            for guild in guilds:
                perms = int(guild.get('permissions', 0))
                if (perms & 0x20) == 0x20 or (perms & 0x8) == 0x8:
                    # Check if bot is in this guild
                    bot_in_guild = bot_instance.get_guild(int(guild['id'])) is not None
                    guild['bot_in_guild'] = bot_in_guild
                    manageable_guilds.append(guild)
                    
            return jsonify(manageable_guilds)

async def check_auth_and_permissions(guild_id):
    token = session.get('access_token')
    if not token:
        return jsonify({"error": "Unauthorized"}), 401
        
    headers = {"Authorization": f"Bearer {token}"}
    async with aiohttp.ClientSession() as aio_session:
        async with aio_session.get(f"{DISCORD_API_ENDPOINT}/users/@me/guilds", headers=headers) as resp:
            if resp.status != 200:
                return jsonify({"error": "Failed to fetch user guilds"}), resp.status
            
            user_guilds = await resp.json()
            has_perm = False
            for guild in user_guilds:
                if guild['id'] == str(guild_id):
                    perms = int(guild.get('permissions', 0))
                    if (perms & 0x20) == 0x20 or (perms & 0x8) == 0x8:
                        has_perm = True
                        break
                        
            if not has_perm:
                return jsonify({"error": "Forbidden"}), 403

    guild = bot_instance.get_guild(int(guild_id))
    if not guild:
        return jsonify({"error": "Bot is not in this guild"}), 404
        
    return guild

@app.route('/api/guilds/<guild_id>/config', methods=['GET', 'POST'])
async def guild_config(guild_id):
    auth_result = await check_auth_and_permissions(guild_id)
    if isinstance(auth_result, tuple):
        return auth_result
    guild = auth_result

    if request.method == 'GET':
        prefix = bot_instance.prefix_cache.get(int(guild_id), '!!')
        
        # Fetch disabled modules
        disabled_modules = bot_instance.disabled_modules_server_cache.get(int(guild_id), set())
        
        return jsonify({
            "prefix": prefix,
            "disabled_modules": list(disabled_modules),
            "name": guild.name,
            "icon": guild.icon.url if guild.icon else None
        })
        
    elif request.method == 'POST':
        data = await request.json
        
        if 'prefix' in data:
            new_prefix = str(data['prefix']).strip()
            
            cursor = bot_instance.db.cursor()
            cursor.execute("REPLACE INTO server_prefixes (server_id, prefix) VALUES (?, ?)", (str(guild_id), new_prefix))
            bot_instance.db.commit()
            cursor.close()
            
            # Update cache
            bot_instance.prefix_cache[int(guild_id)] = new_prefix
            
        return jsonify({"status": "success"})


@app.route('/api/guilds/<guild_id>/channels')
async def get_guild_channels(guild_id):
    auth_result = await check_auth_and_permissions(guild_id)
    if isinstance(auth_result, tuple):
        return auth_result
    guild = auth_result
    channels = [{'id': str(c.id), 'name': c.name} for c in guild.text_channels]
    return jsonify({'channels': channels})

@app.route('/api/guilds/<guild_id>/welcome', methods=['GET', 'POST'])
async def manage_welcome(guild_id):
    auth_result = await check_auth_and_permissions(guild_id)
    if isinstance(auth_result, tuple):
        return auth_result
    guild = auth_result
    
    if request.method == 'GET':
        cursor = bot_instance.db.cursor()
        cursor.execute('SELECT channel_id, message, mention, enabled FROM welcome_config WHERE guild_id = ?', (str(guild_id),))
        row = cursor.fetchone()
        if not row:
            return jsonify({'channel_id': '', 'message': 'Welcome {user} to {server}! 🎉', 'mention': 1, 'enabled': 0})
        return jsonify({'channel_id': row[0], 'message': row[1], 'mention': row[2], 'enabled': row[3]})
    else:
        data = await request.json
        enabled = data.get('enabled', 0)
        channel_id = data.get('channel_id', '')
        message = data.get('message', 'Welcome {user} to {server}! 🎉')
        mention = data.get('mention', 1)
        
        cursor = bot_instance.db.cursor()
        cursor.execute("INSERT OR REPLACE INTO welcome_config (guild_id, channel_id, message, mention, enabled) VALUES (?, ?, ?, ?, ?)", (str(guild_id), channel_id, message, mention, enabled))
        bot_instance.db.commit()
        return jsonify({'success': True})

@app.route('/api/guilds/<guild_id>/welcome/test', methods=['POST'])
async def test_welcome(guild_id):
    auth_result = await check_auth_and_permissions(guild_id)
    if isinstance(auth_result, tuple):
        return auth_result
    guild = auth_result
    
    data = await request.json
    channel_id = data.get('channel_id')
    message_content = data.get('message', 'Welcome {user} to {server}!')
    mention = data.get('mention', 1)
    
    if not channel_id:
        return jsonify({'error': 'No channel selected'}), 400
        
    channel = guild.get_channel(int(channel_id))
    if not channel:
        return jsonify({'error': 'Channel not found'}), 404
        
    # Replace placeholders for test
    formatted_message = message_content.replace('{user}', guild.me.mention if mention else guild.me.display_name)\
                                       .replace('{server}', guild.name)\
                                       .replace('{membercount}', str(guild.member_count))
                                       
    try:
        await channel.send(f"**[TEST WELCOME MESSAGE]**\n{formatted_message}")
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/guilds/<guild_id>/moderation', methods=['GET', 'POST'])
async def manage_moderation(guild_id):
    auth_result = await check_auth_and_permissions(guild_id)
    if isinstance(auth_result, tuple):
        return auth_result
    guild = auth_result
    
    if request.method == 'GET':
        disabled_modules = list(bot_instance.disabled_modules_server_cache.get(int(guild_id), set()))
        disabled_commands = list(bot_instance.disabled_commands_cache.get(int(guild_id), set()))
        return jsonify({
            'disabled_modules': disabled_modules,
            'disabled_commands': disabled_commands
        })
    else:
        data = await request.json
        disabled_modules = data.get('disabled_modules', [])
        disabled_commands = data.get('disabled_commands', [])
        
        cursor = bot_instance.db.cursor()
        
        # Modules
        cursor.execute('DELETE FROM disabled_modules_server WHERE server_id = ?', (str(guild_id),))
        bot_instance.disabled_modules_server_cache[int(guild_id)] = set()
        for mod in disabled_modules:
            cursor.execute('INSERT INTO disabled_modules_server (server_id, module_name) VALUES (?, ?)', (str(guild_id), mod))
            bot_instance.disabled_modules_server_cache[int(guild_id)].add(mod)
            
        # Commands
        cursor.execute('DELETE FROM disabled_commands WHERE server_id = ?', (str(guild_id),))
        bot_instance.disabled_commands_cache[int(guild_id)] = set()
        for cmd in disabled_commands:
            cursor.execute('INSERT INTO disabled_commands (server_id, command_name) VALUES (?, ?)', (str(guild_id), cmd))
            bot_instance.disabled_commands_cache[int(guild_id)].add(cmd)
            
        bot_instance.db.commit()
        return jsonify({'success': True})
