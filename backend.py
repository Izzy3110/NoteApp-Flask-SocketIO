import os
import sys
import threading
from pystray import Icon, MenuItem, Menu
from PIL import Image
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit

# --- Flask app setup ---
if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'static')
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    app = Flask(__name__)

app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='threading')

# --- Database setup ---
db_path = os.path.join(
    sys._MEIPASS, 'instance', 'NoteApp.db'
) if getattr(sys, 'frozen', False) else os.path.join(app.root_path, 'instance', 'NoteApp.db')

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# --- Models ---
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(200), nullable=False)

with app.app_context():
    db.create_all()

# --- Routes ---
@app.route("/submit", methods=["POST"])
def submit():
    data = request.json
    note = Note(category=data.get("category"), description=data.get("description"))
    db.session.add(note)
    db.session.commit()
    return jsonify({"status": "ok", "id": note.id})

@app.route("/notes", methods=["GET"])
def get_notes():
    notes = Note.query.all()
    return jsonify([{"id": n.id, "category": n.category, "description": n.description} for n in notes])

@app.route("/notes/<int:note_id>", methods=["PUT"])
def update_note(note_id):
    note = Note.query.get(note_id)
    if not note:
        return jsonify({"error": "Not found"}), 404
    data = request.json
    note.category = data.get("category", note.category)
    note.description = data.get("description", note.description)
    db.session.commit()
    return jsonify({"status": "ok"})

@app.route("/notes/<int:note_id>", methods=["DELETE"])
def delete_note(note_id):
    note = Note.query.get(note_id)
    if not note:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(note)
    db.session.commit()
    return jsonify({"status": "ok"})

@app.route("/")
def index():
    return render_template("index.html")

# --- PyInstaller resource helper ---
def resource_path(relative_path: str) -> str:
    if getattr(sys, "_MEIPASS", False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# --- Flask server in a thread ---
def run_flask():
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, allow_unsafe_werkzeug=True)

# --- System tray ---
def quit_app(icon, item):
    icon.stop()

tray_icon = Image.open(resource_path("tray_icon-backend.png"))
menu = Menu(MenuItem("Quit", quit_app))
icon = Icon("NoteApp", tray_icon, "NoteApp Backend", menu)

# --- Start server in background thread ---
threading.Thread(target=run_flask, daemon=True).start()

# --- Run tray icon ---
icon.run()
