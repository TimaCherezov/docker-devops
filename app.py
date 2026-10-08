import os

import psycopg
import redis
from flask import Flask, request

app = Flask(__name__)


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "app")
DB_USER = os.getenv("POSTGRES_USER", "app")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "app")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))


def get_db_connection():
    return psycopg.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
)


def init_db():
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id SERIAL PRIMARY KEY,
                    text TEXT NOT NULL
                )
            """)


@app.get("/")
def hello():
    visits = redis_client.incr("visits")

    return f"Привет из контейнера от докера! Посещений: {visits}"


@app.post("/notes")
def add_note():
    text = request.json["text"]

    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO notes (text) VALUES (%s) RETURNING id",
                (text,),
            )
            note_id = cursor.fetchone()[0]

    return {"id": note_id, "text": text}, 201


@app.get("/notes")
def get_notes():
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, text FROM notes ORDER BY id")
            notes = cursor.fetchall()

    return [
        {"id": note_id, "text": text}
        for note_id, text in notes
    ]


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8000)