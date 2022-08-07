_MIN_PORT = 1024
_MAX_PORT = 65534


class Port:
    def __set__(self, instance, value):
        if not _MIN_PORT <= value <= _MAX_PORT:
            raise SystemExit(
                f"Invalid port specified - the port must be in the range {_MIN_PORT} <= value <= {_MAX_PORT}")
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name
