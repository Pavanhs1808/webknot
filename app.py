from flask import Flask, request, jsonify, g
import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "events.db")

app = Flask(__name__)

# ------------------ DB Helpers ------------------

def get_db():
    db = getattr(g, "_db", None)
    if db is None:
        db = g._db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(exception):
    db = getattr(g, "_db", None)
    if db is not None:
        db.close()

def init_db():
    with app.open_resource("schema.sql", mode="r") as f:
        sql = f.read()
    db = get_db()
    db.executescript(sql)
    db.commit()

def row_to_dict(row):
    return {k: row[k] for k in row.keys()}

# ------------------ Startup ------------------

if not os.path.exists(DB_PATH):
    # Initialize database on first run
    with app.app_context():
        init_db()

# ------------------ Routes ------------------

@app.get("/health")
def health():
    return {"status": "ok"}

# ----- Create entities -----

@app.post("/colleges")
def create_college():
    data = request.get_json(force=True)
    name = data.get("name")
    if not name:
        return {"error": "name is required"}, 400
    db = get_db()
    try:
        cur = db.execute("INSERT INTO colleges (name) VALUES (?)", (name,))
        db.commit()
        return {"id": cur.lastrowid, "name": name}, 201
    except sqlite3.IntegrityError as e:
        return {"error": "college already exists or invalid"}, 400

@app.post("/students")
def create_student():
    data = request.get_json(force=True)
    college_id = data.get("college_id")
    name = data.get("name")
    email = data.get("email")
    if not all([college_id, name, email]):
        return {"error": "college_id, name, email are required"}, 400
    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO students (college_id, name, email) VALUES (?,?,?)",
            (college_id, name, email),
        )
        db.commit()
        return {"id": cur.lastrowid, "college_id": college_id, "name": name, "email": email}, 201
    except sqlite3.IntegrityError:
        return {"error": "email already exists or invalid college_id"}, 400

@app.post("/events")
def create_event():
    data = request.get_json(force=True)
    college_id = data.get("college_id")
    name = data.get("name")
    etype = data.get("type")
    date = data.get("date")  # YYYY-MM-DD
    capacity = data.get("capacity")
    venue = data.get("venue")
    description = data.get("description")
    status = data.get("status", "Active")
    if not all([college_id, name, etype, date]):
        return {"error": "college_id, name, type, date are required"}, 400
    db = get_db()
    try:
        cur = db.execute(
            """INSERT INTO events (college_id, name, type, date, capacity, venue, description, status)
               VALUES (?,?,?,?,?,?,?,?)""",
            (college_id, name, etype, date, capacity, venue, description, status),
        )
        db.commit()
        return {"id": cur.lastrowid}, 201
    except sqlite3.IntegrityError as e:
        return {"error": "invalid data: " + str(e)}, 400

# ----- Registration, Attendance, Feedback -----

@app.post("/register")
def register_student():
    data = request.get_json(force=True)
    student_id = data.get("student_id")
    event_id = data.get("event_id")
    if not all([student_id, event_id]):
        return {"error": "student_id and event_id are required"}, 400
    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO registrations (student_id, event_id) VALUES (?,?)",
            (student_id, event_id),
        )
        db.commit()
        return {"registration_id": cur.lastrowid}, 201
    except sqlite3.IntegrityError:
        return {"error": "duplicate registration or invalid student/event"}, 400

@app.post("/attendance")
def mark_attendance():
    data = request.get_json(force=True)
    student_id = data.get("student_id")
    event_id = data.get("event_id")
    present = int(bool(data.get("present", True)))
    if not all([student_id, event_id]):
        return {"error": "student_id and event_id are required"}, 400

    db = get_db()
    # find registration
    reg = db.execute(
        "SELECT id FROM registrations WHERE student_id=? AND event_id=?",
        (student_id, event_id),
    ).fetchone()
    if not reg:
        return {"error": "student is not registered for this event"}, 400

    try:
        db.execute(
            "INSERT INTO attendance (registration_id, present) VALUES (?,?) "
            "ON CONFLICT(registration_id) DO UPDATE SET present=excluded.present, ts=CURRENT_TIMESTAMP",
            (reg["id"], present),
        )
        db.commit()
        return {"ok": True, "registration_id": reg["id"], "present": present}
    except sqlite3.IntegrityError as e:
        return {"error": str(e)}, 400

