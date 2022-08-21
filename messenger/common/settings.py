DEFAULT_ENCODING = 'utf-8'
DEFAULT_IP_ADDRESS = '127.0.0.1'
DEFAULT_PORT = 7777
MAX_PACKET_LENGTH = 4096
MIN_ADMISSIBLE_PORT = 1024
MAX_ADMISSIBLE_PORT = 65535
# -----------------------------------------------------------------------------
ACTION = 'action'
ACCOUNT_NAME = 'account_name'
ADD_CONTACT = 'add'
DESTINATION = 'to'
GET_CONTACTS = 'get_contacts'
ERROR = 'error'
EXIT = 'exit'
LIST_INFO = 'data_list'
MESSAGE = 'message'
MESSAGE_TEXT = 'mess_text'
PRESENCE = 'presence'
REMOVE_CONTACT = 'remove'
RESPONSE = 'response'
SENDER = 'from'
TIME = 'time'
USER = 'user'
USERS_REQUEST = 'get_users'
# -----------------------------------------------------------------------------
RESPONSE_200 = {RESPONSE: 200}
RESPONSE_202 = {RESPONSE: 202, LIST_INFO: None}
RESPONSE_400 = {RESPONSE: 400, ERROR: None}
