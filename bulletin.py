import vobject
from datetime import datetime

class Calendar:
    def __init__(self):
        self.events = []
        self.calendar = vobject.iCalendar()
    
    def import_calendar(self, calendar_str):
        """
        Imports a calendar from a .ics file

        Parameters
        -----
        calendar_str: str
            Readable string of .ics file contents
        """
        import_cal = next(vobject.readComponents(calendar_str))
        for vevt in import_cal.vevent_list:
            evt = Event()
            evt.read_from_vevent(vevt)
            self.events.append(evt)
            # import all events
            self.calendar.add(vevt)
        
    def get_events(self):
        return self.events

    def get_occurring(self, date=datetime.utcnow()):
        rets = []
        for evt in self.events:
            if evt.happening(date):
                rets.append(date)
        return rets

class Event:
    def __init__(self):
        self.summary = ""
        self.intervals = []
        self.location = ""
        self.desc = ""

    def read_from_vevent(self, vevent):
        """
        Creates an event from a vevent provided by the vobject API

        Parameters
        -----
        vevent: vobject.icalendar.RecurringComponent
            The vevent object returned from vevent or vevent_list
        """
        self.summary = vevent.summary.value
        try:
            self.location = vevent.location.value
            self.desc = vevent.description.value
        except:
            pass
        # get interval
        duration = vevent.dtend.value - vevent.dtstart.value
        try:
            for date in vevent.rruleset:
                interval = [date, date + duration]
                self.intervals.append(interval)
        except TypeError:
            interval = [vevent.dtstart.value, vevent.dtend.value]
            self.intervals.append(interval)
        return self

    def happening(self, date=datetime.utcnow()):
        """
        Checks to see if an event is happening at a specified time

        Returns
        -----
        in_interval: bool
            A boolean that is true if the event is happening, and false if the event is not
        date=datetime.utcnow(): datetime.datetime
            The date to check when the event is happening, set to the current date by default
        """
        in_interval = False
        for interval in self.intervals:
            if interval[0] <= date and interval[1] >= date:
                in_interval = True
        return in_interval