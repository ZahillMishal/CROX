"""
CROX — Architecture Blueprint & Budget Management System
Pure Python + MySQL Desktop Edition (Tkinter)

Standalone version:
- Built strictly using Python and MySQL.
- Includes SQLite offline fallback for instant execution.
- Completely isolated in crox_python_mysql/ directory.
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox

# Ensure local package imports work smoothly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crox_python_mysql.database import DatabaseManager
from crox_python_mysql.canvas_view import BlueprintCanvas
from crox_python_mysql.ui_dialogs import (
    NewProjectDialog, EditProjectDialog, AddRoomDialog, EditRoomDialog,
    AddFurnitureDialog, AddFloorDialog, DBSettingsDialog, ProjectSummaryDialog
)


class CroxApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CROX — Architectural Blueprint & Budget Manager (Python + MySQL Edition)")
        self.geometry("1400x880")
        self.minsize(1050, 700)
        self.configure(bg="#0f172a")

        # Initialize Database Manager
        self.db = DatabaseManager()

        # State
        self.current_project = None
        self.current_floor = None
        self.floors = []
        self.active_room_id = None
        self._ignore_tree_select = False

        self._setup_theme()
        self._build_ui()
        self._load_projects()

    def _setup_theme(self):
        style = ttk.Style(self)
        style.theme_use('clam')

        # Global styles
        style.configure('Nav.TFrame', background="#1e293b")
        style.configure('Card.TFrame', background="#1e293b", relief='flat')
        style.configure('Main.TLabel', background="#1e293b", foreground="#f8fafc", font=('Segoe UI', 9))
        style.configure('Title.TLabel', background="#1e293b", foreground="#38bdf8", font=('Segoe UI', 13, 'bold'))
        style.configure('Subtitle.TLabel', background="#1e293b", foreground="#94a3b8", font=('Segoe UI', 8))

        # Buttons
        style.configure('Primary.TButton', background="#2563eb", foreground="#ffffff", font=('Segoe UI', 9, 'bold'), borderwidth=0)
        style.map('Primary.TButton', background=[('active', '#1d4ed8')])

        style.configure('Secondary.TButton', background="#334155", foreground="#f1f5f9", font=('Segoe UI', 9), borderwidth=0)
        style.map('Secondary.TButton', background=[('active', '#475569')])

        style.configure('Danger.TButton', background="#dc2626", foreground="#ffffff", font=('Segoe UI', 8, 'bold'), borderwidth=0)
        style.map('Danger.TButton', background=[('active', '#b91c1c')])

        style.configure('Floor.TButton', background="#1e293b", foreground="#94a3b8", font=('Segoe UI', 9), borderwidth=0)
        style.map('Floor.TButton', background=[('active', '#334155')])

        style.configure('ActiveFloor.TButton', background="#2563eb", foreground="#ffffff", font=('Segoe UI', 9, 'bold'), borderwidth=0)

        # Treeview styling
        style.configure("Treeview", background="#1e293b", foreground="#f8fafc", fieldbackground="#1e293b", font=('Segoe UI', 8))
        style.configure("Treeview.Heading", background="#0f172a", foreground="#94a3b8", font=('Segoe UI', 8, 'bold'))
        style.map("Treeview", background=[('selected', '#2563eb')])

    def _build_ui(self):
        # 1. Top Navbar
        self._build_top_navbar()

        # 2. Floor Selector & Financial Summary Ribbon
        self._build_ribbon()

        # 3. Main Workspace: Left Sidebar | Center Canvas | Right Inspector
        self.workspace = tk.Frame(self, bg="#0f172a")
        self.workspace.pack(fill='both', expand=True, padx=8, pady=(0, 4))

        self._build_left_sidebar()
        self._build_canvas()
        self._build_right_inspector()

        # 4. Bottom Status Bar
        self._build_status_bar()

    # -------------------------------------------------------------
    # 1. Top Navbar
    # -------------------------------------------------------------
    def _build_top_navbar(self):
        nav = tk.Frame(self, bg="#1e293b", height=54, padx=12, pady=6)
        nav.pack(fill='x', side='top')

        # Brand Logo / Title
        brand_frame = tk.Frame(nav, bg="#1e293b")
        brand_frame.pack(side='left', padx=(4, 20))

        tk.Label(brand_frame, text="CROX", font=('Segoe UI', 15, 'bold'), bg="#1e293b", fg="#38bdf8").pack(side='left')
        tk.Label(brand_frame, text="  Architectural Blueprint & Budget System (Python + MySQL)", font=('Segoe UI', 8), bg="#1e293b", fg="#94a3b8").pack(side='left', padx=(5, 0))

        # Project Selector
        proj_frame = tk.Frame(nav, bg="#1e293b")
        proj_frame.pack(side='left', padx=10)

        tk.Label(proj_frame, text="Project:", font=('Segoe UI', 9, 'bold'), bg="#1e293b", fg="#cbd5e1").pack(side='left', padx=(0, 6))
        self.project_combo = ttk.Combobox(proj_frame, state="readonly", width=25, font=('Segoe UI', 9))
        self.project_combo.pack(side='left')
        self.project_combo.bind("<<ComboboxSelected>>", self.on_project_changed)

        ttk.Button(proj_frame, text="+ New", style='Primary.TButton', command=self.action_new_project).pack(side='left', padx=5, ipady=2)
        ttk.Button(proj_frame, text="Edit", style='Secondary.TButton', command=self.action_edit_project).pack(side='left', padx=3, ipady=2)
        ttk.Button(proj_frame, text="Delete", style='Danger.TButton', command=self.action_delete_project).pack(side='left', padx=3, ipady=2)

        # Right Action Buttons
        actions_frame = tk.Frame(nav, bg="#1e293b")
        actions_frame.pack(side='right', padx=5)

        ttk.Button(actions_frame, text="📊 Analytics & Report", style='Secondary.TButton', command=self.action_view_summary).pack(side='left', padx=5, ipady=2)
        ttk.Button(actions_frame, text="⚙ Database Settings", style='Secondary.TButton', command=self.action_db_settings).pack(side='left', padx=5, ipady=2)

    # -------------------------------------------------------------
    # 2. Floor Selector & Financial Ribbon
    # -------------------------------------------------------------
    def _build_ribbon(self):
        ribbon = tk.Frame(self, bg="#0f172a", height=50, padx=12, pady=6)
        ribbon.pack(fill='x', side='top')

        # Floor Tabs container
        self.floors_bar = tk.Frame(ribbon, bg="#0f172a")
        self.floors_bar.pack(side='left', fill='y')

        # Financial Cards on the right
        self.finance_frame = tk.Frame(ribbon, bg="#0f172a")
        self.finance_frame.pack(side='right', fill='y')

        self.lbl_budget = tk.Label(self.finance_frame, text="Budget: $0", bg="#1e293b", fg="#38bdf8", font=('Segoe UI', 8, 'bold'), padx=8, pady=4)
        self.lbl_budget.pack(side='left', padx=4)

        self.lbl_spent = tk.Label(self.finance_frame, text="Spent: $0", bg="#1e293b", fg="#f59e0b", font=('Segoe UI', 8, 'bold'), padx=8, pady=4)
        self.lbl_spent.pack(side='left', padx=4)

        self.lbl_remaining = tk.Label(self.finance_frame, text="Remaining: $0", bg="#1e293b", fg="#10b981", font=('Segoe UI', 8, 'bold'), padx=8, pady=4)
        self.lbl_remaining.pack(side='left', padx=4)

        self.lbl_area = tk.Label(self.finance_frame, text="Area: 0 sq ft", bg="#1e293b", fg="#cbd5e1", font=('Segoe UI', 8), padx=8, pady=4)
        self.lbl_area.pack(side='left', padx=4)

    def _render_floor_buttons(self):
        for widget in self.floors_bar.winfo_children():
            widget.destroy()

        tk.Label(self.floors_bar, text="Floors: ", bg="#0f172a", fg="#94a3b8", font=('Segoe UI', 8, 'bold')).pack(side='left', padx=(0, 4))

        for f in self.floors:
            is_active = (self.current_floor and f['floor_id'] == self.current_floor['floor_id'])
            btn_style = 'ActiveFloor.TButton' if is_active else 'Floor.TButton'
            btn_text = f"{f['name']} (L{f['level']})"
            btn = ttk.Button(self.floors_bar, text=btn_text, style=btn_style,
                             command=lambda fl=f: self.switch_floor(fl))
            btn.pack(side='left', padx=2, ipady=1)

        ttk.Button(self.floors_bar, text="+ Add Floor", style='Secondary.TButton', command=self.action_add_floor).pack(side='left', padx=(6, 2), ipady=1)
        if len(self.floors) > 1:
            ttk.Button(self.floors_bar, text="- Remove Floor", style='Secondary.TButton', command=self.action_delete_floor).pack(side='left', padx=2, ipady=1)

    # -------------------------------------------------------------
    # 3. Main Workspace: Left Sidebar
    # -------------------------------------------------------------
    def _build_left_sidebar(self):
        sidebar = tk.Frame(self.workspace, bg="#1e293b", width=260)
        sidebar.pack(side='left', fill='y', padx=(0, 6))
        sidebar.pack_propagate(False)

        # Rooms Header
        rooms_head = tk.Frame(sidebar, bg="#1e293b", padx=8, pady=6)
        rooms_head.pack(fill='x')
        tk.Label(rooms_head, text="Rooms on this Floor", font=('Segoe UI', 9, 'bold'), bg="#1e293b", fg="#38bdf8").pack(side='left')
        ttk.Button(rooms_head, text="+ Add Room", style='Primary.TButton', command=self.action_add_room).pack(side='right', ipadx=4)

        # Rooms Treeview
        r_cols = ("Name", "Type", "Area")
        self.rooms_tree = ttk.Treeview(sidebar, columns=r_cols, show='headings', height=7, selectmode='browse')
        self.rooms_tree.heading("Name", text="Name")
        self.rooms_tree.heading("Type", text="Type")
        self.rooms_tree.heading("Area", text="Area")
        self.rooms_tree.column("Name", width=95, anchor='w')
        self.rooms_tree.column("Type", width=75, anchor='w')
        self.rooms_tree.column("Area", width=55, anchor='center')
        self.rooms_tree.pack(fill='x', padx=8, pady=(0, 6))
        self.rooms_tree.bind("<<TreeviewSelect>>", self.on_room_tree_select)

        # Room Action quick buttons
        r_btn_box = tk.Frame(sidebar, bg="#1e293b", padx=8)
        r_btn_box.pack(fill='x', pady=(0, 8))
        ttk.Button(r_btn_box, text="🔄 Rotate", style='Secondary.TButton', command=lambda: self.canvas_view.action_rotate_room()).pack(side='left', expand=True, fill='x', padx=1)
        ttk.Button(r_btn_box, text="📋 Duplicate", style='Secondary.TButton', command=lambda: self.canvas_view.action_duplicate_room()).pack(side='left', expand=True, fill='x', padx=1)
        ttk.Button(r_btn_box, text="🗑 Delete", style='Danger.TButton', command=lambda: self.canvas_view.action_delete_room()).pack(side='left', expand=True, fill='x', padx=1)

        # Furniture Section Header
        furn_head = tk.Frame(sidebar, bg="#1e293b", padx=8, pady=6)
        furn_head.pack(fill='x')
        tk.Label(furn_head, text="Furniture in Room", font=('Segoe UI', 9, 'bold'), bg="#1e293b", fg="#f59e0b").pack(side='left')
        ttk.Button(furn_head, text="+ Add Item", style='Secondary.TButton', command=self.action_add_furniture_direct).pack(side='right', ipadx=4)

        # Furniture Treeview
        f_cols = ("Item", "Cost", "Model")
        self.furn_tree = ttk.Treeview(sidebar, columns=f_cols, show='headings', height=7, selectmode='browse')
        self.furn_tree.heading("Item", text="Item")
        self.furn_tree.heading("Cost", text="Cost")
        self.furn_tree.heading("Model", text="Model")
        self.furn_tree.column("Item", width=110, anchor='w')
        self.furn_tree.column("Cost", width=60, anchor='center')
        self.furn_tree.column("Model", width=55, anchor='center')
        self.furn_tree.pack(fill='both', expand=True, padx=8, pady=(0, 6))

        # Furniture Delete button
        f_btn_box = tk.Frame(sidebar, bg="#1e293b", padx=8, pady=4)
        f_btn_box.pack(fill='x')
        ttk.Button(f_btn_box, text="🗑 Remove Selected Item", style='Danger.TButton', command=self.action_delete_furniture).pack(fill='x')

    # -------------------------------------------------------------
    # 3. Main Workspace: Center Canvas
    # -------------------------------------------------------------
    def _build_canvas(self):
        callbacks = {
            'on_select_room': self.on_canvas_select_room,
            'on_data_changed': self.on_canvas_data_changed,
            'on_edit_room': self.action_edit_room_by_id,
            'on_add_furniture': self.action_add_furniture_by_room_id
        }
        self.canvas_view = BlueprintCanvas(self.workspace, self.db, callbacks)
        self.canvas_view.pack(side='left', fill='both', expand=True)

    # -------------------------------------------------------------
    # 3. Main Workspace: Right Inspector
    # -------------------------------------------------------------
    def _build_right_inspector(self):
        self.inspector = tk.Frame(self.workspace, bg="#1e293b", width=240)
        self.inspector.pack(side='right', fill='y', padx=(6, 0))
        self.inspector.pack_propagate(False)

        head = tk.Frame(self.inspector, bg="#1e293b", padx=10, pady=8)
        head.pack(fill='x')
        tk.Label(head, text="Property Inspector", font=('Segoe UI', 10, 'bold'), bg="#1e293b", fg="#38bdf8").pack(side='left')

        # Properties content
        self.props_frame = tk.Frame(self.inspector, bg="#1e293b", padx=10)
        self.props_frame.pack(fill='both', expand=True)

        self._render_inspector_empty()

    def _render_inspector_empty(self):
        for widget in self.props_frame.winfo_children():
            widget.destroy()

        tk.Label(self.props_frame, text="No room selected.\n\nClick on any room on the blueprint canvas to inspect and edit its properties.",
                 bg="#1e293b", fg="#64748b", font=('Segoe UI', 8), justify='center', wraplength=200).pack(pady=40)

    def _render_inspector_room(self, room):
        for widget in self.props_frame.winfo_children():
            widget.destroy()

        unit = self.current_project.get('unit', 'ft')
        w_units = round(room['width'] / 20.0, 1)
        h_units = round(room['height'] / 20.0, 1)

        furniture_items = self.db.get_furniture(room['room_id'])
        furn_cost = sum(f['cost'] for f in furniture_items)
        total_room_cost = room['cost'] + furn_cost

        props = [
            ("Room Name:", room['name']),
            ("Room Type:", room['type']),
            ("Dimensions:", f"{w_units} × {h_units} {unit}"),
            ("Calculated Area:", f"{room['area']:.1f} sq {unit}"),
            ("Flooring:", room['flooring']),
            ("Wall Color:", room['wall_color']),
            ("Windows:", f"{room['windows']} windows"),
            ("Base Cost:", f"${room['cost']:,.2f}"),
            ("Furniture Cost:", f"${furn_cost:,.2f}"),
            ("Total Room Cost:", f"${total_room_cost:,.2f}"),
        ]

        for label, val in props:
            row = tk.Frame(self.props_frame, bg="#1e293b")
            row.pack(fill='x', pady=3)
            tk.Label(row, text=label, bg="#1e293b", fg="#94a3b8", font=('Segoe UI', 8)).pack(side='left')
            color = "#38bdf8" if "Total" in label else "#f1f5f9"
            tk.Label(row, text=val, bg="#1e293b", fg=color, font=('Segoe UI', 8, 'bold')).pack(side='right')

        # Edit button
        ttk.Button(self.props_frame, text="✏ Edit Properties", style='Primary.TButton',
                   command=lambda: self.action_edit_room_by_id(room['room_id'])).pack(fill='x', pady=(15, 5))

    # -------------------------------------------------------------
    # 4. Status Bar
    # -------------------------------------------------------------
    def _build_status_bar(self):
        status_bar = tk.Frame(self, bg="#0f172a", height=24, padx=12, pady=2)
        status_bar.pack(fill='x', side='bottom')

        self.lbl_status = tk.Label(status_bar, text=f"Database: {self.db.status_message}", bg="#0f172a", fg="#94a3b8", font=('Segoe UI', 8))
        self.lbl_status.pack(side='left')

        tip = "💡 Tip: Drag rooms with mouse to magnetically snap adjoining walls and auto-generate doorways and stairs."
        tk.Label(status_bar, text=tip, bg="#0f172a", fg="#64748b", font=('Segoe UI', 8)).pack(side='right')

    # -------------------------------------------------------------
    # Data Loading & Floor Switching
    # -------------------------------------------------------------
    def _load_projects(self):
        projects = self.db.get_all_projects()
        if not projects:
            p_id = self.db.create_project("My First Architecture Project", 100000.0, "ft")
            projects = self.db.get_all_projects()

        names = [f"{p['name']} (${p['budget']:,.0f})" for p in projects]
        self.project_combo['values'] = names
        self.project_combo.current(0)
        self.current_project = projects[0]

        self._load_floors_for_project()

    def _load_floors_for_project(self):
        if not self.current_project:
            return
        p_id = self.current_project['project_id']
        self.floors = self.db.get_floors(p_id)
        if not self.floors:
            self.db._create_default_floors(p_id)
            self.floors = self.db.get_floors(p_id)

        # Default to Ground Floor (level 0) or first floor
        ground = next((f for f in self.floors if f['level'] == 0), self.floors[0])
        self.switch_floor(ground)

    def switch_floor(self, floor):
        self.current_floor = floor
        self._render_floor_buttons()
        self.canvas_view.set_data(
            self.current_project['project_id'],
            self.current_floor['floor_id'],
            self.current_project.get('unit', 'ft')
        )
        self.active_room_id = None
        self._refresh_all_views()

    def _refresh_all_views(self):
        if not self.current_project or not self.current_floor:
            return

        self._ignore_tree_select = True
        try:
            p_id = self.current_project['project_id']
            f_id = self.current_floor['floor_id']
            unit = self.current_project.get('unit', 'ft')

            # 1. Update Financial Ribbon
            summary = self.db.get_project_summary(p_id)
            if summary:
                self.lbl_budget.config(text=f"Total Budget: ${summary['project']['budget']:,.2f}")
                self.lbl_spent.config(text=f"Total Spent: ${summary['total_spending']:,.2f}")
                rem = summary['remaining_budget']
                rem_col = "#10b981" if rem >= 0 else "#ef4444"
                self.lbl_remaining.config(text=f"Remaining: ${rem:,.2f}", fg=rem_col)
                self.lbl_area.config(text=f"Total Area: {summary['total_area']:,.1f} sq {unit}")

            # 2. Update Rooms Treeview
            for item in self.rooms_tree.get_children():
                self.rooms_tree.delete(item)

            floor_rooms = self.db.get_rooms(p_id, f_id)
            for r in floor_rooms:
                self.rooms_tree.insert('', 'end', iid=r['room_id'], values=(
                    r['name'], r['type'], f"{r['area']:.0f} {unit}²"
                ))

            # Select in treeview if active
            if self.active_room_id and self.active_room_id in [r['room_id'] for r in floor_rooms]:
                try:
                    self.rooms_tree.selection_set(self.active_room_id)
                except Exception:
                    pass

            # 3. Update Furniture Treeview & Inspector
            if self.active_room_id:
                room = self.db.get_room(self.active_room_id)
                if room:
                    self._render_inspector_room(room)
                    self._refresh_furniture_tree(self.active_room_id)
                else:
                    self.active_room_id = None
                    self._render_inspector_empty()
                    self._refresh_furniture_tree(None)
            else:
                self._render_inspector_empty()
                self._refresh_furniture_tree(None)
        finally:
            self._ignore_tree_select = False

    def _refresh_furniture_tree(self, room_id):
        for item in self.furn_tree.get_children():
            self.furn_tree.delete(item)

        if not room_id:
            return

        furniture_items = self.db.get_furniture(room_id)
        for f in furniture_items:
            self.furn_tree.insert('', 'end', iid=f['furniture_id'], values=(
                f['name'], f"${f['cost']:,.0f}", f['model']
            ))

    # -------------------------------------------------------------
    # Callbacks from Canvas
    # -------------------------------------------------------------
    def on_canvas_select_room(self, room_id):
        self.active_room_id = room_id
        self._refresh_all_views()

    def on_canvas_data_changed(self):
        self._refresh_all_views()

    def on_room_tree_select(self, event):
        if getattr(self, '_ignore_tree_select', False):
            return
        selected = self.rooms_tree.selection()
        if selected:
            r_id = selected[0]
            if r_id != self.active_room_id:
                self.active_room_id = r_id
                self.canvas_view.selected_room_id = r_id
                self.canvas_view.render()
                self._refresh_all_views()

    def on_project_changed(self, event=None):
        idx = self.project_combo.current()
        projects = self.db.get_all_projects()
        if 0 <= idx < len(projects):
            self.current_project = projects[idx]
            self._load_floors_for_project()

    # -------------------------------------------------------------
    # Actions: Projects
    # -------------------------------------------------------------
    def action_new_project(self):
        dlg = NewProjectDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            p_id = self.db.create_project(
                dlg.result['name'],
                dlg.result['budget'],
                dlg.result['unit']
            )
            self._load_projects()
            # Select new project
            projects = self.db.get_all_projects()
            for i, p in enumerate(projects):
                if p['project_id'] == p_id:
                    self.project_combo.current(i)
                    self.current_project = p
                    self._load_floors_for_project()
                    break

    def action_edit_project(self):
        if not self.current_project:
            return
        dlg = EditProjectDialog(self, self.current_project)
        self.wait_window(dlg)
        if dlg.result:
            self.db.update_project(
                self.current_project['project_id'],
                dlg.result['name'],
                dlg.result['budget'],
                dlg.result['unit']
            )
            self.current_project = self.db.get_project(self.current_project['project_id'])
            self._load_projects()

    def action_delete_project(self):
        if not self.current_project:
            return
        projects = self.db.get_all_projects()
        if len(projects) <= 1:
            messagebox.showwarning("Notice", "You cannot delete the only existing project.", parent=self)
            return

        if messagebox.askyesno("Delete Project", f"Are you sure you want to delete '{self.current_project['name']}' and all its rooms?", parent=self):
            self.db.delete_project(self.current_project['project_id'])
            self._load_projects()

    def action_view_summary(self):
        if not self.current_project:
            return
        summary = self.db.get_project_summary(self.current_project['project_id'])
        dlg = ProjectSummaryDialog(self, summary)

    def action_db_settings(self):
        dlg = DBSettingsDialog(self, self.db.status_message)
        self.wait_window(dlg)
        if dlg.result:
            self.db.initialize_connection()
            self.lbl_status.config(text=f"Database: {self.db.status_message}")
            self._load_projects()

    # -------------------------------------------------------------
    # Actions: Floors
    # -------------------------------------------------------------
    def action_add_floor(self):
        if not self.current_project:
            return
        levels = [f['level'] for f in self.floors]
        dlg = AddFloorDialog(self, levels)
        self.wait_window(dlg)
        if dlg.result:
            new_f_id = self.db.add_floor(
                self.current_project['project_id'],
                dlg.result['name'],
                dlg.result['level']
            )
            self.floors = self.db.get_floors(self.current_project['project_id'])
            new_floor = next((f for f in self.floors if f['floor_id'] == new_f_id), self.floors[0])
            self.switch_floor(new_floor)

    def action_delete_floor(self):
        if len(self.floors) <= 1:
            messagebox.showwarning("Notice", "At least one floor must remain.", parent=self)
            return
        if messagebox.askyesno("Delete Floor", f"Delete '{self.current_floor['name']}' and all its rooms?", parent=self):
            self.db.delete_floor(self.current_floor['floor_id'])
            self.floors = self.db.get_floors(self.current_project['project_id'])
            self.switch_floor(self.floors[0])

    # -------------------------------------------------------------
    # Actions: Rooms
    # -------------------------------------------------------------
    def action_add_room(self):
        if not self.current_project or not self.current_floor:
            return
        dlg = AddRoomDialog(
            self,
            self.floors,
            active_floor_id=self.current_floor['floor_id'],
            unit=self.current_project.get('unit', 'ft')
        )
        self.wait_window(dlg)
        if dlg.result:
            r = dlg.result
            new_id = self.db.add_room(
                project_id=self.current_project['project_id'],
                floor_id=r['floor_id'],
                name=r['name'],
                room_type=r['type'],
                cost=r['cost'],
                width=r['width'],
                height=r['height'],
                area=r['area'],
                flooring=r['flooring'],
                wall_color=r['wall_color'],
                windows=r['windows'],
                x=60.0 + (len(self.rooms_tree.get_children()) * 25.0),
                y=60.0 + (len(self.rooms_tree.get_children()) * 25.0)
            )
            self.active_room_id = new_id
            self.canvas_view.selected_room_id = new_id
            self.canvas_view.refresh()
            self._refresh_all_views()

    def action_edit_room_by_id(self, room_id):
        room = self.db.get_room(room_id)
        if not room:
            return
        dlg = EditRoomDialog(
            self,
            room,
            self.floors,
            unit=self.current_project.get('unit', 'ft')
        )
        self.wait_window(dlg)
        if dlg.result:
            res = dlg.result
            self.db.update_room_details(
                room_id,
                res['name'],
                res['type'],
                res['cost'],
                res['flooring'],
                res['wall_color'],
                res['windows']
            )
            self.db.update_room_size(room_id, res['width'], res['height'], res['area'])
            if res['floor_id'] != room['floor_id']:
                self.db.update_room_floor(room_id, res['floor_id'])

            self.canvas_view.refresh()
            self._refresh_all_views()

    # -------------------------------------------------------------
    # Actions: Furniture
    # -------------------------------------------------------------
    def action_add_furniture_direct(self):
        floor_rooms = self.db.get_rooms(self.current_project['project_id'], self.current_floor['floor_id'])
        if not floor_rooms:
            messagebox.showinfo("Info", "Add a room to this floor first before placing furniture.", parent=self)
            return

        dlg = AddFurnitureDialog(self, floor_rooms)
        self.wait_window(dlg)
        if dlg.result:
            r = dlg.result
            self.db.add_furniture(
                r['room_id'], r['name'], r['cost'], r['position'], r['model'], r['x'], r['y'], r['attached_to']
            )
            self.canvas_view.refresh()
            self._refresh_all_views()

    def action_add_furniture_by_room_id(self, room_id):
        room = self.db.get_room(room_id)
        if not room:
            return
        dlg = AddFurnitureDialog(self, [room])
        self.wait_window(dlg)
        if dlg.result:
            r = dlg.result
            self.db.add_furniture(
                r['room_id'], r['name'], r['cost'], r['position'], r['model'], r['x'], r['y'], r['attached_to']
            )
            self.canvas_view.refresh()
            self._refresh_all_views()

    def action_delete_furniture(self):
        selected = self.furn_tree.selection()
        if not selected:
            messagebox.showinfo("Select Item", "Please select a furniture item from the list to remove.", parent=self)
            return
        furn_id = selected[0]
        if messagebox.askyesno("Remove Item", "Remove this furniture item from the room?", parent=self):
            self.db.delete_furniture(furn_id)
            self.canvas_view.refresh()
            self._refresh_all_views()


def main():
    app = CroxApp()
    app.mainloop()


if __name__ == '__main__':
    main()
