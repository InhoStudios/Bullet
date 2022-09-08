from os.path import join, exists
from os import listdir, remove

import credentials, globals

import discord
from datetime import datetime, timedelta
from calendar import day_name
from pytz import timezone
import requests, json

from bulletin import Calendar

CAL_FOLDER = './calendars/'
WEATHER_BASE_URL = f'http://api.openweathermap.org/data/2.5/weather?appid={credentials.weather_api_key}&lat=49.26&lon=-123.25'

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
        # get user_id from calendar file
        filename = join(CAL_FOLDER, calfile)
        uid = calfile.split('.')[0]
        try:
            uid = uid.split('_')[0]
        except:
            pass
        # open file
        file = open(filename, 'r')
        # create new calendar to save object into
        if uid in users.keys():
            user_cal = users[uid]
        else:
            user_cal = Calendar()
            users[uid] = user_cal
        try:
            user_cal.import_calendar(file.read())
        except:
            pass
        file.close()

@client.event
async def on_message(message):
    # get information
    author = message.author
    authid = str(author.id)
    content = message.content
    chan = message.channel
    attachments = message.attachments
    guild = chan.guild

    print("{} in {}: {}".format(author.name, chan.name, content))

    # skip running if it's a bot message
    if author == client.user:
        return

    if content.startswith(globals.prefix) or content.startswith(globals.prefix_who):
        now = datetime.now().astimezone()
        state = globals.prefix
        if content.startswith(globals.prefix):
            call = content.split(globals.prefix)[1]
        else:
            call = content.split(globals.prefix_who)[1]
            state = globals.prefix_who
        cmd_parameters = get_parameters(call)
        if call.startswith(globals.help):
            title = "Hey, I'm Bullet! I'm here to help!"
            desc = "To get started, download your schedule as a `.ics` file. " \
                    "For UBC students, do this by accessing your timetable from your SSC and downloading as ical (.ics) file.\n" \
                    "Next, upload the .ics file and type `?update` to update your schedule. It will be saved to the system.\n\n"
            embed = discord.Embed(title=title, description=desc)
            embed.add_field(name="?free (hh:mm)", value="Checks who's free right now. Specify a time to see whos free at a given time.")
            embed.add_field(name="?events (@[user]) (week)", value="Lists all of the users events. Show future weeks by specifying how many weeks ahead to look")
            embed.add_field(name="? @[user] (hh:mm)", value="Lists what event @[user] is currently attending. Specify a time check that time instead.")
            embed.add_field(name="?upcoming (hh:mm)", value="Shows what events are happening in the next hour (or at the specified time).")
            embed.add_field(name="?toggle", value="Toggles your status (Available / Busy)")
            embed.add_field(name="?status (@[user])", value="Shows your current status. If a user is mentioned their status is shown instead")
            embed.add_field(name="?update", value="Updates your current calendar. Resets all previously added calendars. (Please attach a valid .ics file)")
            embed.add_field(name="?add", value="Adds a concurrent calendar to your schedule (Please attach a valid .ics file)")
            embed.add_field(name="?weather", value="Shows the weather on UBC campus")
            embed.add_field(name="Want to add Bullet to your own server?", value="Click [here](https://discord.com/api/oauth2/authorize?client_id=900540913053499472&permissions=8&scope=bot) to add the bot, or contact `inho#7094` for more details!", inline=False)
            embed.set_footer(text="Made with ❤️ by InhoStudios")
            await chan.send(embed=embed)
            return
        if call.startswith(globals.status):
            user_id = authid
            if message.mentions:
                user_id = str(message.mentions[0].id)
            msg = ""
            if user_id in users.keys() and client.get_user(int(uid)) in chan.members:
                cal = users[user_id]
                if cal.get_status():
                    msg = "🟡 Busy"
                else:
                    msg = "🟢 Available"
                await chan.send(msg)
            else:
                await chan.send("Unknown user.")
            return
        if call.startswith(globals.events):
            # SET DEFAULT PARAMETERS
            id_to_check = authid
            weeks = 0
            # PARSE PARAMETERS
            if message.mentions:
                id_to_check = str(message.mentions[0].id)
            
            user = client.get_user(int(id_to_check))
            
            try:
                weeks = int(cmd_parameters[-1])
            except:
                pass
            
            if id_to_check in users.keys():
                if user in chan.members:
                    cal = users[id_to_check]
                    date_to_check = datetime.now() + timedelta(days=7*weeks)
                    evt_page = cal.get_week(date_to_check)
                    
                    sunday = date_to_check - timedelta(days=date_to_check.weekday() + 1)
                    saturday = sunday + timedelta(days=6)
                    embed = create_week_embed(evt_page, user, cal.get_status())
                    embed.set_footer(text="From {} to {}".format(sunday.strftime("%d %B"), saturday.strftime("%d %B")))
                    await chan.send(embed=embed)
                else:
                    await chan.send("User does not have access to this channel.")
            else:
                await chan.send("User is not in the system yet. Use ?update")
            return
        if call.startswith(globals.free):
            checked_time = "right now"

            check_dt = now
            if len(cmd_parameters) > 0:
                for param in cmd_parameters:
                    if param != "at":
                        check_dt = parse_time(param, now)
                        checked_time = "at " + check_dt.strftime("%H:%M on %A, %b %d")
                        print(str(check_dt))

            head = ""
            freeList = head
            upcomingList = head
            for member in chan.members:
                user_key = str(member.id)
                print(user_key)
                if user_key in users.keys():
                    cal = users[user_key]
                    if cal.is_free(check_dt):
                        freeList += "<@{}> ".format(user_key)
                    elif cal.is_free(check_dt + timedelta(hours=1)):
                        upcomingList += "<@{}> ".format(user_key)
            # for user_key in users.keys():
            #     if guild.get_member(int(user_key)) != None:
            #         cal = users[user_key]
            #         if cal.is_free(check_dt):
            #             freeList += "<@{}> ".format(user_key)
            #         elif cal.is_free(check_dt + timedelta(hours=1)):
            #             upcomingList += "<@{}> ".format(user_key)
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
                auth_id = str(author.id)
                if filename.endswith(".ics"):
                    FILE_PATH = CAL_FOLDER + auth_id + ".ics"
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
                        if uid == auth_id:
                            remove(filename)
                    # Save current calendar file
                    await attachment.save(save_file)
                    cal = Calendar()
                    with open(save_file, 'r') as f: 
                        try:
                            cal.import_calendar(f.read())
                        except:
                            pass
                    users[auth_id] = cal
            await chan.send("Thanks, {}! Your calendar has been updated.".format(author.display_name))
            return
        if call.startswith(globals.add):
            if len(attachments) == 0:
                await chan.send("Please attach the .ics file in the ?update message")
                return
            for attachment in attachments:
                filename = attachment.filename
                if filename.endswith(".ics"):
                    FILE_PATH = join(CAL_FOLDER, str(authid) + ".ics")
                    save_file = FILE_PATH + ""
                    i = 1
                    while exists(save_file):
                        print(save_file)
                        save_file = join(CAL_FOLDER, str(authid) + "_" + str(i) + ".ics")
                        i += 1
                    await attachment.save(save_file)
                    try:
                        cal = users[authid]
                    except:
                        cal = Calendar()
                        users[authid] = cal
                    with open(save_file, 'r') as f:
                        cal.import_calendar(f.read())
            await chan.send("Thanks, {}! New events have been added to your calendar. Type ?events to see them!".format(author.display_name))
            return
        if call.startswith(globals.toggle):
            if authid in users.keys():
                cal = users[authid]
                cal.toggle_status()
                msg = "Gotcha {}! Your status is updated: ".format(author.display_name)
                if cal.get_status():
                    msg += "Busy"
                else:
                    msg += "Free"
                await chan.send(msg)
            else:
                await chan.send("User is not in the system yet. Use ?update")
            return
        if call.startswith(globals.now):
            checkDT = now
            if authid in users.keys():
                tz = users[authid].timezone
            else:
                tz = timezone("America/Vancouver")
            if len(cmd_parameters) > 0:
                time = cmd_parameters[0]
                print(time)
                try:
                    checkDT = parse_time(time, now)
                    print(str(checkDT))
                except:
                    pass
            await chan.send("The current time is " + str(checkDT.astimezone(tz).strftime("%H:%M on %A, %b %d")) +
                            "\nThe timezone is " + str(checkDT.astimezone(tz).tzinfo))
        if call.startswith(globals.upcoming):
            checked_time = "right now"
            check_dt = now + timedelta(hours=1)
            has_events = False
            if len(cmd_parameters) > 0:
                for param in cmd_parameters:
                    if param != "at":
                        check_dt = parse_time(param, now)
                        checked_time = "at " + check_dt.strftime("%H:%M on %A, %b %d")
            for user_key in users.keys():
                if guild.get_member(int(user_key)) != None:
                    cal = users[user_key]
                    if not cal.is_free(check_dt):
                        has_events = True
                        user = guild.get_member(int(user_key))
                        embed = create_events_embed(cal.get_occurring(check_dt), user, cal.get_status(), title="Upcoming events")
                        await chan.send(embed=embed)
            if not has_events:
                await chan.send(embed=discord.Embed(title="It seems there are no events upcoming!", description="There are no events happening {}".format(checked_time)))
             
        if call.startswith(" <@"):
            uid = str(message.mentions[0].id)
            checkDT = now
            if len(cmd_parameters) > 1:
                time = cmd_parameters[2]
                try:
                    checkDT = parse_time(time, now)
                except:
                    await chan.send("Check a time with `@[user] HH:MM`")
                    return

            if uid in users.keys():
                cal = users[uid]
                user = client.get_user(int(uid))
                if user in chan.members:
                    await chan.send(embed=create_events_embed(cal.get_occurring(checkDT), user, cal.get_status(), "Current event"))
                else:
                    await chan.send("User does not have access to this channel.")
            else:
                await chan.send("User is not in the system yet.")
        if call.startswith("weather"):
            await chan.send(get_current_weather())

