from discord.ext import commands, tasks
import discord
import os
from stayin_alive import keep_alive
import time
from datetime import datetime
import asyncpg
from replit import db
import math
import random
import asyncio
import requests
from better_profanity import profanity
import urllib.parse
import yfinance as yf

# Simple help command
class revisedHelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        e = discord.Embed(color=discord.Color.blurple(),
                          description='',
                          title="RemindMe!")
        e.set_footer(text="Technetium", icon_url=iconUrl)
        e.timestamp = datetime.now()
        for page in self.paginator.pages:
            e.description += page
        await destination.send(embed=e)

# CONSTANTS
# Command prefix that the bot will use to recognise commands.
prefix = "."

# List of commands that fall under "random"
randomCommands = ["coin","num"]

# Time units correspond to 1 of that unit in seconds
timeUnits = {
    "s": {
        "s": 1,
        "n": "second(s)"
    },
    "m": {
        "s": 60,
        "n": "minute(s)"
    },
    "h": {
        "s": 3600,
        "n": "hour(s)"
    },
    "d": {
        "s": 86400,
        "n": "day(s)"
    },
    "w": {
        "s": 604800,
        "n": "weeks(s)"
    },
    "mm": {
        "s": 2592000,
        "n": "months(s)"
    }
}

iconUrl = "https://media.discordapp.net/attachments/833730060753436704/841372371704741898/VelocitySquared.png?width=670&height=670"

# Keys
opwkey = os.environ['open_weather_key']
gkey = os.environ["GOOGLE_KEY"]
wakey = os.environ["WOLFRAM_ALPHA_ID"]
omdbkey = os.environ["OMDB_KEY"]

# Client Setup
client = commands.Bot(command_prefix=prefix,
                    intents=discord.Intents.all(),
                    help_command=revisedHelpCommand())
client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="dogs."))


# When the bot is fully initialised
@client.event
async def on_ready():
    print("Ready to go!")

# When a message is sent in any channel
@client.event
async def on_message(ctx):
    await client.process_commands(ctx)
    # If the contents of that message is "Hello!"
    if ctx.content == "Hello!":
        # It will send "HI!" in the channel the message was sent in.
        responseList = ["Yo!","Bonjour.","Wassup?","Hey.","Hello.","Hi!"]
        await ctx.channel.send(responseList[random.randint(0,len(responseList)-1)])
    if profanity.contains_profanity(ctx.content) is True:
        await ctx.delete()

async def sendError(ctx, *error):
    """
    Handles sending error messages. Accepts the message context and the error message as an *arg.
    """

    # Constructs an embed object to be sent.
    embed = discord.Embed(title="Error encountered!",
                          description=" ".join(error),
                          color=0xFF4500)
    embed.set_footer(text="Technetium", icon_url=iconUrl)
    embed.timestamp = datetime.now()
    return await ctx.channel.send(embed=embed)

class loopCog(commands.Cog):
    """
    Cog that handles looping through the repl database.
    """
    def __init__(self, bot):
        self.bot = bot
        self.data = []
        self.batch_update.add_exception_type(asyncpg.PostgresConnectionError)
        self.batch_update.start()

    def cog_unload(self):
        self.batch_update.cancel()

    # Uses tasks library to loop through this code every second.
    @tasks.loop(seconds=1.0)
    async def batch_update(self):
        # Runs through the Database
        for i in db.keys():
            # Gets the value at that index
            val = db[i]
            # Splits the string into a usable list
            valList = val.split(";")
            # Gets list values
            ttr = float(valList[0])
            reminder = valList[1]
            authorID = valList[2]
            timeSet = valList[3]
            # Checks if the time to remind is less than or equal to the current time.
            if ttr <= time.time():
                # Formats time set
                dateTimeObj = datetime.utcfromtimestamp(float(timeSet))
                timestampStr = dateTimeObj.strftime(
                    "%d of %B, %Y, at %I%p, %Mm, %Ss (UTC)")

                # Initialise embed
                embedSend = discord.Embed(
                    title="Reminder!",
                    description="Here's a reminder you set.")
                embedSend.add_field(name="Time Set",
                                    value=timestampStr,
                                    inline=0)
                embedSend.add_field(name="Reason", value=reminder)
                embedSend.set_thumbnail(
                    url=
                    "https://cdn.ambientedirect.com/chameleon/mediapool/thumbs/6/1d/Magis_Tempo-Wanduhr_800x800-ID44985-4cb53f9a41684fcf6402aa3cf023d377.jpg"
                )
                embedSend.timestamp = datetime.now()
                embedSend.set_footer(text="Technetium", icon_url=iconUrl)

                # Get user and send the message privately
                userObj = await client.fetch_user(int(authorID))
                await userObj.send(embed=embedSend)
                del db[i]

