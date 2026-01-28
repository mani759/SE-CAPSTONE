

# from flask import Flask, render_template, request, redirect
# import sqlite3
# from datetime import datetime

# app = Flask(__name__)

# def db():
#     conn = sqlite3.connect("database.db")
#     conn.row_factory = sqlite3.Row
#     return conn

# def init_db():
#     conn = db()
#     conn.execute('''CREATE TABLE IF NOT EXISTS requirements(
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         title TEXT,
#         description TEXT,
#         type TEXT,
#         priority TEXT,
#         version INTEGER,
#         status TEXT)''')

#     conn.execute('''CREATE TABLE IF NOT EXISTS traceability(
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         req_id INTEGER,
#         design_ref TEXT,
#         code_ref TEXT,
#         test_ref TEXT)''')

#     conn.execute('''CREATE TABLE IF NOT EXISTS changes(
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         req_id INTEGER,
#         change_desc TEXT,
#         impact TEXT,
#         status TEXT,
#         date TEXT)''')
#     conn.commit()
#     conn.close()

# init_db()

# @app.route("/")
# def dashboard():
#     conn = db()
#     total = conn.execute("SELECT COUNT(*) FROM requirements").fetchone()[0]
#     changes = conn.execute("SELECT COUNT(*) FROM changes").fetchone()[0]
#     conn.close()
#     return render_template("dashboard.html", total=total, changes=changes)

# @app.route("/add", methods=["GET","POST"])
# def add_requirement():
#     if request.method == "POST":
#         d = request.form
#         conn = db()
#         conn.execute("INSERT INTO requirements(title,description,type,priority,version,status) VALUES(?,?,?,?,?,?)",
#                      (d["title"],d["description"],d["type"],d["priority"],1,"Draft"))
#         conn.commit()
#         conn.close()
#         return redirect("/requirements")
#     return render_template("add_requirement.html")

# @app.route("/requirements")
# def requirements():
#     conn = db()
#     reqs = conn.execute("SELECT * FROM requirements").fetchall()
#     conn.close()
#     return render_template("requirements.html", reqs=reqs)

# @app.route("/traceability", methods=["GET","POST"])
# def traceability():
#     conn = db()
#     if request.method == "POST":
#         conn.execute("INSERT INTO traceability(req_id,design_ref,code_ref,test_ref) VALUES(?,?,?,?)",
#                      (request.form["req_id"],request.form["design"],request.form["code"],request.form["test"]))
#         conn.commit()
#     traces = conn.execute("SELECT * FROM traceability").fetchall()
#     reqs = conn.execute("SELECT * FROM requirements").fetchall()
#     conn.close()
#     return render_template("traceability.html", traces=traces, reqs=reqs)

# @app.route("/change", methods=["GET","POST"])
# def change():
#     conn = db()
#     if request.method == "POST":
#         conn.execute("INSERT INTO changes(req_id,change_desc,impact,status,date) VALUES(?,?,?,?,?)",
#                      (request.form["req_id"],request.form["change_desc"],request.form["impact"],"Pending",datetime.now()))
#         conn.commit()
#     changes = conn.execute("SELECT * FROM changes").fetchall()
#     reqs = conn.execute("SELECT * FROM requirements").fetchall()
#     conn.close()
#     return render_template("change_request.html", changes=changes, reqs=reqs)

# @app.route("/update_status/<int:id>")
# def update_status(id):
#     conn = db()
#     req = conn.execute("SELECT status FROM requirements WHERE id=?", (id,)).fetchone()
#     order = ["Draft", "Reviewed", "Approved", "Implemented"]
#     new_status = order[(order.index(req["status"]) + 1) % len(order)]
#     conn.execute("UPDATE requirements SET status=? WHERE id=?", (new_status, id))
#     conn.commit()
#     conn.close()
#     return redirect("/requirements")

# @app.route("/edit/<int:id>", methods=["GET","POST"])
# def edit(id):
#     conn = db()
#     if request.method == "POST":
#         d = request.form
#         conn.execute("""UPDATE requirements
#                         SET title=?, description=?, version=version+1
#                         WHERE id=?""",
#                      (d["title"], d["description"], id))
#         conn.commit()
#         return redirect("/requirements")
#     req = conn.execute("SELECT * FROM requirements WHERE id=?", (id,)).fetchone()
#     return render_template("edit.html", req=req)


# @app.route("/search")
# def search():
#     q = request.args.get("q")
#     conn = db()
#     reqs = conn.execute("SELECT * FROM requirements WHERE title LIKE ?", ('%'+q+'%',)).fetchall()
#     return render_template("requirements.html", reqs=reqs)

# @app.route("/impact/<int:id>")
# def impact(id):
#     conn = db()
#     traces = conn.execute("SELECT * FROM traceability WHERE req_id=?", (id,)).fetchall()
#     return render_template("impact.html", traces=traces)


# @app.route("/approve/<int:id>")
# def approve(id):
#     conn = db()
#     conn.execute("UPDATE changes SET status='Approved' WHERE id=?", (id,))
#     conn.commit()
#     return redirect("/change")




# if __name__ == "__main__":
#     app.run(debug=True)



