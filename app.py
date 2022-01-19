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
        try:
            uid = uid.split('_')[0]
        except:
            pass
        file = open(filename, 'rb')
        calendar = Calendar.from_ical(file.read())
        addCalEvents(calendar, uid)
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
        cmd_parameters = getParameters(content)
        if call.startswith(globals.help):
            title = "Hi! Who is here to help!"
            desc = "To get started, download your schedule as a `.ics` file. " \
                    "For UBC students, do this by accessing your timetable from your SSC and downloading as ical (.ics) file.\n" \
                    "Next, upload the .ics file and type `?update` to update your schedule. It will be saved to the system.\n\n"
            embed = discord.Embed(title=title, description=desc)
            embed.add_field(name="?free (hh:mm)", value="Checks who's free right now. Specify a time to see whos free at a given time.")
            embed.add_field(name="?events (@[user]) (page)", value="Lists all of the users events. Show more pages by specifying the page number")
            embed.add_field(name="? @[user] (hh:mm)", value="Lists what event @[user] is currently attending. Specify a time check that time instead.")
            embed.add_field(name="?upcoming (hh:mm))", value="Shows what events are happening in the next hour (or at the specified time).")
            embed.add_field(name="?busy", value="Toggles your status (Available / Busy)")
            embed.add_field(name="?status (@[user])", value="Shows your current status. If a user is mentioned their status is shown instead")
            embed.add_field(name="?update", value="Updates your current calendar. Resets all previously added calendars. (Please attach a valid .ics file)")
            embed.add_field(name="?add", value="Adds a concurrent calendar to your schedule (Please attach a valid .ics file)")
            embed.add_field(name="Want to add Who to your own server?", value="Click [here](https://discord.com/api/oauth2/authorize?client_id=900540913053499472&permissions=8&scope=bot) to add the bot, or contact `inho#7094` for more details!", inline=False)
            embed.set_footer(text="Made with ❤️ by InhoStudios")
            await chan.send(embed=embed)
            return
        if call.startswith(globals.status):
            usr = authid
            if message.mentions:
                usr = str(message.mentions[0].id)
            msg = ""
            if usr in users.keys():
                cal = users[usr]
                if cal.getStatus():
                    msg = "🟡 Busy"
                else:
                    msg = "🟢 Available"
                await chan.send(msg)
            else:
                await chan.send("User is not in the system yet. Use ?update")
            return
        if call.startswith(globals.events):
            # SET DEFAULT PARAMETERS
            checked_id = authid
            user = author
            page_num = 1
            # PARSE PARAMETERS
            if message.mentions:
                checked_id = str(message.mentions[0].id)
            
            try:
                page_num = int(cmd_parameters[-1])
            except:
                pass
            
            if checked_id in users.keys():
                cal = users[checked_id]
                evt_page, tot_pages = cal.getEventPage(now, page_num)
                if page_num > tot_pages:
                    page_num = tot_pages
                embed = parseEvents(evt_page, user, cal.getStatus())
                embed.set_footer(text="Page " + str(page_num) + "/" + str(tot_pages))
                await chan.send(embed=embed)
            else:
                await chan.send("User is not in the system yet. Use ?update")
            return
        if call.startswith(globals.free):
            checked_time = "right now"

            check_dt = now
            if len(cmd_parameters) > 0:
                for param in cmd_parameters:
                    if param != "at":
                        check_dt = parseTime(param, now)
                        checked_time = "at " + check_dt.strftime("%H:%M on %A, %b %d")
                        print(str(check_dt))

            head = ""
            freeList = head
            upcomingList = head
            for user_key in users.keys():
                if guild.get_member(int(user_key)) != None:
                    cal = users[user_key]
                    if cal.checkFree(check_dt):
                        freeList += "<@{}> ".format(user_key)
                    elif cal.checkFree(check_dt + timedelta(hours=1)):
                        upcomingList += "<@{}> ".format(user_key)
            if freeList == head:
                freeList = "Sorry, nobody seems to be free {} :(".format(checked_time)
            embed = discord.Embed(title="These people are free {}!".format(checked_time), description=freeList)
            if upcomingList != head:
                embed.add_field(name="and these people will be free in the hour after", value=upcomingList)
            await chan.send(embed=embed)
            return
        if call.startswith(globals.update):
            if len(attachments) == 0:
                await chan.send("Please attach the .ics file in the ?update message")
                return
            for attachment in attachments:
                filename = attachment.filename
                if filename.endswith(".ics"):
                    FILE_PATH = CAL_FOLDER + str(author.id) + ".ics"
                    save_file = FILE_PATH
                    # Remove previous calendars
                    cals = listdir(CAL_FOLDER)
                    for calfile in cals:
                        filename = join(CAL_FOLDER, calfile)
                        uid = calfile.split('.')[0]
                        try:
                            uid = uid.split("_")[0]
                        except:
                            pass
                        if uid == str(author.id):
                            remove(filename)
                    # Save current calendar file
                    await attachment.save(save_file)

                    cal = Calendar.from_ical(await attachment.read())
                    parseCalendar(cal, str(author.id))
            await chan.send("Thanks, {}! Your calendar has been updated. Type ?events to see them!".format(author.display_name))
            return
        if call.startswith(globals.add):
            if len(attachments) == 0:
                await chan.send("Please attach the .ics file in the ?update message")
                return
            for attachment in attachments:
                filename = attachment.filename
                if filename.endswith(".ics"):
                    FILE_PATH = join(CAL_FOLDER, str(author.id) + ".ics")
                    save_file = FILE_PATH + ""
                    i = 1
                    while exists(save_file):
                        print(save_file)
                        save_file = join(CAL_FOLDER, str(author.id) + "_" + str(i) + ".ics")
                        i += 1
                    await attachment.save(save_file)
                    cal = Calendar.from_ical(await attachment.read())
                    addCalEvents(cal, str(author.id))
            await chan.send("Thanks, {}! New events have been added to your calendar. Type ?events to see them!".format(author.display_name))
            return
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
            return
        if call.startswith(globals.now):
            checkDT = now
            if len(cmd_parameters) > 0:
                time = cmd_parameters[0]
                print(time)
                try:
                    checkDT = parseTime(time, now)
                    print(str(checkDT))
                except:
                    pass
            await chan.send("The current time is " + str(checkDT) +
                            "\nThe timezone is " + str(checkDT.astimezone().tzinfo))
        if call.startswith(globals.upcoming):
            checked_time = "right now"
            check_dt = now + timedelta(hours=1)
            has_events = False
            if len(cmd_parameters) > 0:
                for param in cmd_parameters:
                    if param != "at":
                        check_dt = parseTime(param, now)
                        checked_time = "at " + check_dt.strftime("%H:%M on %A, %b %d")
            for user_key in users.keys():
                if guild.get_member(int(user_key)) != None:
                    cal = users[user_key]
                    if not cal.checkFree(check_dt):
                        has_events = True
                        user = guild.get_member(int(user_key))
                        embed = parseEvents(cal.getCurrentEvents(check_dt), user, cal.getStatus())
                        await chan.send(embed=embed)
            if not has_events:
                await chan.send(embed=discord.Embed(title="It seems there are no events upcoming!", description="There are no events happening {}".format(checked_time)))

                    
        if call.startswith(" <@!"):
            uid = str(message.mentions[0].id)
            checkDT = now
            if len(cmd_parameters) > 1:
                time = cmd_parameters[2]
                try:
                    checkDT = parseTime(time, now)
                except:
                    await chan.send("Check a time with `@[user] HH:MM`")
                    return

            if uid in users.keys():
                cal = users[uid]
                user = client.get_user(int(uid))
                await chan.send(embed=parseEvents(cal.getCurrentEvents(checkDT), user, cal.getStatus()))
            else:
                await chan.send("User is not in the system yet. Use ?update")

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