# Start loop
laLoop = loopCog(client)

class moderationCog(commands.Cog, name="Moderation"):
    """
    A collection of commands aimed at making moderation easier.
    """
    def __init__(self, client):
        self.client = client
     
    @commands.command(usage="<Message Count>", aliases=["exterminatus"])
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, count=None):
        """
        Purges a set amount of messages.
        """
        if count is None:
            await sendError(
                ctx, "Please enter the amount of messages you want to remove.")
        else:
            count = int(count)
            # API only allows for up to 100 messages purged at once, so we need to iterate if the user asks for more than 100 messages
            if count > 100:
                # Gets the amount of times to loop through
                loopC = math.ceil(count/100)
                for i in range(loopC):
                    if i == loopC-1:
                        # Probably works
                        await ctx.channel.purge(limit=count-loopC*100)
                    else:
                        await ctx.channel.purge(limit=100)
            else:
                await ctx.channel.purge(limit=count)
    
    # Handles the permissions error as a result of the user not having permissions for .purge
    @purge.error
    async def purge_error_handler(self,ctx,error):
        if isinstance(error, commands.MissingPermissions):
            errMsg = await sendError(ctx, "Insufficient permissions: Manage Messages")
            # Waits 5 seconds, then deletes the error message and the user's command
            await asyncio.sleep(5)
            await errMsg.delete()
            await ctx.message.delete()

