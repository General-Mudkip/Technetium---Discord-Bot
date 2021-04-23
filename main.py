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

# Simple help command
class revisedHelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        e = discord.Embed(color=discord.Color.blurple(),
                          description='',
                          title="RemindMe!")
        e.set_footer(text="By Bence")
        e.timestamp = datetime.now()
        for page in self.paginator.pages:
            e.description += page
        await destination.send(embed=e)

# CONSTANTS

# Command prefix that the bot will use to recognise commands.
prefix = "."

# List of commands that fall under "random"
randomCommands = ["coin","number"]

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

# Client Setup
client = commands.Bot(command_prefix=prefix,
                      intents=discord.Intents.all(),
                      help_command=revisedHelpCommand())

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
        await ctx.channel.send("Hi!")

async def sendError(ctx, *error):
    """
    Handles sending error messages. Accepts the message context and the error message as an *arg.
    """

    # Constructs an embed object to be sent.
    embed = discord.Embed(title="Error encountered!",
                          description=" ".join(error),
                          color=0xFF4500)
    await ctx.channel.send(embed=embed)

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
                # Format time set
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
                embedSend.set_footer(text="By Bence")

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

    @commands.command(usage="<Message Count>")
    async def purge(self, ctx, count=None):
        """
        Purges a set amount of messages.
        """
        if count == None:
            await sendError(
                ctx, "Please enter the amount of messages you want to remove.")
        else:
            count = int(count)
            if count > 100:
                loopC = math.ceil(count/100)
                for i in range(loopC):
                    pass    
            else:
                await ctx.channel.purge(limit=count)


class utilityCog(commands.Cog, name="Utility"):
    """
    Some rather simple utility commands, aimed at improving quality of life.
    """
    @commands.command(usage="<Time Scale> <Time Period> [Reason}")
    async def remindme(self, ctx, timeScale, timePeriod, *reason):
        """
        Allows you to set reminders that you'll recieve in your DMs after the specified time!
        """
        author = ctx.message.author
        timeScale = int(timeScale)
        if timePeriod.lower() not in timeUnits:
            await sendError(
                ctx,
                "Invalid time period! Please chose from seconds (s), minutes (m), hours (h), days (d), weeks (w), months (mm)"
            )
        else:
            timeInc = timeUnits[timePeriod.lower()]["s"] * timeScale
            if timeInc > 315400000:
                await sendError(
                    ctx,
                    "Time period is too long! Must be less than 10 years.")
            else:
                timeToRemind = time.time() + timeInc

                if reason != () or reason != []:
                    reasonF = " ".join(reason)
                else:
                    reasonF = "None!"

                timeName = timeUnits[timePeriod.lower()]["n"]
                embed = discord.Embed(
                    title="Reminder Set!",
                    description=f"We'll remind you in {timeScale} {timeName}.")
                embed.add_field(name="Reason", value=reasonF, inline=False)
                embed.set_footer(text="By Bence")
                embed.timestamp = datetime.now()
                await ctx.channel.send(embed=embed)

                # Reminders stored as a string, due to DB shenanigans
                # (timeToRemind);(reason);(Author ID);(Time Set)
                reminderObj = f"{timeToRemind};{reasonF};{ctx.author.id};{time.time()}"
                db[str(len(db.keys()))] = reminderObj

class funCog(commands.Cog, name="Fun"):
    """
    Commands that don't necessarily serve a purpose or fit in any specific category. Give them a go!
    """
    @commands.command()
    async def random(self, ctx, *cmdArgs):
        if cmdArgs == ():
            ranCmdStr = ", ".join(randomCommands)
            await sendError(ctx, f"Please enter a valid generator, such as: {ranCmdStr}.")
        else:
            if str(cmdArgs[0]) not in randomCommands:
                ranCmdStr = ", ".join(randomCommands)
                await sendError(ctx, f"Please enter a valid generator, such as: {ranCmdStr}.")
            else:
                if str(cmdArgs[0]) == "coin":
                    embed=discord.Embed(title="Flipping a Coin!", description="Give it a second...", color=0xddd736)
                    embed.set_thumbnail(url="https://i.pinimg.com/originals/d7/49/06/d74906d39a1964e7d07555e7601b06ad.gif")
                    embed.add_field(name="Result...", value="Wait!", inline=False)
                    msgToEdit = await ctx.send(embed=embed)
                    await asyncio.sleep(3)
                    
                    if random.randint(0,1) == 0:
                        cResult = "Heads!"
                        cImg = "https://images-na.ssl-images-amazon.com/images/I/51xs7F%2BtP5L._AC_.jpg"
                    else:
                        cResult = "Tails!"
                        cImg = "https://m.media-amazon.com/images/I/51NyMaKLydL._SL500_.jpg"
                    embed=discord.Embed(title="Flipped a coin!", description="Here's the result", color=0xddd736)
                    embed.set_thumbnail(url=cImg)
                    embed.add_field(name="Result...", value=cResult, inline=False)
                    await msgToEdit.edit(embed=embed)


client.add_cog(utilityCog(client))
client.add_cog(moderationCog(client))
client.add_cog(funCog(client))

keep_alive()
token = os.environ.get("DISCORD_TOKEN")
client.run(token)