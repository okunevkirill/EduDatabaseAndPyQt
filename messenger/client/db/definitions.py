from datetime import datetime


class KnownUser:
    def __init__(self, username):
        self.id = None
        self.username = username

    def __repr__(self):
        return f'{self.__class__.__name__}(id={self.id!r}, username={self.username!r})'


class MessageHistory:
    def __init__(self, username, direction, msg_text, created_at=None):
        self.id = None
        self.username = username
        self.direction = direction
        self.msg_text = msg_text
        self.created_at = created_at or datetime.now()

    def __repr__(self):
        return f'{self.__class__.__name__}(id={self.id!r}, username={self.username!r}, direction={self.direction!r})'


class Contact:
    def __init__(self, username):
        self.id = None
        self.username = username

    def __repr__(self):
        return f'{self.__class__.__name__}(id={self.id!r}, username={self.username!r})'


