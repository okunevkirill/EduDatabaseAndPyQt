import inspect
import logging
from functools import wraps


def log_calls(logger_name: str = __name__):
    """Decorator for logging call sequence and passed arguments (implementation via function)"""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name)
            result = func(*args, **kwargs)
            logger.debug(
                f'Function {func.__name__!r} was called from function {inspect.stack()[1][3]!r} '
                f'with arguments args={args!r}, kwargs={kwargs!r}',

                stacklevel=2,
            )
            return result

        return wrapper

    return decorator


class LogCalls:
    """Decorator for logging call sequence and passed arguments (implementation via class)"""

    def __init__(self, logger_name: str):
        self.logger_name = logger_name

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(self.logger_name)
            result = func(*args, **kwargs)
            logger.debug(
                f'Function {func.__name__!r} was called from function {inspect.stack()[1][3]!r} '
                f'with arguments args={args!r}, kwargs={kwargs!r}',

                stacklevel=2,
            )
            return result

        return wrapper
