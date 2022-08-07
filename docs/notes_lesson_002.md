# Пояснения и примечания по уроку №002

## Формулировка задания

Продолжение работы с проектом «Мессенджер»:

1. Реализовать метакласс ClientVerifier, выполняющий базовую проверку класса «Клиент» (для некоторых проверок уместно
   использовать модуль dis):
   отсутствие вызовов accept и listen для сокетов;
   использование сокетов для работы по TCP;
2. Реализовать метакласс ServerVerifier, выполняющий базовую проверку класса «Сервер»:
   отсутствие вызовов connect для сокетов;
   использование сокетов для работы по TCP.
3. Реализовать дескриптор для класса серверного сокета, а в нем — проверку номера порта.

- Это должно быть целое число (>=0).
- Значение порта по умолчанию равняется 7777.
- Дескриптор надо создать в отдельном классе.
- Его экземпляр добавить в пределах класса серверного сокета.
- Номер порта передается в экземпляр дескриптора при запуске сервера.

## Примечания

1. Задания брал с вебинара - был разговор, что требуется именно
   данное задание (иллюстрировали на примере предыдущего потока).
2. Не стал добавлять метаклассы в основную ветку по разработке (`dev`) - считаю
   что не совсем корректно их использовать для задачи (если ошибаюсь -
   объясните почему).
3. Пришлось немного откорректировать создание сервера для отслеживания
   протоколов (через `create_server` 'SOCK_STREAM' и 'AF_INET' в атрибутах
   не отображается).
4. Старался не нарушить свой проект, выполнив при этом задание.
5. Защиту у порта через дескриптор сделал более правильную чем `(>=0)`.
6. Поскольку абстрактный класс также реализован через метакласс, для простоты 
   заменил абстрактный метод через `NotImplementedError` в `BaseApplication`.
 

___

## Содержимое методов и атрибутов при работе сервера

```text
-------_global_methods-------
{'KeyboardInterrupt',
 'LOGGER',
 'Message',
 'MessageType',
 'OSError',
 'SystemExit',
 'TypeError',
 'ValueError',
 'deque',
 'dict',
 'select',
 'set',
 'socket',
 'super'}
------------------------------------------
-------_tos_methods-------
{'_MessengerServer__connection_handling',
 '_MessengerServer__process_incoming_message',
 '_MessengerServer__process_outgoing_message',
 '_asdict',
 'accept',
 'add',
 'append',
 'bind',
 'close',
 'copy',
 'critical',
 'debug',
 'discard',
 'get',
 'get_socket_data',
 'getpeername',
 'info',
 'is_valid_ip_address',
 'items',
 'listen',
 'parse_args',
 'popleft',
 'select',
 'settimeout',
 'socket'}
------------------------------------------
-------_attrs-------
{'AF_INET',
 'MAX_NUMBER_CONNECTIONS',
 'MESSAGE',
 'PRESENCE',
 'SOCK_STREAM',
 'TIMEOUT_BLOCKING_SOCKET',
 '__init__',
 'addr',
 'clients_app',
 'connections',
 'messages_app',
 'parser',
 'pop',
 'port',
 'send_data_to_socket',
 'sender',
 'set_defaults',
 'socket_app',
 'to',
 'value'}
------------------------------------------
```

## Содержимое методов и атрибутов при работе клиента

```text
-------_global_methods-------
{'KeyboardInterrupt',
 'LOGGER',
 'Message',
 'MessageType',
 'OSError',
 'UnicodeError',
 'ValueError',
 'input',
 'isinstance',
 'print',
 'socket',
 'str',
 'super',
 'threading',
 'time'}
------------------------------------------
-------_tos_methods-------
{'_MessengerClient__connection_handling',
 '_MessengerClient__presence_exchange',
 '_MessengerClient__presence_obj_generation',
 '_asdict',
 'close',
 'connect',
 'create_message',
 'critical',
 'debug',
 'error',
 'get_launch_arguments',
 'get_socket_data',
 'info',
 'is_alive',
 'lower',
 'show_help',
 'sleep',
 'socket',
 'start',
 'strip',
 'time'}
------------------------------------------
-------_attrs-------
{'AF_INET',
 'MESSAGE',
 'PRESENCE',
 'SOCK_STREAM',
 'Thread',
 '_MessengerClient__respond_to_user_actions',
 '_MessengerClient__work_with_server_msgs',
 '__init__',
 'add_argument',
 'addr',
 'name',
 'parser',
 'port',
 'send_data_to_socket',
 'sender',
 'socket_app',
 'text',
 'username',
 'value'}
------------------------------------------
```