@app.post("/feedback")
def add_feedback():
    data = request.get_json(force=True)
    student_id = data.get("student_id")
    event_id = data.get("event_id")
    rating = data.get("rating")
    comment = data.get("comment")
    if not all([student_id, event_id, rating]):
        return {"error": "student_id, event_id and rating are required"}, 400
    if not (1 <= int(rating) <= 5):
        return {"error": "rating must be between 1 and 5"}, 400

    db = get_db()
    reg = db.execute(
        "SELECT id FROM registrations WHERE student_id=? AND event_id=?",
        (student_id, event_id),
    ).fetchone()
    if not reg:
        return {"error": "student is not registered for this event"}, 400

    try:
        db.execute(
            "INSERT INTO feedback (registration_id, rating, comment) VALUES (?,?,?) "
            "ON CONFLICT(registration_id) DO UPDATE SET rating=excluded.rating, comment=excluded.comment, ts=CURRENT_TIMESTAMP",
            (reg["id"], rating, comment),
        )
        db.commit()
        return {"ok": True, "registration_id": reg["id"], "rating": int(rating)}
    except sqlite3.IntegrityError as e:
        return {"error": str(e)}, 400

# ----- Reports -----

@app.get("/reports/event-popularity")
def event_popularity():
    event_type = request.args.get("type")  # filter optional
    college_id = request.args.get("college_id")
    db = get_db()
    query = """
        SELECT e.id, e.name, e.type, e.date, e.college_id,
               COUNT(r.id) as registrations
        FROM events e
        LEFT JOIN registrations r ON r.event_id = e.id
        WHERE 1=1
    """
    params = []
    if event_type:
        query += " AND e.type = ?"
        params.append(event_type)
    if college_id:
        query += " AND e.college_id = ?"
        params.append(college_id)
    query += " GROUP BY e.id ORDER BY registrations DESC, e.date DESC"
    rows = db.execute(query, params).fetchall()
    return {"data": [row_to_dict(r) for r in rows]}

@app.get("/reports/attendance")
def attendance_report():
    event_id = request.args.get("event_id")
    if not event_id:
        return {"error": "event_id is required"}, 400
    db = get_db()
    row = db.execute(
        """
        SELECT
          e.id as event_id,
          e.name,
          COUNT(DISTINCT r.id) AS total_registrations,
          SUM(CASE WHEN a.present=1 THEN 1 ELSE 0 END) AS present_count,
          ROUND(100.0 * SUM(CASE WHEN a.present=1 THEN 1 ELSE 0 END) / NULLIF(COUNT(DISTINCT r.id),0), 2) AS attendance_percentage
        FROM events e
        LEFT JOIN registrations r ON r.event_id = e.id
        LEFT JOIN attendance a ON a.registration_id = r.id
        WHERE e.id = ?
        GROUP BY e.id
        """,
        (event_id,),
    ).fetchone()
    return {"data": row_to_dict(row)} if row else {"data": None}

@app.get("/reports/feedback")
def feedback_report():
    event_id = request.args.get("event_id")
    if not event_id:
        return {"error": "event_id is required"}, 400
    db = get_db()
    row = db.execute(
        """
        SELECT
          e.id as event_id,
          e.name,
          ROUND(AVG(f.rating), 2) AS avg_rating,
          COUNT(f.id) as feedback_count
        FROM events e
        LEFT JOIN registrations r ON r.event_id = e.id
        LEFT JOIN feedback f ON f.registration_id = r.id
        WHERE e.id = ?
        GROUP BY e.id
        """,
        (event_id,),
    ).fetchone()
    return {"data": row_to_dict(row)} if row else {"data": None}

@app.get("/reports/student-participation")
def student_participation():
    student_id = request.args.get("student_id")
    if not student_id:
        return {"error": "student_id is required"}, 400
    db = get_db()
    rows = db.execute(
        """
        SELECT s.id as student_id, s.name, COUNT(a.id) AS events_attended
        FROM students s
        LEFT JOIN registrations r ON r.student_id = s.id
        LEFT JOIN attendance a ON a.registration_id = r.id AND a.present=1
        WHERE s.id = ?
        GROUP BY s.id
        """,
        (student_id,),
    ).fetchall()
    return {"data": [row_to_dict(r) for r in rows]}

@app.get("/reports/top-students")
def top_students():
    limit = int(request.args.get("limit", 3))
    college_id = request.args.get("college_id")
    db = get_db()
    query = """
        SELECT s.id as student_id, s.name, s.email, s.college_id,
               COUNT(a.id) AS events_attended
        FROM students s
        LEFT JOIN registrations r ON r.student_id = s.id
        LEFT JOIN attendance a ON a.registration_id = r.id AND a.present=1
        WHERE 1=1
    """
    params = []
    if college_id:
        query += " AND s.college_id = ?"
        params.append(college_id)
    query += " GROUP BY s.id ORDER BY events_attended DESC, s.name ASC LIMIT ?"
    params.append(limit)
    rows = db.execute(query, params).fetchall()
    return {"data": [row_to_dict(r) for r in rows]}

if __name__ == "__main__":
    app.run(debug=True)
