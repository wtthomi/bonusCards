from flask import session,Flask, request, render_template, redirect, url_for
from tinydb import TinyDB, Query

app = Flask(__name__)
app.secret_key = 'eirgjpewjgiowejopgjwpg'
db = TinyDB('db.json')
@app.route("/")
def hello_world():
    print("Hello World")
    return "<p>Hello, World!</p>"

@app.route('/signUp', methods=["POST"])
def signUp():
    card_id = request.form.get('card_id')
    print("card_id:", card_id)
    name = request.form.get('name')
    print("name:", name)
    password = request.form.get('password')
    email = request.form.get('email')
    if name == "" or card_id == "" or password == "" or email == "":
        return render_template('login invalid.html', fehler="Es sind nicht alle Felder ausgefüllt oder die Card ID fehlt")
    try:
        db.search(Query().card_id == card_id)[0]
        return render_template('login invalid.html', fehler="Du bist bereits angemeldet")
    except IndexError:
        db.insert({'name': name, 'card_id': card_id, "loggedIn": True, "password": password, "email": email, "points": 50, "history": {}})
        session['card_id'] = card_id
        session['name'] = name
        session['loggedIn'] = True
        session["points"] = 50
        return redirect(url_for('status'))

@app.route('/testCard', methods=["GET"])
def testCard():
    session['card_id'] = request.args.get('card_id')
    card_id = request.args.get('card_id')
    print("testCard: card_id:", card_id)
    try:
        db.search(Query().card_id == card_id)[0]
        return redirect(url_for('login'))
    except IndexError:
        return redirect(url_for('signCard') + '?card_id=' + card_id)

@app.route('/signCard', methods=["GET"])
def signCard():
    card_id = request.args.get('card_id')
    print("signCard: card_id:", card_id)
    return render_template('signCard.html', card_id=card_id)

@app.route('/status', methods=["GET"])
def status():
    if 'card_id' not in session:
        return redirect(url_for('login'))
    return render_template('success.html', name=session['name'], card_id=session['card_id'], points=session["points"])


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == 'POST':
        print(request.form.get('card_id'))
        print(request.form.get('password'))
        try:
            card = db.search(Query().card_id == request.form.get('card_id'))
            if card[0]["password"] is not None and card[0]["password"] == request.form.get('password'):
                print("Login successful")
                session['card_id'] = request.form.get('card_id')
                session['name'] = db.search(Query().card_id == request.form.get('card_id'))[0]["name"]
                session['loggedIn'] = True
                session["points"] = db.search(Query().card_id == request.form.get('card_id'))[0]["points"]
                return redirect(url_for('status'))
        except IndexError:
            print("Login failed")
            return render_template('login invalid.html', fehler="Login fehlgeschlagen. <a href='/login'>Erneut versuchen</a>")
        return redirect(url_for('status'))
    else:
        if 'card_id' in session:
            return render_template('login.html', card_id=session['card_id'])
        else:
            return render_template('login.html', card_id="")
@app.route('/logout')
def logout():
    session.pop('card_id', None)
    session.pop('name', None)
    session.pop('loggedIn', None)
    session.pop("points", None)
    return redirect(url_for('login'))