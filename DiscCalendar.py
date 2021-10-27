class DiscCalendar:

    events = []

    def __init__(self):
        pass

    def addEvent(self, calEvt):
        self.events.append(calEvt)

    def checkFree(self):
        free = True
        for event in self.events:
            if event.eventHappening():
                free = False
        return free