from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime
import requests

app = Flask(__name__)

# 🔑 ADD YOUR OPENROUTER KEY
OPENROUTER_API_KEY = "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"
MODEL = "openai/gpt-4o-mini"

# ---------------- DATABASE ----------------
def db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    conn.execute('''CREATE TABLE IF NOT EXISTS requirements(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        type TEXT,
        priority TEXT,
        version INTEGER,
        status TEXT)''')

    conn.execute('''CREATE TABLE IF NOT EXISTS traceability(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        req_id INTEGER,
        design_ref TEXT,
        code_ref TEXT,
        test_ref TEXT)''')

    conn.execute('''CREATE TABLE IF NOT EXISTS changes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        req_id INTEGER,
        change_desc TEXT,
        impact TEXT,
        status TEXT,
        date TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ---------------- AI FUNCTION ----------------
def ask_ai(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]

# ---------------- ROUTES ----------------

@app.route("/")
def dashboard():
    conn = db()
    total = conn.execute("SELECT COUNT(*) FROM requirements").fetchone()[0]
    changes = conn.execute("SELECT COUNT(*) FROM changes").fetchone()[0]
    conn.close()
    return render_template("dashboard.html", total=total, changes=changes)

@app.route("/add", methods=["GET","POST"])
def add_requirement():
    if request.method == "POST":
        d = request.form
        conn = db()
        conn.execute("INSERT INTO requirements(title,description,type,priority,version,status) VALUES(?,?,?,?,?,?)",
                     (d["title"],d["description"],d["type"],d["priority"],1,"Draft"))
        conn.commit()
        conn.close()
        return redirect("/requirements")
    return render_template("add_requirement.html")

@app.route("/requirements")
def requirements():
    conn = db()
    reqs = conn.execute("SELECT * FROM requirements").fetchall()
    conn.close()
    return render_template("requirements.html", reqs=reqs)

# ---------- AI FEATURES ----------
@app.route("/analyze/<int:id>")
def analyze_requirement(id):
    conn = db()
    req = conn.execute("SELECT * FROM requirements WHERE id=?", (id,)).fetchone()
    conn.close()
    prompt = f"Analyze requirement: {req['description']}. Tell type, priority, clarity score, ambiguity."
    result = ask_ai(prompt)
    return render_template("ai_result.html", result=result)

@app.route("/refine/<int:id>")
def refine_requirement(id):
    conn = db()
    req = conn.execute("SELECT * FROM requirements WHERE id=?", (id,)).fetchone()
    conn.close()
    prompt = f"Rewrite this into professional SRS format: {req['description']}"
    result = ask_ai(prompt)
    return render_template("ai_result.html", result=result)

# ---------- TRACEABILITY ----------
@app.route("/traceability", methods=["GET","POST"])
def traceability():
    conn = db()
    if request.method == "POST":
        conn.execute("INSERT INTO traceability(req_id,design_ref,code_ref,test_ref) VALUES(?,?,?,?)",
                     (request.form["req_id"],request.form["design"],request.form["code"],request.form["test"]))
        conn.commit()
    traces = conn.execute("SELECT * FROM traceability").fetchall()
    reqs = conn.execute("SELECT * FROM requirements").fetchall()
    conn.close()
    return render_template("traceability.html", traces=traces, reqs=reqs)

# ---------- CHANGE MANAGEMENT + AI IMPACT ----------
@app.route("/change", methods=["GET","POST"])
def change():
    conn = db()
    if request.method == "POST":
        desc = request.form["change_desc"]
        ai_prompt = f"A change request: {desc}. Predict dev effort, testing effort, risk level."
        impact = ask_ai(ai_prompt)
        conn.execute("INSERT INTO changes(req_id,change_desc,impact,status,date) VALUES(?,?,?,?,?)",
                     (request.form["req_id"], desc, impact, "Pending", datetime.now()))
        conn.commit()
    changes = conn.execute("SELECT * FROM changes").fetchall()
    reqs = conn.execute("SELECT * FROM requirements").fetchall()
    conn.close()
    return render_template("change_request.html", changes=changes, reqs=reqs)

@app.route("/update_status/<int:id>")
def update_status(id):
    conn = db()
    req = conn.execute("SELECT status FROM requirements WHERE id=?", (id,)).fetchone()
    order = ["Draft", "Reviewed", "Approved", "Implemented"]
    new_status = order[(order.index(req["status"]) + 1) % len(order)]
    conn.execute("UPDATE requirements SET status=? WHERE id=?", (new_status, id))
    conn.commit()
    conn.close()
    return redirect("/requirements")

@app.route("/edit/<int:id>", methods=["GET","POST"])
def edit(id):
    conn = db()
    if request.method == "POST":
        conn.execute("UPDATE requirements SET title=?, description=?, version=version+1 WHERE id=?",
                     (request.form["title"], request.form["description"], id))
        conn.commit()
        return redirect("/requirements")
    req = conn.execute("SELECT * FROM requirements WHERE id=?", (id,)).fetchone()
    return render_template("edit.html", req=req)

if __name__ == "__main__":
    app.run(debug=True)
