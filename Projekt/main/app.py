from flask import session,Flask, request, render_template, redirect, url_for
from tinydb import TinyDB, Query
from passlib.hash import sha256_crypt
from admin_handling import *
from tinydb.operations import delete, add, subtract
import json_dict
import time
from history import render_history
app = Flask(__name__)
app.secret_key = 'eirgjpewjgiowejopgjwpg'
db = TinyDB('db.json')
@app.route("/")
def index():
    return render_template('index.html')
winnings= TinyDB('winnings.json')
@app.route('/signUp', methods=["POST"])
def signUp():
    card_id = request.form.get('card_id')
    print("signUp: card_id:", card_id)
    name = request.form.get('name')
    print("signUp: name:", name)
    password = request.form.get('password')
    email = request.form.get('email')
    print("signUp: email:", email)
    if name == "" or card_id == "" or password == "" or email == "":
        print("signUp: empty fields")
        return render_template('login invalid.html', fehler="Es sind nicht alle Felder ausgefüllt oder die Card ID fehlt")
    try:
        db.search(Query().card_id == card_id)[0]
        print("signUp: user already signed up")
        return render_template('login invalid.html', fehler="Diese Karte ist bereits registriert.")
    except IndexError:
        db.insert({'name': name, 'card_id': card_id, "password": sha256_crypt.encrypt(password), "email": email, "points": 50, "history": {}})
        session['card_id'] = card_id
        session['name'] = name
        session['loggedIn'] = True
        session["points"] = 50
        print("signUp: user signed up successfully")
        return redirect(url_for('status'))

@app.route('/testCard', methods=["GET"])
def testCard():
    card_id = request.args.get('card_id')
    print("testCard: card_id:", card_id)
    try:
        if session["admin_name"] is not None:
            session["admin_card_id"] = card_id
            print("testCard: admin logged in")
            return redirect(url_for('admin_dashboard_placeholders'))
    except KeyError:
        print("testCard: admin not logged in, Weiterleitung wird geskipt")
    try:
        db.search(Query().card_id == card_id)[0]
        print("testCard: user found")
        return redirect(url_for('login'))
    except IndexError:
        print("testCard: user not found")
        return redirect(url_for('signCard') + '?card_id=' + card_id)

@app.route('/signCard', methods=["GET"])
def signCard():
    if request.method == 'GET':
        card_id = request.args.get('card_id')
        print("signCard: card_id:", card_id)
        if card_id is None:
            return render_template('login invalid.html', fehler="Card ID fehlt. Versuche, dich einzuloggen oder wende dich an das Support.")
        try:
            db.search(Query().card_id == card_id)[0]["password"]
            print("signCard: user already signed up")
            return redirect(url_for('login'))
        except IndexError:
            print("signCard: user not signed up")
            return render_template('signCard.html', card_id=card_id)

@app.route('/status', methods=["GET"])
def status():

    if 'card_id' not in session:
        print("status: not logged in")
        return redirect(url_for('login'))
    session["points"] = db.search(Query().card_id == session['card_id'])[0]["points"]
    print("status: logged in")
    print("status: points:", session["points"])
    print("status: id:", session["card_id"])
    winnings_html = ""
    template = """<div class="progress">
                <div class="progress-bar" role="progressbar" aria-valuenow="40" aria-valuemin="0" aria-valuemax="100" style="width:{{ progress }}%">
                    <span class="sr-only"></span>
                </div>
            </div><p>{{win}}: {{ progress }}% geschafft! </p>"""
    for name, points in get_winnings_dict().items():
        newbar = template
        if int(session["points"]) >= int(points):
            newbar = newbar.replace("{{win}}", "✅ "+name+" - "+str(points)+"P ✅").replace("{{ progress }}", "100")
        else:
            newbar = newbar.replace("{{win}}", name+" - "+str(points)+"P").replace("{{ progress }}", str(round(int(session["points"])/int(points)*100)))
        winnings_html += newbar
    print(winnings_html)
    history = render_history(str(session["card_id"]), db)
    return render_template('success.html', name=session['name'], card_id=session['card_id'], points=db.search(Query().card_id == session['card_id'])[0]["points"], progress_bars=winnings_html, history=history)

