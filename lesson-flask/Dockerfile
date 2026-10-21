# Учебный образ: та же идея, что в уроке VPe02, но с пояснением к каждой строке.
FROM python:3.12-slim

# 1) Переменные окружения.
#    PYTHONUNBUFFERED — логи идут в docker logs сразу, а не после остановки контейнера.
#    PYTHONDONTWRITEBYTECODE — не создавать __pycache__ (иначе старый байткод может
#       попасть в следующий слой образа и «залипнуть» в контейнере).
#    PORT — порт приложения; его же пробрасываем наружу.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=5000

WORKDIR /app

# 2) Зависимости отдельным слоем ДО копирования кода.
#    Пока requirements.txt не менялся, Docker берёт этот слой из кеша —
#    пересборка после правки app.py занимает секунды вместо минуты.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 3) Код приложения.
COPY app.py ./

# 4) Отдельный пользователь: приложение не должно работать от root.
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

# 5) EXPOSE только документирует порт: сам проброс делается при запуске
#    (docker run -p 5000:5000 или ports в compose).
EXPOSE 5000

# 6) exec-форма: python получает SIGTERM напрямую и завершается корректно.
CMD ["python", "app.py"]
