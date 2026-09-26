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
        self.name=name; self.budget=budget; self.unit=unit; self.rooms={}
        self.floors=[{"id":"f_basement","name":"Basement","level":-1},{"id":"f_ground","name":"Ground Floor","level":0},{"id":"f_first","name":"First Floor","level":1},{"id":"f_second","name":"Second Floor","level":2},{"id":"f_attic","name":"Attic","level":3},{"id":"f_rooftop","name":"Rooftop","level":4}]
    def get_total_spending(self):
        return sum(r.get('cost',0)+sum(f.get('cost',0) for f in r.get('furniture',{}).values()) for r in self.rooms.values())
    def get_remaining_money(self): return self.budget-self.get_total_spending()
    def to_dict(self): return {'name':self.name,'budget':self.budget,'unit':self.unit,'rooms':self.rooms,'floors':self.floors}
    def from_dict(self,data):
        self.name=data.get('name','Untitled Project'); self.budget=data.get('budget',100000); self.unit=data.get('unit','ft'); self.rooms=data.get('rooms',{})
        for room in self.rooms.values():
            room.setdefault('flooring','Standard'); room.setdefault('wall_color','Warm White'); room.setdefault('floor_texture',room.get('flooring','Standard')); room.setdefault('floor_color','Natural'); room.setdefault('wall_texture','Paint')
        self.floors=data.get('floors',[{"id":"f_basement","name":"Basement","level":-1},{"id":"f_ground","name":"Ground Floor","level":0},{"id":"f_first","name":"First Floor","level":1},{"id":"f_second","name":"Second Floor","level":2},{"id":"f_attic","name":"Attic","level":3},{"id":"f_rooftop","name":"Rooftop","level":4}]); self.floors=sorted(self.floors,key=lambda x:x['level'])

projects={}
def save_data():
    with open(DATA_FILE,'w') as f: json.dump({pid:h.to_dict() for pid,h in projects.items()},f,indent=4)
def load_data():
    global projects
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f: data=json.load(f)
        for pid,hd in data.items(): h=House(); h.from_dict(hd); projects[pid]=h
    elif os.path.exists(LEGACY_FILE):
        with open(LEGACY_FILE) as f: data=json.load(f)
        h=House('Legacy Project'); h.from_dict(data); h.name='Legacy Project'; projects[str(uuid.uuid4())]=h; save_data()
    else: projects[str(uuid.uuid4())]=House('My First Project'); save_data()
load_data()

@app.route('/log_error',methods=['POST'])
def log_error(): print(f"BROWSER ERROR: {request.get_data(as_text=True)}"); return 'OK'
@app.route('/')
def dashboard(): return render_template('dashboard.html',projects=projects)
@app.route('/create_project',methods=['POST'])
def create_project():
    name=request.form.get('name','New Project'); name=name if name.strip() else 'New Project'; budget=request.form.get('budget',type=float,default=100000); pid=str(uuid.uuid4()); projects[pid]=House(name,budget); save_data(); return redirect(url_for('project_editor',project_id=pid))
@app.route('/delete_project/<project_id>',methods=['POST'])
def delete_project(project_id):
    if project_id in projects: del projects[project_id]; save_data()
    return redirect(url_for('dashboard'))
@app.route('/project/<project_id>')
def project_editor(project_id):
    if project_id not in projects:return redirect(url_for('dashboard'))
    return render_template('index.html',house=projects[project_id],project_id=project_id)
@app.route('/project/<project_id>/set_budget',methods=['POST'])
def set_budget(project_id):
    if project_id in projects:
        b=request.form.get('budget',type=float)
        if b is not None: projects[project_id].budget=b; save_data()
    return redirect(url_for('project_editor',project_id=project_id))
@app.route('/project/<project_id>/set_unit',methods=['POST'])
def set_unit(project_id):
    if project_id in projects:
        unit=request.form.get('unit')
        if unit in ['ft','m']: projects[project_id].unit=unit; save_data()
    return redirect(url_for('project_editor',project_id=project_id))
@app.route('/project/<project_id>/add_room',methods=['POST'])
def add_room(project_id):
    if project_id not in projects:return redirect(url_for('dashboard'))
    h=projects[project_id]; name=request.form.get('name'); room_type=request.form.get('type'); floor=request.form.get('floor','f_ground'); cost=request.form.get('cost',type=float,default=0.0); wu=request.form.get('width',type=float,default=11.0); lu=request.form.get('length',type=float,default=9.0); flooring=request.form.get('flooring','Standard'); wall_color=request.form.get('wall_color','Warm White'); windows=request.form.get('windows',type=int,default=0)
    if name and room_type:
        rid=str(uuid.uuid4()); off=len(h.rooms)*30; h.rooms[rid]={'id':rid,'name':name,'type':room_type,'floor':floor,'cost':cost,'area':wu*lu,'flooring':flooring,'floor_texture':flooring,'floor_color':'Natural','wall_color':wall_color,'wall_texture':'Paint','windows':windows,'x':20+off,'y':20+off,'width':wu*20,'height':lu*20,'furniture':{}}; save_data()
    return redirect(url_for('project_editor',project_id=project_id))
@app.route('/project/<project_id>/update_size',methods=['POST'])
def update_size(project_id):
    if project_id not in projects:return jsonify({'status':'error'}),400
    d=request.get_json() or {}; rid=d.get('room_id'); w=d.get('width'); hh=d.get('height')
    if rid in projects[project_id].rooms and w is not None and hh is not None:
        r=projects[project_id].rooms[rid]; r['width']=float(w); r['height']=float(hh); r['area']=(float(w)/20)*(float(hh)/20); save_data(); return jsonify({'status':'success'})
    return jsonify({'status':'error'}),400
@app.route('/project/<project_id>/update_coordinates',methods=['POST'])
def update_coordinates(project_id):
    if project_id not in projects:return jsonify({'status':'error'}),400
    d=request.get_json() or {}; rid=d.get('room_id'); x=d.get('x'); y=d.get('y')
    if rid in projects[project_id].rooms and x is not None and y is not None:
        projects[project_id].rooms[rid]['x']=float(x); projects[project_id].rooms[rid]['y']=float(y); save_data(); return jsonify({'status':'success'})
    return jsonify({'status':'error'}),400
@app.route('/project/<project_id>/update_floor',methods=['POST'])
def update_floor(project_id):
    if project_id not in projects:return jsonify({'status':'error'}),400
    d=request.get_json() or {}; rid=d.get('room_id'); floor=d.get('floor')
    if rid in projects[project_id].rooms and floor: projects[project_id].rooms[rid]['floor']=floor; save_data(); return jsonify({'status':'success'})
    return jsonify({'status':'error'}),400
@app.route('/project/<project_id>/delete_room/<room_id>',methods=['POST'])
def delete_room(project_id,room_id):
    if project_id in projects and room_id in projects[project_id].rooms: del projects[project_id].rooms[room_id]; save_data()
    return redirect(url_for('project_editor',project_id=project_id))
@app.route('/project/<project_id>/api/rotate_room',methods=['POST'])
def rotate_room(project_id):
    if project_id not in projects:return jsonify({'status':'error'}),400
    rid=(request.get_json() or {}).get('room_id')
    if rid in projects[project_id].rooms:
        r=projects[project_id].rooms[rid]; w=r.get('width',220); hh=r.get('height',180); r['width']=hh; r['height']=w; save_data(); return jsonify({'status':'success','width':hh,'height':w})
    return jsonify({'status':'error'}),400
@app.route('/project/<project_id>/api/duplicate_room',methods=['POST'])
def duplicate_room(project_id):
    if project_id not in projects:return jsonify({'status':'error'}),400
    rid=(request.get_json() or {}).get('room_id')
    if rid in projects[project_id].rooms:
        orig=projects[project_id].rooms[rid]; nr=copy.deepcopy(orig); nid=str(uuid.uuid4()); nr['id']=nid; nr['x']=orig.get('x',20)+40; nr['y']=orig.get('y',20)+40; nf={}
        for f in nr.get('furniture',{}).values(): fid=str(uuid.uuid4()); nf[fid]={**copy.deepcopy(f),'id':fid}
        nr['furniture']=nf; projects[project_id].rooms[nid]=nr; save_data(); return jsonify({'status':'success'})
    return jsonify({'status':'error'}),400
@app.route('/project/<project_id>/api/delete_room',methods=['POST'])
def api_delete_room(project_id):
    if project_id not in projects:return jsonify({'status':'error'}),400
    rid=(request.get_json() or {}).get('room_id')
    if rid in projects[project_id].rooms: del projects[project_id].rooms[rid]; save_data(); return jsonify({'status':'success'})
    return jsonify({'status':'error'}),400
@app.route('/project/<project_id>/add_furniture',methods=['POST'])
def add_furniture(project_id):
    if project_id not in projects:return redirect(url_for('dashboard'))
    h=projects[project_id]; rid=request.form.get('room_id'); name=request.form.get('name'); cost=request.form.get('cost',type=float,default=0.0); pos=request.form.get('position'); model=request.form.get('model','box')
    if rid in h.rooms and name:
        fid=str(uuid.uuid4()); h.rooms[rid]['furniture'][fid]={'id':fid,'name':name,'cost':cost,'position':pos,'model':model,'x':20,'y':20,'attached_to':'floor'}; save_data()
    return redirect(url_for('project_editor',project_id=project_id))
@app.route('/project/<project_id>/delete_furniture/<room_id>/<furn_id>',methods=['POST'])
def delete_furniture(project_id,room_id,furn_id):
    if project_id in projects and room_id in projects[project_id].rooms: projects[project_id].rooms[room_id]['furniture'].pop(furn_id,None); save_data()
    return redirect(url_for('project_editor',project_id=project_id))
@app.route('/project/<project_id>/api/update_furniture',methods=['POST'])
def update_furniture(project_id):
    if project_id not in projects:return jsonify({'status':'error'}),400
    h=projects[project_id]; d=request.get_json() or {}; rid=d.get('room_id'); old=d.get('old_room_id'); fid=d.get('furn_id')
    if old and old!=rid and old in h.rooms and fid in h.rooms[old]['furniture'] and rid in h.rooms:
        f=h.rooms[old]['furniture'].pop(fid); f['x']=d.get('x',f.get('x',20)); f['y']=d.get('y',f.get('y',20)); f['attached_to']=d.get('attached_to',f.get('attached_to','floor')); h.rooms[rid]['furniture'][fid]=f; save_data(); return jsonify({'status':'success'})
    if rid in h.rooms and fid in h.rooms[rid]['furniture']:
        f=h.rooms[rid]['furniture'][fid]; f['x']=d.get('x',f.get('x',20)); f['y']=d.get('y',f.get('y',20)); f['attached_to']=d.get('attached_to',f.get('attached_to','floor')); save_data(); return jsonify({'status':'success'})
    return jsonify({'status':'error'}),400
@app.route('/project/<project_id>/add_floor',methods=['POST'])
def add_floor(project_id):
    if project_id in projects:
        h=projects[project_id]; name=request.form.get('name'); level=request.form.get('level',type=int)
        if name and level is not None: h.floors.append({'id':str(uuid.uuid4()),'name':name,'level':level}); h.floors=sorted(h.floors,key=lambda f:f['level']); save_data()
    return redirect(url_for('project_editor',project_id=project_id))
@app.route('/project/<project_id>/delete_floor/<floor_id>',methods=['POST'])
def delete_floor(project_id,floor_id):
    if project_id in projects: projects[project_id].floors=[f for f in projects[project_id].floors if f['id']!=floor_id]; save_data()
    return redirect(url_for('project_editor',project_id=project_id))

@app.route('/project/<project_id>/api/room_appearance',methods=['GET'])
def room_appearance(project_id):
    if project_id not in projects:return jsonify({'status':'error'}),404
    h=projects[project_id]; names={f['id']:f['name'] for f in h.floors}; rooms=[]
    for r in h.rooms.values(): rooms.append({'id':r['id'],'name':r.get('name','Unnamed Room'),'type':r.get('type',''),'floor':r.get('floor','f_ground'),'floor_name':names.get(r.get('floor'),'Unknown Floor'),'floor_texture':r.get('floor_texture',r.get('flooring','Standard')),'floor_color':r.get('floor_color','Natural'),'wall_texture':r.get('wall_texture','Paint'),'wall_color':r.get('wall_color','Warm White')})
    return jsonify({'status':'success','rooms':rooms})
@app.route('/project/<project_id>/api/update_room_appearance',methods=['POST'])
def update_room_appearance(project_id):
    if project_id not in projects:return jsonify({'status':'error'}),404
    d=request.get_json() or {}; rid=d.get('room_id'); r=projects[project_id].rooms.get(rid)
    if not r:return jsonify({'status':'error','message':'Room not found'}),404
    ft={'Light Oak','Natural Oak','Walnut','Herringbone Oak','White Marble','Travertine','Concrete','Dark Slate','Porcelain Stone','Soft Carpet','Grey Tile'}; fc={'Natural','Light','Warm','Cool','Dark'}; wt={'Paint','Microcement','Travertine','Fluted Oak','Natural Stone','White Marble','Vertical Walnut Slat','Plaster'}; wc={'Warm White','Soft Greige','Sand Beige','Sage Mist','Dusty Blue','Slate Blue','Charcoal','Taupe','Terracotta','Olive Grey','Pure White'}
    if d.get('floor_texture') in ft:r['floor_texture']=d['floor_texture'];r['flooring']=d['floor_texture']
    if d.get('floor_color') in fc:r['floor_color']=d['floor_color']
    if d.get('wall_texture') in wt:r['wall_texture']=d['wall_texture']
    if d.get('wall_color') in wc:r['wall_color']=d['wall_color']
    save_data(); return jsonify({'status':'success','room':r})

@app.after_request
def add_header(r):
    r.headers['Cache-Control']='no-cache, no-store, must-revalidate'; r.headers['Pragma']='no-cache'; r.headers['Expires']='0'
    if r.content_type and 'text/html' in r.content_type and request.path.startswith('/project/'):
        body=r.get_data(as_text=True)
        if 'crox-materials.css' not in body: body=body.replace('</head>','<link rel="stylesheet" href="/static/crox-materials.css"></head>')
        if 'crox-materials.js' not in body: body=body.replace('</body>','<script src="/static/crox-materials.js"></script></body>')
        r.set_data(body)
    return r
if __name__=='__main__': app.run(debug=True)
