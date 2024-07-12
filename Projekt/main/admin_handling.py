from flask import session,Flask, request, render_template, redirect, url_for
from tinydb import TinyDB, Query
from passlib.hash import sha256_crypt
from app import *
winnings = TinyDB('winnings.json')
def admin_einloggen(admin_name, password):
    print("Admin login function called with admin_name:", admin_name, "and password:", password)
    admin_db = TinyDB('admin_db.json')
    """admin_db.insert({'admin_name': admin_name, 'password': sha256_crypt.encrypt("1234")})"""
    if admin_name == "" or password == "":
        print("Credentials are empty")
        return {"success":False, "fehler":"Es sind nicht alle Felder ausgefüllt"}
    else:
        try:
            if sha256_crypt.verify(password, admin_db.search(Query().admin_name == admin_name)[0]["password"]):
                session['admin_name'] = admin_name
                session['admin_password'] = password
                print("Login successful")
                return {"success":True}
            else:
                print("Login failed - incorrect email or password")
                return {"success":False, "fehler":"Login fehlgeschlagen  - Email oder PIN falsch"}
        except IndexError:
            print("Login failed - no admin account found")
            return {"success":False, "fehler":"Login fehlgeschlagen  - Du hast noch keinen Admin-Account."}
def verify_admin(admin_name, password):
    print("Verifying admin with admin_name:", admin_name, "and password:", password)
    admin_db = TinyDB('admin_db.json')
    try:
        if sha256_crypt.verify(password, admin_db.search(Query().admin_name == admin_name)[0]["password"]):
            print("Admin verification hat geklappt")
            return True
        else:
            print("Admin verification failed - falsches PW")
            return False
    except IndexError:
        print("Admin verification failed - kein Admin gefunden")
        return False
def add_winning(points, name):
    try:
        winnings.search(Query().name == name)[0] #Wenn der Name bereits existiert, gib eine Fehlermeldung aus
    except IndexError:
        print("Gewinn mit dem Namen "+str(name)+" existiert noch nicht")
        winnings.insert({'name': name, 'points': points})
def delete_winning(name):
    try:
        winnings.remove(Query().name == name)
    except IndexError:
        print("Gewinn mit dem Namen "+str(name)+" nicht gefunden")
def get_winnings_dict():
    winnings_dict = {} #Erstellt ein leeres Dictionary in das winnings eingetragen werden
    for winning in winnings.search(Query()["name"] != 0):
        print(winning)
        winnings_dict[winning["name"]]=winning["points"]
    print(winnings_dict)
    return winnings_dict
def get_winnings():
    print(winnings.all())
    return list(winnings.all())
def dashboard(message="", card_id=""):
    return render_template('admin_dashboard_placeholders.html', winnings=get_winnings(), msg=message, card_id=card_id)

