[![CircleCI](https://circleci.com/bb/educiteam/educi.svg?style=svg)](https://circleci.com/bb/educiteam/educi)

# Локальное развертывание проекта

Для начала необходимо получить текущую версию:

```bash
$ git clone https://Dementiy@bitbucket.org/Dementiy/educi.git
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

Если для локального развертывания проекта не используется [Docker](https://www.docker.com/), то желательно использовать виртуальное окружение:

```bash
$ python3 -m venv venv
$ . venv/bin/activate
$ pip install -r requirements/dev.txt
```

При использовании докера:

```bash
$ docker-compose build && docker-compose up
```

По адресу [http://localhost:8000/](http://localhost:8000/) должна открываться стартовая страница проекта.

## Взаимодействие с Vue.js

Устанавливаем `node.js` и `npm`:

```bash
$ brew install node
$ node -v
v11.6.0
$ npm -v
6.5.0
```

Устанавливаем необходимые зависимости (описание зависимостей см. в файле `src/educi-frontend/src/package.json`):

```bash
$ cd src/educi-frontend && npm install
```

Собрать проект и запустить сервер в режиме разработки:

```bash
$ npm run serve
```

По адресу [http://localhost:8080/](http://localhost:8080/) должна быть доступна стартовая страница Vue.js.

## Интеграция с CircleCI

Устанавливаем [CircleCI CLI](https://circleci.com/docs/2.0/local-cli/):

```bash
$ brew install circleci
$ circleci version
0.1.4786+bad101f
```

Конфигурационный файл для CircleCI находится в `.circleci/config.yml`. При внесении изменений в файл конфигурации следует проверить не было ли допущено ошибок:

```bash
$ circleci config validate
```

И затем запустить локальную сборку:

```bash
$ circleci local execute --job build
```
