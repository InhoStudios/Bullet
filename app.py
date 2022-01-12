from os.path import join, exists
from os import listdir, remove

import credentials, globals

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

    if content.startswith(globals.prefix) or content.startswith(globals.prefix_who):
        tz = ptz("America/Vancouver")
        now = tz.localize(datetime.now())
        state = globals.prefix
        # if str(now.astimezone().tzinfo) == "PST" or str(now.astimezone().tzinfo) == "Pacific Standard Time":
        #     now = now - timedelta(hours=1)
        if content.startswith(globals.prefix):
            call = content.split(globals.prefix)[1]
        else:
            call = content.split(globals.prefix_who)[1]
            state = globals.prefix_who
        if call.startswith(globals.help):
            title = "Hi! Who is here to help!"
            desc = "To get started, download your schedule as a `.ics` file. " \
                    "For UBC students, do this by accessing your timetable from your SSC and downloading as ical (.ics) file.\n" \
                    "Next, upload the .ics file and type `?update` to update your schedule. It will be saved to the system.\n\n"
            embed = discord.Embed(title=title, description=desc)
            embed.add_field(name="?update", value="Updates your current calendar (please attach a valid .ics file)")
            embed.add_field(name="?free", value="Checks who's free at the moment. Type `?free HH:MM` to see whos free at a given time.")
            embed.add_field(name="?events (@[user])", value="Lists all of your events. If a user is mentioned, their events will be listed instead")
            embed.add_field(name="? @[user]", value="Lists what event @[user] is currently attending. Type `? @[user] HH:MM` to see if that user is free at a given time.")
            embed.add_field(name="?busy", value="Toggles your status (Available / Busy)")
            embed.add_field(name="?status (@[user])", value="Shows your current status. If a user is mentioned their status is shown instead")
            embed.set_footer(text="Made with ❤️ by InhoStudios")
            await chan.send(embed=embed)
        if call.startswith(" <@!"):
            uid = call.split(">")[0].replace(" <@!","")
            checkDT = now
            time = call.split(">")[1].replace(" ","")

            if time != "":
                try:
                    checkDT = parseTime(time, now)
                    print(str(checkDT))
                except:
                    await chan.send("Check a time with `@[user] HH:MM`")
                    return

            if uid in users.keys():
                cal = users[uid]
                user = client.get_user(int(uid))
                await chan.send(embed=parseEvents(cal.getCurrentEvents(checkDT), user, cal.getStatus()))
            else:
                await chan.send("User is not in the system yet. Use ?update")
        if call.startswith(globals.status):
            usr = getParameters(call, globals.status).replace(" ","")
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
                    usr = usr.split(">")[0]
                    if usr in users.keys():
                        cal = users[usr]
                        if cal.getStatus():
                            msg = "🟡 Busy"
                        else:
                            msg = "🟢 Available"
                        await chan.send(msg)
                    else:
                        await chan.send("User is not in the system yet. Use ?update")
                except:
                    await chan.send("Please tag a user")
        if call.startswith(globals.events):
            params = getParameters(call, globals.events)
            checked_id = authid
            user = author
            if params != "":
                try:
                    checked_id = params.replace(" <@!","").replace(">","")
                    user = client.get_user(int(checked_id))
                except:
                    await chan.send("Please mention a user")
                    return

            if checked_id in users.keys():
                cal = users[checked_id]
                embed = parseEvents(cal.getAllEvents(now), user, cal.getStatus())
                await chan.send(embed=embed)
            else:
                await chan.send("User is not in the system yet. Use ?update")
        if call.startswith(globals.free):
            checked_time = "right now"

            checkDT = now
            params = getParameters(call, globals.free)
            if params != "":
                try:
                    time = params.replace(" ","")
                    checkDT = parseTime(time, now)
                    checked_time = "at " + checkDT.strftime("%H:%M on %A, %b %d")
                    print(str(checkDT))
                except:
                    pass
            head = ""
            freeList = head
            upcomingList = head
            for user_key in users.keys():
                if guild.get_member(int(user_key)) != None:
                    cal = users[user_key]
                    if cal.checkFree(checkDT):
                        freeList += "<@{}> ".format(user_key)
                    elif cal.checkFree(checkDT + timedelta(hours=1)):
                        upcomingList += "<@{}>".format(user_key)
            if freeList == head:
                freeList = "Sorry, nobody seems to be free {} :(".format(checked_time)
            embed = discord.Embed(title="These people are free {}!".format(checked_time), description=freeList)
            if upcomingList != head:
                embed.add_field(name="and these people will be free in the next hour", value=upcomingList)
            await chan.send(embed=embed)
        if call.startswith(globals.update):
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
        if call.startswith(globals.busy):
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
        if call.startswith(globals.now):
            checkDT = now
            params = getParameters(call, globals.now)
            if params != "":
                try:
                    time = params.replace(" ","")
                    checkDT = parseTime(time, now)
                    print(str(checkDT))
                except:
                    pass
            await chan.send("The current time is " + str(checkDT) +
                            "\nThe timezone is " + str(checkDT.astimezone().tzinfo))

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
        embed.description = "This user is free!"
    if status:
        embed.color = 0xFFAA00
        embed.description = "This user is busy :("
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

def getParameters(msg, command):
    try:
        return msg.split(command)[1]
    except:
        return ""

# PRE: Time string in the format HH:MM, datetime to be modified
# POST: Returns a datetime with updated hours
def parseTime(time, now):
    cur_time = datetime.strptime(time, "%H:%M")
    parsed_time = now.replace(hour=cur_time.hour, minute=cur_time.minute)
    # check if hour is less than today
    if now.hour > cur_time.hour:
        parsed_time = parsed_time + timedelta(days=1)
    if cur_time.hour < 8:
        parsed_time = parsed_time + timedelta(hours=12)
    return parsed_time


client.run(credentials.token)
