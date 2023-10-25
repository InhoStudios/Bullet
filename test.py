import requests

url = "https://calendar.google.com/calendar/ical/sd11e1vkokea7ibcn2t99218ss%40group.calendar.google.com/private-0bcd20858fd37ba8fa983c3a088720a1/basic.ics"

r = requests.get(url, allow_redirects=True)

open("./calendars/cal.ics", "wb").write(r.content)