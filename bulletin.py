import vobject
from datetime import datetime, timedelta
from pytz import timezone, utc

class Calendar:
    def __init__(self):
        self.events = []
        self.calendar = vobject.iCalendar()
        self.busy = False
        self.timezone = None
    
    def import_calendar(self, calendar_str):
        """
        Imports a calendar from a .ics file

        Parameters
        -----
        calendar_str: str
            Readable string of .ics file contents
        """
        import_cal = next(vobject.readComponents(calendar_str))
        # import timezone
        try:
            tz_str = import_cal.vtimezone.tzid.value
        except AttributeError:
            tz_index = calendar_str.find("X-WR-TIMEZONE")
            if tz_index == -1:
                return None
            tz_index = tz_index + len("X-WR-TIMEZONE") + 1
            tz_str = calendar_str[tz_index:]
            tz_str = tz_str[:tz_str.find('\n')]
        self.timezone = timezone(tz_str)

        for vevt in import_cal.vevent_list:
            evt = Event(self.timezone)
            evt.read_from_vevent(vevt)
            self.events.append(evt)
            # import all events
            self.calendar.add(vevt)
        

    def get_events(self):
        return self.events

    def get_occurring(self, date=datetime.now()):
        """
        Checks what events are occurring at a specified time

        Parameters
        -----
        date=datetime.now(): datetime.datetime
            The date to check, set to the current date by default
        """
        rets = []
        for evt in self.events:
            if evt.happening(date):
                rets.append(evt.copy())
        return rets
    
    def is_free(self, date=datetime.now()):
        """
        Checks if user is free at a specified time

        Parameters
        -----
        date=datetime.now(): datetime.datetime
            The date to check, set to the current date by default
        """
        return len(self.get_occurring(date)) == 0 and not self.busy
    
    def get_week(self, date=datetime.now()):
        """
        Gets the weeks events of any specified date, starting on Sunday

        Parameters
        -----
        date=datetime.now(): datetime.datetime
            The date to check, set to the current date by default
        
        Returns
        -----
        week: list
            A list of all events happening in any given week
        """
        sunday = date - timedelta(days=date.weekday() + 1)
        saturday = sunday + timedelta(days=6)
        tz = timezone('America/Vancouver')
        sunday = self.timezone.localize(sunday)
        saturday = self.timezone.localize(saturday)
        events = []
        for event in self.events:
            in_period, intervals = event.in_period(sunday, saturday)
            if in_period:
                events.append(event.copy().set_intervals(intervals))
        return events

    def toggle_status(self):
        self.busy = not self.busy
        return self

    def get_status(self):
        return self.busy

class Event:

    def __init__(self, timezone):
        self.summary = ""
        self.intervals = []
        self.location = ""
        self.desc = ""
        self.timezone = timezone
    
    def copy(self):
        new_evt = Event(self.timezone)
        new_evt.summary = self.summary
        new_evt.location = self.location
        new_evt.desc = self.desc
        new_evt.intervals = self.intervals.copy()
        return new_evt

    def read_from_vevent(self, vevent):
        """
        Creates an event from a vevent provided by the vobject API

        Parameters
        -----
        vevent: vobject.icalendar.RecurringComponent
            The vevent object returned from vevent or vevent_list
        """
        self.summary = vevent.summary.value

        # fill in location and description if they exist
        try:
            self.location = vevent.location.value
        except:
            pass
        try:
            self.desc = vevent.description.value
        except:
            pass
        # get interval
        try:
            duration = vevent.dtend.value - vevent.dtstart.value
        except AttributeError:
            duration = vevent.duration.value
        try:
            total_intervals = 365
            num_intervals = 0
            for date in vevent.rruleset:
                if num_intervals >= total_intervals:
                    break
                try:
                    date = self.timezone.localize(date).astimezone(utc)
                except (ValueError, AttributeError):
                    pass
                interval = [date, date + duration]
                self.intervals.append(interval)
                num_intervals += 1
        except TypeError:
            try:
                interval = [vevent.dtstart.value, vevent.dtend.value]
            except AttributeError:
                interval = [vevent.dtstart.value, vevent.dtstart.value + vevent.duration.value]
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
            except AttributeError:
                if start_date.date() <= interval[0] and end_date.date() >= interval[0]:
                    in_period = True
                    intervals.append(interval.copy())
            except TypeError:
                if start_date <= interval[0] and end_date >= interval[0]:
                    in_period = True
                    intervals.append(interval.copy())
        return in_period, intervals

    def happening(self, date=datetime.now()):
        """
        Checks to see if an event is happening at a specified time

        Parameters
        -----
        date=datetime.now(): datetime.datetime
            The date to check when the event is happening, set to the current date by default

        Returns
        -----
        in_interval: bool
            A boolean that is true if the event is happening, and false if the event is not
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