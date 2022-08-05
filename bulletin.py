import vobject
from datetime import datetime, timedelta
import calendar

class Calendar:
    def __init__(self):
        self.events = []
        self.calendar = vobject.iCalendar()
        self.busy = False
    
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
        
        Returns
        -----
        week: list
            A list of all events happening in any given week
        """
        sunday = date - timedelta(days=date.weekday())
        saturday = sunday + timedelta(days=7)
        events = []
        for event in self.events:
            in_period, intervals = event.in_period(sunday, saturday)
            if in_period:
                events.append(event.copy().set_intervals(intervals))
        return events

    def toggle_status(self):
        self.busy = not self.busy

    def get_status(self):
        return self.busy

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

    def set_intervals(self, intervals):
        """
        Sets time intervals of an event

        Parameters
        -----
        intervals: list
            List of time intervals to add to event
        """
        self.intervals = intervals
        return self

    def in_period(self, start_date, end_date):
        """
        Checks to see if there are intervals within a given period

        Parameters
        -----
        start_date: date
            The lower bound to check, must be earlier than end_date
        end_date: date
            The upper bound to check

        Returns
        -----
        in_period: bool
            Whether or not the event is within the given period
        intervals: list
            A list of the intervals of the event that occurs within the period
        """
        assert(start_date <= end_date)
        in_period = False
        intervals = []
        for interval in self.intervals:
            try:
                if start_date <= interval[0].date() and end_date >= interval[0].date():
                    in_period = True
                    intervals.append(interval.copy())
            except TypeError:
                if start_date <= interval[0] and end_date >= interval[0]:
                    in_period = True
                    intervals.append(interval.copy())
        return in_period, intervals

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