@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == 'POST':
        card_id = request.form.get('card_id')
        print("login: card_id:", card_id)
        password = request.form.get('password')
        print("login: password:", password)
        try:
            card = db.search(Query().card_id == card_id)
            if card[0]["password"] is not None and sha256_crypt.verify(password, card[0]["password"]):
                print("login: login successful")
                session['card_id'] = card_id
                session['name'] = card[0]["name"]
                session['loggedIn'] = True
                session["points"] = card[0]["points"]
                return redirect(url_for('status'))
            else:
                print("login: login failed")
                return render_template('login invalid.html', fehler="Login fehlgeschlagen  - Card ID oder PIN falsch")
        except IndexError:
            print("login: user not found")
            return render_template('login invalid.html', fehler="Login fehlgeschlagen  - Diese Karte wurde noch nicht registriert. Scanne den QR Code auf der Karte, um dich zu registrieren.")
    else:
        if 'card_id' in session:
            print("login: already logged in")
            return render_template('login.html', card_id=session['card_id'])
        else:
            print("login: not logged in")
            return render_template('login.html', card_id="", nachricht=" Übrigens, mit dem QR Code sparst du dir die Eingabe deiner Kartennummer.")

@app.route('/logout')
def logout():
    session.pop('card_id', None)
    session.pop('name', None)
    session.pop('loggedIn', None)
    session.pop("points", None)
    print("logout: logged out")
    return redirect(url_for('login'))

@app.route("/admin_login")
def admin_login():
    return render_template('admin_login.html')

@app.route("/admin_dashboard")
def admin_dashboard():
    if 'admin_name' not in session:
        print("admin_status: not logged in")
        return redirect(url_for('admin_login'))
    else: 
        print("admin_status: logged in")
        return dashboard()
@app.route("/admin_check", methods=["POST"])
def admin_check():
    admin_name = request.form.get('admin_name')
    password = request.form.get('password')
    print("admin_check: admin_name:", admin_name, "password:", password)
    if admin_einloggen(admin_name, password)["success"]:
        return redirect(url_for('admin_dashboard'))
    else:
        return render_template('admin_login invalid.html')
@app.route("/admin_logout")
def admin_logout():
    session.pop('admin_name', None)
    session.pop('admin_password', None)
    print("admin_logout: logged out")
    return redirect(url_for('admin_login'))
@app.route("/admin_add", methods=["POST", "GET"])
def admin_add():
    if request.method == 'GET':
        return redirect(url_for('admin_dashboard'))
    card_id = request.form.get('card_id')
    points = request.form.get('points')
    session["admin_card_id"] = card_id
    print("admin_add: card_id:", card_id, "points:", points)
    if verify_admin(session["admin_name"], session["admin_password"]):
        try:
            db.search(Query().card_id == card_id)[0]
        except IndexError:
            print("admin_add: user not found")
            return dashboard(card_id=session["admin_card_id"], message="Die Karte existiert nicht. Ist sie registriert?")
        try:
            db.update(add("points", int(points)), Query().card_id == card_id)
        except ValueError:
            print("admin_add: invalid points")
            return dashboard(card_id=session["admin_card_id"], message="Ungültige Punktzahl. Bitte gib eine Ganzzahl ein.")
        print("admin_add: added points to card_id:", card_id, "points:", points)
        print(db.search(Query().card_id == card_id)[0]["history"])
        prev_history = db.search(Query().card_id == card_id)[0]["history"]
        print(prev_history)
        name_here="Einkauf - Wir sagen Danke"
        prev_history[str(time.time())] = {"points": points, "reason": name_here}
        db.update({"history": prev_history}, Query().card_id == card_id)
        return dashboard(card_id=session["admin_card_id"], message=""+str(points)+" Punkte wurden hinzugefügt.")
    else:
        return redirect(url_for('admin_login'))
