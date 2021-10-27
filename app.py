import credentials
import discord
from icalendar import Calendar, Event
from datetime import datetime
from pytz import UTC

client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    author = message.author
    content = message.content
    chan = message.channel
    attachments = message.attachments

    if author == client.user:
        return


    if content.startswith('?'):
        cmd = content.split('?')[0]
        if cmd == "free":
            #TODO: Implement calendar checking
            print('do something')
        if cmd == "update":
            await chan.send("Updating...")
            events = ""
            for attachment in attachments:
                filename = attachment.filename
                print(filename)
                if filename.endswith(".ics"):
                    cal = Calendar.from_ical(await attachment.read())
                    for component in cal.walk():
                        if component.name == "VEVENT":
                            events += component.get("summary") + "\n"
            await chan.send(events)
                
def createCalendar(gcal):
    for component in gcal.walk():
        if component.name == "VEVENT":
            # handle each event

client.run(credentials.token)