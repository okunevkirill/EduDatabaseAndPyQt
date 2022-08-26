server package
==============
Серверная часть приложения для обмена сообщениями.
Для запуска требуется перейти в директорию messenger и запустить
через интерпретатор файл server_run.py.

:code:`python server_run.py -a <ip сервера> -P <порт>`

1. ``-a или --adr`` - адрес сервера сообщений (если пустой то идёт
прослушивание всех возможных адресов на сервере).
2. ``-P или --port`` - порт по которому принимаются подключения

.. image:: /_static/server.png

Subpackages
-----------

.. toctree::
   :maxdepth: 2

   server.db
   server.gui

Submodules
----------

server.logger module
--------------------

.. automodule:: server.logger
   :members:
   :undoc-members:
   :show-inheritance:

server.services module
----------------------

.. automodule:: server.services
   :members:
   :undoc-members:
   :show-inheritance:

Module contents
---------------

.. automodule:: server
   :members:
   :undoc-members:
   :show-inheritance:
