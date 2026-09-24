import json
import os
import uuid
import copy
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

DATA_FILE = 'projects_data.json'
LEGACY_FILE = 'house_data.json'

class House:
    def __init__(self, name="Untitled Project", budget=100000, unit="ft"):
        self.name = name
        self.budget = budget
        self.unit = unit
        self.rooms = {}
        self.floors = [
            {"id": "f_basement", "name": "Basement", "level": -1},
            {"id": "f_ground", "name": "Ground Floor", "level": 0},
            {"id": "f_first", "name": "First Floor", "level": 1},
            {"id": "f_second", "name": "Second Floor", "level": 2},
            {"id": "f_attic", "name": "Attic", "level": 3},
            {"id": "f_rooftop", "name": "Rooftop", "level": 4}
        ]

    def get_total_spending(self):
        total = 0
        for room in self.rooms.values():
            total += room.get('cost', 0)
            for furn in room.get('furniture', {}).values():
                total += furn.get('cost', 0)
        return total

    def get_remaining_money(self):
        return self.budget - self.get_total_spending()

    def to_dict(self):
        return {
            'name': self.name,
            'budget': self.budget,
            'unit': self.unit,
            'rooms': self.rooms,
            'floors': self.floors
        }

    def from_dict(self, data):
        self.name = data.get('name', 'Untitled Project')
        self.budget = data.get('budget', 100000)
        self.unit = data.get('unit', 'ft')
        self.rooms = data.get('rooms', {})
        self.floors = data.get('floors', [
            {"id": "f_basement", "name": "Basement", "level": -1},
            {"id": "f_ground", "name": "Ground Floor", "level": 0},
            {"id": "f_first", "name": "First Floor", "level": 1},
            {"id": "f_second", "name": "Second Floor", "level": 2},
            {"id": "f_attic", "name": "Attic", "level": 3},
            {"id": "f_rooftop", "name": "Rooftop", "level": 4}
        ])
        self.floors = sorted(self.floors, key=lambda x: x['level'])

projects = {}

def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump({pid: h.to_dict() for pid, h in projects.items()}, f, indent=4)

def load_data():
    global projects
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            for pid, h_data in data.items():
                h = House()
                h.from_dict(h_data)
                projects[pid] = h
    else:
        if os.path.exists(LEGACY_FILE):
            with open(LEGACY_FILE, 'r') as f:
                data = json.load(f)
                h = House(name="Legacy Project")
                h.from_dict(data)
                h.name = "Legacy Project"
                default_id = str(uuid.uuid4())
                projects[default_id] = h
                save_data()
        else:
            default_id = str(uuid.uuid4())
            projects[default_id] = House(name="My First Project")
            save_data()

load_data()

@app.route('/log_error', methods=['POST'])
def log_error():
    print(f"BROWSER ERROR: {request.get_data(as_text=True)}")
    return "OK"

@app.route('/')
def dashboard():
    return render_template('dashboard.html', projects=projects)

@app.route('/create_project', methods=['POST'])
def create_project():
    name = request.form.get('name', 'New Project')
    if not name.strip():
        name = 'New Project'
    budget = request.form.get('budget', type=float, default=100000)
    pid = str(uuid.uuid4())
    projects[pid] = House(name=name, budget=budget)
    save_data()
    return redirect(url_for('project_editor', project_id=pid))

@app.route('/delete_project/<project_id>', methods=['POST'])
def delete_project(project_id):
    if project_id in projects:
        del projects[project_id]
        save_data()
    return redirect(url_for('dashboard'))

@app.route('/project/<project_id>')
def project_editor(project_id):
    if project_id not in projects:
        return redirect(url_for('dashboard'))
    return render_template('index.html', house=projects[project_id], project_id=project_id)

@app.route('/project/<project_id>/set_budget', methods=['POST'])
def set_budget(project_id):
    if project_id in projects:
        new_budget = request.form.get('budget', type=float)
        if new_budget is not None:
            projects[project_id].budget = new_budget
            save_data()
    return redirect(url_for('project_editor', project_id=project_id))

@app.route('/project/<project_id>/set_unit', methods=['POST'])
def set_unit(project_id):
    if project_id in projects:
        unit = request.form.get('unit')
        if unit in ['ft', 'm']:
            projects[project_id].unit = unit
            save_data()
    return redirect(url_for('project_editor', project_id=project_id))

