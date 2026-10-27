"""
Interactive 2D Blueprint Canvas Module for CROX Python + MySQL Version.
Handles CAD-style grid, rooms with magnetic snapping, doorways, staircases,
furniture rendering, mouse dragging, and context menus.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import math

# Color palette for architectural styling
WALL_PALETTE = {
    "White": ("#f8fafc", "#334155"),
    "Warm Beige": ("#fef3c7", "#78350f"),
    "Slate Gray": ("#e2e8f0", "#475569"),
    "Sage Green": ("#dcfce7", "#166534"),
    "Deep Navy": ("#e0f2fe", "#0369a1"),
    "Terracotta": ("#ffedd5", "#9a3412"),
    "Soft Peach": ("#ffe4e6", "#9f1239"),
    "Charcoal": ("#cbd5e1", "#1e293b")
}

FURNITURE_COLORS = {
    "sofa": ("#6366f1", "#4338ca", "SOFA"),
    "bed": ("#8b5cf6", "#6d28d9", "BED"),
    "table": ("#f59e0b", "#b45309", "TABLE"),
    "desk": ("#10b981", "#047857", "DESK"),
    "chair": ("#06b6d4", "#0e7490", "CHAIR"),
    "wardrobe": ("#ec4899", "#be185d", "WARDROBE"),
    "counter": ("#64748b", "#334155", "COUNTER"),
    "bath": ("#38bdf8", "#0284c7", "BATH"),
    "shelf": ("#a855f7", "#7e22ce", "SHELF"),
    "tv": ("#1e293b", "#0f172a", "TV"),
    "plant": ("#22c55e", "#15803d", "PLANT"),
    "box": ("#94a3b8", "#64748b", "ITEM")
}


class BlueprintCanvas(tk.Frame):
    def __init__(self, parent, db, callbacks):
        super().__init__(parent, bg="#0f172a")
        self.db = db
        self.callbacks = callbacks  # Dict of callback functions

        self.current_project_id = None
        self.current_floor_id = None
        self.current_unit = "ft"

        self.rooms = []
        self.all_project_rooms = []
        self.floors = []
        self.furniture_by_room = {}

        self.selected_room_id = None
        self.selected_furn_id = None

        # Drag state
        self.drag_item_type = None  # 'room' or 'furniture'
        self.drag_item_id = None
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_orig_x = 0
        self.drag_orig_y = 0

        # Create canvas with scrollbars
        self.canvas = tk.Canvas(self, bg="#0f172a", highlightthickness=0)
        self.h_scroll = ttk.Scrollbar(self, orient='horizontal', command=self.canvas.xview)
        self.v_scroll = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)

        self.h_scroll.pack(side='bottom', fill='x')
        self.v_scroll.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)

        self.canvas.configure(scrollregion=(0, 0, 2400, 1800))

        # Event bindings
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<B1-Motion>", self.on_left_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_left_release)
        self.canvas.bind("<Button-3>", self.on_right_click)

        # Context Menu
        self.context_menu = tk.Menu(self, tearoff=0, bg="#1e293b", fg="#f1f5f9", activebackground="#2563eb", activeforeground="#ffffff")
        self.context_menu.add_command(label="Rotate 90°", command=self.action_rotate_room)
        self.context_menu.add_command(label="Duplicate Room", command=self.action_duplicate_room)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="+ Add Furniture Here", command=self.action_add_furniture)
        self.context_menu.add_command(label="Edit Room Properties", command=self.action_edit_room)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Delete Room", command=self.action_delete_room)

    def set_data(self, project_id, floor_id, unit="ft"):
        self.current_project_id = project_id
        self.current_floor_id = floor_id
        self.current_unit = unit
        self.refresh()

    def refresh(self):
        if not self.current_project_id or not self.current_floor_id:
            self.canvas.delete("all")
            return

        self.floors = self.db.get_floors(self.current_project_id)
        self.all_project_rooms = self.db.get_rooms(self.current_project_id)
        self.rooms = [r for r in self.all_project_rooms if r['floor_id'] == self.current_floor_id]

        self.furniture_by_room = {}
        for r in self.rooms:
            self.furniture_by_room[r['room_id']] = self.db.get_furniture(r['room_id'])

        self.render()

    def render(self):
        self.canvas.delete("all")
        self._draw_grid()
        self._draw_rooms()
        self._draw_staircases()
        self._draw_doorways()
        self._draw_furniture()

    # -------------------------------------------------------------
    # Grid Rendering
    # -------------------------------------------------------------
    def _draw_grid(self):
        # Subtle architectural grid (20px = 1 ft/m)
        w, h = 2400, 1800
        step = 20
        # Draw minor grid lines
        for x in range(0, w, step):
            color = "#1e293b" if x % 100 != 0 else "#334155"
            self.canvas.create_line(x, 0, x, h, fill=color, width=1, tags="grid")

        for y in range(0, h, step):
            color = "#1e293b" if y % 100 != 0 else "#334155"
            self.canvas.create_line(0, y, w, y, fill=color, width=1, tags="grid")

        # Ruler text marks
        for x in range(100, w, 100):
            units = int(x / 20)
            self.canvas.create_text(x + 2, 10, text=f"{units}{self.current_unit}", fill="#64748b", font=('Segoe UI', 7), anchor='nw', tags="grid")

        for y in range(100, h, 100):
            units = int(y / 20)
            self.canvas.create_text(10, y + 2, text=f"{units}{self.current_unit}", fill="#64748b", font=('Segoe UI', 7), anchor='nw', tags="grid")

    # -------------------------------------------------------------
    # Room Rendering
    # -------------------------------------------------------------
    def _draw_rooms(self):
        for room in self.rooms:
            r_id = room['room_id']
            x1 = room['x']
            y1 = room['y']
            x2 = x1 + room['width']
            y2 = y1 + room['height']

            fill_bg, border_color = WALL_PALETTE.get(room['wall_color'], ("#f8fafc", "#334155"))
            is_selected = (r_id == self.selected_room_id)

            # Room shadow
            self.canvas.create_rectangle(x1 + 3, y1 + 3, x2 + 3, y2 + 3, fill="#050811", outline="", tags=(f"room_{r_id}", "room"))

            # Room floor body
            outline_color = "#38bdf8" if is_selected else border_color
            outline_width = 3 if is_selected else 2

            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=fill_bg,
                outline=outline_color,
                width=outline_width,
                tags=(f"room_{r_id}", "room", "room_body")
            )

            # Header Banner
            banner_height = 28
            self.canvas.create_rectangle(
                x1, y1, x2, y1 + banner_height,
                fill=border_color,
                outline="",
                tags=(f"room_{r_id}", "room")
            )

            # Room Title Text
            w_units = round(room['width'] / 20.0, 1)
            h_units = round(room['height'] / 20.0, 1)
            header_text = f"{room['name']}  ({w_units} × {h_units} {self.current_unit})"
            self.canvas.create_text(
                x1 + 8, y1 + 14,
                text=header_text,
                fill="#ffffff",
                font=('Segoe UI', 9, 'bold'),
                anchor='w',
                tags=(f"room_{r_id}", "room")
            )

            # Footer / Area & Flooring badge
            footer_text = f"{room['type']} • {room['area']:.1f} sq {self.current_unit} • {room['flooring']}"
            self.canvas.create_text(
                x1 + 10, y2 - 12,
                text=footer_text,
                fill="#64748b",
                font=('Segoe UI', 8),
                anchor='w',
                tags=(f"room_{r_id}", "room")
            )

            # Window markers along walls
            if room['windows'] > 0:
                self._draw_room_windows(x1, y1, x2, y2, room['windows'], r_id)

    def _draw_room_windows(self, x1, y1, x2, y2, count, r_id):
        """Draws small architectural window symbols along outer walls."""
        w = x2 - x1
        spacing = w / (count + 1)
        for i in range(1, count + 1):
            wx = x1 + (spacing * i)
            # Top wall window
            self.canvas.create_rectangle(wx - 10, y1 - 2, wx + 10, y1 + 2, fill="#38bdf8", outline="#0284c7", tags=(f"room_{r_id}", "window"))

    # -------------------------------------------------------------
    # Doorways Detection & Rendering
    # -------------------------------------------------------------
    def _draw_doorways(self):
        """Finds adjoining snapped rooms on current floor and draws doorways."""
        for i in range(len(self.rooms)):
            for j in range(i + 1, len(self.rooms)):
                A = self.rooms[i]
                B = self.rooms[j]

                aL, aT = A['x'], A['y']
                aR, aB = aL + A['width'], aT + A['height']
                bL, bT = B['x'], B['y']
                bR, bB = bL + B['width'], bT + B['height']

                overlapX = max(0, min(aR, bR) - max(aL, bL))
                overlapY = max(0, min(aB, bB) - max(aT, bT))

                # Horizontal adjacency (Left-Right shared wall)
                if abs(aR - bL) <= 4 or abs(bR - aL) <= 4:
                    if overlapY >= 40:
                        wallX = (aR + bL) / 2 if abs(aR - bL) <= 4 else (bR + aL) / 2
                        doorY = max(aT, bT) + (overlapY / 2)
                        self._render_doorway_symbol(wallX, doorY, is_vertical=True)

                # Vertical adjacency (Top-Bottom shared wall)
                elif abs(aB - bT) <= 4 or abs(bB - aT) <= 4:
                    if overlapX >= 40:
                        wallY = (aB + bT) / 2 if abs(aB - bT) <= 4 else (bB + aT) / 2
                        doorX = max(aL, bL) + (overlapX / 2)
                        self._render_doorway_symbol(doorX, wallY, is_vertical=False)

    def _render_doorway_symbol(self, cx, cy, is_vertical):
        """Draws an open architectural door swing symbol."""
        door_size = 24
        if is_vertical:
            # Door opening gap
            self.canvas.create_rectangle(cx - 3, cy - door_size // 2, cx + 3, cy + door_size // 2, fill="#f8fafc", outline="", tags="doorway")
            # Swing arc
            self.canvas.create_arc(cx - door_size, cy - door_size, cx + door_size, cy + door_size,
                                   start=0, extent=90, style='arc', outline="#f59e0b", width=2, tags="doorway")
            # Door leaf line
            self.canvas.create_line(cx, cy, cx, cy - door_size, fill="#d97706", width=2, tags="doorway")
        else:
            self.canvas.create_rectangle(cx - door_size // 2, cy - 3, cx + door_size // 2, cy + 3, fill="#f8fafc", outline="", tags="doorway")
            self.canvas.create_arc(cx - door_size, cy - door_size, cx + door_size, cy + door_size,
                                   start=270, extent=90, style='arc', outline="#f59e0b", width=2, tags="doorway")
            self.canvas.create_line(cx, cy, cx + door_size, cy, fill="#d97706", width=2, tags="doorway")

    # -------------------------------------------------------------
    # Staircases Detection & Rendering
    # -------------------------------------------------------------
    def _draw_staircases(self):
        """Detects overlapping rooms with adjacent floor levels and draws stairs."""
        floor_level_map = {f['floor_id']: f['level'] for f in self.floors}
        current_level = floor_level_map.get(self.current_floor_id, 0)

        # Check all other rooms in project on adjacent levels (current_level + 1 or - 1)
        adjacent_rooms = [
            r for r in self.all_project_rooms
            if abs(floor_level_map.get(r['floor_id'], -99) - current_level) == 1
        ]

        for r_curr in self.rooms:
            cL, cT = r_curr['x'], r_curr['y']
            cR, cB = cL + r_curr['width'], cT + r_curr['height']

            for r_adj in adjacent_rooms:
                aL, aT = r_adj['x'], r_adj['y']
                aR, aB = aL + r_adj['width'], aT + r_adj['height']

                overlapX = max(0, min(cR, aR) - max(cL, aL))
                overlapY = max(0, min(cB, aB) - max(cT, aT))

                if overlapX >= 60 and overlapY >= 60:
                    # Overlap is big enough for a staircase!
                    sx = max(cL, aL) + 10
                    sy = max(cT, aT) + 10
                    sw = min(overlapX - 20, 80)
                    sh = min(overlapY - 20, 110)

                    adj_level = floor_level_map.get(r_adj['floor_id'])
                    direction = "UP" if adj_level > current_level else "DN"

                    # Render Staircase Block
                    self.canvas.create_rectangle(sx, sy, sx + sw, sy + sh, fill="#fef3c7", outline="#b45309", width=2, tags="staircase")
                    # Treads
                    num_steps = 7
                    step_h = sh / num_steps
                    for s in range(1, num_steps):
                        self.canvas.create_line(sx, sy + (s * step_h), sx + sw, sy + (s * step_h), fill="#d97706", width=1, tags="staircase")

                    # Direction Label
                    self.canvas.create_text(
                        sx + sw // 2, sy + sh // 2,
                        text=f"STAIRS {direction}\n(Lvl {adj_level})",
                        fill="#78350f",
                        font=('Segoe UI', 7, 'bold'),
                        justify='center',
                        tags="staircase"
                    )

    # -------------------------------------------------------------
    # Furniture Rendering
    # -------------------------------------------------------------
    def _draw_furniture(self):
        for room in self.rooms:
            r_id = room['room_id']
            rx, ry = room['x'], room['y']
            furniture_list = self.furniture_by_room.get(r_id, [])

            for f in furniture_list:
                f_id = f['furniture_id']
                fx = rx + f['x']
                fy = ry + f['y']
                model = f.get('model', 'box')

                bg_col, border_col, text_badge = FURNITURE_COLORS.get(model, ("#94a3b8", "#64748b", "FURN"))
                fw, fh = 46, 32

                is_selected = (f_id == self.selected_furn_id)
                border = "#38bdf8" if is_selected else border_col

                # Furniture box
                self.canvas.create_rectangle(
                    fx, fy, fx + fw, fy + fh,
                    fill=bg_col,
                    outline=border,
                    width=2 if is_selected else 1,
                    tags=(f"furn_{f_id}", "furniture")
                )

                # Label text
                self.canvas.create_text(
                    fx + fw // 2, fy + fh // 2,
                    text=f"{text_badge}\n${f['cost']:,.0f}",
                    fill="#ffffff",
                    font=('Segoe UI', 6, 'bold'),
                    justify='center',
                    tags=(f"furn_{f_id}", "furniture")
                )

    # -------------------------------------------------------------
    # Mouse Interaction: Selection, Dragging, Magnetic Snapping
    # -------------------------------------------------------------
    def on_left_click(self, event):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        # Check if clicked on furniture first
        clicked_furn = None
        clicked_room = None
        for room in self.rooms:
            rx, ry = room['x'], room['y']
            for f in self.furniture_by_room.get(room['room_id'], []):
                fx = rx + f['x']
                fy = ry + f['y']
                if fx <= canvas_x <= fx + 46 and fy <= canvas_y <= fy + 32:
                    clicked_furn = f
                    clicked_room = room
                    break
            if clicked_furn:
                break

        if clicked_furn and clicked_room:
            self.selected_furn_id = clicked_furn['furniture_id']
            self.selected_room_id = clicked_furn['room_id']
            self.drag_item_type = 'furniture'
            self.drag_item_id = clicked_furn['furniture_id']
            self.drag_start_x = canvas_x
            self.drag_start_y = canvas_y
            self.drag_furn_abs_x = clicked_room['x'] + clicked_furn['x']
            self.drag_furn_abs_y = clicked_room['y'] + clicked_furn['y']
            self.render()
            if 'on_select_room' in self.callbacks:
                self.callbacks['on_select_room'](self.selected_room_id)
            return

        # Check if clicked on room
        clicked_room = None
        for room in reversed(self.rooms):  # topmost first
            rx1, ry1 = room['x'], room['y']
            rx2, ry2 = rx1 + room['width'], ry1 + room['height']
            if rx1 <= canvas_x <= rx2 and ry1 <= canvas_y <= ry2:
                clicked_room = room
                break

        if clicked_room:
            self.selected_room_id = clicked_room['room_id']
            self.selected_furn_id = None
            self.drag_item_type = 'room'
            self.drag_item_id = clicked_room['room_id']
            self.drag_start_x = canvas_x
            self.drag_start_y = canvas_y
            self.drag_orig_x = clicked_room['x']
            self.drag_orig_y = clicked_room['y']
            self.render()
            if 'on_select_room' in self.callbacks:
                self.callbacks['on_select_room'](self.selected_room_id)
        else:
            # Clicked empty space
            self.selected_room_id = None
            self.selected_furn_id = None
            self.drag_item_type = None
            self.render()
            if 'on_select_room' in self.callbacks:
                self.callbacks['on_select_room'](None)

    def on_left_drag(self, event):
        if not self.drag_item_type or not self.drag_item_id:
            return

        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        dx = canvas_x - self.drag_start_x
        dy = canvas_y - self.drag_start_y

        if self.drag_item_type == 'room':
            room = next((r for r in self.rooms if r['room_id'] == self.drag_item_id), None)
            if not room:
                return

            new_x = max(0, self.drag_orig_x + dx)
            new_y = max(0, self.drag_orig_y + dy)

            # Snap to 20px grid
            new_x = round(new_x / 20.0) * 20.0
            new_y = round(new_y / 20.0) * 20.0

            # Magnetic Snapping to other rooms (within 15px threshold)
            snap_threshold = 18.0
            r_w = room['width']
            r_h = room['height']

            for other in self.rooms:
                if other['room_id'] == room['room_id']:
                    continue
                o_x, o_y = other['x'], other['y']
                o_w, o_h = other['width'], other['height']

                # Snap X edges
                if abs(new_x - (o_x + o_w)) < snap_threshold:
                    new_x = o_x + o_w
                elif abs((new_x + r_w) - o_x) < snap_threshold:
                    new_x = o_x - r_w
                elif abs(new_x - o_x) < snap_threshold:
                    new_x = o_x

                # Snap Y edges
                if abs(new_y - (o_y + o_h)) < snap_threshold:
                    new_y = o_y + o_h
                elif abs((new_y + r_h) - o_y) < snap_threshold:
                    new_y = o_y - r_h
                elif abs(new_y - o_y) < snap_threshold:
                    new_y = o_y

            room['x'] = new_x
            room['y'] = new_y
            self.render()

        elif self.drag_item_type == 'furniture':
            cur_abs_x = self.drag_furn_abs_x + dx
            cur_abs_y = self.drag_furn_abs_y + dy

            # Check if hovering over any room
            target_room = None
            for r in self.rooms:
                if r['x'] <= cur_abs_x + 23 <= r['x'] + r['width'] and r['y'] <= cur_abs_y + 16 <= r['y'] + r['height']:
                    target_room = r
                    break

            # Find item across all rooms
            furn_item = None
            for f_list in self.furniture_by_room.values():
                for item in f_list:
                    if item['furniture_id'] == self.drag_item_id:
                        furn_item = item
                        break
                if furn_item:
                    break

            if furn_item:
                if target_room:
                    # Relocate to target room if crossed room boundary
                    if furn_item['room_id'] != target_room['room_id']:
                        old_list = self.furniture_by_room.get(furn_item['room_id'], [])
                        if furn_item in old_list:
                            old_list.remove(furn_item)
                        furn_item['room_id'] = target_room['room_id']
                        self.furniture_by_room.setdefault(target_room['room_id'], []).append(furn_item)
                        self.selected_room_id = target_room['room_id']

                    furn_item['x'] = max(5, min(target_room['width'] - 50, cur_abs_x - target_room['x']))
                    furn_item['y'] = max(30, min(target_room['height'] - 35, cur_abs_y - target_room['y']))
                else:
                    room = next((r for r in self.rooms if r['room_id'] == furn_item['room_id']), self.rooms[0])
                    furn_item['x'] = max(5, min(room['width'] - 50, cur_abs_x - room['x']))
                    furn_item['y'] = max(30, min(room['height'] - 35, cur_abs_y - room['y']))

            self.render()

    def on_left_release(self, event):
        if self.drag_item_type == 'room' and self.drag_item_id:
            room = next((r for r in self.rooms if r['room_id'] == self.drag_item_id), None)
            if room:
                self.db.update_room_position(room['room_id'], room['x'], room['y'])
                if 'on_data_changed' in self.callbacks:
                    self.callbacks['on_data_changed']()

        elif self.drag_item_type == 'furniture' and self.drag_item_id:
            furn_item = None
            for f_list in self.furniture_by_room.values():
                for item in f_list:
                    if item['furniture_id'] == self.drag_item_id:
                        furn_item = item
                        break
                if furn_item:
                    break

            if furn_item:
                room = next((r for r in self.rooms if r['room_id'] == furn_item['room_id']), None)
                if room:
                    furn_item['x'] = max(5, min(room['width'] - 50, furn_item['x']))
                    furn_item['y'] = max(30, min(room['height'] - 35, furn_item['y']))
                    self.db.update_furniture_pos(
                        furn_item['furniture_id'],
                        furn_item['x'],
                        furn_item['y'],
                        room_id=furn_item['room_id']
                    )
                if 'on_data_changed' in self.callbacks:
                    self.callbacks['on_data_changed']()
            self.render()

        self.drag_item_type = None
        self.drag_item_id = None

    def on_right_click(self, event):
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        # Find clicked room
        clicked_room = None
        for room in reversed(self.rooms):
            rx1, ry1 = room['x'], room['y']
            rx2, ry2 = rx1 + room['width'], ry1 + room['height']
            if rx1 <= canvas_x <= rx2 and ry1 <= canvas_y <= ry2:
                clicked_room = room
                break

        if clicked_room:
            self.selected_room_id = clicked_room['room_id']
            self.render()
            if 'on_select_room' in self.callbacks:
                self.callbacks['on_select_room'](self.selected_room_id)
            self.context_menu.post(event.x_root, event.y_root)

    # -------------------------------------------------------------
    # Context Menu Actions
    # -------------------------------------------------------------
    def action_rotate_room(self):
        if not self.selected_room_id:
            return
        room = self.db.get_room(self.selected_room_id)
        if room:
            new_w = room['height']
            new_h = room['width']
            self.db.update_room_size(self.selected_room_id, new_w, new_h, room['area'])
            self.refresh()
            if 'on_data_changed' in self.callbacks:
                self.callbacks['on_data_changed']()

    def action_duplicate_room(self):
        if not self.selected_room_id:
            return
        new_id = self.db.duplicate_room(self.selected_room_id)
        if new_id:
            self.selected_room_id = new_id
            self.refresh()
            if 'on_data_changed' in self.callbacks:
                self.callbacks['on_data_changed']()

    def action_edit_room(self):
        if not self.selected_room_id or 'on_edit_room' not in self.callbacks:
            return
        self.callbacks['on_edit_room'](self.selected_room_id)

    def action_add_furniture(self):
        if not self.selected_room_id or 'on_add_furniture' not in self.callbacks:
            return
        self.callbacks['on_add_furniture'](self.selected_room_id)

    def action_delete_room(self):
        if not self.selected_room_id:
            return
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this room and its furniture?", parent=self):
            self.db.delete_room(self.selected_room_id)
            self.selected_room_id = None
            self.refresh()
            if 'on_data_changed' in self.callbacks:
                self.callbacks['on_data_changed']()
            if 'on_select_room' in self.callbacks:
                self.callbacks['on_select_room'](None)
