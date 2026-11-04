from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from contextlib import contextmanager
import os
import pymysql

app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)


@contextmanager
def connect():
    db = pymysql.connect(
        host=os.getenv("DB_HOST", "mysql"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "cloudops"),
        password=os.getenv("DB_PASSWORD", "cloudops-dev-password"),
        database=os.getenv("DB_NAME", "cloudops"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with db.cursor() as cursor:
            yield cursor
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def initialize_database():
    with connect() as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS tasks "
            "(id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY, "
            "title TEXT NOT NULL, done TINYINT(1) NOT NULL DEFAULT 0)"
        )


initialize_database()

@app.get('/api/health')
def health(): return jsonify(status='ok', service='cloudops-api')

@app.get('/api/tasks')
def tasks():
    with connect() as db:
        db.execute('SELECT * FROM tasks ORDER BY id DESC')
        return jsonify([dict(row) for row in db.fetchall()])

@app.post('/api/tasks')
def add_task():
    title = (request.json or {}).get('title', '').strip()
    if not title: return jsonify(error='Task title is required'), 400
    with connect() as db:
        db.execute('INSERT INTO tasks(title) VALUES (%s)', (title,))
        db.execute('SELECT * FROM tasks WHERE id=%s', (db.lastrowid,))
        row = db.fetchone()
        return jsonify(dict(row)), 201

@app.patch('/api/tasks/<int:task_id>')
def toggle_task(task_id):
    with connect() as db:
        db.execute('SELECT * FROM tasks WHERE id=%s', (task_id,))
        row = db.fetchone()
        if row is None: return jsonify(error='Task not found'), 404
        db.execute('UPDATE tasks SET done=%s WHERE id=%s', (0 if row['done'] else 1, task_id))
        db.execute('SELECT * FROM tasks WHERE id=%s', (task_id,))
        return jsonify(dict(db.fetchone()))

@app.delete('/api/tasks/<int:task_id>')
def delete_task(task_id):
    with connect() as db: db.execute('DELETE FROM tasks WHERE id=%s', (task_id,))
    return '', 204

@app.get('/')
def index(): return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