@app.route('/project/<project_id>/add_room', methods=['POST'])
def add_room(project_id):
    if project_id not in projects:
        return redirect(url_for('dashboard'))
    house = projects[project_id]
    
    name = request.form.get('name')
    room_type = request.form.get('type')
    floor = request.form.get('floor', default='f_ground')
    cost = request.form.get('cost', type=float, default=0.0)
    
    width_units = request.form.get('width', type=float, default=11.0)
    length_units = request.form.get('length', type=float, default=9.0)
    
    # 20 pixels = 1 unit (ft or m)
    width_px = width_units * 20
    length_px = length_units * 20
    area = width_units * length_units
    flooring = request.form.get('flooring', default='Standard')
    wall_color = request.form.get('wall_color', default='White')
    windows = request.form.get('windows', type=int, default=0)
    
    if name and room_type:
        room_id = str(uuid.uuid4())
        offset = len(house.rooms) * 30
        house.rooms[room_id] = {
            'id': room_id,
            'name': name,
            'type': room_type,
            'floor': floor,
            'cost': cost,
            'area': area,
            'flooring': flooring,
            'wall_color': wall_color,
            'windows': windows,
            'x': 20 + offset,
            'y': 20 + offset,
            'width': width_px,
            'height': length_px,
            'furniture': {}
        }
        save_data()
    return redirect(url_for('project_editor', project_id=project_id))

@app.route('/project/<project_id>/update_size', methods=['POST'])
def update_size(project_id):
    if project_id not in projects:
        return jsonify({"status": "error"}), 400
    house = projects[project_id]
    
    data = request.get_json()
    room_id = data.get('room_id')
    w = data.get('width')
    h = data.get('height')
    
    if room_id in house.rooms and w is not None and h is not None:
        house.rooms[room_id]['width'] = float(w)
        house.rooms[room_id]['height'] = float(h)
        house.rooms[room_id]['area'] = (float(w) / 20) * (float(h) / 20)
        save_data()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

@app.route('/project/<project_id>/update_coordinates', methods=['POST'])
def update_coordinates(project_id):
    if project_id not in projects:
        return jsonify({"status": "error"}), 400
    house = projects[project_id]
    
    data = request.get_json()
    room_id = data.get('room_id')
    x = data.get('x')
    y = data.get('y')
    
    if room_id in house.rooms and x is not None and y is not None:
        house.rooms[room_id]['x'] = float(x)
        house.rooms[room_id]['y'] = float(y)
        save_data()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

@app.route('/project/<project_id>/update_floor', methods=['POST'])
def update_floor(project_id):
    if project_id not in projects:
        return jsonify({"status": "error"}), 400
    house = projects[project_id]
    
    data = request.get_json()
    room_id = data.get('room_id')
    floor = data.get('floor')
    
    if room_id in house.rooms and floor:
        house.rooms[room_id]['floor'] = floor
        save_data()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

@app.route('/project/<project_id>/delete_room/<room_id>', methods=['POST'])
def delete_room(project_id, room_id):
    if project_id in projects:
        house = projects[project_id]
        if room_id in house.rooms:
            del house.rooms[room_id]
            save_data()
    return redirect(url_for('project_editor', project_id=project_id))

@app.route('/project/<project_id>/api/rotate_room', methods=['POST'])
def rotate_room(project_id):
    if project_id not in projects:
        return jsonify({"status": "error"}), 400
    house = projects[project_id]
    
    data = request.get_json()
    room_id = data.get('room_id')
    if room_id in house.rooms:
        room = house.rooms[room_id]
        w = room.get('width', 220)
        h = room.get('height', 180)
        room['width'] = h
        room['height'] = w
        save_data()
        return jsonify({"status": "success", "width": h, "height": w})
    return jsonify({"status": "error"}), 400

@app.route('/project/<project_id>/api/duplicate_room', methods=['POST'])
def duplicate_room(project_id):
    if project_id not in projects:
        return jsonify({"status": "error"}), 400
    house = projects[project_id]
    
    data = request.get_json()
    room_id = data.get('room_id')
    if room_id in house.rooms:
        orig = house.rooms[room_id]
        new_room = copy.deepcopy(orig)
        new_id = str(uuid.uuid4())
        new_room['id'] = new_id
        new_room['x'] = orig.get('x', 20) + 40
        new_room['y'] = orig.get('y', 20) + 40
        new_furn = {}
        for f in new_room.get('furniture', {}).values():
            new_f_id = str(uuid.uuid4())
            new_f = copy.deepcopy(f)
            new_f['id'] = new_f_id
            new_furn[new_f_id] = new_f
        new_room['furniture'] = new_furn
        
        house.rooms[new_id] = new_room
        save_data()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

