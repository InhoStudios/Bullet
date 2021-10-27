class DiscCalendar:

    def __init__(self):
        self.events = []

    def addEvent(self, calEvt):
        self.events.append(calEvt)

    def checkFree(self, now):
        free = True
        for event in self.events:
            if event.eventHappening(now):
                free = False
        return free
    
    def getCurrentEvents(self, now):
        curEvts = []
        for event in self.events:
            if event.eventHappening(now):
                curEvts.append(event)
        return curEvts
    
    def getAllEvents(self, now):
        curEvts = []
        for event in self.events:
            if event.inPeriod(now):
                curEvts.append(event)
        return curEvts