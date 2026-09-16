import os, time, hashlib, base64, secrets, sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import (Flask, request, jsonify, render_template,
                   redirect, url_for, session, flash)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
DB = os.environ.get("DB_PATH", os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "license.db"))
AU = os.environ.get("ADMIN_USER", "bjo0vj")
AP = os.environ.get("ADMIN_PASS", "Phat@0833")

def get_db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL"); return c

def init_db():
    c = get_db()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS keys(
      id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT UNIQUE NOT NULL,
      note TEXT DEFAULT '', created_at TEXT NOT NULL, expires_at TEXT,
      bound_machine TEXT, bound_at TEXT, is_active INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS logs(
      id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL,
      action TEXT NOT NULL, key TEXT, machine_id TEXT, ip TEXT, detail TEXT);
    '''); c.commit(); c.close()

init_db()
_now = lambda: datetime.now(timezone.utc)
_nows = lambda: _now().strftime("%Y-%m-%d %H:%M:%S")

def _parse_exp(s):
    if not s or s.lower() == "lifetime": return None
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

def is_expired(s):
    d = _parse_exp(s); return d is not None and _now() > d

def gen_key():
    p = [secrets.token_hex(2).upper() for _ in range(3)]
    return f"ADOX-{p[0]}-{p[1]}-{p[2]}"

def calc_exp(dtype, dval):
    if dtype == "lifetime": return "lifetime"
    n, v = _now(), int(dval)
    if dtype == "days": e = n + timedelta(days=v)
    elif dtype == "months":
        m = n.month + v; y = n.year + (m-1)//12; m = (m-1)%12+1
        ml = [31, 29 if y%4==0 and (y%100!=0 or y%400==0) else 28,
              31,30,31,30,31,31,30,31,30,31]
        e = n.replace(year=y, month=m, day=min(n.day, ml[m-1]))
    elif dtype == "years": e = n.replace(year=n.year+v)
    else: e = n + timedelta(days=v)
    return e.strftime("%Y-%m-%d %H:%M:%S")

def _log(act, key=None, mid=None, detail=None):
    c = get_db()
    c.execute("INSERT INTO logs(ts,action,key,machine_id,ip,detail)"
              "VALUES(?,?,?,?,?,?)",
              (_nows(), act, key, mid, request.remote_addr, detail))
    c.commit(); c.close()

def login_required(f):
    @wraps(f)
    def d(*a, **k):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*a, **k)
    return d

def _data():
    if request.content_type and "json" in request.content_type:
        return request.json or {}
    return request.form

# ===== API =====
@app.route("/")
def index():
    return jsonify({"status": "ok", "service": "AdoExport License Server"})

@app.route("/ping")
def ping():
    return "pong", 200

@app.route("/verify", methods=["POST"])
def verify():
    d = _data(); key = d.get("key","").strip(); mid = d.get("machine_id","").strip()
    c = get_db(); row = c.execute("SELECT * FROM keys WHERE key=?", (key,)).fetchone()
    if not row:
        _log("verify_fail", key, mid, "not found"); c.close()
        return jsonify({"ok": False, "message": "Invalid license key"})
    if not row["is_active"]:
        _log("verify_fail", key, mid, "disabled"); c.close()
        return jsonify({"ok": False, "message": "License key disabled"})
    if is_expired(row["expires_at"]):
        _log("verify_fail", key, mid, "expired"); c.close()
        return jsonify({"ok": False, "message": "License key expired"})
    if row["bound_machine"] and row["bound_machine"] != mid:
        _log("verify_fail", key, mid, "bound:" + row["bound_machine"]); c.close()
        return jsonify({"ok": False, "message": "Key bound to another machine"})
    if not row["bound_machine"]:
        c.execute("UPDATE keys SET bound_machine=?,bound_at=? WHERE key=?",
                  (mid, _nows(), key))
        c.commit()
    _log("verify_ok", key, mid)
    sym = base64.b64encode(
        hashlib.sha256((mid + "::" + key).encode()).digest()).decode()
    c.close()
    return jsonify({
        "ok": True, "message": "License activated successfully",
        "expires_at": row["expires_at"] or "lifetime",
        "calibration": 1.0, "sym": sym,
        "can_self_unbind": True, "self_unbind_allowed": True,
        "timestamp": int(time.time()),
    })

@app.route("/self_unbind", methods=["POST"])
def self_unbind():
    d = _data(); key = d.get("key","").strip(); mid = d.get("machine_id","").strip()
    c = get_db(); row = c.execute("SELECT * FROM keys WHERE key=?", (key,)).fetchone()
    if not row:
        c.close(); return jsonify({"ok": False, "message": "Invalid key"})
    if row["bound_machine"] != mid:
        c.close(); return jsonify({"ok": False, "message": "Machine mismatch"})
    c.execute("UPDATE keys SET bound_machine=NULL,bound_at=NULL WHERE key=?", (key,))
    c.commit(); _log("unbind", key, mid); c.close()
    return jsonify({"ok": True, "message": "Machine unbound successfully"})


# ===== ADMIN =====
@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if (request.form.get("username") == AU and
                request.form.get("password") == AP):
            session["logged_in"] = True
            return redirect(url_for("admin_panel"))
        flash("Invalid credentials")
    return render_template("login.html")

@app.route("/admin/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/admin")
@login_required
def admin_panel():
    c = get_db()
    rows = c.execute("SELECT * FROM keys ORDER BY id DESC").fetchall()
    logs = c.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 50").fetchall()
    c.close()
    keys = []; total = len(rows); act = bnd = exp = 0
    for r in rows:
        e = is_expired(r["expires_at"])
        d = dict(r); d["is_expired"] = e; keys.append(d)
        if r["is_active"] and not e: act += 1
        if r["bound_machine"]: bnd += 1
        if e: exp += 1
    return render_template("admin.html", keys=keys, logs=logs,
                           total=total, active=act, bound=bnd, expired=exp)

@app.route("/admin/generate", methods=["POST"])
@login_required
def admin_generate():
    qty = min(int(request.form.get("qty", 1)), 100)
    dt = request.form.get("duration_type", "days")
    dv = request.form.get("duration_value", "30")
    note = request.form.get("note", "")
    exp = calc_exp(dt, dv if dt != "lifetime" else "0")
    c = get_db(); gen = []
    for _ in range(qty):
        k = gen_key()
        c.execute("INSERT INTO keys(key,note,created_at,expires_at)"
                  "VALUES(?,?,?,?)",
                  (k, note, _nows(), exp if exp != "lifetime" else None))
        gen.append(k)
    c.commit(); c.close()
    _log("generate", detail=str(qty) + " keys," + dt + "=" + dv)
    flash("Generated " + str(qty) + " key(s): " + ", ".join(gen), "success")
    return redirect(url_for("admin_panel"))

@app.route("/admin/delete", methods=["POST"])
@login_required
def admin_delete():
    k = request.form.get("key")
    c = get_db()
    c.execute("DELETE FROM keys WHERE key=?", (k,))
    c.commit(); c.close()
    _log("delete", k)
    flash("Deleted " + k, "success")
    return redirect(url_for("admin_panel"))

@app.route("/admin/toggle", methods=["POST"])
@login_required
def admin_toggle():
    k = request.form.get("key")
    a = request.form.get("action")
    v = 1 if a == "enable" else 0
    c = get_db()
    c.execute("UPDATE keys SET is_active=? WHERE key=?", (v, k))
    c.commit(); c.close()
    _log("key_" + a, k)
    flash(k + (" enabled" if v else " disabled"), "success")
    return redirect(url_for("admin_panel"))

@app.route("/admin/unbind", methods=["POST"])
@login_required
def admin_unbind():
    k = request.form.get("key")
    c = get_db()
    c.execute("UPDATE keys SET bound_machine=NULL,bound_at=NULL WHERE key=?",
              (k,))
    c.commit(); c.close()
    _log("admin_unbind", k)
    flash("Unbound " + k, "success")
    return redirect(url_for("admin_panel"))

@app.route("/admin/update_note", methods=["POST"])
@login_required
def admin_update_note():
    k = request.form.get("key")
    n = request.form.get("note", "")
    c = get_db()
    c.execute("UPDATE keys SET note=? WHERE key=?", (n, k))
    c.commit(); c.close()
    return redirect(url_for("admin_panel"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print("Server: http://127.0.0.1:" + str(port))
    print("Admin:  http://127.0.0.1:" + str(port) + "/admin")
    print("Login:  " + AU + " / " + AP)
    app.run(host="0.0.0.0", port=port, debug=True)
