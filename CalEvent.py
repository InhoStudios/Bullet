from icalendar import Calendar, Event
from datetime import datetime, timedelta
import calendar
from dateutil.parser import parse
from pytz import timezone

class CalEvent:

    week = timedelta(days=7)
    tz = timezone('America/Vancouver')

    def __init__(self, event):
        self.title = event.get("summary")
        self.start_date = event.get("dtstart").dt
        self.start_time = self.start_date
        self.end_time = event.get("dtend").dt
        self.end_date = self.tz.localize(event.get("rrule")['UNTIL'][0])
        self.location = event.get("location")

    # Returns whether or not an event is happening at the current time
    def eventHappening(self, now):
        now = self.tz.localize(now)
        while (now - self.start_time > self.week and self.dateInBounds()):
            self.start_time = self.start_time + self.week
            self.end_time = self.end_time + self.week
        return now > self.start_time and now < self.end_time
    
    # Checks if the dates for this event are within the end date
    def dateInBounds(self):
        return self.start_time < self.end_date

    def getDetails(self):
        title = self.title
        day = calendar.day_name[self.start_time.weekday()]
        st_time = self.start_time.strftime("%H:%M")
        end_time = self.end_time.strftime("%H:%M")
        return {
            'title': title,
            'day': day,
            'start': st_time,
            'end':end_time
        }
    
    def inPeriod(self, now):
        now = self.tz.localize(now)
        return now >= self.start_date and now <= self.end_date