def create_week_embed(events, user, status, title="Schedule"):
    embed = discord.Embed(title=title)
    embed.set_author(name=user.display_name, icon_url=user.avatar_url)
    weekday_vals = ["", "", "", "", "", "", ""]
    timezone = users[str(user.id)].timezone
    embed.description = "Timezone: {}".format(timezone)
    for event in events:
        for interval in event.intervals:
            start_time = interval[0].astimezone(timezone).strftime("%H:%M")
            end_time = interval[1].astimezone(timezone).strftime("%H:%M")
            weekday_vals[int(interval[0].weekday())] = weekday_vals[int(interval[0].weekday())] + "```{}\n{}-{}```".format(event.summary, start_time, end_time)
    for i in range(len(weekday_vals)):
        if (weekday_vals[i] == ""):
            weekday_vals[i] = "No events to display."
        name = day_name[i]
        if (datetime.now().weekday() == i):
            name = "[   " + name + "   ]"
        embed.add_field(name=name, value=weekday_vals[i])
    if len(events) == 0:
        embed.color = 0x00FF00
        embed.description = "This user is free!"
    if status:
        embed.color = 0xFFAA00
        embed.description = "This user is busy"
    return embed


def create_events_embed(events, user, status, title="Calendar"):
    embed = discord.Embed(title=title)
    embed.set_author(name=user.display_name, icon_url=user.avatar_url)
    timezone = users[str(user.id)].timezone
    for event in events:
        date = event.intervals[0]
        date_str = date[0].astimezone(timezone).strftime("%A %d %B, %Y")
        start_time = date[0].astimezone(timezone).strftime("%H:%M")
        end_time = date[1].astimezone(timezone).strftime("%H:%M")
        location = ""
        if event.location != "":
            location = "\nLocation: {}".format(event.location)
        embed.add_field(name=event.summary, value="```{}\n{}-{}{}```".format(date_str, start_time, end_time, location), inline=False)
    if len(events) == 0:
        embed.color = 0x00FF00
        embed.description = "This user is free!"
    if status:
        embed.color = 0xFFAA00
        embed.description = "This user is busy"
    return embed

def get_parameters(msg):
    try:
        return msg.split(" ")[1:]
    except:
        return []

# PRE: Time string in the format HH:MM, datetime to be modified
# POST: Returns a datetime with updated hours
def parse_time(time, now):
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

def get_current_weather():
    response = requests.get(WEATHER_BASE_URL, verify=False)
    weather_json = response.json()
    print(weather_json)
    if weather_json["cod"] != "404":
        info = weather_json['main']
        temp = int(info['temp']) - 273
        weather = weather_json['weather']
        desc = weather[0]['description']

        return f"Currently, {temp}°C at UBC. Expect {desc}"
    else:
        return "Weather info not found. Sorry!"


client.run(credentials.token)
