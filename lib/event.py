import logging
log = logging.getLogger(__name__)


class Event():
    def __init__(self):
        self.state = 'ok'
        self.ttl = 60

    def dict(self):
        return vars(self)