# PRE: Takes in a new icalendar object and a user ID
# POST: Creates new calendar and populates it with events
def parseCalendar(gcal, id):
    users[id] = None
    cal = DiscCalendar()
    users[id] = cal
    addCalEvents(gcal, id)

def addCalEvents(gcal, id):
    try:
        cal = users[id]
    except:
        cal = DiscCalendar()
        users[id] = cal
    for event in gcal.walk():
        if event.name == "VEVENT":
            evt = CalEvent(event)
            cal.addEvent(evt)
    users[id] = cal

def getParameters(msg):
    try:
        return msg.split(" ")[1:]
    except:
        return []

# PRE: Time string in the format HH:MM, datetime to be modified
# POST: Returns a datetime with updated hours
def parseTime(time, now):
    try:
        cur_time = datetime.strptime(time, "%H")
        cur_time = cur_time.replace(minute=0) 
    except:
        cur_time = datetime.strptime(time, "%H:%M")
    parsed_time = now.replace(hour=cur_time.hour, minute=cur_time.minute)
    # check if hour is less than today
    if cur_time.hour < 8:
        parsed_time = parsed_time + timedelta(hours=12)
    if now > parsed_time:
        parsed_time = parsed_time + timedelta(days=1)
    return parsed_time


client.run(credentials.token)
