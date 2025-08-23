from flask import Flask, request, redirect, url_for, render_template, jsonify, abort
from pony.orm import db_session, select
from datetime import datetime
from db import db, Trening

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

def parse_iso_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()

def parse_hhmm(s):
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).time()
        except ValueError:
            continue
    raise ValueError(f"Neispravno vrijeme: {s!r} (očekujem HH:MM ili HH:MM:SS)")

# HTML (templating)
@app.route("/")
@db_session
def home():
    treninzi = select(t for t in Trening).order_by(lambda t: (t.datum, t.vrijeme))[:]
    return render_template("index.html", treninzi=treninzi)

@app.route("/treninzi/create", methods=["POST"])
@db_session
def create_trening_form():
    try:
        datum = parse_iso_date(request.form["datum"])
        vrijeme = parse_hhmm(request.form["vrijeme"])
        intenzitet = int(request.form["intenzitet"])
        trajanje = int(request.form["trajanje"])
        vrsta = request.form["vrsta_treninga"].strip()
        if not (1 <= intenzitet <= 10): raise ValueError("Intenzitet mora biti 1–10")
        if trajanje <= 0: raise ValueError("Trajanje mora biti > 0")
        Trening(datum=datum, vrijeme=vrijeme, intenzitet=intenzitet, trajanje=trajanje, vrsta_treninga=vrsta)
        return redirect(url_for("home"))
    except Exception as e:
        return f"Neispravan unos: {e}", 400

@app.route("/treninzi/<int:tid>/edit")
@db_session
def edit_trening_page(tid):
    t = Trening.get(id_treninga=tid)
    if not t: abort(404)
    return render_template("edit.html", t=t)

@app.route("/treninzi/<int:tid>/update", methods=["POST"])
@db_session
def update_trening_form(tid):
    t = Trening.get(id_treninga=tid)
    if not t: abort(404)
    try:
        t.datum = parse_iso_date(request.form["datum"])
        t.vrijeme = parse_hhmm(request.form["vrijeme"])
        t.intenzitet = int(request.form["intenzitet"])
        t.trajanje = int(request.form["trajanje"])
        t.vrsta_treninga = request.form["vrsta_treninga"].strip()
        if not (1 <= t.intenzitet <= 10): raise ValueError("Intenzitet mora biti 1–10")
        if t.trajanje <= 0: raise ValueError("Trajanje mora biti > 0")
        return redirect(url_for("home"))
    except Exception as e:
        return f"Neispravan unos: {e}", 400

@app.route("/treninzi/<int:tid>/delete", methods=["POST"])
@db_session
def delete_trening_form(tid):
    t = Trening.get(id_treninga=tid)
    if t: t.delete()
    return redirect(url_for("home"))

@app.route("/stats")
@db_session
def stats_page():
    year = request.args.get("year", default=datetime.now().year, type=int)
    month = request.args.get("month", default=datetime.now().month, type=int)

    # filtrirat
    treninzi = select(t for t in Trening if t.datum.year == year and t.datum.month == month)[:]

    # agregati
    ukupno_treninga = len(treninzi)
    ukupno_trajanje = sum(t.trajanje for t in treninzi) if treninzi else 0
    prosjecni_intenzitet = round(sum(t.intenzitet for t in treninzi)/ukupno_treninga, 2) if treninzi else 0

    # po vrsti, broj i trajanje
    po_vrsti = {}
    for t in treninzi:
        g = po_vrsti.setdefault(t.vrsta_treninga, {"broj": 0, "trajanje": 0})
        g["broj"] += 1
        g["trajanje"] += t.trajanje

    # po danu minute/dani
    by_day = {}
    for t in treninzi:
        d = t.datum.isoformat()
        by_day[d] = by_day.get(d, 0) + t.trajanje

    # za nizove za Chart.js
    labels_by_day = sorted(by_day.keys())
    data_by_day = [by_day[d] for d in labels_by_day]

    labels_types = list(po_vrsti.keys())
    data_types_count = [po_vrsti[k]["broj"] for k in labels_types]
    data_types_duration = [po_vrsti[k]["trajanje"] for k in labels_types]

    return render_template(
        "stats.html",
        year=year, month=month,
        ukupno_treninga=ukupno_treninga,
        ukupno_trajanje=ukupno_trajanje,
        prosjecni_intenzitet=prosjecni_intenzitet,
        po_vrsti=po_vrsti,
        by_day=by_day,
        labels_by_day=labels_by_day,
        data_by_day=data_by_day,
        labels_types=labels_types,
        data_types_count=data_types_count,
        data_types_duration=data_types_duration
    )

