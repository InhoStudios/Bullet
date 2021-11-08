from os.path import join, exists
from os import listdir, remove

import credentials
import discord
from icalendar import Calendar
from CalEvent import CalEvent
from DiscCalendar import DiscCalendar
from datetime import datetime, timezone, timedelta
from pytz import timezone as ptz

CAL_FOLDER = './calendars/'

intents = discord.Intents().all()
client = discord.Client(intents=intents)

users = {}

@client.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.listening, name="?help")
    await client.change_presence(status=discord.Status.online, activity=activity)
    print('Logged in as {0.user}'.format(client))
    #TODO: load all .ics files from directory
    cals = listdir(CAL_FOLDER)
    for calfile in cals:
        filename = join(CAL_FOLDER, calfile)
        uid = calfile.split('.')[0]
        file = open(filename, 'rb')
        calendar = Calendar.from_ical(file.read())
        parseCalendar(calendar, uid)
        file.close()

@client.event
async def on_message(message):
    author = message.author
    authid = str(author.id)
    content = message.content
    chan = message.channel
    attachments = message.attachments
    guild = chan.guild

    print("{} in {}: {}".format(author.name, chan.name, content))

    if author == client.user:
        return

    if content.startswith('?'):
        tz = ptz("America/Vancouver")
        now = tz.localize(datetime.now())
        if str(now.astimezone().tzinfo) == "PST":
            now = now - timedelta(hours=1)
        cmd = content.split('?')[1]
        if cmd == "help":
            title = "Hi! Who is here to help!"
            desc = "To get started, download your schedule as a `.ics` file. " \
                    "For UBC students, do this by accessing your timetable from your SSC and downloading as ical (.ics) file.\n" \
                    "Next, upload the .ics file and type `?update` to update your schedule. It will be saved to the system.\n\n"
            embed = discord.Embed(title=title, description=desc)
            embed.add_field(name="?update", value="Updates your current calendar (please attach a valid .ics file)")
            embed.add_field(name="?free", value="Checks who's free at the moment")
            embed.add_field(name="?events", value="Lists all of your events")
            embed.add_field(name="? @[user]", value="Lists what event @[user] is currently attending")
            embed.add_field(name="?busy", value="Toggles your status (Available / Busy)")
            embed.add_field(name="?status (@[user])", value="Shows your current status. If a user is mentioned their status is shown instead")
            embed.set_footer(text="Made with ❤️ by InhoStudios")
            await chan.send(embed=embed)
        if cmd.startswith(" <@!"):
            uid = cmd.split(">")[0].replace(" <@!","")
            if uid in users.keys():
                cal = users[uid]
                user = client.get_user(int(uid))
                await chan.send(embed=parseEvents(cal.getCurrentEvents(now), user, cal.getStatus()))
            else:
                await chan.send("User is not in the system yet. Use ?update")
        if cmd.startswith("status"):
            usr = cmd.replace("status","").replace(" ","")
            msg = ""
            if usr == "":
                if authid in users.keys():
                    cal = users[authid]
                    if cal.getStatus():
                        msg = "🟡 Busy"
                    else:
                        msg = "🟢 Available"
                    await chan.send(msg)
                else:
                    await chan.send("User is not in the system yet. Use ?update")
            else:
                try:
                    usr = usr.split("<@!")[1]
                    usr = usr.split(">")[1]
                    if authid in users.keys():
                        cal = users[authid]
                        if cal.getStatus():
                            msg = "🟡 Busy"
                        else:
                            msg = "🟢 Available"
                        await chan.send(msg)
                    else:
                        await chan.send("User is not in the system yet. Use ?update")
                except:
                    await chan.send("Please tag a user")
        if cmd == "events":
            if authid in users.keys():
                cal = users[authid]
                await chan.send(embed=parseEvents(cal.getAllEvents(now), author, cal.getStatus()))
            else:
                await chan.send("User is not in the system yet. Use ?update")
        if cmd == "free":
            head = ""
            freeList = head
            for user_key in users.keys():
                if guild.get_member(int(user_key)) != None:
                    cal = users[user_key]
                    if cal.checkFree(now):
                        freeList += "<@{}> ".format(user_key)
            if freeList == head:
                freeList = "Sorry, nobody seems to be free right now :("
            embed = discord.Embed(title="The following users are free:", description=freeList)
            await chan.send(embed=embed)
        if cmd == "update":
            if len(attachments) == 0:
                await chan.send("Please attach the .ics file in the ?update message")
                return
            for attachment in attachments:
                filename = attachment.filename
                if filename.endswith(".ics"):
                    await attachment.save(CAL_FOLDER + str(author.id) + ".ics")
                    cal = Calendar.from_ical(await attachment.read())
                    parseCalendar(cal, str(author.id))
            await chan.send("Thanks, {}! Your calendar has been updated".format(author.display_name))
        if cmd == "busy":
            if authid in users.keys():
                cal = users[authid]
                cal.toggleBusy()
                msg = "Gotcha {}! Your status is updated: ".format(author.name)
                if cal.getStatus():
                    msg += "Busy"
                else:
                    msg += "Free"
                await chan.send(msg)
            else:
                await chan.send("User is not in the system yet. Use ?update")
        if cmd == "now":
            await chan.send("The current time is " + str(now))

def parseEvents(curEvts, user, status):
    embed = discord.Embed(title="Calendar")
    embed.set_author(name=user.display_name, icon_url=user.avatar_url)
    for event in curEvts:
        details = event.getDetails()
        embed.add_field(name=details['title'], value=details['day'], inline=False)
        embed.add_field(name="Start:", value=details['start'], inline=True)
        embed.add_field(name="End:", value=details['end'], inline=True)
        embed.add_field(name="Location:", value=details['location'], inline=True)
    if len(curEvts) == 0:
        embed.description = "There are no events to display"
    if status:
        embed.color = 0xFFAA00
    else:
        embed.color = 0x00FF00
    return embed

def parseCalendar(gcal, id):
    users[id] = None
    cal = DiscCalendar()
    for event in gcal.walk():
        if event.name == "VEVENT":
            evt = CalEvent(event)
            cal.addEvent(evt)
    users[id] = cal

client.run(credentials.token)
