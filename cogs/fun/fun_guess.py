import discord
from discord.ext import commands
import database
import aiohttp
import random
import asyncio
import time
import os


class HintView(discord.ui.View):
    def __init__(self, cog, server_id, answer, hint2_text):
        super().__init__(timeout=60)
        self.cog = cog
        self.server_id = server_id
        self.answer = answer
        self.hint2_text = hint2_text

    @discord.ui.button(label="Hint 1 (Letters)", style=discord.ButtonStyle.primary, custom_id="hint1")
    async def hint1(self, interaction: discord.Interaction, button: discord.ui.Button):
        revealed = self.cog.get_letter_hint(self.answer)
        await interaction.response.send_message(f"🤫 **Hint 1 (by {interaction.user.display_name}):** The answer looks like this: `{revealed}`")

    @discord.ui.button(label="Hint 2 (Details)", style=discord.ButtonStyle.secondary, custom_id="hint2")
    async def hint2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"🕵️ **Hint 2 (by {interaction.user.display_name}):** {self.hint2_text}")

    @discord.ui.button(label="Hint 3 (Reveal)", style=discord.ButtonStyle.danger, custom_id="hint3")
    async def hint3(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        self.cog.block_user(self.server_id, user_id)
        
        if self.server_id in self.cog.active_games:
            game = self.cog.active_games[self.server_id]
            game['current_question'] = None
            if 'round_event' in game:
                game['round_event'].set()
                
        await interaction.response.send_message(
            f"🚨 **ANSWER REVEALED by {interaction.user.display_name}:** The answer is **{self.answer}**.\n"
            f"*Note: They cannot guess for the next round!*"
        )

class FunGuess(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {} # server_id -> game_dict
        self.flags_cache = []
        self._init_db()

    def _init_db(self):
        db = database.connect()
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS guess_config (
            server_id TEXT PRIMARY KEY,
            channel_id TEXT
        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS guess_scores (
            server_id TEXT,
            user_id TEXT,
            score INTEGER,
            PRIMARY KEY (server_id, user_id)
        )''')
        db.commit()
        db.close()

    def get_letter_hint(self, answer):
        words = answer.split()
        res = []
        for w in words:
            if len(w) <= 2:
                res.append(w)
            else:
                # Reveal 1/3rd of the letters
                reveal_count = max(1, len(w) // 3)
                indices = random.sample(range(len(w)), reveal_count)
                chars = []
                for i, c in enumerate(w):
                    if i in indices or not c.isalpha():
                        chars.append(c)
                    else:
                        chars.append("_")
                res.append("".join(chars))
        return " ".join(res)

    def block_user(self, server_id, user_id):
        if server_id in self.active_games:
            game = self.active_games[server_id]
            game['blocked_users'].add(user_id)
            game['next_round_blocked'].add(user_id)

    async def fetch_random_question(self, category=None):
        apis = ['dog', 'pokemon', 'flag']
            
        if category and category.lower() in apis:
            choice = category.lower()
        else:
            choice = random.choice(apis)
        
        async with aiohttp.ClientSession() as session:
            try:
                if choice == 'dog':
                    async with session.get("https://dog.ceo/api/breeds/image/random") as resp:
                        data = await resp.json()
                        image_url = data['message']
                        part = image_url.split('/breeds/')[1].split('/')[0]
                        parts = part.split('-')
                        parts.reverse()
                        answer = " ".join(parts).title()
                        return {
                            "type": "breed of this dog",
                            "answer": answer,
                            "image_url": image_url,
                            "hint2": f"It is a type of dog, part of the {parts[-1].title()} family."
                        }
                elif choice == 'pokemon':
                    poke_id = random.randint(1, 1010)
                    async with session.get(f"https://pokeapi.co/api/v2/pokemon/{poke_id}") as resp:
                        data = await resp.json()
                        answer = data['name'].replace('-', ' ').title()
                        image_url = data['sprites']['other']['official-artwork']['front_default']
                        types = ", ".join([t['type']['name'].title() for t in data['types']])
                        return {
                            "type": "Pokémon",
                            "answer": answer,
                            "image_url": image_url,
                            "hint2": f"This Pokémon is of type(s): {types}."
                        }
                elif choice == 'flag':
                    if not self.flags_cache:
                        async with session.get("https://flagcdn.com/en/codes.json") as resp:
                            codes = await resp.json()
                            self.flags_cache = [{'code': k, 'name': v} for k, v in codes.items() if '-' not in k]
                    
                    country = random.choice(self.flags_cache)
                    answer = country['name']
                    image_url = f"https://flagcdn.com/w320/{country['code']}.png"
                    return {
                        "type": "country flag",
                        "answer": answer,
                        "image_url": image_url,
                        "hint2": f"The country name has {len(answer.replace(' ', ''))} letters."
                    }
            except Exception as e:
                print(f"[GuessGame] API Fetch Error ({choice}): {e}")
                # Fallback question if API fails
                return {
                    "type": "Fallback Question",
                    "answer": "Error",
                    "image_url": "https://via.placeholder.com/400x300.png?text=API+Error",
                    "hint2": "An error occurred fetching the image."
                }

    async def game_loop(self, server_id, channel, category=None):
        rounds_played = 0
        while server_id in self.active_games:
            try:
                game = self.active_games[server_id]
                game['blocked_users'] = game.get('next_round_blocked', set())
                game['next_round_blocked'] = set()
                
                question = await self.fetch_random_question(category)
                if question['answer'] == "Error":
                    await asyncio.sleep(5)
                    continue

                game['current_question'] = question
                
                embed = discord.Embed(
                    title=f"🤔 Guess the {question['type']}!",
                    description="Type your answer in the chat!\nYou have **1 minute**.\n\n" + (question.get('description', '')),
                    color=discord.Color.blue()
                )
                if question.get('image_url'):
                    embed.set_image(url=question['image_url'])
                
                await channel.send(embed=embed)
                
                game['round_event'] = asyncio.Event()
                
                try:
                    await asyncio.wait_for(game['round_event'].wait(), timeout=60.0)
                except asyncio.TimeoutError:
                    if server_id in self.active_games:
                        timeout_embed = discord.Embed(
                            title="⏰ Time's up!",
                            description="No one guessed it! The answer will remain a secret. 🤫",
                            color=discord.Color.red()
                        )
                        await channel.send(embed=timeout_embed)
                
                # Small pause before next question
                if server_id in self.active_games:
                    rounds_played += 1
                    if rounds_played % 10 == 0:
                        db = database.connect()
                        cursor = db.cursor()
                        cursor.execute('SELECT user_id, score FROM guess_scores WHERE server_id = ? ORDER BY score DESC LIMIT 10', (server_id,))
                        rows = cursor.fetchall()
                        db.close()

                        if rows:
                            lb_embed = discord.Embed(title="🏆 Leaderboard (Current Standings)", color=discord.Color.gold())
                            leaderboard_text = ""
                            for i, (uid, score) in enumerate(rows):
                                leaderboard_text += f"**{i+1}.** <@{uid}> - {score} points\n"
                            
                            lb_embed.description = leaderboard_text
                            await channel.send(f"📊 **Standings after {rounds_played} turns:**", embed=lb_embed)

                    await asyncio.sleep(3)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[GuessGame] Game Loop Error: {e}")
                await asyncio.sleep(5)

    @commands.group(invoke_without_command=True)  # type: ignore
    async def guess(self, ctx):
        """Guessing game commands."""
        embed = discord.Embed(title="🎮 Guessing Game", color=discord.Color.green())
        embed.add_field(name="!!setguesschannel #channel", value="Set the guessing channel (Admin)", inline=False)
        embed.add_field(name="!!guess start", value="Start the game", inline=False)
        embed.add_field(name="!!guess stop", value="Stop the current game", inline=False)
        embed.add_field(name="!!guess end", value="End the game and see the leaderboard", inline=False)
        embed.add_field(name="!!hint", value="Get a hint for the current question", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setguesschannel(self, ctx, channel: discord.TextChannel = None):
        """Set the channel for the guessing game."""
        channel = channel or ctx.channel
        db = database.connect()
        cursor = db.cursor()
        cursor.execute('''
            INSERT INTO guess_config (server_id, channel_id) 
            VALUES (?, ?) 
            ON CONFLICT(server_id) DO UPDATE SET channel_id=excluded.channel_id
        ''', (str(ctx.guild.id), str(channel.id)))
        db.commit()
        db.close()
        await ctx.send(f"✅ Guessing game channel set to {channel.mention}!")

    @guess.command()
    async def start(self, ctx, category: str = None):
        server_id = str(ctx.guild.id)
        
        valid_apis = ['dog', 'pokemon', 'flag']

        if category and category.lower() not in valid_apis:
            return await ctx.send(f"❌ Invalid category! Available categories: `{', '.join(valid_apis)}`")
        
        db = database.connect()
        cursor = db.cursor()
        cursor.execute('SELECT channel_id FROM guess_config WHERE server_id = ?', (server_id,))
        row = cursor.fetchone()
        db.close()

        if not row:
            return await ctx.send("❌ Game channel is not set! Admin must use `!!setguesschannel #channel` first.")
            
        channel_id = row[0]
        channel = self.bot.get_channel(int(channel_id))
        
        if not channel:
            return await ctx.send("❌ Configured channel no longer exists!")

        if server_id in self.active_games:
            return await ctx.send("⚠️ The game is already running!")

        self.active_games[server_id] = {
            'channel_id': channel_id,
            'current_question': None,
            'task': None,
            'blocked_users': set(),
            'next_round_blocked': set(),
            'category': category
        }

        category_msg = f" (Category: **{category.title()}**)" if category else ""
        await ctx.send(f"🚀 Guessing game is starting in {channel.mention}!{category_msg}")
        
        # Start the loop task
        task = self.bot.loop.create_task(self.game_loop(server_id, channel, category))
        self.active_games[server_id]['task'] = task

    @guess.command()
    async def stop(self, ctx):
        server_id = str(ctx.guild.id)
        if server_id not in self.active_games:
            return await ctx.send("❌ No game is currently running.")
            
        game = self.active_games[server_id]
        if game['task']:
            game['task'].cancel()
            
        del self.active_games[server_id]
        await ctx.send("🛑 Guessing game has been stopped.")

    @guess.command()
    async def end(self, ctx):
        server_id = str(ctx.guild.id)
        
        # Stop if running
        if server_id in self.active_games:
            game = self.active_games[server_id]
            if game['task']:
                game['task'].cancel()
            del self.active_games[server_id]

        db = database.connect()
        cursor = db.cursor()
        cursor.execute('SELECT user_id, score FROM guess_scores WHERE server_id = ? ORDER BY score DESC LIMIT 10', (server_id,))
        rows = cursor.fetchall()
        db.close()

        if not rows:
            return await ctx.send("🛑 Game ended! No one scored any points yet.")

        embed = discord.Embed(title="🏆 Guessing Game Leaderboard", color=discord.Color.gold())
        leaderboard_text = ""
        for i, (uid, score) in enumerate(rows):
            leaderboard_text += f"**{i+1}.** <@{uid}> - {score} points\n"
        
        embed.description = leaderboard_text
        await ctx.send("🛑 Game ended! Here are the top players:", embed=embed)

    @commands.command()
    async def hint(self, ctx):
        server_id = str(ctx.guild.id)
        if server_id not in self.active_games:
            return await ctx.send("❌ No active game in this server!")
            
        game = self.active_games[server_id]
        if str(ctx.channel.id) != game['channel_id']:
            return await ctx.send(f"❌ Play the game in <#{game['channel_id']}>!")
            
        question = game.get('current_question')
        if not question:
            return await ctx.send("❌ No question is currently active!")
            
        view = HintView(self, server_id, question['answer'], question['hint2'])
        embed = discord.Embed(
            title="💡 Need a hint?", 
            description="Click a button below for a hint!\n*Warning: Hint 3 will reveal the answer but block you from playing.*", 
            color=discord.Color.yellow()
        )
        await ctx.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: 
            return
            
        server_id = str(message.guild.id)
        if server_id not in self.active_games: 
            return
            
        game = self.active_games[server_id]
        if str(message.channel.id) != game['channel_id']: 
            return
            
        question = game.get('current_question')
        if not question: 
            return
            
        user_id = message.author.id
        if user_id in game['blocked_users']:
            return
            
        guess = message.content.strip().lower()
        answer = question['answer'].lower()
        
        # Exact match or very close
        if guess == answer:
            game['current_question'] = None
            await message.add_reaction("✅")
            await message.reply(f"🎉 **{message.author.mention} got it right!** The answer is **{question['answer']}**.")
            
            db = database.connect()
            cursor = db.cursor()
            cursor.execute("""
            INSERT INTO guess_scores (server_id, user_id, score)
            VALUES (?, ?, 1)
            ON CONFLICT(server_id, user_id) DO UPDATE SET score = score + 1
            """, (server_id, str(user_id)))
            db.commit()
            db.close()
            
            if 'round_event' in game:
                game['round_event'].set()
        else:
            if len(guess) < 30:
                await message.add_reaction("❌")

async def setup(bot):
    await bot.add_cog(FunGuess(bot))