class utilityCog(commands.Cog, name="Utility"):
    """
    Some rather simple utility commands, aimed at improving quality of life.
    """

    @commands.command(usage="<Movie Name>")
    async def movie(self, ctx, *movieName):
        """
        Uses the OMDB API to return movie data.
        """

        try:
            inputer = " ".join(movieName)
            query = urllib.parse.quote_plus(inputer)

            req = requests.get(f"http://www.omdbapi.com/?apikey={omdbkey}&t={query}")

            rjson = req.json()

            e = discord.Embed(title=rjson['Title'],description=f"Released in {rjson['Released']}, rated {rjson['Rated']}")

            e.add_field(name="Production",value=rjson['Production'])
            e.add_field(name="Box Office",value=rjson['BoxOffice'])

            e.set_thumbnail(url=rjson["Poster"])

            await ctx.channel.send(embed=e)
        except BaseException:
            await sendError(ctx, "Error encountered!")

    @commands.command(usage="<Time Scale> <Time Period> [Reason}")
    async def remindme(self, ctx, timeScale, timePeriod, *reason):
        """
        Allows you to set reminders that you'll recieve in your DMs after the specified time!
        """
        timeScale = int(timeScale)
        if timePeriod.lower() not in timeUnits:
            await sendError(
                ctx,
                "Invalid time period! Please chose from seconds (s), minutes (m), hours (h), days (d), weeks (w), months (mm)"
            )
        else:
            # Converts the time scale to seconds
            timeInc = timeUnits[timePeriod.lower()]["s"] * timeScale
            if timeInc > 315400000:
                await sendError(
                    ctx,
                    "Time period is too long! Must be less than 10 years.")
            else:
                # Gets the UTC time at which the user should be reminded
                timeToRemind = time.time() + timeInc

                # Checks if there was a reason provided
                if reason != () or reason != []:
                    reasonF = " ".join(reason)
                else:
                    reasonF = "None!"

                # Gets the name of the unit they provided, e.g d:days, or s:seconds
                timeName = timeUnits[timePeriod.lower()]["n"]
                embed = discord.Embed(
                    title="Reminder Set!",
                    description=f"We'll remind you in {timeScale} {timeName}.")
                embed.add_field(name="Reason", value=reasonF, inline=False)
                embed.set_footer(text="Technetium", icon_url=iconUrl)
                embed.timestamp = datetime.now()
                await ctx.channel.send(embed=embed)

                # Reminders stored as a string, due to DB shenanigans
                # (timeToRemind);(reason);(Author ID);(Time Set)
                reminderObj = f"{timeToRemind};{reasonF};{ctx.author.id};{time.time()}"
                db[str(len(db.keys()))] = reminderObj

    @commands.command(usage = "<city>")
    async def weather(self, ctx, city):
        """
        Returns weather data about a given city.
        """

        # Gets json data from API using city name + api key
        wReq = requests.get(f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={opwkey}")

        # Checks if city was found or not
        if wReq.status_code == 404:
            await sendError(ctx, "City not found!") 
        else:
            wjson = wReq.json()

            # Creates initial embed
            e = discord.Embed(title=f"Current Weather",description=f"Checked {city}'s current weather.")
            e.timestamp = datetime.now()
            e.set_footer(text="Provided by OpenWeather", icon_url=iconUrl)

            # Coordinate data
            e.add_field(name="Longitude",value=wjson["coord"]["lon"])
            e.add_field(name="Latitude",value=wjson["coord"]["lat"])

            # Empty field, acts as a separator
            e.add_field(name="\u200B",value="\u200B",inline=False)

            # Getting weather data
            clouds = wjson["clouds"]["all"]
            temp = wjson["main"]["temp"]
            feels_like = wjson["main"]["feels_like"]
            pressure = wjson["main"]["pressure"]
            humidity = wjson["main"]["humidity"]  

            # Adding weather data to embed
            e.add_field(name="Weather",value=wjson["weather"][0]["description"].title())
            e.add_field(name="Cloud Coverage",value=f"{clouds}%")

            e.add_field(name="\u200B",value="\u200B",inline=False)

            e.add_field(name="Temperature",value=f"{temp}K",inline=1)
            e.add_field(name="Feels Like",value=f"{feels_like}K",inline=1)
            e.add_field(name="Pressure",value=f"{pressure} hPa",inline=1)
            e.add_field(name="Humidity",value=f"{humidity}%",inline=1)

            # CITY IMAGES
            # Google Cloud API shenanigans
            
            # Gets the Place ID from the Google API
            placeID = requests.get(f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={city}&key={gkey}&inputtype=textquery")

            # Checks if an ID was returned
            if placeID.json()["status"] == "OK":
                photoid = placeID.json()["candidates"][0]["place_id"]

                # Grabs the place details JSON using the Place ID
                place_details = requests.get(f"https://maps.googleapis.com/maps/api/place/details/json?place_id={photoid}&key={gkey}&fields=photo")

                # Gets the Photo Reference from the JSON provided by the details request
                photoref = place_details.json()["result"]["photos"][0]["photo_reference"]

                try:
                    # Sets the embed image to the place's photo, using the photoreference
                    e.set_image(url=f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photoref}&key={gkey}&maxwidth=1600")
                except BaseException: 
                    print("Error fetching image.")


            await ctx.channel.send(embed=e)

    @commands.command(usage = "<equation>")
    async def equation(self, ctx, *equation):
        inputer = " ".join(equation)
        query = urllib.parse.quote_plus(inputer)

        e = discord.Embed(title="Equation!", description="Here's your equation:")
        e.set_image(url=f"https://chart.apis.google.com/chart?chf=bg,s,fffff0&cht=tx&chl={query}")

        e.set_footer(text="Technetium", icon_url=iconUrl)
        e.timestamp = datetime.now()

        await ctx.channel.send(embed=e) 
        
    @commands.command(usage="<country>")
    async def country(self, ctx, cName):
        try:
            req = requests.get(f"https://restcountries.eu/rest/v2/name/{cName.lower()}")

            rjs = req.json()

            c_name = rjs[0]["name"]

            e = discord.Embed(title=f"{c_name}!",description=f"Here's some data I found about {c_name}.")

            e.add_field(name="Region",value=rjs[0]["region"])
            e.add_field(name="Subregion",value=rjs[0]["subregion"])
            e.add_field(name="Capital",value=rjs[0]["capital"])
            e.add_field(name="Latitude", value=rjs[0]["latlng"][0])
            e.add_field(name="Longitude", value=rjs[0]["latlng"][1])

            e.add_field(name="\u200B",value="\u200B",inline=False)

            e.add_field(name="Population",value=rjs[0]["population"])
            e.add_field(name="Timezone",value=rjs[0]["timezones"][0])
            e.add_field(name="Currency", value=rjs[0]["currencies"][0]["name"])
            e.add_field(name="Lanague",value=rjs[0]["languages"][0]["name"])

            cc = rjs[0]["alpha2Code"]

            furl = f"https://www.countryflags.io/{cc}/flat/64.png"

            e.set_thumbnail(url=furl)

            e.timestamp = datetime.now()
            e.set_footer(text="Technetium", icon_url=iconUrl)

            await ctx.channel.send(embed=e)
        except BaseException: 
            await sendError(ctx, "Unexpected error encountered.")

class stocksCog(commands.Cog, name = "Stocks"):
    """
    All commands surrounding stocks!
    """
    @commands.command(usage = "<ticker>")
    async def ticker(self, ctx, ticker):

        print("Recieved")
        tickData = yf.Ticker(ticker)

        tjs = tickData.info
        print("Data gotten")

        #try:
        e = discord.Embed(title=tjs["shortName"],description=f"Here's some info on ${ticker.upper()}")

        mc = f'{tjs["marketCap"]:,d}'
        print(type(mc))
        v = f'{tjs["volume"]:,d}'
        dh = f'{tjs["dayHigh"]:,d}'
        dl = f'{tjs["dayLow"]:,d}'
        fdh = f'{tjs["fiftyTwoWeekHigh"]:,d}'
        fdl = f'{tjs["fiftyTwoWeekLow"]:,d}'

        e.add_field(name="Market Cap", value=f"{mc}$",inline=1)
        e.add_field(name="Volume", value=f"{v}",inline=1)

        e.add_field(name="\u200B",value="\u200B",inline=False)

        e.add_field(name="Day High",value=f"{dh}$",inline=1)
        e.add_field(name="Day Low",value=f"{dl}$", inline=1)

        e.add_field(name="\u200B",value="\u200B",inline=False)

        e.add_field(name="52 Week High",value=f"{fdh}$")
        e.add_field(name="53 Week Low",value=f"{fdl}$")

        e.set_thumbnail(url=tjs["logo_url"])
        e.timestamp = datetime.now()
        e.set_footer(text="Technetium",icon_url=iconUrl)

        await ctx.channel.send(embed=e) 
        #except BaseException:
        #    await sendError(ctx, "Unexpected error encountered!")

class funCog(commands.Cog, name="Fun"):
    """
    Commands that don't necessarily serve a purpose or fit in any specific category. Give them a go!
    """
    @commands.command(usage="[coin, num] [. . . args . . .]",description="Generates some random stuff. Very cool.")
    async def random(self, ctx, *cmdArgs):
        # Checks if the user has entered any arguments
        if cmdArgs == ():
            ranCmdStr = ", ".join(randomCommands)
            await sendError(ctx, f"Please enter a valid generator, such as: {ranCmdStr}.")
        else:
            # Checks if their random option is valid
            if str(cmdArgs[0]) not in randomCommands:
                ranCmdStr = ", ".join(randomCommands)
                await sendError(ctx, f"Please enter a valid generator, such as: {ranCmdStr}.")
            else:
                # Coin flip code
                if str(cmdArgs[0]) == "coin":
                    # Creates simple embed to show coin flip
                    embed=discord.Embed(title="Flipping a Coin!", description="Give it a second...", color=0xddd736)
                    embed.set_thumbnail(url="https://i.pinimg.com/originals/d7/49/06/d74906d39a1964e7d07555e7601b06ad.gif")
                    embed.add_field(name="Result...", value="Wait!", inline=False)
                    embed.set_footer(text="Technetium")
                    embed.timestamp = datetime.now()
                    msgToEdit = await ctx.send(embed=embed)
                    # Waits 3 seconds
                    await asyncio.sleep(3)
                    
                    # Gets heads or tails, and text + img url for respective choice
                    if random.randint(0,1) == 0:
                        cResult = "Heads!"
                        cImg = "https://images-na.ssl-images-amazon.com/images/I/51xs7F%2BtP5L._AC_.jpg"
                    else:
                        cResult = "Tails!"
                        cImg = "https://m.media-amazon.com/images/I/51NyMaKLydL._SL500_.jpg"
                    
                    # Edits existing embed
                    embed=discord.Embed(title="Flipped a coin!", description="Here's the result", color=0xddd736)
                    embed.set_thumbnail(url=cImg)
                    embed.add_field(name="Result...", value=cResult, inline=False)
                    embed.set_footer(text="Technetium", icon_url=iconUrl)
                    embed.timestamp = datetime.now()
                    await msgToEdit.edit(embed=embed)
                
                if str(cmdArgs[0]) == "num":
                    try:
                        # Sets both arguments to integers
                        ran1 = int(cmdArgs[1])
                        ran2 = int(cmdArgs[2])
                        print(ran1, ran2)

                        # Sets the numbers in order
                        if ran1 > ran2:
                            tempRan1 = ran1

                            ran1 = ran2
                            ran2 = tempRan1
                        
                        #print(ran1,ran2)

                        # Generates a random integer between the 2 bounds the user provided
                        ranReturn = random.randint(ran1, ran2)

                        # Creates and sends embed
                        e = discord.Embed(title="Random Number!", description=f"Generated between {ran1} and {ran2}.")
                        e.add_field(name="Result...",value=f"{ranReturn}!")
                        e.timestamp = datetime.now()
                        e.set_footer(text="Technetium", icon_url=iconUrl)

                        await ctx.channel.send(embed=e)
                    # Error handling
                    except IndexError:
                        await sendError(ctx, "Please enter 2 numbers!")
                    except ValueError:
                        await sendError(ctx, "Please enter a valid number.")
                    except BaseException: 
                        await sendError(ctx, "Unexpected error encountered.")

    @commands.command()
    async def dog(self, ctx):
        """
        Sends a random image of a dog, using the dog.ceo API.
        """
        # Gets json data from API
        dogReq = requests.get("https://dog.ceo/api/breeds/image/random")
        # Creates embed
        embed = discord.Embed(title="Dog!",description="Here's a random dog I found.")
        embed.set_footer(text="Provided by dog.ceo", icon_url=iconUrl)
        embed.timestamp = datetime.now()
        # Gets the image url from the json and sets it to the embed's image
        embed.set_image(url=dogReq.json()["message"])
        await ctx.channel.send(embed=embed)
    
    @commands.command()
    async def cat(self, ctx):
        """
        Sends a random image of a cat, using the thecatapi API.
        """
        # Gets json data from API
        catReq = requests.get("https://api.thecatapi.com/v1/images/search")
        # Creates embed
        embed = discord.Embed(title="Cat!",description="Here's a random cat I found.")
        # Gets the image url from the json and sets it to the embed's image
        embed.set_image(url=catReq.json()[0]["url"])
        embed.set_footer(text="Provided by thecatapi.com", icon_url=iconUrl)
        embed.timestamp = datetime.now()
        await ctx.channel.send(embed=embed)
    
    @commands.command()
    async def fox(self, ctx):
        """
        Sends a random image of a fox, using the randomfox.ca API.
        """

        # Gets json data from API
        foxReq = requests.get("https://randomfox.ca/floof/")
        # Creates embed
        embed = discord.Embed(title="Fox!",description="Here's a random fox I found.")
        # Gets the image url from the json and sets it to the embed's image
        embed.set_image(url=foxReq.json()["image"])
        embed.set_footer(text="Provided by randomfox.ca", icon_url=iconUrl)
        await ctx.channel.send(embed=embed)

    @commands.command(useage = "<number>")
    async def numfact(self,ctx,num):
        """
        Sends a random fact about a specified number, using the numbersapi API.
        """
        try:
            # Gets the trivia fact from the API as a string
            numReq = requests.get(f"http://numbersapi.com/{num},1")
            # Creates + sends the embed
            embed=discord.Embed(title=f"Number Fact for {num}!", description=numReq.json()[num])
            embed.set_footer(text="Provided by numbersapi.com", icon_url=iconUrl)
            embed.timestamp = datetime.now()
            await ctx.channel.send(embed=embed)
        # Error handling
        except BaseException: 
            await sendError(ctx, "Please enter a valid number!")

    @commands.command(usage = "<pokemon>")
    async def pokemon(self, ctx, pokemon):
        try:
            req = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon.lower()}")
            e = discord.Embed(title=f"{pokemon.title()}!",description=f"Here's a photo of {pokemon.title()}")
            e.set_image(url=req.json()["sprites"]["front_default"])
            
            e.set_footer(text="Technetium", icon_url=iconUrl)
            e.timestamp = datetime.now()

            await ctx.channel.send(embed=e)
        except BaseException: 
            await sendError(ctx, "Unexpected error encountered!")

    @commands.command()
    async def credits(self, ctx):
        e = discord.Embed(title="Credits",url="https://github.com/General-Mudkip/Technetium---Discord-Bot", description="Thanks for all the help!")

        e.add_field(name="Creator",value="Bence R.",inline = 0)
        e.add_field(name="Thanks to:",value="All my teachers and friends that helped debug and give feedback.")
        e.add_field(name="GitHub Repo",value="This bot is open source, so feel free to commit any changes you feel like to the repo!")

        e.set_thumbnail(url=iconUrl)

        e.set_footer(text="Technetium",icon_url=iconUrl)
        e.timestamp = datetime.now()

        await ctx.channel.send(embed=e)

# Adds all of the cogs (classes) to the bot
client.add_cog(utilityCog(client))
client.add_cog(moderationCog(client))
client.add_cog(funCog(client))
client.add_cog(stocksCog(client))

# Starts up the bot processes.
keep_alive()
# Gets the bot's token from the environment file. Stored in an .env file to stop public from accessing the token and gaining full access to it.
token = os.environ.get("DISCORD_TOKEN")
client.run(token)