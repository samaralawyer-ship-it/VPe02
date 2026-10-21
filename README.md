# Docker: урок VPe02 на двух примерах

Практическое руководство: тема урока разбирается дважды — на учебном Flask-приложении
(как в уроке) и на вашем проекте «Агрегатор новостей и вакансий».

Запускать всё нужно **в своём терминале** (PowerShell), из корня проекта
`C:\Users\Working hard\Documents\Zerocoder\VPk01.1`.

Перед началом проверьте, что Docker Desktop запущен:

```powershell
docker version
```

Должны быть видны и клиент, и сервер (демон). Если только клиент — запустите Docker Desktop.

---

## Часть 1. Учебный пример (как в уроке)

Файлы: `learning/lesson-flask/`

### Шаг 1.1. Сборка образа

```powershell
cd learning\lesson-flask
docker build -t lesson-flask:1 .
```

Что происходит: Docker читает `Dockerfile`, скачивает базу `python:3.12-slim`,
ставит Flask, копирует код, создаёт пользователя `appuser`. Каждая строка Dockerfile —
это **слой**, и они кешируются.

Что смотреть в выводе: строки `DONE` и `CACHED`. В первый раз всё `DONE`.
Проверка результата:

```powershell
docker images lesson-flask
```

Образ — это «замороженный слепок», он ещё ничего не выполняет.

### Шаг 1.2. Запуск контейнера с пробросом порта

```powershell
docker run -d -p 5000:5000 --name lesson-app lesson-flask:1
```

Разбор флагов — это и есть тема урока:

| Флаг | Смысл |
|---|---|
| `-d` | detach: контейнер работает в фоне, терминал свободен |
| `-p 5000:5000` | `порт_хоста:порт_контейнера`. Левое — куда стучаться снаружи |
| `--name lesson-app` | имя контейнера, чтобы не путать с другими |

Проверка:

```powershell
docker ps
```

В колонке PORTS должно быть `0.0.0.0:5000->5000/tcp`. Это и есть проброс.

### Шаг 1.3. Проверка эндпоинтов

```powershell
Invoke-RestMethod http://localhost:5000/
Invoke-RestMethod http://localhost:5000/health
Invoke-RestMethod http://localhost:5000/info
Invoke-RestMethod http://localhost:5000/divide/10/2
Invoke-RestMethod http://localhost:5000/multiply/10/10
Invoke-RestMethod http://localhost:5000/calc/2/3
```

**Задание для закрепления:** посмотрите на `/info` и ответьте себе на три вопроса:

1. `hostname` — почему он не совпадает с именем вашего компьютера?
2. `pid` — почему у сервера PID 1?
3. `python` — какая версия, и совпадает ли она с версией в вашем `.venv` (3.14.5)?

Ответ: контейнер — это изолированный Linux-процесс со своим hostname; PID 1 —
потому что Python запущен как первый процесс в контейнере; версия 3.12.15 — из образа
`python:3.12-slim`, и она **намеренно** не обязана совпадать с локальной.

Логи приложения:

```powershell
docker logs lesson-app
docker logs -f lesson-app     # следить в реальном времени, Ctrl+C для выхода
```

### Шаг 1.4. Кеш слоёв — главный практический эффект

Поменяйте в `app.py` только значение `APP_VERSION = "2"` на `"3"` и пересоберите:

```powershell
docker build -t lesson-flask:1 .
```

Обратите внимание на время: **секунды**, и строки `CACHED` напротив слоя `pip install`.
Теперь поменяйте `requirements.txt` (добавьте например пустую строку) и пересоберите:

```powershell
docker build -t lesson-flask:1 .
```

Слой `pip install` пересобирается заново — это уже десятки секунд. Вывод: **порядок
строк в Dockerfile определяет скорость пересборки**. Зависимости — раньше, код — позже.

### Шаг 1.5. Почему пересборка не меняет работающий контейнер

Это второй ключевой момент урока. После пересборки из шага 1.4 проверьте:

```powershell
Invoke-RestMethod http://localhost:5000/version
```

Там будет **старая** версия. Причина: контейнер был создан из предыдущего образа
и продолжает работать на нём. Образ и контейнер — разные сущности.

Проверьте, что `restart` не помогает:

```powershell
docker restart lesson-app
Invoke-RestMethod http://localhost:5000/version    # всё ещё старое
```

Правильный порядок обновления — **удалить контейнер и создать заново**:

```powershell
docker rm -f lesson-app
docker run -d -p 5000:5000 --name lesson-app lesson-flask:1
Invoke-RestMethod http://localhost:5000/version    # теперь новая версия
```

Сверьте ID, как это описано в уроке:

```powershell
docker inspect lesson-app --format '{{.Image}}'
docker inspect lesson-flask:1 --format '{{.Id}}'
```

Значения должны совпасть — контейнер теперь использует актуальный образ.

### Шаг 1.6. Compose: два сервиса

В уроке это финальная часть — «объединяем контейнеры». Здесь `docker compose` вместо
длинных `docker run`. Остановите ручной контейнер, чтобы не занимал порт:

```powershell
docker rm -f lesson-app
docker compose up -d
```

