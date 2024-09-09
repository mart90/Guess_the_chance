class Event(object):
    def __init__(self, id):
        self.id = id
        self.users = []
        self.resolved_at = None
        self.result = None
