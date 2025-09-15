from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

socketio = SocketIO(app)


@socketio.on('message')
def handle_message(data):
    print('received message: ' + data["data"])
    emit("my_response", {"data": data}, broadcast=True)


@socketio.on('json')
def handle_json(json):
    print('received json: ' + str(json))
    emit("my_response", {"data": json, "json": True}, broadcast=True)


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(200), nullable=False)


with app.app_context():
    # db.drop_all()
    db.create_all()


@app.route("/submit", methods=["POST"])
def submit():
    data = request.json
    note = Note(category=data.get("category"), description=data.get("description"))
    db.session.add(note)
    db.session.commit()
    return jsonify({"status": "ok", "id": note.id})


# Get all notes (for DataTables)
@app.route("/notes", methods=["GET"])
def get_notes():
    notes = Note.query.all()
    return jsonify([{"id": n.id, "category": n.category, "description": n.description} for n in notes])


# Update a note
@app.route("/notes/<int:note_id>", methods=["PUT"])
def update_note(note_id):
    note = db.session.query(Note).filter_by(id=note_id).one_or_none()
    # note = Note.query.get(note_id)
    if not note:
        return jsonify({"error": "Not found"}), 404
    data: dict = request.json
    print(data)
    note.category = data.get("category", note.category)
    note.description = data.get("description", note.description)
    db.session.commit()
    return jsonify({"status": "ok"})


# Optional: delete a note
@app.route("/notes/<int:note_id>", methods=["DELETE"])
def delete_note(note_id):
    note = Note.query.get(note_id)
    if not note:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(note)
    db.session.commit()
    return jsonify({"status": "ok"})


# Serve frontend
@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)