Что произойдёт: соберётся `backend` (наше Flask-приложение, порт 5000) и скачается
готовый `nginx:alpine` для `frontend` (порт 8080). Проверка:

```powershell
docker compose ps                     # оба сервиса Up
Invoke-RestMethod http://localhost:5000/health
Start-Process http://localhost:8080   # фронтенд в браузере
```

В браузере нажмите кнопки — запросы уйдут в бэкенд. Обратите внимание на важную деталь:
**из браузера запрос идёт на `localhost:5000`**, потому что браузер работает на хосте;
а внутри compose сервисы обращаются друг к другу **по имени сервиса** (`backend:5000`),
потому что у каждого контейнера свой localhost.

Логи и остановка:

```powershell
docker compose logs -f
docker compose down          # остановить и удалить контейнеры
docker compose down -v       # то же плюс удалить тома
```

### Шаг 1.7. Если браузер пишет «TypeError: Failed to fetch»

Это самая частая ошибка при двух сервисах, и она **не про Docker**. Причина называется
CORS (Cross-Origin Resource Sharing).

Страница открыта на `http://localhost:8080`, а запрос идёт на `http://localhost:5000`.
Для браузера это **разные origin** — origin определяется тройкой «схема + хост + порт».
Даже различие только в порте делает запрос кросс-доменным, и браузер не отдаёт ответ
странице, если сервер не разрешил это явно заголовком `Access-Control-Allow-Origin`.

Как это выглядит:

| Где смотреть | Что видно |
|---|---|
| На странице | `Ошибка: TypeError: Failed to fetch` |
| В Network (F12) | запрос выполнен, но ответ браузер странице не отдал |
| `docker compose logs backend` | `GET /health 200` — сервер-то ответил! |

Именно последняя строка сбивает с толку: сервер работает и отвечает, а браузер ответ
скрывает. Проблема не в сети, не в контейнере и не в портах.

**Как проверить из терминала** (браузерные ограничения там не действуют):

```powershell
# без заголовка Origin ответ идёт без CORS-разрешений — это нормально
Invoke-WebRequest http://localhost:5000/health -UseBasicParsing

# с Origin видно, разрешает ли сервер этот источник
$r = Invoke-WebRequest http://localhost:5000/health -UseBasicParsing -Headers @{ Origin = "http://localhost:8080" }
$r.Headers['Access-Control-Allow-Origin']      # пусто => браузер заблокирует
```

**Решение** — разрешение выдаёт сервер. В `app.py` это делает обработчик
`@app.after_request`:

```python
ALLOWED_ORIGINS = {"http://localhost:8080", "http://127.0.0.1:8080"}

@app.after_request
def allow_cors(response):
    origin = request.headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
    return response
```

После правки бэкенда — обычное правило Docker: пересобрать и пересоздать контейнер,
затем обновить страницу с `Ctrl+Shift+R`, чтобы не взялась старая версия из кеша:

```powershell
docker compose up -d --build
```

Альтернативы: `pip install flask-cors` и `CORS(app, origins=[...])` — то же одной строкой;
`CORS(app)` разрешит всех (`*`), что допустимо для демо, но не для продакшена.

Главное правило: **CORS — это разрешение на стороне сервера.** Клиентский код починить
нельзя: никакие заголовки в `fetch` не помогут, пока сервер не ответит разрешением.

---


## Часть 4. Если что-то пойдёт не так

| Симптом | Причина и решение |
|---|---|
| `permission denied ... npipe` | Docker Desktop не запущен; запустите и дождитесь «Engine running» |
| `port is already allocated` | порт 5000/8080 занят: `docker ps`, затем `docker rm -f <имя>` |
| `docker compose up` не видит `.env` | файл должен лежать рядом с `docker-compose.yml` |
| Бот в контейнере молчит | проверьте `docker compose logs`: сеть/прокси/токен; `api.telegram.org` может быть недоступен без VPN |
| Дайджест не пришёл | смотрите логи: возможно, «новых материалов нет» — это штатное поведение |
| `restart` не обновил код | так и должно быть: нужен `up -d --build` |
| Контейнер сразу завершился | `docker compose logs --tail 50`, код возврата: `docker inspect <имя> --format '{{.State.ExitCode}}'` |

Полезные команды для уборки:

```powershell
docker compose down                 # остановить и удалить контейнеры проекта
docker rm -f lesson-app             # удалить учебный контейнер
docker rmi lesson-flask:1 lesson-flask:2 lesson-flask:3
docker system df                    # сколько места занимает Docker
docker system prune                 # удалить всё неиспользуемое (осторожно)
```

---

## Что сдать по заданию урока

По формату сдачи нужен один из вариантов: ссылка на репозиторий, скриншоты работающего
контейнера или zip проекта. Для вашего случая проще всего скриншоты:

1. `docker compose ps` — сервис `Up`;
2. `docker compose logs` — строки сбора и `дайджест отправлен`;
3. `docker exec news-vacancy-aggregator python main.py --check` — база на томе.

Для учебного примера (как в уроке) — скриншот `docker compose up -d` и ответа
`http://localhost:5000/health` и страницы `http://localhost:8080`.
