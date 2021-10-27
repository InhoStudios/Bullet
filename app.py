import credentials
import discord
from icalendar import Calendar
from CalEvent import CalEvent
from DiscCalendar import DiscCalendar
from datetime import datetime

client = discord.Client()

users = {}

@client.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.listening, name="?help")
    await client.change_presence(status=discord.Status.online, activity=activity)
    print('Logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    author = message.author
    content = message.content
    chan = message.channel
    attachments = message.attachments
    guild = message.guild

    print("{} in {}: {}".format(author.name, chan.name, content))

    if author == client.user:
        return

    if content.startswith('?'):
        now = datetime.now()
        cmd = content.split('?')[1]
        if cmd == "help":
            msg = "Hi! **Who** is here to help!\n" + \
                    "To get started, download your schedule as a `.ics` file. " \
                    "For UBC students, do this by accessing your timetable from your SSC and downloading as ical (.ics) file.\n" \
                    "Next, upload the .ics file and type `?update` to update your schedule. It will be saved to the system.\n" \
                    "To check who's free, type `?free`."
            await chan.send(msg)
        if cmd.startswith(" <@!"):
            uid = cmd.split(">")[0].replace(" <@!","")
            if uid in users.keys():
                cal = users[uid]
                await chan.send(parseEvents(cal.getCurrentEvents(now)))
            else:
                await chan.send("User is not in the system yet. Use ?update")
        if cmd == "events":
            uid = str(author.id)
            if uid in users.keys():
                cal = users[uid]
                await chan.send(parseEvents(cal.getAllEvents(now)))
            else:
                await chan.send("User is not in the system yet. Use ?update")
        if cmd == "free":
            freeList = "The following users are free right now: "
            for user_key in users.keys():
                # if guild.get_member(int(user_key)) != None:
                cal = users[user_key]
                if cal.checkFree(now):
                    freeList += "<@{}> ".format(user_key)
            await chan.send(freeList)
        if cmd == "update":
            if not str(author.id) in users:
                cal = DiscCalendar()
                users[str(author.id)] = cal

            if len(attachments) == 0:
                await chan.send("Please attach the .ics file in the ?update message")
                return
            await chan.send("Updating...")
            events = ""
            for attachment in attachments:
                filename = attachment.filename
                if filename.endswith(".ics"):
                    cal = Calendar.from_ical(await attachment.read())
                    parseCalendar(cal, author.id)
            await chan.send("Thanks, <@{}>! Your calendar has been updated".format(author.id))

def parseEvents(curEvts):
    evtMsg = ""
    for event in curEvts:
        details = event.getDetails()
        msgStr = "{}: {} - ({} - {})".format(details['day'], details['title'], details['start'], details['end'])
        evtMsg += msgStr + "\n"
    if evtMsg == "":
        evtMsg = "There are no events to display."
    return evtMsg

def parseCalendar(gcal, id):
    cal = users[str(id)]
    cal = DiscCalendar()
    for event in gcal.walk():
        if event.name == "VEVENT":
            evt = CalEvent(event)
            cal.addEvent(evt)
    return None

client.run(credentials.token)
