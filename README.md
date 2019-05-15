[![CircleCI](https://circleci.com/bb/educiteam/educi.svg?style=svg)](https://circleci.com/bb/educiteam/educi)

# Локальное развертывание проекта

Для начала необходимо получить текущую версию:

```bash
$ git clone https://github.com/terdenan/educi.git
```

Переменные «окружения», используемые для конфигурации проекта, должны быть описаны в файле `src/config/settings/settings.ini`, например:

```
[settings]
SECRET_KEY=MY_SECRET_KEY
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=
DB_HOST=db
DB_PORT=5432
```

Запуск проекта:
```bash
$ docker-compose build && docker-compose up
```