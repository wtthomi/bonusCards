from tinydb import TinyDB, Query
def render_history(card_id, db):
    history = db.search(Query().card_id == card_id)[0]["history"]
    history_list = ""
    for event in history:
        print(history[event])
        print(history[event]['points'])
        if int(history[event]["points"]) < 0:
            history_list += "<li style='color: red;'>"+history[event]['reason']+": "+str(history[event]['points'])+"</li>§§§X"
        else:
                        history_list += "<li style='color: green;'>"+history[event]['reason']+": "+str(history[event]['points'])+"</li>§§§X"
    history_list = history_list.split("§§§X")
    history_list.reverse()
    print(history_list)
    history_list = "".join(history_list)
    history_ready = "<ul class='history'>"  + history_list + "</ul>"
    return history_ready
