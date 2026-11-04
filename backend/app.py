from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os, sqlite3

app = Flask(__name__, static_folder="../frontend", static_url_path="")
CORS(app)
DB = os.getenv("DB_PATH", "/data/tasks.db")
os.makedirs(os.path.dirname(DB), exist_ok=True)

def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    db.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, title TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0)")
    return db

@app.get('/api/health')
def health(): return jsonify(status='ok', service='cloudops-api')

@app.get('/api/tasks')
def tasks():
    with connect() as db: return jsonify([dict(r) for r in db.execute('SELECT * FROM tasks ORDER BY id DESC')])

@app.post('/api/tasks')
def add_task():
    title = (request.json or {}).get('title', '').strip()
    if not title: return jsonify(error='Task title is required'), 400
    with connect() as db:
        cur = db.execute('INSERT INTO tasks(title) VALUES (?)', (title,))
        row = db.execute('SELECT * FROM tasks WHERE id=?', (cur.lastrowid,)).fetchone()
        return jsonify(dict(row)), 201

@app.patch('/api/tasks/<int:task_id>')
def toggle_task(task_id):
    with connect() as db:
        row = db.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone()
        if row is None: return jsonify(error='Task not found'), 404
        db.execute('UPDATE tasks SET done=? WHERE id=?', (0 if row['done'] else 1, task_id))
        return jsonify(dict(db.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone()))

@app.delete('/api/tasks/<int:task_id>')
def delete_task(task_id):
    with connect() as db: db.execute('DELETE FROM tasks WHERE id=?', (task_id,))
    return '', 204

@app.get('/')
def index(): return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__': app.run(host='0.0.0.0', port=5000)
