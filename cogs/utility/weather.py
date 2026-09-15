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
        
        safe_location = urllib.parse.quote(location)
        
        try:
            async with aiohttp.ClientSession() as session:
                geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={safe_location}&count=1"
                async with session.get(geocode_url) as geo_resp:
                    if geo_resp.status != 200:
                        return await ctx.send(f"⚠️ Geocoding API returned an error: `{geo_resp.status}`")
                    geo_data = await geo_resp.json()
                    
                    if not geo_data.get('results'):
                        return await ctx.send(f"❌ No weather data found for `{location}`.")
                        
                    loc_data = geo_data['results'][0]
                    lat, lon = loc_data['latitude'], loc_data['longitude']
                    
                    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m&timezone=auto"
                    
                    async with session.get(weather_url) as weather_resp:
                        if weather_resp.status != 200:
                            return await ctx.send(f"⚠️ Weather API returned an error: `{weather_resp.status}`")
                        
                        w_data = await weather_resp.json()
                        current = w_data['current']
                        
                        weather_codes = {
                            0: ("Clear sky", "☀️"),
                            1: ("Mainly clear", "🌤️"), 2: ("Partly cloudy", "⛅"), 3: ("Overcast", "☁️"),
                            45: ("Fog", "🌫️"), 48: ("Depositing rime fog", "🌫️"),
                            51: ("Light drizzle", "🌧️"), 53: ("Moderate drizzle", "🌧️"), 55: ("Dense drizzle", "🌧️"),
                            56: ("Light freezing drizzle", "🌧️"), 57: ("Dense freezing drizzle", "🌧️"),
                            61: ("Slight rain", "🌧️"), 63: ("Moderate rain", "🌧️"), 65: ("Heavy rain", "🌧️"),
                            66: ("Light freezing rain", "🌧️"), 67: ("Heavy freezing rain", "🌧️"),
                            71: ("Slight snow fall", "🌨️"), 73: ("Moderate snow fall", "🌨️"), 75: ("Heavy snow fall", "🌨️"),
                            77: ("Snow grains", "🌨️"),
                            80: ("Slight rain showers", "🌦️"), 81: ("Moderate rain showers", "🌦️"), 82: ("Violent rain showers", "🌦️"),
                            85: ("Slight snow showers", "🌨️"), 86: ("Heavy snow showers", "🌨️"),
                            95: ("Thunderstorm", "⛈️"), 96: ("Thunderstorm, slight hail", "⛈️"), 99: ("Thunderstorm, heavy hail", "⛈️"),
                        }
                        
                        code = current['weather_code']
                        condition_text, emoji = weather_codes.get(code, ("Unknown", "❓"))
                        
                        region_text = f", {loc_data.get('admin1')}" if loc_data.get('admin1') else ""
                        embed = discord.Embed(
                            title=f"☁️ Weather in {loc_data['name']}{region_text}, {loc_data.get('country', '')}",
                            color=discord.Color.blue()
                        )
                        
                        temp_c = current['temperature_2m']
                        temp_f = round(temp_c * 9/5 + 32, 1)
                        feels_c = current['apparent_temperature']
                        
                        embed.add_field(name="🌡️ Temperature", value=f"{temp_c}°C / {temp_f}°F", inline=True)
                        embed.add_field(name="🌤️ Condition", value=f"{emoji} {condition_text}", inline=True)
                        embed.add_field(name="💧 Humidity", value=f"{current['relative_humidity_2m']}%", inline=True)
                        embed.add_field(name="💨 Wind", value=f"{current['wind_speed_10m']} km/h", inline=True)
                        embed.add_field(name="🤒 Feels Like", value=f"{feels_c}°C", inline=True)
                        
                        embed.set_footer(text=f"Requested by {ctx.author.name} | Data from Open-Meteo", icon_url=ctx.author.display_avatar.url)
                        
                        await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"⚠️ An error occurred while fetching weather data: `{str(e)}`")

async def setup(bot):
    await bot.add_cog(Weather(bot))