# REST API
@app.route("/api/treninzi", methods=["GET"])
@db_session
def list_treninzi():
    q = select(t for t in Trening).order_by(lambda t: (t.datum, t.vrijeme))
    return jsonify([{
        "id_treninga": t.id_treninga,
        "datum": t.datum.isoformat(),
        "vrijeme": t.vrijeme.strftime("%H:%M"),
        "intenzitet": t.intenzitet,
        "trajanje": t.trajanje,
        "vrsta_treninga": t.vrsta_treninga
    } for t in q])

@app.route("/api/treninzi/<int:tid>", methods=["GET"])
@db_session
def get_trening(tid):
    t = Trening.get(id_treninga=tid)
    if not t: return jsonify({"error":"Not found"}), 404
    return jsonify({
        "id_treninga": t.id_treninga,
        "datum": t.datum.isoformat(),
        "vrijeme": t.vrijeme.strftime("%H:%M"),
        "intenzitet": t.intenzitet,
        "trajanje": t.trajanje,
        "vrsta_treninga": t.vrsta_treninga
    })

@app.route("/api/treninzi", methods=["POST"])
@db_session
def create_trening():
    data = request.get_json()
    t = Trening(
        datum=parse_iso_date(data["datum"]),
        vrijeme=parse_hhmm(data["vrijeme"]),
        intenzitet=int(data["intenzitet"]),
        trajanje=int(data["trajanje"]),
        vrsta_treninga=data["vrsta_treninga"].strip()
    )
    return jsonify({"id_treninga": t.id_treninga}), 201

@app.route("/api/treninzi/<int:tid>", methods=["PUT", "PATCH"])
@db_session
def update_trening(tid):
    t = Trening.get(id_treninga=tid)
    if not t: return jsonify({"error":"Not found"}), 404
    data = request.get_json()
    if "datum" in data: t.datum = parse_iso_date(data["datum"])
    if "vrijeme" in data: t.vrijeme = parse_hhmm(data["vrijeme"])
    if "intenzitet" in data: t.intenzitet = int(data["intenzitet"])
    if "trajanje" in data: t.trajanje = int(data["trajanje"])
    if "vrsta_treninga" in data: t.vrsta_treninga = data["vrsta_treninga"].strip()
    return jsonify({"ok": True})

@app.route("/api/treninzi/<int:tid>", methods=["DELETE"])
@db_session
def delete_trening(tid):
    t = Trening.get(id_treninga=tid)
    if not t: return jsonify({"error":"Not found"}), 404
    t.delete()
    return jsonify({"ok": True})

@app.route("/api/stats/mjesec", methods=["GET"])
@db_session
def stats_mjesec():
    year = int(request.args.get("year"))
    month = int(request.args.get("month"))
    treninzi = select(t for t in Trening if t.datum.year == year and t.datum.month == month)[:]
    ukupno_treninga = len(treninzi)
    ukupno_trajanje = sum(t.trajanje for t in treninzi) if treninzi else 0
    prosjecni_intenzitet = round(sum(t.intenzitet for t in treninzi)/ukupno_treninga, 2) if treninzi else 0

    po_vrsti_map = {}
    for t in treninzi:
        g = po_vrsti_map.setdefault(t.vrsta_treninga, {"broj":0, "trajanje":0})
        g["broj"] += 1
        g["trajanje"] += t.trajanje
    po_vrsti = [{"vrsta":k, **v} for k,v in po_vrsti_map.items()]

    by_day = {}
    for t in treninzi:
        d = t.datum.isoformat()
        by_day[d] = by_day.get(d, 0) + t.trajanje
    dnevna_serija = [{"datum": d, "trajanje": by_day[d]} for d in sorted(by_day.keys())]

    return jsonify({
        "ukupno_treninga": ukupno_treninga,
        "ukupno_trajanje": ukupno_trajanje,
        "prosjecni_intenzitet": prosjecni_intenzitet,
        "po_vrsti": po_vrsti,
        "dnevna_serija": dnevna_serija
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
