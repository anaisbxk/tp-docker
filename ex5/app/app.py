import os
import time

import psycopg2
from flask import Flask, jsonify, request
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

COLUMNS = "id, title, done, created_at"


def get_connection(retries=3, delay=1):
    """Ouvre une connexion PostgreSQL (quelques tentatives avant d'abandonner)."""
    last_error = None
    for _ in range(retries):
        try:
            return psycopg2.connect(
                host=os.getenv("DB_HOST", "db"),
                port=int(os.getenv("DB_PORT", "5432")),
                user=os.environ["POSTGRES_USER"],
                password=os.environ["POSTGRES_PASSWORD"],
                dbname=os.environ["POSTGRES_DB"],
                connect_timeout=3,
            )
        except psycopg2.OperationalError as exc:
            last_error = exc
            time.sleep(delay)
    raise last_error


def run_query(sql, params=None, fetch="all"):
    """Exécute une requête dans une transaction et renvoie les lignes."""
    conn = get_connection()
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params)
            if fetch == "all":
                return cur.fetchall()
            if fetch == "one":
                return cur.fetchone()
            return None
    finally:
        conn.close()


@app.errorhandler(psycopg2.OperationalError)
def base_indisponible(_exc):
    return jsonify(error="Base de données indisponible"), 503


@app.get("/")
def index():
    return jsonify(
        service="API de tâches - TP Docker",
        endpoints=["GET /health", "GET /tasks", "POST /tasks",
                   "PUT /tasks/<id>/done", "DELETE /tasks/<id>"],
    )


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/tasks")
def list_tasks():
    return jsonify(run_query(f"SELECT {COLUMNS} FROM tasks ORDER BY id"))


@app.post("/tasks")
def create_task():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify(error="Le champ 'title' est obligatoire"), 400
    task = run_query(
        f"INSERT INTO tasks (title) VALUES (%s) RETURNING {COLUMNS}",
        (title,),
        fetch="one",
    )
    return jsonify(task), 201


@app.put("/tasks/<int:task_id>/done")
def mark_done(task_id):
    task = run_query(
        f"UPDATE tasks SET done = TRUE WHERE id = %s RETURNING {COLUMNS}",
        (task_id,),
        fetch="one",
    )
    if task is None:
        return jsonify(error="Tâche introuvable"), 404
    return jsonify(task)


@app.delete("/tasks/<int:task_id>")
def delete_task(task_id):
    task = run_query(
        "DELETE FROM tasks WHERE id = %s RETURNING id", (task_id,), fetch="one"
    )
    if task is None:
        return jsonify(error="Tâche introuvable"), 404
    return "", 204
