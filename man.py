from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "hjhjsdahhds"
socketio = SocketIO(app)

rooms = {}
# Função para gerar o código da sala
def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
    
    return code

@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)
         # Mensagens de erros para caso o usuario tenta criar uma sala sem nome ou tente entrar numa sala sem código
       
        if not name:
            return render_template("home.html", error="Por favor insira seu nome", code=code, name=name)

        if join != False and not code:
            return render_template("home.html", error="Digite o código da sala.", code=code, name=name)
        
        room = code
        if create != False:
            room = generate_unique_code(4) # A variavel room é o código da sala e a variavel rooms é uma lista vazia
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("home.html", error="A sala não existe.", code=code, name=name)
        
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room")) # Depois de determinar a sala e o nome, o usuario será redirecionado para a sala de bate papo

    return render_template("home.html")

@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return 
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} falou: {data['data']}")

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": "Você entrou na sala"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

 #Quando uma pessoa sai da sala, o numero de membros dimimui usando uma atribuição -=1
@socketio.on("disconnect") 
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    
    send({"name": name, "message": "Você deixo a sala"}, to=room)
    print(f"{name} has left the room {room}")

if __name__ == "__main__":
    socketio.run(app, debug=True)