@app.route('/project/<project_id>/api/delete_room', methods=['POST'])
def api_delete_room(project_id):
    if project_id not in projects:
        return jsonify({"status": "error"}), 400
    house = projects[project_id]
    
    data = request.get_json()
    room_id = data.get('room_id')
    if room_id in house.rooms:
        del house.rooms[room_id]
        save_data()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

@app.route('/project/<project_id>/add_furniture', methods=['POST'])
def add_furniture(project_id):
    if project_id not in projects:
        return redirect(url_for('dashboard'))
    house = projects[project_id]
    
    room_id = request.form.get('room_id')
    name = request.form.get('name')
    cost = request.form.get('cost', type=float, default=0.0)
    position = request.form.get('position')
    model = request.form.get('model', 'box')
    
    if room_id in house.rooms and name:
        furn_id = str(uuid.uuid4())
        house.rooms[room_id]['furniture'][furn_id] = {
            'id': furn_id,
            'name': name,
            'cost': cost,
            'position': position,
            'model': model,
            'x': 20,
            'y': 20,
            'attached_to': 'floor'
        }
        save_data()
    return redirect(url_for('project_editor', project_id=project_id))

@app.route('/project/<project_id>/delete_furniture/<room_id>/<furn_id>', methods=['POST'])
def delete_furniture(project_id, room_id, furn_id):
    if project_id in projects:
        house = projects[project_id]
        if room_id in house.rooms and furn_id in house.rooms[room_id]['furniture']:
            del house.rooms[room_id]['furniture'][furn_id]
            save_data()
    return redirect(url_for('project_editor', project_id=project_id))

@app.route('/project/<project_id>/api/update_furniture', methods=['POST'])
def update_furniture(project_id):
    if project_id not in projects:
        return jsonify({"status": "error"}), 400
    house = projects[project_id]
    
    data = request.json
    room_id = data.get('room_id')
    old_room_id = data.get('old_room_id')
    furn_id = data.get('furn_id')
    
    # If moving between rooms
    if old_room_id and old_room_id != room_id:
        if old_room_id in house.rooms and furn_id in house.rooms[old_room_id]['furniture']:
            furn = house.rooms[old_room_id]['furniture'].pop(furn_id)
            if room_id in house.rooms:
                furn['x'] = data.get('x', furn.get('x', 20))
                furn['y'] = data.get('y', furn.get('y', 20))
                furn['attached_to'] = data.get('attached_to', furn.get('attached_to', 'floor'))
                house.rooms[room_id]['furniture'][furn_id] = furn
            save_data()
            return jsonify({"status": "success"})
            
    # Regular update
    if room_id in house.rooms and furn_id in house.rooms[room_id]['furniture']:
        furn = house.rooms[room_id]['furniture'][furn_id]
        furn['x'] = data.get('x', furn.get('x', 20))
        furn['y'] = data.get('y', furn.get('y', 20))
        furn['attached_to'] = data.get('attached_to', furn.get('attached_to', 'floor'))
        save_data()
        return jsonify({"status": "success"})
    return jsonify({"status": "error"}), 400

@app.route('/project/<project_id>/add_floor', methods=['POST'])
def add_floor(project_id):
    if project_id in projects:
        house = projects[project_id]
        name = request.form.get('name')
        level = request.form.get('level', type=int)
        if name and level is not None:
            floor_id = str(uuid.uuid4())
            house.floors.append({"id": floor_id, "name": name, "level": level})
            house.floors = sorted(house.floors, key=lambda f: f['level'])
            save_data()
    return redirect(url_for('project_editor', project_id=project_id))

@app.route('/project/<project_id>/delete_floor/<floor_id>', methods=['POST'])
def delete_floor(project_id, floor_id):
    if project_id in projects:
        house = projects[project_id]
        house.floors = [f for f in house.floors if f['id'] != floor_id]
        save_data()
    return redirect(url_for('project_editor', project_id=project_id))

@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r

if __name__ == '__main__':
    app.run(debug=True)
