import discord
from discord.ext import commands
import aiohttp
import os
import re

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

async def fetch_url_content(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    html = await resp.text()
                    # Remove script and style tags
                    html = re.sub(r'<(script|style).*?>.*?</\1>', '', html, flags=re.IGNORECASE | re.DOTALL)
                    # Remove HTML tags
                    text = re.sub(r'<.*?>', ' ', html)
                    # Remove extra whitespace
                    text = re.sub(r'\s+', ' ', text).strip()
                    # Limit the text to avoid token limits
                    return text[:3000]
    except Exception:
        pass
    return None

class UtilitySearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="search", aliases=["ask", "gpt", "grok", "gemini"])
    async def search_command(self, ctx, *, query: str = None):
        if not query:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Please provide something to search for.\nUsage: `{ctx.prefix}search <query>`",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
            
        if not GROQ_API_KEY:
            return await ctx.send("The search API is currently unavailable (API key missing).")
            
        # Send a typing indicator while processing the request
        await ctx.typing()
        
        # Extract URLs from the query
        urls = re.findall(r'(https?://\S+)', query)
        url_contents = {}
        if urls:
            for url in urls[:2]: # Max 2 URLs to prevent abuse/timeout
                content = await fetch_url_content(url)
                if content:
                    url_contents[url] = content
                    
        # Construct the context if URLs were found
        context = ""
        if url_contents:
            context = "\n\nContext from provided links:\n"
            for url, content in url_contents.items():
                context += f"--- Content from {url} ---\n{content}\n"
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "llama3-8b-8192",  # Fast and smart model provided by Groq
                    "messages": [
                        {
                            "role": "system", 
                            "content": "You are a helpful and knowledgeable Discord bot assistant. Answer the user's questions concisely, accurately, and format your output using Discord's markdown features (bolding, code blocks, bullet points) when appropriate. Keep your answers straight to the point."
                        },
                        {
                            "role": "user", 
                            "content": query + context
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2048
                }
                
                async with session.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        answer = data['choices'][0]['message']['content']
                        
                        # Discord limits embed descriptions to 4096 chars.
                        # We will send the message out directly or in an embed.
                        if len(answer) > 4000:
                            answer = answer[:3996] + "..."
                            
                        embed = discord.Embed(
                            title=f"🔍 Search Result",
                            description=answer,
                            color=discord.Color.blurple()
                        )
                        embed.set_footer(text=f"Requested by {ctx.author.name} | Powered by Groq AI", icon_url=ctx.author.display_avatar.url)
                        await ctx.send(embed=embed)
                    else:
                        error_text = await resp.text()
                        await ctx.send(f"⚠️ Search failed. AI API returned status `{resp.status}`.")
        except Exception as e:
            await ctx.send(f"⚠️ An error occurred while searching: `{str(e)}`")


async def setup(bot):
    await bot.add_cog(UtilitySearch(bot))
