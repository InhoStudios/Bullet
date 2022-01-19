from math import ceil


class DiscCalendar:
    events_per_page = 5

    def __init__(self):
        self.events = []
        self.busy = False

    def addEvent(self, calEvt):
        self.events.append(calEvt)

    def checkFree(self, now):
        free = True
        for event in self.events:
            if event.eventHappening(now):
                free = False
        return free and not self.busy
    
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

    # PRE: Takes in the current time and the page number
    # POST: Returns the N%5-th page of events. Returns total number of events
    def getEventPage(self, now, pageNum):
        curEvts = []
        numEvts = 0
        start_idx = (pageNum - 1) * self.events_per_page
        for event in self.events:
            if event.inPeriod(now):
                numEvts += 1
                curEvts.append(event)
        curEvts = curEvts[start_idx:start_idx + 5]
        return curEvts, ceil(numEvts / self.events_per_page)

    def toggleBusy(self):
        self.busy = not self.busy

    def getStatus(self):
        return self.busy