client package
==============
Клиентская часть приложения для обмена сообщениями.
Для запуска требуется перейти в директорию messenger и запустить
через интерпретатор файл client_run.py.

:code:`python client_run.py -a <ip сервера> -P <порт> -n <имя пользователя> -p <пароль>`

1. ``-a или --adr`` - адрес сервера сообщений.
2. ``-P или --port`` - порт по которому принимаются подключения
3. ``-n или --name`` - имя пользователя с которым произойдёт вход в систему.
4. ``-p или --password`` - пароль пользователя.

.. image:: /_static/client.png

Subpackages
-----------

.. toctree::
   :maxdepth: 2

   client.db
   client.gui

Submodules
----------

client.logger module
--------------------

.. automodule:: client.logger
   :members:
   :undoc-members:
   :show-inheritance:

client.transport module
-----------------------

.. automodule:: client.transport
   :members:
   :undoc-members:
   :show-inheritance:

Module contents
---------------

.. automodule:: client
   :members:
   :undoc-members:
   :show-inheritance:
