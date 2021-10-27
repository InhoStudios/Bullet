import credentials
import discord
from icalendar import Calendar, Event
from datetime import datetime
from dateutil.parser import parse
from pytz import timezone, utc

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
        cmd = content.split('?')[1]
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
                    parseCalendar(cal)
            await chan.send(events)
                
def parseCalendar(gcal):
    for event in gcal.walk():
        if event.name == "VEVENT":
            title = event.get("summary")
            start_time = event.get("dtstart").dt
            end_time = event.get("dtend").dt
            repeat = event.get("rrule")['UNTIL']
            print(repeat)
            now = datetime.now(tz=utc).astimezone(timezone('America/Vancouver'))
            delta = start_time - now
            print(delta)
    return None

client.run(credentials.token)