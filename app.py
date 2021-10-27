import credentials
import discord
from icalendar import Calendar, Event
from datetime import datetime, timedelta
from dateutil.parser import parse
from pytz import UTC, timezone
from CalEvent import CalEvent
from DiscCalendar import DiscCalendar

client = discord.Client()

users = {}

@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    author = message.author
    content = message.content
    chan = message.channel
    attachments = message.attachments
    guild = message.guild

    if author == client.user:
        return
    
    if not str(author.id) in users:
        cal = DiscCalendar()
        users[str(author.id)] = cal

    if content.startswith('?'):
        cmd = content.split('?')[1]
        if cmd == "free":
            freeList = "The following users are free right now: "
            for user_key in users.keys():
                cal = users[user_key]
                if cal.checkFree():
                    freeList += "<@{}> ".format(user_key)
            await chan.send(freeList)
        if cmd == "update":
            await chan.send("Updating...")
            events = ""
            for attachment in attachments:
                filename = attachment.filename
                print(filename)
                if filename.endswith(".ics"):
                    cal = Calendar.from_ical(await attachment.read())
                    parseCalendar(cal, author.id)
            await chan.send("Thanks, <@{}>! Your calendar has been updated".format(author.id))
                
def parseCalendar(gcal, id):
    cal = users[str(id)]
    for event in gcal.walk():
        if event.name == "VEVENT":
            evt = CalEvent(event)
            cal.addEvent(evt)
    return None

client.run(credentials.token)
