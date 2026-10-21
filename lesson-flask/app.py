"""Простое Flask-приложение для отработки Docker — как в уроке VPe02.

Эндпоинты:
    /                         — главная: подтверждение, что контейнер работает
    /health                   — статус для проверки
    /info                     — сведения о среде внутри контейнера
    /version                  — версия приложения (демонстрация пересборки)
    /calc/<int:a>/<int:b>     — сложение
    /multiply/<int:a>/<int:b> — умножение (маршрут из урока)
    /divide/<int:a>/<int:b>   — деление (маршрут из урока)

Порядок важен: все @app.get(...) объявлены ДО блока
`if __name__ == "__main__": app.run(...)`. app.run() блокирующий —
код, записанный ниже, не выполнится, пока сервер работает.
"""

from __future__ import annotations

import os
import platform
import socket
import sys

from flask import Flask, jsonify, request

app = Flask(__name__)

APP_VERSION = "3"


# ── CORS ──────────────────────────────────────────────────────────────────────
# Зачем это нужно. Фронтенд отдаётся nginx с порта 8080, а API живёт на порту 5000.
# Для браузера это РАЗНЫЕ origin (схема+хост+порт), поэтому обычный fetch
# блокируется политикой same-origin: JS получает «TypeError: Failed to fetch»,
# хотя сервер отвечает 200 (проверено: ответ был, заголовка не было).
# Сервер обязан явно разрешить такой запрос заголовком Access-Control-Allow-Origin.
#
# В учебном примере разрешаем конкретные origin, а не «*»: так видно, что
# заголовок — это осознанное разрешение, а не «отключить безопасность».
ALLOWED_ORIGINS = {
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    # на случай, если страницу открыли напрямую с бэкенда
    "http://localhost:5000",
    "http://127.0.0.1:5000",
}


@app.after_request
def allow_cors(response):
    """Добавить CORS-заголовки к каждому ответу, включая preflight (OPTIONS)."""
    origin = request.headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Vary"] = "Origin"       # важно для кешей: ответ зависит от origin
    return response


def container_marker() -> str:
    """Отличить запуск в контейнере от запуска на хосте."""
    if os.path.exists("/.dockerenv"):
        return "да, это контейнер"
    return "нет, это хост"


@app.get("/")
def index():
    return jsonify({
        "message": "Контейнер успешно запущен",
        "app": "lesson-flask-in-docker",
        "version": APP_VERSION,
        "endpoints": ["/health", "/info", "/version", "/calc/<a>/<b>", "/multiply/<a>/<b>", "/divide/<a>/<b>"],
    })


@app.get("/health")
def health():
    return jsonify({"status": "healthy"})


@app.get("/version")
def version():
    return jsonify({
        "version": APP_VERSION,
        "note": "если видите 2 — пересборка доехала до контейнера",
    })


@app.get("/info")
def info():
    return jsonify({
        "in_container": container_marker(),
        "hostname": socket.gethostname(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "cwd": os.getcwd(),
        "pid": os.getpid(),
    })


@app.get("/calc/<int:a>/<int:b>")
def calc(a: int, b: int):
    return jsonify({"operation": "add", "a": a, "b": b, "result": a + b}), 200


@app.get("/multiply/<int:a>/<int:b>")
def multiply(a: int, b: int):
    return jsonify({"operation": "multiply", "a": a, "b": b, "result": a * b}), 200


@app.get("/divide/<int:a>/<int:b>")
def divide(a: int, b: int):
    if b == 0:
        return jsonify({"error": "деление на ноль"}), 400
    return jsonify({"operation": "divide", "a": a, "b": b, "result": a / b}), 200


# Всё, что ниже, выполняется только при прямом запуске файла.
# Маршруты выше уже зарегистрированы — теперь можно блокироваться в app.run().
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
