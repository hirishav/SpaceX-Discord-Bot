import discord
from discord.ext import commands
import aiohttp
import os
import re
import urllib.parse


async def fetch_url_content(url):
    try:
        headers = {'User-Agent': 'SpaceXBot/1.0 (Discord Bot, https://github.com/hirishav/SpaceX-Discord-Bot)'}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    html = re.sub(r'<(script|style).*?>.*?</\1>', '', html, flags=re.IGNORECASE | re.DOTALL)
                    text = re.sub(r'<.*?>', ' ', html)
                    text = re.sub(r'\s+', ' ', text).strip()
                    return text[:3000]
    except Exception:
        pass
    return None

class UtilitySearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _handle_ai_command(self, ctx, query, api_url, api_key, model_name, bot_name):
        if not query:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Please provide something to ask.\nUsage: `{ctx.prefix}{ctx.invoked_with} <query>`",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
            
        if not api_key:
            return await ctx.send(f"The {bot_name} API is currently unavailable (API key missing).")
            
        await ctx.typing()
        
        urls = re.findall(r'(https?://\S+)', query)
        url_contents = {}
        if urls:
            for url in urls[:2]:
                content = await fetch_url_content(url)
                if content:
                    url_contents[url] = content
                    
        context = ""
        if url_contents:
            context = "\n\nContext from provided links:\n"
            for url, content in url_contents.items():
                context += f"--- Content from {url} ---\n{content}\n"
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": model_name,
                    "messages": [
                        {
                            "role": "system", 
                            "content": f"You are a helpful and knowledgeable Discord bot assistant powered by {bot_name}. Answer the user's questions concisely, accurately, and format your output using Discord's markdown features (bolding, code blocks, bullet points) when appropriate. Keep your answers straight to the point."
                        },
                        {
                            "role": "user", 
                            "content": query + context
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2048
                }
                
                async with session.post(api_url, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        answer = data['choices'][0]['message']['content']
                        
                        if len(answer) > 4000:
                            answer = answer[:3996] + "..."
                            
                        embed = discord.Embed(
                            title=f"🤖 {bot_name} Result",
                            description=answer,
                            color=discord.Color.green() if bot_name == "ChatGPT" else discord.Color.blurple()
                        )
                        embed.set_footer(text=f"Requested by {ctx.author.name} | Powered by {bot_name}", icon_url=ctx.author.display_avatar.url)
                        await ctx.send(embed=embed)
                    elif resp.status == 429 and bot_name == "ChatGPT":
                        fallback_msg = await ctx.send("⚠️ ChatGPT is rate-limited or out of quota (429). Falling back to Grok AI...")
                        
                        groq_key = os.getenv("GROQ_API_KEY")
                        if not groq_key:
                            return await fallback_msg.edit(content="⚠️ ChatGPT is rate-limited, and Grok fallback failed (API key missing).")
                            
                        headers["Authorization"] = f"Bearer {groq_key}"
                        payload["model"] = "llama-3.1-8b-instant"
                        
                        async with session.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload) as fallback_resp:
                            if fallback_resp.status == 200:
                                data = await fallback_resp.json()
                                answer = data['choices'][0]['message']['content']
                                if len(answer) > 4000:
                                    answer = answer[:3996] + "..."
                                embed = discord.Embed(
                                    title="🤖 Grok AI Result (Fallback)",
                                    description=answer,
                                    color=discord.Color.blurple()
                                )
                                embed.set_footer(text=f"Requested by {ctx.author.name} | Fallback from ChatGPT", icon_url=ctx.author.display_avatar.url)
                                await fallback_msg.edit(content=None, embed=embed)
                            else:
                                await fallback_msg.edit(content=f"⚠️ Fallback search failed. Grok AI returned status `{fallback_resp.status}`.")
                    else:
                        error_text = await resp.text()
                        await ctx.send(f"⚠️ Search failed. {bot_name} API returned status `{resp.status}`.")
        except Exception as e:
            await ctx.send(f"⚠️ An error occurred while communicating with {bot_name}: `{str(e)}`")


    @commands.command(name="gpt", aliases=["chatgpt"])
    async def gpt_command(self, ctx, *, query: str = None):
        await self._handle_ai_command(
            ctx, 
            query, 
            api_url="https://api.openai.com/v1/chat/completions", 
            api_key=os.getenv("CHATGPT_API_KEY"), 
            model_name="gpt-4o-mini", 
            bot_name="ChatGPT"
        )

    @commands.command(name="grok")
    async def grok_command(self, ctx, *, query: str = None):
        await self._handle_ai_command(
            ctx, 
            query, 
            api_url="https://api.groq.com/openai/v1/chat/completions", 
            api_key=os.getenv("GROQ_API_KEY"), 
            model_name="llama-3.1-8b-instant", 
            bot_name="Grok AI (via Groq)"
        )

    @commands.command(name="search", aliases=["wiki", "wikipedia"])
    async def search_command(self, ctx, *, query: str = None):
        if not query:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Please provide something to search for.\nUsage: `{ctx.prefix}search <query>`",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
            
        await ctx.typing()
        
        try:
            headers = {'User-Agent': 'SpaceXBot/1.0 (Discord Bot, https://github.com/hirishav/SpaceX-Discord-Bot)'}
            async with aiohttp.ClientSession(headers=headers) as session:
                # 1. Search Wikipedia for the best matching page title
                clean_query = query.lower()
                prefixes_to_remove = ["what is a ", "what is an ", "what is ", "who is ", "where is ", "meaning of ", "define ", "what are ", "kya hai "]
                suffixes_to_remove = [" kya hai", " kise kehte hai", " kise kehte hain", " ka matlab", " ka kya matlab hai"]
                
                for prefix in prefixes_to_remove:
                    if clean_query.startswith(prefix):
                        clean_query = clean_query[len(prefix):]
                        break
                        
                for suffix in suffixes_to_remove:
                    if clean_query.endswith(suffix):
                        clean_query = clean_query[:-len(suffix)]
                        break
                        
                clean_query = clean_query.rstrip("?").strip()
                
                # Check suffixes again in case the question mark was removed
                for suffix in suffixes_to_remove:
                    if clean_query.endswith(suffix):
                        clean_query = clean_query[:-len(suffix)]
                        break
                        
                clean_query = clean_query.strip()
                if not clean_query:
                    clean_query = query
                    
                safe_query = urllib.parse.quote(clean_query)
                search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={safe_query}&utf8=&format=json&srlimit=1"
                
                async with session.get(search_url) as resp:
                    if resp.status != 200:
                        return await ctx.send("⚠️ Failed to connect to Wikipedia.")
                        
                    data = await resp.json()
                    
                    if 'query' not in data or not data['query']['search']:
                        return await ctx.send(f"❌ No results found on Wikipedia for `{query}`.")
                        
                    page_title = data['query']['search'][0]['title']
                    page_link = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(page_title.replace(' ', '_'))}"
                    
                # 2. Fetch the summary for that page
                summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(page_title.replace(' ', '_'))}"
                async with session.get(summary_url) as sum_resp:
                    if sum_resp.status != 200:
                        return await ctx.send("⚠️ Failed to fetch Wikipedia summary.")
                        
                    sum_data = await sum_resp.json()
                    extract = sum_data.get('extract', 'No summary available.')
                    thumbnail = sum_data.get('thumbnail', {}).get('source', None)
                    
                    if len(extract) > 4000:
                        extract = extract[:3996] + "..."
                        
                    embed = discord.Embed(
                        title=f"🔍 Wikipedia: {page_title}",
                        url=page_link,
                        description=extract,
                        color=discord.Color.blue()
                    )
                    
                    if thumbnail:
                        embed.set_thumbnail(url=thumbnail)
                        
                    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
                    await ctx.send(embed=embed)
                    
        except Exception as e:
            await ctx.send(f"⚠️ An error occurred while searching: `{str(e)}`")


async def setup(bot):
    await bot.add_cog(UtilitySearch(bot))
