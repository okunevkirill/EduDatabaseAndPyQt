# Encoding with which the application works
BASE_ENCODING = 'utf-8'

# Base IP address on which the application is running
BASE_IP_ADDRESS = '127.0.0.1'

# Base port on which the application is running
BASE_PORT = 7777

# Maximum packet length when transmitting a message, bytes
MAX_PACKET_LENGTH = 1024

# Allowed ports for the application to work
MIN_ADMISSIBLE_PORT = 1024
MAX_ADMISSIBLE_PORT = 65535

# JIM protocol master keys
ACTION = 'action'
TIME = 'time'
USER = 'user'
ACCOUNT_NAME = 'account_name'
SENDER = 'from'
DESTINATION = 'to'
PRESENCE = 'presence'
RESPONSE = 'response'
ERROR = 'error'
MESSAGE = 'message'
MESSAGE_TEXT = 'mess_text'
EXIT = 'exit'
GET_CONTACTS = 'get_contacts'
LIST_INFO = 'data_list'
REMOVE_CONTACT = 'remove'
ADD_CONTACT = 'add'
USERS_REQUEST = 'get_users'
