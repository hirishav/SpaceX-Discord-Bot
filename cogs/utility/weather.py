import discord
from discord.ext import commands
import aiohttp
import os
import urllib.parse

class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name="weather", aliases=["weatcher"])
    async def weather(self, ctx, *, location: str = None):
        if not location:
            embed = discord.Embed(
                title="❌ Error",
                description=f"Please provide a location to check the weather.\nUsage: `{ctx.prefix}weather <location>`",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
            
        await ctx.typing()
        
        api_key = os.getenv("WEATHER_API_KEY")
        if not api_key:
            return await ctx.send("⚠️ Weather API key is not configured.")
            
        safe_location = urllib.parse.quote(location)
        url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={safe_location}&aqi=yes"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        loc_data = data['location']
                        current = data['current']
                        
                        region_text = f", {loc_data['region']}" if loc_data.get('region') else ""
                        embed = discord.Embed(
                            title=f"☁️ Weather in {loc_data['name']}{region_text}, {loc_data['country']}",
                            color=discord.Color.blue()
                        )
                        
                        embed.add_field(name="🌡️ Temperature", value=f"{current['temp_c']}°C / {current['temp_f']}°F", inline=True)
                        embed.add_field(name="🌤️ Condition", value=f"{current['condition']['text']}", inline=True)
                        embed.add_field(name="💧 Humidity", value=f"{current['humidity']}%", inline=True)
                        embed.add_field(name="💨 Wind", value=f"{current['wind_kph']} km/h ({current['wind_dir']})", inline=True)
                        embed.add_field(name="🤒 Feels Like", value=f"{current['feelslike_c']}°C", inline=True)
                        embed.add_field(name="☀️ UV Index", value=f"{current['uv']}", inline=True)
                        
                        icon_url = current['condition']['icon']
                        if icon_url.startswith("//"):
                            icon_url = "https:" + icon_url
                        embed.set_thumbnail(url=icon_url)
                        
                        embed.set_footer(text=f"Requested by {ctx.author.name} | Data from WeatherAPI", icon_url=ctx.author.display_avatar.url)
                        
                        await ctx.send(embed=embed)
                    elif resp.status == 400:
                        await ctx.send(f"❌ No weather data found for `{location}`.")
                    else:
                        await ctx.send(f"⚠️ Weather API returned an error: `{resp.status}`")
        except Exception as e:
            await ctx.send(f"⚠️ An error occurred while fetching weather data: `{str(e)}`")

async def setup(bot):
    await bot.add_cog(Weather(bot))
