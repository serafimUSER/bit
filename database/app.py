from flask import Flask, render_template, redirect, request
from flask import jsonify, session

import json
import hashlib


app = Flask(__name__)
app.debug = True
app.secret_key = b'_1#@&1s12s"81g2\n\1asd]/'

def load():
    with open("database_/data.json", "r") as data:
        data = json.loads(data.read())
        
    return data
        
data = load()
    

# Login page
@app.route('/', methods=["GET", "POST"])
def login():
    if 'username' in session:
        return redirect('/tasks')
    if request.method == "POST":
        with open('database_/users.json', 'r') as file:
            users = json.loads(file.read()) 
            
        # if users == {}:
        #     user_id = 0
        # else:
        #     user_id = list(user_id.keys())
            
        for user in users:
            username = hashlib.sha256(request.form['username'].encode()).hexdigest()
            password = hashlib.sha256(request.form['password'].encode()).hexdigest()
            if users[user]["username"] == username and \
                users[user]["password"] == password:
                
                session['username'] = f"{username}{password}"
                
                return redirect('/tasks')
        return render_template("login.html")
    return render_template("login.html")

@app.route('/api/v1/data')
def get_data():
    data = load()
    return jsonify(data)

@app.route('/registr', methods=["POST", "GET"])
def registr():
    if request.method == "POST":
        try:
            with open("database/token.json", "r") as file:
                data_load = json.loads(file.read())
            if request.form["token"] == data_load["token"]:
                with open("database_/users.json", "r") as file:
                    data_file = json.loads(file.read())

                ind = len(data_file)
                username = hashlib.sha256(request.form["username"].encode()).hexdigest()
                password = hashlib.sha256(request.form["password"].encode()).hexdigest()

                data_file[ind] = {
                    "username": username,
                    "password": password
                }
                
                with open("database_/users.json", "w+") as file:
                    file.write(json.dumps(data_file, indent=4))

                session['username'] = f"{username}{password}"

                return redirect('/tasks')

        except Exception as ex:
            return redirect('/registr')

    return render_template('registr.html')

# Tasks
@app.route('/tasks')
def tasks():
    if 'username' not in session:
        return redirect('/')
    data = load()
    tasks = data["tasks"]
        
    return render_template("tasks.html", tasks=tasks)

@app.route('/api/tasks/<int:id_task>', methods=["DELETE"])
def tasks_delete(id_task):
    data = load()
    data["tasks"].pop(str(id_task))
    with open("database_/data.json", "w+") as file:
        file.write(json.dumps(data, indent=4))
    return "202"

@app.route('/create/task/', methods=["GET", "POST"])
def create_task():
    data = load()
    if request.method == "POST":
        try:
            description = request.form['description']
            tags = list(filter(lambda x: x != "", request.form["tags"].replace(" ", "").split(",")))
            
            data["tasks"][len(data["tasks"])] = {
                "text": description,
                "tags": tags
            }
            
            with open('database_/data.json', 'w+') as file:
                file.write(json.dumps(data, indent=4))
            return redirect('/tasks')
        
        except Exception as ex:
            print(ex)
            return redirect('/create/task')
    return render_template('create.html', status='task', length=len(data["tasks"]))

@app.route('/update/task/<int:id_task>', methods=["GET", "POST"])
def tasks_update(id_task):
    data = load()
    if request.method == "POST":
        try:
            description = request.form["description"]
            tags = list(filter(lambda x: x != "", request.form["tags"].replace(" ", "").split(",")))
            
            data["tasks"][str(id_task)] = {
                "text": description,
                "tags": tags
            }
            
            with open('database_/data.json', 'w+') as file:
                file.write(json.dumps(data, indent=4))
                
            return redirect('/tasks')
        except Exception as ex:
            print(ex)
        
    tasks = data["tasks"][str(id_task)]
    tags = ""
    
    for tag in tasks["tags"]:
        if tags.split(',') == len(tasks["tags"]):
            tags += tag
        else:
            tags += f"{tag}, "
    
    return render_template('update.html', tags=tags, id_task=id_task, tasks=tasks ,status="task")


# Modes
@app.route('/modes')
def modes():
    if 'username' not in session:
        return redirect('/')
    data = load()
    modes = data["modes"]
    return render_template("modes.html", modes=modes)

@app.route('/api/modes/<mode>', methods=["DELETE"])
def modes_delete(mode):
    data = load()
    data["modes"].pop(str(mode))
    with open("database_/data.json", "w+") as file:
        file.write(json.dumps(data, indent=4))
    return "202"

@app.route('/update/mode/<mode>', methods=["GET", "POST"])
def modes_update(mode):
    if 'username' not in session:
        return redirect('/')
    data = load()
    if request.method == "POST":
        try:
            title = request.form["title"]
            tags = list(filter(lambda x: x != "", request.form["tags"].replace(" ", "").split(",")))
            
            mode1 = mode
            if title != mode:
                data["modes"].pop(mode)
                mode1 = title
            
            data["modes"][str(mode1)] = {
                "tags": tags
            }
            
            with open('database_/data.json', 'w+') as file:
                file.write(json.dumps(data, indent=4))
                
            return redirect('/modes')
        except Exception as ex:
            return redirect("/update/mode/"+mode)
        
    modes = data["modes"][mode]
    tags = ""
    
    for tag in modes["tags"]:
        if tags.split(',') == len(modes["tags"]):
            tags += tag
        else:
            tags += f"{tag}, "
    
    return render_template('update.html', tags=tags, mode=mode)

@app.route('/create/mode/', methods=["GET", "POST"])
def create_mode():
    data = load()
    if request.method == "POST":
        try:
            title = request.form['title']
            tags = list(filter(lambda x: x != "", request.form["tags"].replace(" ", "").split(",")))
            
            data["modes"][title] = {
                "tags": tags
            }
            
            with open('database_/data.json', 'w+') as file:
                file.write(json.dumps(data, indent=4))
            return redirect('/modes')
        except Exception as ex:
            print(ex)
            return redirect('/create/mode')
    return render_template('create.html')

if __name__ == "__main__":
    app.run()