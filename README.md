# 📚 Репозиторий для курса "Базы данных и PyQt"

В рамках курса продолжается работа над проектом многопоточного мессенджера.

[Примечания по уроку №005](docs/notes_lesson_006.md)

## Информация о структуре репозитория

1. Домашние задания к урокам размешены в отдельных ветках, а непосредственно работы с
   проектом производятся в ветке `dev`.
2. После завершения курса планируется слияние веток с `master` (для удобства
   навигации завершённые ветки не будут удаляться).
3. Пояснения и примечания по урокам приведены в каталоге `docs`.

## Информация по запуску

Для запуска мессенджера требуется перейти в директорию `messenger` и
запустить через интерпретатор файл `server_run.py` или `client_run.py` (сервер и клиент
соответственно). Также можно воспользоваться `launcher.py`.

_Примечания_:

1. Для linux необходимо прописывать `python3` вместо `python`.

```shell
cd messenger/
```

```shell
python server_run.py
```

```shell
python client_run.py
```

```shell
python launcher
```

