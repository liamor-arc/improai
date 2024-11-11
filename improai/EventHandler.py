class EventHandler:
    def __init__(self):
        self.events = {}
        
    def addEventHandler(self, name, callback):
        if name not in self.events:
            self.events[name] = []
        if callback not in self.events[name]:
            self.events[name].append(callback)
    
    def removeEventHandler(self, name, callback):
        if name not in self.events:
            return
        self.events[name].remove(callback)
        
    def emit(self, name, *args, **kwargs):
        if name not in self.events:
            print(f"{name} not in events")
            return
        for callback in self.events[name]:
            callback(*args, **kwargs)