import os

import redis
from flask import Flask

app = Flask(__name__)

cache = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    socket_connect_timeout=3,
)


@app.route("/")
def index():
    visites = cache.incr("visites")
    return f"Bonjour ! Cette page a été vue {visites} fois.\n"


@app.route("/reset")
def reset():
    cache.set("visites", 0)
    return "Compteur remis à zéro.\n"
