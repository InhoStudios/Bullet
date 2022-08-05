import vobject
from datetime import datetime, timedelta
import calendar

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
        """
        Checks what events are occurring at a specified time

        Parameters
        -----
        date=datetime.utcnow(): datetime.datetime
            The date to check, set to the current date by default
        """
        rets = []
        for evt in self.events:
            if evt.happening(date):
                rets.append(evt)
        return rets
    
    def is_free(self, date=datetime.utcnow()):
        """
        Checks if user is free at a specified time

        Parameters
        -----
        date=datetime.utcnow(): datetime.datetime
            The date to check, set to the current date by default
        """
        return len(self.get_occurring(date)) == 0
    
    def get_week(self, date=datetime.utcnow()):
        """
        Gets the weeks events of any specified date, starting on Sunday

        Parameters
        -----
        date=datetime.utcnow(): datetime.datetime
            The date to check, set to the current date by default
        """
        sunday = date - timedelta(days=date.weekday())
        pass

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

    def get_details(self):
        """
        Gets all relevant event details

        Returns
        -----
        dict {title, day, start, end, location, description}
        """
        return


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
            try:
                if interval[0] <= date and interval[1] >= date:
                    in_interval = True
            except TypeError:
                if interval[0] == date.date() or interval[1] == date.date():
                    in_interval = True
        return in_interval