import datetime


class AllUsers:
    def __init__(self, username):
        self.id = None
        self.username = username
        self.last_login = datetime.datetime.now()

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id!r}, name={self.username!r})"


class ActiveUser:
    def __init__(self, user_id, ip_address, port, login_time):
        self.id = None
        self.user_id = user_id
        self.ip_address = ip_address
        self.port = port
        self.login_time = login_time

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id!r}, user_id={self.user_id!r})"


class LoginHistory:
    def __init__(self, user_id, date, ip_address, port):
        self.id = None
        self.user_id = user_id
        self.date_time = date
        self.ip_address = ip_address
        self.port = port

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id!r}, user_id={self.user_id!r}, " \
               f"address='{self.ip_address}:{self.port}')"


class UserContact:
    def __init__(self, user_id, contact_id):
        self.id = None
        self.user_id = user_id
        self.contact_id = contact_id

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id!r}, user_id={self.user_id!r}, contact_id={self.contact_id!r})"


class UserHistory:
    def __init__(self, user_id):
        self.id = None
        self.user_id = user_id
        self.sent = 0
        self.accepted = 0

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self.id!r}, user_id={self.user_id!r})"
