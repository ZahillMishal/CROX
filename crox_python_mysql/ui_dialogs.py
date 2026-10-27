"""
UI Dialogs Module for CROX Python + MySQL Version
Modal dialogs for Projects, Rooms, Furniture, Floors, and Database Settings.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from .config import load_db_config, save_db_config

ROOM_TYPES = [
    "Living Room", "Master Bedroom", "Bedroom", "Kitchen", "Dining Room",
    "Bathroom", "Study / Office", "Balcony", "Garage", "Storage", "Hallway"
]

FLOORING_OPTIONS = [
    "Standard", "Hardwood Oak", "Ceramic Tile", "Italian Marble",
    "Carpet", "Polished Concrete", "Parquet", "Vinyl"
]

WALL_COLORS = [
    "White", "Warm Beige", "Slate Gray", "Sage Green",
    "Deep Navy", "Terracotta", "Soft Peach", "Charcoal"
]

FURNITURE_MODELS = [
    ("Sofa", "sofa"),
    ("Bed", "bed"),
    ("Dining Table", "table"),
    ("Desk", "desk"),
    ("Armchair", "chair"),
    ("Wardrobe", "wardrobe"),
    ("Kitchen Counter", "counter"),
    ("Bathtub / Sink", "bath"),
    ("Bookshelf", "shelf"),
    ("TV Console", "tv"),
    ("Indoor Plant", "plant")
]


class BaseDialog(tk.Toplevel):
    def __init__(self, parent, title="Dialog", width=420, height=480):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)
        
        # Center dialog relative to parent
        self.geometry(f"{width}x{height}")
        self.update_idletasks()
        try:
            x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (width // 2)
            y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (height // 2)
            self.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        self.result = None
        self.configure(bg="#1e222d")

        # Custom ttk styles
        self._setup_styles()

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('Dark.TLabel', background="#1e222d", foreground="#e1e7f0", font=('Segoe UI', 9))
        style.configure('Header.TLabel', background="#1e222d", foreground="#60a5fa", font=('Segoe UI', 12, 'bold'))
        style.configure('Dark.TButton', background="#2563eb", foreground="#ffffff", font=('Segoe UI', 9, 'bold'), borderwidth=0)
        style.map('Dark.TButton', background=[('active', '#1d4ed8')])
        style.configure('Cancel.TButton', background="#374151", foreground="#e5e7eb", font=('Segoe UI', 9), borderwidth=0)
        style.map('Cancel.TButton', background=[('active', '#4b5563')])


class NewProjectDialog(BaseDialog):
    def __init__(self, parent):
        super().__init__(parent, title="Create New Architectural Project", width=420, height=320)

        header = ttk.Label(self, text="New Architecture Project", style='Header.TLabel')
        header.pack(pady=(20, 15))

        form = tk.Frame(self, bg="#1e222d")
        form.pack(fill='x', padx=30)

        ttk.Label(form, text="Project Name:", style='Dark.TLabel').grid(row=0, column=0, sticky='w', pady=8)
        self.name_entry = tk.Entry(form, font=('Segoe UI', 10), bg="#2d3748", fg="#ffffff", insertbackground="white")
        self.name_entry.insert(0, "Luxury Modern Residence")
        self.name_entry.grid(row=0, column=1, sticky='ew', padx=(10, 0))

        ttk.Label(form, text="Total Budget ($ / ₹):", style='Dark.TLabel').grid(row=1, column=0, sticky='w', pady=8)
        self.budget_entry = tk.Entry(form, font=('Segoe UI', 10), bg="#2d3748", fg="#ffffff", insertbackground="white")
        self.budget_entry.insert(0, "150000")
        self.budget_entry.grid(row=1, column=1, sticky='ew', padx=(10, 0))

        ttk.Label(form, text="Measurement Unit:", style='Dark.TLabel').grid(row=2, column=0, sticky='w', pady=8)
        self.unit_combo = ttk.Combobox(form, values=["ft (Feet)", "m (Meters)"], state="readonly", font=('Segoe UI', 9))
        self.unit_combo.current(0)
        self.unit_combo.grid(row=2, column=1, sticky='ew', padx=(10, 0))

        form.columnconfigure(1, weight=1)

        btn_box = tk.Frame(self, bg="#1e222d")
        btn_box.pack(pady=25)

        ttk.Button(btn_box, text="Create Project", style='Dark.TButton', command=self.on_submit).pack(side='left', padx=10, ipadx=10, ipady=4)
        ttk.Button(btn_box, text="Cancel", style='Cancel.TButton', command=self.destroy).pack(side='left', padx=10, ipadx=10, ipady=4)

    def on_submit(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Validation Error", "Please enter a project name.", parent=self)
            return
        try:
            budget = float(self.budget_entry.get().strip())
        except ValueError:
            messagebox.showwarning("Validation Error", "Please enter a valid numeric budget.", parent=self)
            return

        unit = "ft" if "ft" in self.unit_combo.get() else "m"
        self.result = {'name': name, 'budget': budget, 'unit': unit}
        self.destroy()


class EditProjectDialog(BaseDialog):
    def __init__(self, parent, project):
        super().__init__(parent, title="Edit Project Settings", width=420, height=320)

        header = ttk.Label(self, text="Project Settings", style='Header.TLabel')
        header.pack(pady=(20, 15))

        form = tk.Frame(self, bg="#1e222d")
        form.pack(fill='x', padx=30)

        ttk.Label(form, text="Project Name:", style='Dark.TLabel').grid(row=0, column=0, sticky='w', pady=8)
        self.name_entry = tk.Entry(form, font=('Segoe UI', 10), bg="#2d3748", fg="#ffffff", insertbackground="white")
        self.name_entry.insert(0, project['name'])
        self.name_entry.grid(row=0, column=1, sticky='ew', padx=(10, 0))

        ttk.Label(form, text="Total Budget ($ / ₹):", style='Dark.TLabel').grid(row=1, column=0, sticky='w', pady=8)
        self.budget_entry = tk.Entry(form, font=('Segoe UI', 10), bg="#2d3748", fg="#ffffff", insertbackground="white")
        self.budget_entry.insert(0, str(project['budget']))
        self.budget_entry.grid(row=1, column=1, sticky='ew', padx=(10, 0))

        ttk.Label(form, text="Measurement Unit:", style='Dark.TLabel').grid(row=2, column=0, sticky='w', pady=8)
        self.unit_combo = ttk.Combobox(form, values=["ft (Feet)", "m (Meters)"], state="readonly", font=('Segoe UI', 9))
        self.unit_combo.current(0 if project['unit'] == 'ft' else 1)
        self.unit_combo.grid(row=2, column=1, sticky='ew', padx=(10, 0))

        form.columnconfigure(1, weight=1)

        btn_box = tk.Frame(self, bg="#1e222d")
        btn_box.pack(pady=25)

        ttk.Button(btn_box, text="Save Changes", style='Dark.TButton', command=self.on_submit).pack(side='left', padx=10, ipadx=10, ipady=4)
        ttk.Button(btn_box, text="Cancel", style='Cancel.TButton', command=self.destroy).pack(side='left', padx=10, ipadx=10, ipady=4)

    def on_submit(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Validation Error", "Please enter a project name.", parent=self)
            return
        try:
            budget = float(self.budget_entry.get().strip())
        except ValueError:
            messagebox.showwarning("Validation Error", "Please enter a valid numeric budget.", parent=self)
            return

        unit = "ft" if "ft" in self.unit_combo.get() else "m"
        self.result = {'name': name, 'budget': budget, 'unit': unit}
        self.destroy()


class AddRoomDialog(BaseDialog):
    def __init__(self, parent, floors, active_floor_id=None, unit="ft"):
        super().__init__(parent, title="Add Architectural Room", width=460, height=520)
        self.floors = floors
        self.unit = unit

        header = ttk.Label(self, text="Add Room to Blueprint", style='Header.TLabel')
        header.pack(pady=(15, 12))

        form = tk.Frame(self, bg="#1e222d")
        form.pack(fill='both', expand=True, padx=30)

        # Name
        ttk.Label(form, text="Room Name:", style='Dark.TLabel').grid(row=0, column=0, sticky='w', pady=6)
        self.name_entry = tk.Entry(form, font=('Segoe UI', 9), bg="#2d3748", fg="#ffffff", insertbackground="white")
        self.name_entry.insert(0, "Master Bedroom")
        self.name_entry.grid(row=0, column=1, sticky='ew', padx=(10, 0))

        # Room Type
        ttk.Label(form, text="Room Type:", style='Dark.TLabel').grid(row=1, column=0, sticky='w', pady=6)
        self.type_combo = ttk.Combobox(form, values=ROOM_TYPES, state="readonly", font=('Segoe UI', 9))
        self.type_combo.current(1)
        self.type_combo.grid(row=1, column=1, sticky='ew', padx=(10, 0))

        # Floor
        ttk.Label(form, text="Floor Level:", style='Dark.TLabel').grid(row=2, column=0, sticky='w', pady=6)
        floor_names = [f"{f['name']} (Lvl {f['level']})" for f in self.floors]
        self.floor_combo = ttk.Combobox(form, values=floor_names, state="readonly", font=('Segoe UI', 9))
        default_idx = 0
        if active_floor_id:
            for i, f in enumerate(self.floors):
                if f['floor_id'] == active_floor_id:
                    default_idx = i
                    break
        self.floor_combo.current(default_idx)
        self.floor_combo.grid(row=2, column=1, sticky='ew', padx=(10, 0))

        # Width
        ttk.Label(form, text=f"Width ({unit}):", style='Dark.TLabel').grid(row=3, column=0, sticky='w', pady=6)
        self.width_entry = tk.Entry(form, font=('Segoe UI', 9), bg="#2d3748", fg="#ffffff", insertbackground="white")
        self.width_entry.insert(0, "12.0")
        self.width_entry.grid(row=3, column=1, sticky='ew', padx=(10, 0))

        # Length / Height
        ttk.Label(form, text=f"Length ({unit}):", style='Dark.TLabel').grid(row=4, column=0, sticky='w', pady=6)
        self.height_entry = tk.Entry(form, font=('Segoe UI', 9), bg="#2d3748", fg="#ffffff", insertbackground="white")
        self.height_entry.insert(0, "10.0")
        self.height_entry.grid(row=4, column=1, sticky='ew', padx=(10, 0))

        # Estimated Cost
        ttk.Label(form, text="Est. Cost ($ / ₹):", style='Dark.TLabel').grid(row=5, column=0, sticky='w', pady=6)
        self.cost_entry = tk.Entry(form, font=('Segoe UI', 9), bg="#2d3748", fg="#ffffff", insertbackground="white")
        self.cost_entry.insert(0, "14000")
        self.cost_entry.grid(row=5, column=1, sticky='ew', padx=(10, 0))

        # Flooring
        ttk.Label(form, text="Flooring:", style='Dark.TLabel').grid(row=6, column=0, sticky='w', pady=6)
        self.flooring_combo = ttk.Combobox(form, values=FLOORING_OPTIONS, state="readonly", font=('Segoe UI', 9))
        self.flooring_combo.current(1)
        self.flooring_combo.grid(row=6, column=1, sticky='ew', padx=(10, 0))

        # Wall Color
        ttk.Label(form, text="Wall Color:", style='Dark.TLabel').grid(row=7, column=0, sticky='w', pady=6)
        self.wall_combo = ttk.Combobox(form, values=WALL_COLORS, state="readonly", font=('Segoe UI', 9))
        self.wall_combo.current(0)
        self.wall_combo.grid(row=7, column=1, sticky='ew', padx=(10, 0))

        # Windows count
        ttk.Label(form, text="Windows:", style='Dark.TLabel').grid(row=8, column=0, sticky='w', pady=6)
        self.windows_spin = tk.Spinbox(form, from_=0, to=8, font=('Segoe UI', 9), bg="#2d3748", fg="#ffffff", buttonbackground="#374151")
        self.windows_spin.delete(0, 'end')
        self.windows_spin.insert(0, "2")
        self.windows_spin.grid(row=8, column=1, sticky='ew', padx=(10, 0))

        form.columnconfigure(1, weight=1)

        btn_box = tk.Frame(self, bg="#1e222d")
        btn_box.pack(pady=15)

        ttk.Button(btn_box, text="Add Room", style='Dark.TButton', command=self.on_submit).pack(side='left', padx=10, ipadx=10, ipady=4)
        ttk.Button(btn_box, text="Cancel", style='Cancel.TButton', command=self.destroy).pack(side='left', padx=10, ipadx=10, ipady=4)

    def on_submit(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Validation Error", "Please provide a room name.", parent=self)
            return

        try:
            w_units = float(self.width_entry.get().strip())
            h_units = float(self.height_entry.get().strip())
            cost = float(self.cost_entry.get().strip())
            windows = int(self.windows_spin.get().strip())
        except ValueError:
            messagebox.showwarning("Validation Error", "Dimensions, cost, and windows must be numeric.", parent=self)
            return

        if w_units <= 0 or h_units <= 0:
            messagebox.showwarning("Validation Error", "Dimensions must be greater than zero.", parent=self)
            return

        floor_idx = self.floor_combo.current()
        floor_id = self.floors[floor_idx]['floor_id']
        area = w_units * h_units
        # 20 pixels per unit
        width_px = w_units * 20.0
        height_px = h_units * 20.0

        self.result = {
            'name': name,
            'type': self.type_combo.get(),
            'floor_id': floor_id,
            'width': width_px,
            'height': height_px,
            'area': area,
            'cost': cost,
            'flooring': self.flooring_combo.get(),
            'wall_color': self.wall_combo.get(),
            'windows': windows
        }
        self.destroy()


class EditRoomDialog(BaseDialog):
    def __init__(self, parent, room, floors, unit="ft"):
        super().__init__(parent, title="Edit Room Properties", width=460, height=520)
        self.room = room
        self.floors = floors
        self.unit = unit

        header = ttk.Label(self, text="Edit Room Details", style='Header.TLabel')
        header.pack(pady=(15, 12))

        form = tk.Frame(self, bg="#1e222d")
        form.pack(fill='both', expand=True, padx=30)

        # Name
        ttk.Label(form, text="Room Name:", style='Dark.TLabel').grid(row=0, column=0, sticky='w', pady=6)
        self.name_entry = tk.Entry(form, font=('Segoe UI', 9), bg="#2d3748", fg="#ffffff", insertbackground="white")
        self.name_entry.insert(0, room['name'])
        self.name_entry.grid(row=0, column=1, sticky='ew', padx=(10, 0))

        # Room Type
        ttk.Label(form, text="Room Type:", style='Dark.TLabel').grid(row=1, column=0, sticky='w', pady=6)
        self.type_combo = ttk.Combobox(form, values=ROOM_TYPES, state="readonly", font=('Segoe UI', 9))
        if room['type'] in ROOM_TYPES:
            self.type_combo.current(ROOM_TYPES.index(room['type']))
        else:
            self.type_combo.current(0)
        self.type_combo.grid(row=1, column=1, sticky='ew', padx=(10, 0))

        # Floor
        ttk.Label(form, text="Floor Level:", style='Dark.TLabel').grid(row=2, column=0, sticky='w', pady=6)
        floor_names = [f"{f['name']} (Lvl {f['level']})" for f in self.floors]
        self.floor_combo = ttk.Combobox(form, values=floor_names, state="readonly", font=('Segoe UI', 9))
        default_idx = 0
        for i, f in enumerate(self.floors):
            if f['floor_id'] == room['floor_id']:
                default_idx = i
                break
        self.floor_combo.current(default_idx)
        self.floor_combo.grid(row=2, column=1, sticky='ew', padx=(10, 0))

        # Width
        ttk.Label(form, text=f"Width ({unit}):", style='Dark.TLabel').grid(row=3, column=0, sticky='w', pady=6)
        self.width_entry = tk.Entry(form, font=('Segoe UI', 9), bg="#2d3748", fg="#ffffff", insertbackground="white")
        self.width_entry.insert(0, str(round(room['width'] / 20.0, 1)))
        self.width_entry.grid(row=3, column=1, sticky='ew', padx=(10, 0))

        # Length / Height
        ttk.Label(form, text=f"Length ({unit}):", style='Dark.TLabel').grid(row=4, column=0, sticky='w', pady=6)
        self.height_entry = tk.Entry(form, font=('Segoe UI', 9), bg="#2d3748", fg="#ffffff", insertbackground="white")
        self.height_entry.insert(0, str(round(room['height'] / 20.0, 1)))
        self.height_entry.grid(row=4, column=1, sticky='ew', padx=(10, 0))

        # Cost
        ttk.Label(form, text="Est. Cost ($ / ₹):", style='Dark.TLabel').grid(row=5, column=0, sticky='w', pady=6)
        self.cost_entry = tk.Entry(form, font=('Segoe UI', 9), bg="#2d3748", fg="#ffffff", insertbackground="white")
        self.cost_entry.insert(0, str(room['cost']))
        self.cost_entry.grid(row=5, column=1, sticky='ew', padx=(10, 0))

        # Flooring
        ttk.Label(form, text="Flooring:", style='Dark.TLabel').grid(row=6, column=0, sticky='w', pady=6)
        self.flooring_combo = ttk.Combobox(form, values=FLOORING_OPTIONS, state="readonly", font=('Segoe UI', 9))
        if room['flooring'] in FLOORING_OPTIONS:
            self.flooring_combo.current(FLOORING_OPTIONS.index(room['flooring']))
        else:
            self.flooring_combo.current(0)
        self.flooring_combo.grid(row=6, column=1, sticky='ew', padx=(10, 0))

        # Wall Color
        ttk.Label(form, text="Wall Color:", style='Dark.TLabel').grid(row=7, column=0, sticky='w', pady=6)
        self.wall_combo = ttk.Combobox(form, values=WALL_COLORS, state="readonly", font=('Segoe UI', 9))
        if room['wall_color'] in WALL_COLORS:
            self.wall_combo.current(WALL_COLORS.index(room['wall_color']))
        else:
            self.wall_combo.current(0)
        self.wall_combo.grid(row=7, column=1, sticky='ew', padx=(10, 0))

        # Windows
        ttk.Label(form, text="Windows:", style='Dark.TLabel').grid(row=8, column=0, sticky='w', pady=6)
        self.windows_spin = tk.Spinbox(form, from_=0, to=8, font=('Segoe UI', 9), bg="#2d3748", fg="#ffffff", buttonbackground="#374151")
        self.windows_spin.delete(0, 'end')
        self.windows_spin.insert(0, str(room['windows']))
        self.windows_spin.grid(row=8, column=1, sticky='ew', padx=(10, 0))

        form.columnconfigure(1, weight=1)

        btn_box = tk.Frame(self, bg="#1e222d")
        btn_box.pack(pady=15)

        ttk.Button(btn_box, text="Save Room", style='Dark.TButton', command=self.on_submit).pack(side='left', padx=10, ipadx=10, ipady=4)
        ttk.Button(btn_box, text="Cancel", style='Cancel.TButton', command=self.destroy).pack(side='left', padx=10, ipadx=10, ipady=4)

    def on_submit(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Validation Error", "Please provide a room name.", parent=self)
            return

        try:
            w_units = float(self.width_entry.get().strip())
            h_units = float(self.height_entry.get().strip())
            cost = float(self.cost_entry.get().strip())
            windows = int(self.windows_spin.get().strip())
        except ValueError:
            messagebox.showwarning("Validation Error", "Invalid numeric values entered.", parent=self)
            return

        floor_idx = self.floor_combo.current()
        floor_id = self.floors[floor_idx]['floor_id']
        area = w_units * h_units

        self.result = {
            'name': name,
            'type': self.type_combo.get(),
            'floor_id': floor_id,
            'width': w_units * 20.0,
            'height': h_units * 20.0,
            'area': area,
            'cost': cost,
            'flooring': self.flooring_combo.get(),
            'wall_color': self.wall_combo.get(),
            'windows': windows
        }
        self.destroy()


class AddFurnitureDialog(BaseDialog):
    def __init__(self, parent, rooms):
        super().__init__(parent, title="Place Furniture Item", width=420, height=380)
        self.rooms = rooms

        header = ttk.Label(self, text="Add Furniture Item", style='Header.TLabel')
        header.pack(pady=(15, 12))

        form = tk.Frame(self, bg="#1e222d")
        form.pack(fill='both', expand=True, padx=30)

        # Room target
        ttk.Label(form, text="Target Room:", style='Dark.TLabel').grid(row=0, column=0, sticky='w', pady=6)
        room_names = [r['name'] for r in self.rooms]
        self.room_combo = ttk.Combobox(form, values=room_names, state="readonly", font=('Segoe UI', 9))
        self.room_combo.current(0 if room_names else 0)
        self.room_combo.grid(row=0, column=1, sticky='ew', padx=(10, 0))

        # Model / Category
        ttk.Label(form, text="Model Type:", style='Dark.TLabel').grid(row=1, column=0, sticky='w', pady=6)
        model_labels = [label for label, _ in FURNITURE_MODELS]
        self.model_combo = ttk.Combobox(form, values=model_labels, state="readonly", font=('Segoe UI', 9))
        self.model_combo.current(0)
        self.model_combo.grid(row=1, column=1, sticky='ew', padx=(10, 0))
        self.model_combo.bind("<<ComboboxSelected>>", self.on_model_change)

        # Name
        ttk.Label(form, text="Item Label:", style='Dark.TLabel').grid(row=2, column=0, sticky='w', pady=6)
        self.name_entry = tk.Entry(form, font=('Segoe UI', 9), bg="#2d3748", fg="#ffffff", insertbackground="white")
        self.name_entry.insert(0, "Living Room Sofa")
        self.name_entry.grid(row=2, column=1, sticky='ew', padx=(10, 0))

        # Cost
        ttk.Label(form, text="Cost ($ / ₹):", style='Dark.TLabel').grid(row=3, column=0, sticky='w', pady=6)
        self.cost_entry = tk.Entry(form, font=('Segoe UI', 9), bg="#2d3748", fg="#ffffff", insertbackground="white")
        self.cost_entry.insert(0, "1500")
        self.cost_entry.grid(row=3, column=1, sticky='ew', padx=(10, 0))

        # Position
        ttk.Label(form, text="Anchor Position:", style='Dark.TLabel').grid(row=4, column=0, sticky='w', pady=6)
        self.pos_combo = ttk.Combobox(form, values=["Center", "Top-Left", "Top-Right", "Bottom-Left", "Bottom-Right"], state="readonly", font=('Segoe UI', 9))
        self.pos_combo.current(0)
        self.pos_combo.grid(row=4, column=1, sticky='ew', padx=(10, 0))

        form.columnconfigure(1, weight=1)

        btn_box = tk.Frame(self, bg="#1e222d")
        btn_box.pack(pady=15)

        ttk.Button(btn_box, text="Place Item", style='Dark.TButton', command=self.on_submit).pack(side='left', padx=10, ipadx=10, ipady=4)
        ttk.Button(btn_box, text="Cancel", style='Cancel.TButton', command=self.destroy).pack(side='left', padx=10, ipadx=10, ipady=4)

    def on_model_change(self, event=None):
        chosen_label = self.model_combo.get()
        self.name_entry.delete(0, 'end')
        self.name_entry.insert(0, chosen_label)

    def on_submit(self):
        if not self.rooms:
            messagebox.showerror("Error", "No rooms exist on this floor to place furniture.", parent=self)
            return

        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Validation Error", "Please provide a name for the item.", parent=self)
            return

        try:
            cost = float(self.cost_entry.get().strip())
        except ValueError:
            messagebox.showwarning("Validation Error", "Cost must be numeric.", parent=self)
            return

        room_idx = self.room_combo.current()
        room_id = self.rooms[room_idx]['room_id']
        model_idx = self.model_combo.current()
        model_code = FURNITURE_MODELS[model_idx][1]

        self.result = {
            'room_id': room_id,
            'name': name,
            'cost': cost,
            'position': self.pos_combo.get(),
            'model': model_code,
            'x': 40.0,
            'y': 40.0,
            'attached_to': 'floor'
        }
        self.destroy()


class AddFloorDialog(BaseDialog):
    def __init__(self, parent, existing_levels):
        super().__init__(parent, title="Add Architectural Floor Level", width=380, height=280)
        self.existing_levels = existing_levels

        header = ttk.Label(self, text="Add New Floor", style='Header.TLabel')
        header.pack(pady=(15, 12))

        form = tk.Frame(self, bg="#1e222d")
        form.pack(fill='both', expand=True, padx=25)

        ttk.Label(form, text="Floor Name:", style='Dark.TLabel').grid(row=0, column=0, sticky='w', pady=8)
        self.name_entry = tk.Entry(form, font=('Segoe UI', 9), bg="#2d3748", fg="#ffffff", insertbackground="white")
        self.name_entry.insert(0, "Third Floor")
        self.name_entry.grid(row=0, column=1, sticky='ew', padx=(10, 0))

        ttk.Label(form, text="Level Number:", style='Dark.TLabel').grid(row=1, column=0, sticky='w', pady=8)
        # Recommend next level
        next_lvl = max(existing_levels) + 1 if existing_levels else 0
        self.level_spin = tk.Spinbox(form, from_=-5, to=20, font=('Segoe UI', 9), bg="#2d3748", fg="#ffffff", buttonbackground="#374151")
        self.level_spin.delete(0, 'end')
        self.level_spin.insert(0, str(next_lvl))
        self.level_spin.grid(row=1, column=1, sticky='ew', padx=(10, 0))

        form.columnconfigure(1, weight=1)

        btn_box = tk.Frame(self, bg="#1e222d")
        btn_box.pack(pady=15)

        ttk.Button(btn_box, text="Add Floor", style='Dark.TButton', command=self.on_submit).pack(side='left', padx=10, ipadx=10, ipady=4)
        ttk.Button(btn_box, text="Cancel", style='Cancel.TButton', command=self.destroy).pack(side='left', padx=10, ipadx=10, ipady=4)

    def on_submit(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Validation Error", "Please provide a floor name.", parent=self)
            return

        try:
            level = int(self.level_spin.get().strip())
        except ValueError:
            messagebox.showwarning("Validation Error", "Level must be an integer.", parent=self)
            return

        if level in self.existing_levels:
            messagebox.showwarning("Conflict", f"A floor with level {level} already exists.", parent=self)
            return

        self.result = {'name': name, 'level': level}
        self.destroy()


class DBSettingsDialog(BaseDialog):
    def __init__(self, parent, current_status=""):
        super().__init__(parent, title="MySQL Database Configuration", width=460, height=440)
        self.config = load_db_config()

        header = ttk.Label(self, text="MySQL Connection Settings", style='Header.TLabel')
        header.pack(pady=(15, 8))

        status_lbl = tk.Label(self, text=f"Status: {current_status}", bg="#1e222d", fg="#94a3b8", font=('Segoe UI', 8), wraplength=400)
        status_lbl.pack(pady=(0, 10))

        form = tk.Frame(self, bg="#1e222d")
        form.pack(fill='both', expand=True, padx=30)

        # Host
        ttk.Label(form, text="Host:", style='Dark.TLabel').grid(row=0, column=0, sticky='w', pady=6)
        self.host_entry = tk.Entry(form, font=('Segoe UI', 9), bg="#2d3748", fg="#ffffff", insertbackground="white")
        self.host_entry.insert(0, self.config.get('host', 'localhost'))
        self.host_entry.grid(row=0, column=1, sticky='ew', padx=(10, 0))

        # Port
        ttk.Label(form, text="Port:", style='Dark.TLabel').grid(row=1, column=0, sticky='w', pady=6)
        self.port_entry = tk.Entry(form, font=('Segoe UI', 9), bg="#2d3748", fg="#ffffff", insertbackground="white")
        self.port_entry.insert(0, str(self.config.get('port', 3306)))
        self.port_entry.grid(row=1, column=1, sticky='ew', padx=(10, 0))

        # User
        ttk.Label(form, text="Username:", style='Dark.TLabel').grid(row=2, column=0, sticky='w', pady=6)
        self.user_entry = tk.Entry(form, font=('Segoe UI', 9), bg="#2d3748", fg="#ffffff", insertbackground="white")
        self.user_entry.insert(0, self.config.get('user', 'root'))
        self.user_entry.grid(row=2, column=1, sticky='ew', padx=(10, 0))

        # Password
        ttk.Label(form, text="Password:", style='Dark.TLabel').grid(row=3, column=0, sticky='w', pady=6)
        self.pwd_entry = tk.Entry(form, show="*", font=('Segoe UI', 9), bg="#2d3748", fg="#ffffff", insertbackground="white")
        self.pwd_entry.insert(0, self.config.get('password', ''))
        self.pwd_entry.grid(row=3, column=1, sticky='ew', padx=(10, 0))

        # Database
        ttk.Label(form, text="Database Name:", style='Dark.TLabel').grid(row=4, column=0, sticky='w', pady=6)
        self.db_entry = tk.Entry(form, font=('Segoe UI', 9), bg="#2d3748", fg="#ffffff", insertbackground="white")
        self.db_entry.insert(0, self.config.get('database', 'crox_db'))
        self.db_entry.grid(row=4, column=1, sticky='ew', padx=(10, 0))

        # Prefer MySQL check
        self.prefer_var = tk.BooleanVar(value=self.config.get('prefer_mysql', True))
        self.prefer_chk = tk.Checkbutton(form, text="Attempt MySQL connection before SQLite fallback",
                                         variable=self.prefer_var, bg="#1e222d", fg="#e2e8f0",
                                         selectcolor="#2d3748", activebackground="#1e222d", activeforeground="#ffffff")
        self.prefer_chk.grid(row=5, column=0, columnspan=2, sticky='w', pady=10)

        form.columnconfigure(1, weight=1)

        btn_box = tk.Frame(self, bg="#1e222d")
        btn_box.pack(pady=15)

        ttk.Button(btn_box, text="Test Connection", style='Cancel.TButton', command=self.on_test).pack(side='left', padx=5, ipadx=8, ipady=4)
        ttk.Button(btn_box, text="Save & Connect", style='Dark.TButton', command=self.on_save).pack(side='left', padx=5, ipadx=8, ipady=4)
        ttk.Button(btn_box, text="Cancel", style='Cancel.TButton', command=self.destroy).pack(side='left', padx=5, ipadx=8, ipady=4)

    def on_test(self):
        host = self.host_entry.get().strip()
        port = int(self.port_entry.get().strip() or 3306)
        user = self.user_entry.get().strip()
        pwd = self.pwd_entry.get()

        try:
            import mysql.connector
            conn = mysql.connector.connect(host=host, port=port, user=user, password=pwd, connect_timeout=3)
            conn.close()
            messagebox.showinfo("Success", f"Successfully reached MySQL server at {host}:{port}!", parent=self)
        except Exception as e:
            try:
                import pymysql
                conn = pymysql.connect(host=host, port=port, user=user, password=pwd, connect_timeout=3)
                conn.close()
                messagebox.showinfo("Success", f"Successfully reached MySQL server at {host}:{port}!", parent=self)
            except Exception as e2:
                messagebox.showerror("Connection Failed", f"Could not connect to MySQL server:\n{e2}\n\nMake sure MySQL is running (e.g. XAMPP/WAMP or MySQL service).", parent=self)

    def on_save(self):
        new_config = {
            "host": self.host_entry.get().strip(),
            "port": int(self.port_entry.get().strip() or 3306),
            "user": self.user_entry.get().strip(),
            "password": self.pwd_entry.get(),
            "database": self.db_entry.get().strip() or "crox_db",
            "prefer_mysql": self.prefer_var.get()
        }
        save_db_config(new_config)
        self.result = new_config
        self.destroy()


class ProjectSummaryDialog(BaseDialog):
    def __init__(self, parent, summary_data):
        super().__init__(parent, title="Project Analytics & Financial Summary", width=620, height=540)
        self.summary = summary_data
        proj = summary_data['project']

        header = ttk.Label(self, text=f"Architectural Report: {proj['name']}", style='Header.TLabel')
        header.pack(pady=(15, 8))

        # Top metric cards
        metrics_frame = tk.Frame(self, bg="#2d3748", padx=10, pady=8)
        metrics_frame.pack(fill='x', padx=20, pady=5)

        rem_color = "#10b981" if summary_data['remaining_budget'] >= 0 else "#ef4444"

        tk.Label(metrics_frame, text=f"Total Budget:\n${summary_data['project']['budget']:,.2f}", bg="#2d3748", fg="#94a3b8", font=('Segoe UI', 9, 'bold')).pack(side='left', expand=True)
        tk.Label(metrics_frame, text=f"Total Spent:\n${summary_data['total_spending']:,.2f}", bg="#2d3748", fg="#f59e0b", font=('Segoe UI', 9, 'bold')).pack(side='left', expand=True)
        tk.Label(metrics_frame, text=f"Remaining:\n${summary_data['remaining_budget']:,.2f}", bg="#2d3748", fg=rem_color, font=('Segoe UI', 9, 'bold')).pack(side='left', expand=True)
        tk.Label(metrics_frame, text=f"Total Area:\n{summary_data['total_area']:,.1f} sq {proj['unit']}", bg="#2d3748", fg="#60a5fa", font=('Segoe UI', 9, 'bold')).pack(side='left', expand=True)

        # Rooms Table Notebook
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=20, pady=10)

        # Tab 1: Rooms
        rooms_frame = tk.Frame(notebook, bg="#1e222d")
        notebook.add(rooms_frame, text=f"Rooms ({len(summary_data['rooms'])})")

        room_cols = ("Name", "Type", f"Area ({proj['unit']}²)", "Cost ($)", "Flooring", "Wall Color")
        room_tree = ttk.Treeview(rooms_frame, columns=room_cols, show='headings', height=7)
        for col in room_cols:
            room_tree.heading(col, text=col)
            room_tree.column(col, width=90, anchor='center')
        room_tree.column("Name", width=120, anchor='w')

        for r in summary_data['rooms']:
            room_tree.insert('', 'end', values=(
                r['name'], r['type'], f"{r['area']:.1f}", f"${r['cost']:,.2f}", r['flooring'], r['wall_color']
            ))
        room_tree.pack(fill='both', expand=True)

        # Tab 2: Furniture
        furn_frame = tk.Frame(notebook, bg="#1e222d")
        notebook.add(furn_frame, text=f"Furniture ({len(summary_data['furniture'])})")

        furn_cols = ("Item Name", "Cost ($)", "Model", "Anchor")
        furn_tree = ttk.Treeview(furn_frame, columns=furn_cols, show='headings', height=7)
        for col in furn_cols:
            furn_tree.heading(col, text=col)
            furn_tree.column(col, width=120, anchor='center')

        for f in summary_data['furniture']:
            furn_tree.insert('', 'end', values=(
                f['name'], f"${f['cost']:,.2f}", f['model'], f['position']
            ))
        furn_tree.pack(fill='both', expand=True)

        # Close button
        btn_box = tk.Frame(self, bg="#1e222d")
        btn_box.pack(pady=10)
        ttk.Button(btn_box, text="Close Report", style='Dark.TButton', command=self.destroy).pack(ipadx=12, ipady=4)
