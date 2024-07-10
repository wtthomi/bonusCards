from flask import session,Flask, request, render_template, redirect, url_for
from tinydb import TinyDB, Query
from passlib.hash import sha256_crypt
from admin_handling import *
from tinydb.operations import delete, add
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
    winnings_dict = {}
    winnings_html = ""
    template = """<div class="progress">
                <div class="progress-bar" role="progressbar" aria-valuenow="40" aria-valuemin="0" aria-valuemax="100" style="width:{{ progress }}%">
                    <span class="sr-only"></span>
                </div>
            </div><p>{{win}}: {{ progress }}% geschafft! </p>"""
    for winning in winnings.search(Query()["name"] != 0):
        print(winning)
        winnings_dict[winning["name"]]=winning["points"]
    print(winnings_dict)
    for name, points in winnings_dict.items():
        winnings_html += template.replace("{{win}}", name).replace("{{ progress }}", str(round(session["points"]/points*100)))
    print(winnings_html)
    return render_template('success.html', name=session['name'], card_id=session['card_id'], points=db.search(Query().card_id == session['card_id'])[0]["points"], progress_bars=winnings_html)

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
        return render_template('admin_dashboard.html')

@app.route("/admin_check", methods=["POST"])
def admin_check():
    admin_name = request.form.get('admin_name')
    password = request.form.get('password')
    print("admin_check: admin_name:", admin_name, "password:", password)
    if admin_einloggen(admin_name, password)["success"]:
        return redirect(url_for('admin_dashboard'))
    else:
        return render_template('admin_login invalid.html', fehler=admin_einloggen(admin_name, password)["fehler"])
@app.route("/admin_logout")
def admin_logout():
    session.pop('admin_name', None)
    session.pop('admin_password', None)
    print("admin_logout: logged out")
    return redirect(url_for('admin_login'))
@app.route("/admin_add", methods=["POST", "GET"])
def admin_add():
    if request.method == 'GET':
        return render_template('admin_dashboard.html')
    card_id = request.form.get('card_id')
    points = request.form.get('points')
    print("admin_add: card_id:", card_id, "points:", points)
    if verify_admin(session["admin_name"], session["admin_password"]):
        db.update(add("points", int(points)), Query().card_id == card_id)
        print("admin_add: added points to card_id:", card_id, "points:", points)
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('admin_login invalid.html', fehler="Admin konnte nicht verifiziert werden."))
@app.route("/admin_substract", methods=["POST", "GET"])
def admin_substract():
    if request.method == 'GET':
        return render_template('admin_dashboard.html')
    card_id = request.form.get('card_id')
    points = request.form.get('points')
    print("admin_add: card_id:", card_id, "points:", points)
    if verify_admin(session["admin_name"], session["admin_password"]):
        try:
            db.search(Query().card_id == card_id)[0]["points"] -= int(points)
            print("admin_substract: added points to card_id:", card_id, "points:", points)
            return render_template('admin_dashboard.html', message=""+str(points)+" Punkte wurden abgezogen für "+str(card_id)+" Kartennummer.")
        except IndexError: 
            return render_template('admin_dashboard.html', message="Die Kartennummer "+str(card_id)+" ist nicht in der Datenbank verfügbar.")
@app.route("/admin_dashboard_placeholders", methods=["POST", "GET"])
def admin_dashboard_placeholders():
    if request.method == 'GET':
        return render_template('admin_dashboard_placeholders.html', card_id=session["admin_card_id"])
@app.errorhandler(404) 
def not_found(e):
    print("not_found: 404 error")
    return render_template('404.html'), 404

