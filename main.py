from discord.ext import commands, tasks
import discord
import os
from stayin_alive import keep_alive
import time
from datetime import datetime
import asyncpg
from replit import db
import math


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


prefix = "."

# Client Setup
client = commands.Bot(command_prefix=prefix,
                      intents=discord.Intents.all(),
                      help_command=revisedHelpCommand())

# Constants
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

@client.event
async def on_ready():
    print("Ready to go!")


@client.event
async def on_message(ctx):
    await client.process_commands(ctx)
    if ctx.content == "Hello!":
        await ctx.channel.send("Hi!")


async def sendError(ctx, *error):
    embed = discord.Embed(title="Error encountered!",
                          description=" ".join(error),
                          color=0xFF4500)
    await ctx.channel.send(embed=embed)


class loopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data = []
        self.batch_update.add_exception_type(asyncpg.PostgresConnectionError)
        self.batch_update.start()

    def cog_unload(self):
        self.batch_update.cancel()

    @tasks.loop(seconds=1.0)
    async def batch_update(self):
        for i in db.keys():
            val = db[i]
            valList = val.split(";")
            ttr = float(valList[0])
            reminder = valList[1]
            authorID = valList[2]
            timeSet = valList[3]
            if ttr > time.time():
                print("Skipped.")
            elif ttr <= time.time():
                dateTimeObj = datetime.utcfromtimestamp(float(timeSet))
                timestampStr = dateTimeObj.strftime(
                    "%d of %B, %Y, at %I%p, %Mm, %Ss (UTC)")

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

                userObj = await client.fetch_user(int(authorID))
                await userObj.send(embed=embedSend)
                del db[i]


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


client.add_cog(utilityCog(client))
client.add_cog(moderationCog(client))

keep_alive()
token = os.environ.get("DISCORD_TOKEN")
client.run(token)