@app.route("/admin_substract", methods=["POST", "GET"])
def admin_substract():
    if request.method == 'GET':
        return dashboard(card_id=session["admin_card_id"], message="debug:get")
    card_id = request.form.get('card_id')
    session["admin_card_id"] = card_id
    points = request.form.get('points')
    print("admin_substract: card_id:", card_id, "points:", points)
    if verify_admin(session["admin_name"], session["admin_password"]):
        try:            
            print(points)
            db.update(subtract("points", int(points)), Query().card_id == card_id)
            if int(db.search(Query().card_id == card_id)[0]["points"]) < 0:
                db.update(add("points", int(points)), Query().card_id == card_id)
                print("zu wenig Punkte")
                return dashboard(card_id=session["admin_card_id"], message="Die Kartennummer "+str(card_id)+" hat zu wenig Punkte.")
            print("admin_substract: subbed points to card_id:", card_id, "points:", points)
            try:
                win = winnings.search(Query().points == str(points))[0]
                name_here = win["name"]
            except IndexError:
                name_here = "Korrektur"
            prev_history = db.search(Query().card_id == card_id)[0]["history"]
            print(prev_history)
            prev_history[str(time.time())] = {"points": str("-"+points), "reason": name_here}
            db.update({"history": prev_history}, Query().card_id == card_id)
            return dashboard(message=""+str(points)+" Punkte wurden abgezogen für "+str(card_id)+" Kartennummer.")
        except IndexError: 
            return dashboard(card_id=session["admin_card_id"], message="Die Kartennummer "+str(card_id)+" ist nicht in der Datenbank verfügbar.")
@app.route("/admin_dashboard_placeholders", methods=["POST", "GET"])
def admin_dashboard_placeholders():
    if request.method == 'GET':
        winnings = get_winnings()
        return dashboard(card_id=session["admin_card_id"])
@app.route("/admin_winnings")
def admin_winnings():
    if verify_admin(session["admin_name"], session["admin_password"]):
        return render_template("admin_winnings.html", winnings=get_winnings())
    else:
        return redirect(url_for('admin_login'))
@app.route("/admin_addwinning", methods=["POST", "GET"])
def admin_addWinning():
    if request.method == 'GET':
        return redirect(url_for('admin_winnings'))
    winning_name = request.form.get('winning_name')
    points = request.form.get('points')
    print("admin_addWinning: winning_name:", winning_name, "points:", points)
    if verify_admin(session["admin_name"], session["admin_password"]):
        add_winning(name=winning_name, points=points)
        print("admin_addWinning: added winning_name:", winning_name, "points:", points)
        return redirect(url_for('admin_winnings'))
    else:
        return redirect(url_for('admin_login'))
@app.route("/admin_deletewinning", methods=["POST", "GET"])
def admin_deletewinning():
    if request.method == 'GET':
        return redirect(url_for('admin_winnings'))
    winning_name = request.form.get('winning_name')
    print("admin_deletewinning: winning_name:", winning_name)
    if verify_admin(session["admin_name"], session["admin_password"]):
        delete_winning(winning_name)
        print("admin_deletewinning: deleted winning_name:", winning_name)
        return redirect(url_for('admin_winnings'))
    else:
        return redirect(url_for('admin_login'))
@app.errorhandler(404) 
def not_found(e):
    print("not_found: 404 error")
    return render_template('404.html'), 404
@app.route("/cardPoints", methods=["POST"])
def cardPoints():
    card_id = request.get_json()["card_id"]
    print("cardPoints: card_id:", card_id)
    try :
        return str(db.search(Query().card_id == card_id)[0]["points"])
    except IndexError:
        return "0 bzw nicht in der Datenbank"
@app.errorhandler(500)
def server_error(e):
    print("server_error: 500 error")
    print(e)
    print(e.with_traceback)
    error_type = str(type(e).__name__)
    return render_template('500.html', fehler=error_type), 500
