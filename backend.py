import logging
import os
import shutil
import sys
import threading
import webbrowser
from datetime import datetime

from pystray import Icon, MenuItem, Menu
from PIL import Image
from flask import Flask, request, jsonify, render_template, session
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv

from socketio import Client

# Determine log file path
exe_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.abspath(".")
logs_dir = os.path.join(exe_dir, "logs")
if not os.path.isdir(logs_dir):
    os.makedirs(logs_dir, exist_ok=True)

log_file = os.path.join(logs_dir, "backend.log")

if os.path.isfile(log_file):
    shutil.move(log_file, f"{log_file}.{os.stat(log_file).st_ctime}")

# Create file handler
file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)  # capture everything
formatter = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
file_handler.setFormatter(formatter)

# Root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(file_handler)

# Werkzeug (HTTP requests) logger
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.setLevel(logging.DEBUG)
werkzeug_logger.addHandler(file_handler)
werkzeug_logger.propagate = True

sio_url = "http://127.0.0.1:5000"

async_client = Client()


@async_client.event
def connect():
    print("Connected to Backend")


@async_client.event
def disconnect():
    print("Disconnected from server")


def async_client_connect():
    async_client.connect(url=sio_url)
    async_client.send({"data": "New"})
    async_client.sleep(1)
    async_client.disconnect()


# --- Flask app setup ---
if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'static')
    exe_dir = os.path.dirname(sys.executable)
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    app = Flask(__name__)
    exe_dir = os.path.abspath(".")

load_dotenv(os.path.join(exe_dir, '.env'))
backend_host = os.getenv('BACKEND_HOST')

# Ensure 'instance' folder exists
instance_dir = exe_dir
os.makedirs(instance_dir, exist_ok=True)

app.config['SECRET_KEY'] = 'secret!'


socketio = SocketIO(
    app,
    async_mode='threading',
    logger=True,          # SocketIO debug logs
    engineio_logger=True  # EngineIO debug logs
)


@socketio.event
def message(data):
    emit('my_response',
         {'data': str(data)}, broadcast=True)


# --- Database setup ---
db_path = os.path.join(instance_dir, "NoteApp.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Flask app logger
app.logger.setLevel(logging.DEBUG)
app.logger.addHandler(file_handler)

db = SQLAlchemy(app)


# --- Models ---
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now()  # set on insert
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now(),  # set on insert
        onupdate=datetime.now()  # set on update
    )


with app.app_context():
    # db.drop_all()
    db.create_all()


# --- Routes ---
@app.route("/submit", methods=["POST"])
def submit():
    global async_client
    data = request.json
    note = Note(category=data.get("category"), description=data.get("description"))
    db.session.add(note)
    db.session.commit()

    client = Client()
    client.connect(sio_url)

    client.send({"data": "New"})
    client.sleep(2)
    client.disconnect()

    return jsonify({"status": "ok", "id": note.id})


@app.route("/notes", methods=["GET"])
def get_notes():
    notes = db.session.query(Note).all()
    return jsonify([
        {
            "id": n.id,
            "category": n.category,
            "description": n.description,
            "created_at": n.created_at.isoformat() if n.created_at else None,
            "updated_at": n.updated_at.isoformat() if n.updated_at else None,
        } for n in notes])


@app.route("/notes/<int:note_id>", methods=["PUT"])
def update_note(note_id):
    note = db.session.query(Note).filter_by(id=note_id).one_or_none()
    if not note:
        return jsonify({"error": "Not found"}), 404
    data = request.json
    note.category = data.get("category", note.category)
    note.description = data.get("description", note.description)
    db.session.commit()

    client = Client()
    client.connect(sio_url)

    client.send({"data": "New"})
    client.sleep(2)
    client.disconnect()
    return jsonify({"status": "ok"})


@app.route("/notes/<int:note_id>", methods=["DELETE"])
def delete_note(note_id):
    note = db.session.query(Note).filter_by(id=note_id).one_or_none()
    if not note:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(note)
    db.session.commit()
    return jsonify({"status": "ok"})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/test")
def test():
    async_client_connect()
    return jsonify({})


# --- PyInstaller resource helper ---
def resource_path(relative_path: str) -> str:
    if getattr(sys, "_MEIPASS", False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# --- Flask server in a thread ---
def run_flask():
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)


# --- System tray ---
def quit_app(icon_, item):
    icon_.stop()


tray_icon = Image.open(resource_path("tray_icon-backend.png"))


def open_backend(icon_, item):
    webbrowser.open(backend_host)


menu = Menu(
    MenuItem("> Open Backend", open_backend),
    Menu.SEPARATOR,
    MenuItem("Quit", quit_app)
)

icon = Icon("NoteApp", tray_icon, "NoteApp Backend", menu)

# --- Start server in background thread ---
threading.Thread(target=run_flask, daemon=True).start()

# --- Run tray icon ---
icon.run()
