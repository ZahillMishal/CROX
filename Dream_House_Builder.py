"""
=====================================================================
 DREAM HOUSE BUILDER
 An interactive 2D interior-design studio
 Python (Tkinter) + MySQL
=====================================================================
 How this file is organised (useful for the viva):

   1. SETTINGS         - database login, colours, fonts
   2. DATA             - furniture catalogue, room types, floor types
   3. MODEL CLASSES    - Item (furniture) and Room
   4. DATABASE CLASS   - every MySQL query lives here
   5. FURNITURE ART    - how each piece of furniture is drawn on the canvas
   6. UI WIDGETS       - rounded buttons, icons, scroll frames
   7. DIALOGS          - pop-up windows (add room, edit item, load ...)
   8. MAIN APP CLASS   - the window, drag & drop, save / load

 Run:  python Dream_House_Builder.py
 Needs:  pip install mysql-connector-python
"""

import os
import sys
import math
import random
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, messagebox, colorchooser
from datetime import datetime

import mysql.connector
from mysql.connector import errorcode


# =====================================================================
# 1. SETTINGS
# =====================================================================
DB_NAME = "dream_house_builder"
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "jan130109",          # <-- put your MySQL password here (or type it when asked)
}

DEFAULT_BUDGET = 1_000_000   # Rs 10,00,000
LAYOUT_VERSION = 2           # version 2 = positions stored in tenths of a foot
MIN_SIZE, MAX_SIZE = 6, 40   # smallest / largest room side in feet
WALL_FT = 0.3                # half the wall thickness, in feet

# ---- colour palette (dark navy interface, vibrant accents) ----
BG = "#08121D"
PANEL = "#0F1E2E"
PANEL2 = "#162B40"
PANEL3 = "#1E3951"
LINE = "#2A4A63"
TEXT = "#F6F4EF"
MUTED = "#9FB3C4"
GREEN = "#4CE08A"
GOLD = "#FFC24B"
CYAN = "#3DD6F5"
RED = "#FF6B6B"
BLUE = "#4F6DF5"
DARK_RED = "#4A2430"
CANVAS_BG = "#EDF0F3"
GRID = "#E1E6EB"
GRID_MAJOR = "#D3DAE1"
WALL_EDGE = "#232A33"

# ---- fonts: the first one that is installed is used (bubbly ones first) ----
FONT_FAMILY = "Segoe UI"
FONT_CHOICES = ("Fredoka", "Baloo 2", "Varela Round", "Nunito", "Comic Sans MS",
                "Segoe UI", "Helvetica")


def load_private_fonts():
    """Loads the .ttf files from the 'fonts' folder next to this script (Windows).
    On other systems install the fonts normally instead."""
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
    if not os.path.isdir(folder) or not sys.platform.startswith("win"):
        return
    try:
        import ctypes
        for name in os.listdir(folder):
            if name.lower().endswith((".ttf", ".otf")):
                ctypes.windll.gdi32.AddFontResourceExW(os.path.join(folder, name), 0x10, 0)
    except Exception:
        pass


def choose_font(root):
    """Picks the first available font from FONT_CHOICES."""
    global FONT_FAMILY
    available = set(tkfont.families(root))
    for name in FONT_CHOICES:
        if name in available:
            FONT_FAMILY = name
            return


def F(size, bold=False):
    """Returns a Tk font tuple using the chosen bubbly font."""
    return (FONT_FAMILY, size, "bold" if bold else "normal")


# =====================================================================
# 2. DATA
# =====================================================================
# name -> price (Rs), category, width (ft), length (ft), default colour, drawing name
CATALOG = {
    "Chair":           dict(price=8000,  cat="Seating",    w=1.7, h=1.7, color="#B565C9", art="chair"),
    "Sofa":            dict(price=50000, cat="Seating",    w=6.5, h=3.0, color="#6F767F", art="sofa"),
    "Armchair":        dict(price=18000, cat="Seating",    w=2.8, h=2.8, color="#E0728A", art="armchair"),
    "Center Table":    dict(price=15000, cat="Tables",     w=3.6, h=2.2, color="#A9673C", art="table"),
    "Dining Table":    dict(price=20000, cat="Tables",     w=7.0, h=5.0, color="#B07A45", art="dining"),
    "Study Desk":      dict(price=12000, cat="Tables",     w=4.2, h=3.4, color="#C98F5A", art="desk"),
    "Bed":             dict(price=40000, cat="Beds",       w=5.6, h=6.8, color="#7E8794", art="bed"),
    "Wardrobe":        dict(price=30000, cat="Storage",    w=4.2, h=2.0, color="#9A5F36", art="wardrobe"),
    "TV Unit":         dict(price=25000, cat="Storage",    w=5.0, h=1.7, color="#7A4B2D", art="tvunit"),
    "Bookshelf":       dict(price=16000, cat="Storage",    w=3.6, h=1.3, color="#B5773F", art="bookshelf"),
    "Carpet":          dict(price=10000, cat="Decor",      w=7.5, h=5.0, color="#7FA37A", art="carpet"),
    "Round Rug":       dict(price=8000,  cat="Decor",      w=5.0, h=5.0, color="#E5736B", art="rug"),
    "Plant":           dict(price=5000,  cat="Plants",     w=1.8, h=1.8, color="#3FAE5A", art="plant"),
    "Big Plant":       dict(price=9000,  cat="Plants",     w=2.8, h=2.8, color="#2E9E55", art="plant"),
    "Lamp":            dict(price=7000,  cat="Lighting",   w=1.1, h=1.1, color="#F6D77A", art="lamp"),
    "Floor Lamp":      dict(price=9000,  cat="Lighting",   w=1.5, h=1.5, color="#F3C85A", art="floorlamp"),
    "Refrigerator":    dict(price=28000, cat="Appliances", w=2.6, h=2.6, color="#D5E1E8", art="fridge"),
    "Kitchen Counter": dict(price=22000, cat="Appliances", w=6.0, h=2.1, color="#5E646C", art="counter"),
    "Sink":            dict(price=12000, cat="Appliances", w=3.4, h=2.1, color="#7E8A93", art="sink"),
    "Stove":           dict(price=15000, cat="Appliances", w=2.6, h=2.2, color="#3A4047", art="stove"),
    "Toilet":          dict(price=12000, cat="Appliances", w=1.6, h=2.5, color="#F4F8FA", art="toilet"),
    "Washbasin":       dict(price=9000,  cat="Appliances", w=2.2, h=1.8, color="#F4F8FA", art="basin"),
    "Bathtub":         dict(price=35000, cat="Appliances", w=5.6, h=2.7, color="#F4F8FA", art="bathtub"),
}
CATEGORIES = ["All", "Seating", "Tables", "Beds", "Storage", "Decor", "Appliances", "Plants", "Lighting"]
LOW_LAYER = ("Carpet", "Round Rug")   # rugs are drawn underneath other furniture

# floor type -> look.  'kind' decides which pattern is drawn.
FLOORS = {
    "Wooden":     dict(base="#E2B27C", line="#C99556", kind="planks"),
    "Dark Wood":  dict(base="#9A6440", line="#744A2D", kind="planks"),
    "Tiles":      dict(base="#EFE6D6", line="#D5C8B0", kind="tiles", size=2),
    "Blue Tiles": dict(base="#A8D5E8", line="#86BBD4", kind="tiles", size=1),
    "Terracotta": dict(base="#DC8F62", line="#C0734A", kind="tiles", size=1.5),
    "Marble":     dict(base="#F4F4F2", line="#D8DADD", kind="marble", size=3),
    "Carpet":     dict(base="#B8A1DB", line="#A38BC8", kind="carpet"),
}
FLOOR_EXTRA = {"Wooden": 0, "Dark Wood": 60, "Tiles": 0, "Blue Tiles": 0,
               "Terracotta": 0, "Marble": 200, "Carpet": 40}   # extra Rs per sq ft

# room type -> default size, floor, wall colour, cost per sq ft, accent colour, icon furniture
ROOM_TYPES = {
    "Living Room": dict(w=18, h=14, floor="Wooden",     wall="#E6CDA3", rate=715,  accent="#F5A742", icon="Sofa"),
    "Bedroom":     dict(w=16, h=14, floor="Wooden",     wall="#CFC3EA", rate=670,  accent="#9B7DF0", icon="Bed"),
    "Kitchen":     dict(w=14, h=12, floor="Tiles",      wall="#F4DDA9", rate=745,  accent="#FF7F50", icon="Stove"),
    "Bathroom":    dict(w=10, h=8,  floor="Blue Tiles", wall="#BFE3EE", rate=1000, accent="#2EC4D6", icon="Bathtub"),
    "Balcony":     dict(w=8,  h=6,  floor="Terracotta", wall="#CDE5B8", rate=1040, accent="#5CC96E", icon="Plant"),
    "Study Room":  dict(w=12, h=10, floor="Dark Wood",  wall="#F4C9C0", rate=700,  accent="#F0627E", icon="Study Desk"),
    "Dining Room": dict(w=14, h=12, floor="Wooden",     wall="#EBCFA8", rate=700,  accent="#F2C230", icon="Dining Table"),
}


# =====================================================================
# HELPER FUNCTIONS
# =====================================================================
def money(value):
    """Formats a number the Indian way: 1000000 -> Rs 10,00,000"""
    value = int(round(value))
    sign = "-" if value < 0 else ""
    digits = str(abs(value))
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        digits = ",".join(parts + [tail])
    return sign + "\u20b9" + digits


def is_hex(colour):
    """True if the text looks like a colour such as #A1B2C3."""
    if not isinstance(colour, str) or len(colour) != 7 or colour[0] != "#":
        return False
    try:
        int(colour[1:], 16)
        return True
    except ValueError:
        return False


def shade(colour, amount):
    """Makes a colour lighter (amount > 0) or darker (amount < 0).  amount is -1 .. 1"""
    r, g, b = (int(colour[i:i + 2], 16) for i in (1, 3, 5))
    if amount >= 0:
        r, g, b = (int(v + (255 - v) * amount) for v in (r, g, b))
    else:
        r, g, b = (int(v * (1 + amount)) for v in (r, g, b))
    return "#%02x%02x%02x" % (r, g, b)


def rects_overlap(ax, ay, aw, ah, bx, by, bw, bh):
    """True if two rectangles overlap (just touching does NOT count)."""
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


# =====================================================================
# 3. MODEL CLASSES
# =====================================================================
class Item:
    """One piece of furniture placed inside a room.
    x, y  = centre of the item in feet, measured from the room's top-left corner
    rot   = number of clockwise quarter turns (0, 1, 2, 3)  ->  0, 90, 180, 270 degrees"""
    _count = 0

    def __init__(self, kind, x=0.0, y=0.0, rot=0, name=None, price=None, color=None):
        Item._count += 1
        self.uid = Item._count
        self.kind = kind if kind in CATALOG else "Center Table"
        spec = CATALOG[self.kind]
        self.name = name or kind
        self.price = spec["price"] if price is None else int(price)
        self.color = color if is_hex(color) else spec["color"]
        self.x, self.y, self.rot = x, y, rot % 4

    @property
    def w(self):          # width on the plan (swaps when turned sideways)
        spec = CATALOG[self.kind]
        return spec["w"] if self.rot % 2 == 0 else spec["h"]

    @property
    def h(self):
        spec = CATALOG[self.kind]
        return spec["h"] if self.rot % 2 == 0 else spec["w"]

    def clamp_into(self, room):
        """Keeps the item inside the room walls."""
        lo_x, hi_x = self.w / 2 + WALL_FT, room.w - self.w / 2 - WALL_FT
        lo_y, hi_y = self.h / 2 + WALL_FT, room.h - self.h / 2 - WALL_FT
        self.x = min(max(self.x, lo_x), max(lo_x, hi_x))
        self.y = min(max(self.y, lo_y), max(lo_y, hi_y))

    def contains(self, fx, fy):
        return abs(fx - self.x) <= self.w / 2 and abs(fy - self.y) <= self.h / 2


class Room:
    """One room of the house.  x, y, w, h are in feet on the big floor plan."""
    _count = 0

    def __init__(self, room_type="Living Room", name=None, x=0, y=0, w=None, h=None,
                 floor=None, wall=None, cost=None):
        Room._count += 1
        self.uid = Room._count
        self.type = room_type if room_type in ROOM_TYPES else "Living Room"
        info = ROOM_TYPES[self.type]
        self.name = name or self.type
        self.x, self.y = x, y
        self.w = w or info["w"]
        self.h = h or info["h"]
        self.floor = floor if floor in FLOORS else info["floor"]
        self.wall = wall if is_hex(wall) else info["wall"]
        self.items = []
        self.cost = 0
        if cost is None:
            self.recalc_cost()
        else:
            self.cost = int(cost)

    @property
    def accent(self):
        return ROOM_TYPES[self.type]["accent"]

    def recalc_cost(self):
        """Room cost = area x (rate + floor extra), rounded to the nearest Rs 1000."""
        rate = ROOM_TYPES[self.type]["rate"] + FLOOR_EXTRA[self.floor]
        self.cost = int(round(self.w * self.h * rate / 1000.0)) * 1000

    def furniture_total(self):
        return sum(i.price for i in self.items)

    def total(self):
        return self.cost + self.furniture_total()

    def add_item(self, kind, x, y, rot=0):
        item = Item(kind, x, y, rot)
        item.clamp_into(self)
        self.items.append(item)
        return item

    def ordered_items(self):
        """Drawing order: rugs first so that furniture sits on top of them."""
        return sorted(self.items, key=lambda i: 0 if i.kind in LOW_LAYER else 1)

    def contains(self, fx, fy):
        return self.x <= fx <= self.x + self.w and self.y <= fy <= self.y + self.h


# =====================================================================
# 4. DATABASE CLASS  (all MySQL code is here)
# =====================================================================
SCHEMA = [
    """CREATE TABLE IF NOT EXISTS projects (
        project_id     INT AUTO_INCREMENT PRIMARY KEY,
        project_name   VARCHAR(100) NOT NULL,
        budget         BIGINT NOT NULL DEFAULT 1000000,
        layout_version INT NOT NULL DEFAULT 2,
        created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS rooms (
        room_id     INT AUTO_INCREMENT PRIMARY KEY,
        project_id  INT NOT NULL,
        room_name   VARCHAR(80) NOT NULL,
        room_type   VARCHAR(30) NOT NULL DEFAULT 'Living Room',
        width_ft    INT NOT NULL,
        length_ft   INT NOT NULL,
        floor_type  VARCHAR(40) DEFAULT 'Wooden',
        wall_color  VARCHAR(20) DEFAULT '#DCC69F',
        base_cost   BIGINT NOT NULL DEFAULT 0,
        pos_x       INT NOT NULL DEFAULT 0,
        pos_y       INT NOT NULL DEFAULT 0,
        FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE
    )""",
    """CREATE TABLE IF NOT EXISTS furniture (
        furniture_id INT AUTO_INCREMENT PRIMARY KEY,
        room_id      INT NOT NULL,
        item_name    VARCHAR(80) NOT NULL,
        item_type    VARCHAR(40) NOT NULL DEFAULT '',
        price        BIGINT NOT NULL,
        pos_x        INT DEFAULT 0,
        pos_y        INT DEFAULT 0,
        rotation     INT DEFAULT 0,
        color        VARCHAR(10) DEFAULT NULL,
        FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE CASCADE
    )""",
]

# columns that older versions of this project did not have (added automatically)
UPGRADES = [
    ("projects", "layout_version", "INT NOT NULL DEFAULT 1"),
    ("rooms", "room_type", "VARCHAR(30) NOT NULL DEFAULT 'Living Room'"),
    ("rooms", "pos_x", "INT NOT NULL DEFAULT 0"),
    ("rooms", "pos_y", "INT NOT NULL DEFAULT 0"),
    ("furniture", "pos_x", "INT DEFAULT 0"),
    ("furniture", "pos_y", "INT DEFAULT 0"),
    ("furniture", "rotation", "INT DEFAULT 0"),
    ("furniture", "item_type", "VARCHAR(40) NOT NULL DEFAULT ''"),
    ("furniture", "color", "VARCHAR(10) DEFAULT NULL"),
]


class Database:
    """Creates the database / tables if needed, then saves, loads and deletes projects."""

    def __init__(self, config):
        # Step 1: connect to the server and make sure the database exists
        server = mysql.connector.connect(**config)
        try:
            cur = server.cursor()
            cur.execute("CREATE DATABASE IF NOT EXISTS " + DB_NAME)
            cur.close()
        except mysql.connector.Error:
            pass                       # database may already exist and we may lack the CREATE right
        finally:
            server.close()
        # Step 2: connect to the database itself
        self.conn = mysql.connector.connect(database=DB_NAME, autocommit=True, **config)
        cur = self.conn.cursor()
        for sql in SCHEMA:
            cur.execute(sql)
        for table, column, definition in UPGRADES:
            self._add_column_if_missing(cur, table, column, definition)
        cur.close()

    @staticmethod
    def _add_column_if_missing(cur, table, column, definition):
        cur.execute("SELECT COUNT(*) FROM information_schema.COLUMNS "
                    "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s",
                    (DB_NAME, table, column))
        if cur.fetchone()[0] == 0:
            cur.execute("ALTER TABLE " + table + " ADD COLUMN " + column + " " + definition)

    def _ready(self):
        self.conn.ping(reconnect=True, attempts=2, delay=1)

    def list_projects(self):
        """Returns [(id, name, budget, created, room_count, item_count), ...] newest first."""
        self._ready()
        cur = self.conn.cursor()
        cur.execute(
            "SELECT p.project_id, p.project_name, p.budget, p.created_at, "
            "       COUNT(DISTINCT r.room_id), COUNT(f.furniture_id) "
            "FROM projects p "
            "LEFT JOIN rooms r ON r.project_id = p.project_id "
            "LEFT JOIN furniture f ON f.room_id = r.room_id "
            "GROUP BY p.project_id, p.project_name, p.budget, p.created_at "
            "ORDER BY p.project_id DESC")
        rows = cur.fetchall()
        cur.close()
        return rows

    def save_project(self, project_id, name, budget, rooms):
        """Saves the whole house.  Returns the project id.  Uses a transaction:
        either everything is saved or nothing is."""
        self._ready()
        cur = self.conn.cursor()
        self.conn.start_transaction()
        try:
            exists = False
            if project_id is not None:
                cur.execute("SELECT 1 FROM projects WHERE project_id=%s", (project_id,))
                exists = cur.fetchone() is not None
            if exists:
                cur.execute("UPDATE projects SET project_name=%s, budget=%s, layout_version=%s "
                            "WHERE project_id=%s", (name, budget, LAYOUT_VERSION, project_id))
                cur.execute("DELETE FROM rooms WHERE project_id=%s", (project_id,))   # furniture goes too (CASCADE)
            else:
                cur.execute("INSERT INTO projects (project_name, budget, layout_version) "
                            "VALUES (%s, %s, %s)", (name, budget, LAYOUT_VERSION))
                project_id = cur.lastrowid
            for room in rooms:
                cur.execute(
                    "INSERT INTO rooms (project_id, room_name, room_type, width_ft, length_ft, "
                    "floor_type, wall_color, base_cost, pos_x, pos_y) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (project_id, room.name, room.type, room.w, room.h, room.floor,
                     room.wall, room.cost, room.x, room.y))
                room_id = cur.lastrowid
                rows = [(room_id, i.name, i.kind, i.price, int(round(i.x * 10)),
                         int(round(i.y * 10)), i.rot * 90, i.color) for i in room.items]
                if rows:
                    cur.executemany(
                        "INSERT INTO furniture (room_id, item_name, item_type, price, pos_x, "
                        "pos_y, rotation, color) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", rows)
            self.conn.commit()
            return project_id
        except mysql.connector.Error:
            self.conn.rollback()
            raise
        finally:
            cur.close()

    def load_project(self, project_id):
        """Returns a dictionary describing the saved house, or None if not found."""
        self._ready()
        cur = self.conn.cursor()
        cur.execute("SELECT project_name, budget, layout_version FROM projects WHERE project_id=%s",
                    (project_id,))
        head = cur.fetchone()
        if head is None:
            cur.close()
            return None
        project = {"id": project_id, "name": head[0], "budget": head[1],
                   "version": head[2], "rooms": []}
        cur.execute("SELECT room_id, room_name, room_type, width_ft, length_ft, floor_type, "
                    "wall_color, base_cost, pos_x, pos_y FROM rooms "
                    "WHERE project_id=%s ORDER BY room_id", (project_id,))
        for r in cur.fetchall():
            project["rooms"].append({"db_id": r[0], "name": r[1], "type": r[2], "w": r[3], "h": r[4],
                                     "floor": r[5], "wall": r[6], "cost": r[7],
                                     "x": r[8], "y": r[9], "items": []})
        for room in project["rooms"]:
            cur.execute("SELECT item_name, item_type, price, pos_x, pos_y, rotation, color "
                        "FROM furniture WHERE room_id=%s ORDER BY furniture_id", (room["db_id"],))
            for f in cur.fetchall():
                room["items"].append({"name": f[0], "type": f[1], "price": f[2],
                                      "x": f[3] or 0, "y": f[4] or 0, "rot": f[5] or 0, "color": f[6]})
        cur.close()
        return project

    def delete_project(self, project_id):
        self._ready()
        cur = self.conn.cursor()
        cur.execute("DELETE FROM projects WHERE project_id=%s", (project_id,))
        cur.close()

    def close(self):
        try:
            self.conn.close()
        except mysql.connector.Error:
            pass


# =====================================================================
# 5. FURNITURE ART
# =====================================================================
def round_rect(canvas, x1, y1, x2, y2, r, **kw):
    """Draws a rounded rectangle (a smoothed polygon)."""
    r = max(0, min(r, abs(x2 - x1) / 2, abs(y2 - y1) / 2))
    if r < 1:
        return canvas.create_rectangle(x1, y1, x2, y2, **kw)
    pts = [x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y1 + r,
           x2, y2 - r, x2, y2 - r, x2, y2, x2 - r, y2, x2 - r, y2, x1 + r, y2, x1 + r, y2,
           x1, y2, x1, y2 - r, x1, y2 - r, x1, y1 + r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


class Painter:
    """Draws the shapes of ONE furniture item.
    The shapes use LOCAL coordinates: (0, 0) is the centre of the item and +y is its front.
    pt() turns local coordinates into canvas coordinates for the item's rotation,
    so every drawing function works for all four rotations."""

    def __init__(self, canvas, cx, cy, rot=0, tags=(), unit=1.0):
        self.c, self.cx, self.cy, self.rot, self.tags = canvas, cx, cy, rot % 4, tags
        self.lw = max(1, round(unit))            # basic line width

    def pt(self, x, y):
        if self.rot == 1:
            x, y = -y, x
        elif self.rot == 2:
            x, y = -x, -y
        elif self.rot == 3:
            x, y = y, -x
        return self.cx + x, self.cy + y

    def rect(self, x1, y1, x2, y2, fill="", outline="", width=1, r=0):
        a, b = self.pt(x1, y1), self.pt(x2, y2)
        if r > 0:
            kw = dict(fill=fill, outline=outline, width=width, tags=self.tags)
            return round_rect(self.c, min(a[0], b[0]), min(a[1], b[1]),
                              max(a[0], b[0]), max(a[1], b[1]), r, **kw)
        return self.c.create_rectangle(a[0], a[1], b[0], b[1], fill=fill, outline=outline,
                                       width=width, tags=self.tags)

    def oval(self, x1, y1, x2, y2, fill="", outline="", width=1):
        a, b = self.pt(x1, y1), self.pt(x2, y2)
        return self.c.create_oval(a[0], a[1], b[0], b[1], fill=fill, outline=outline,
                                  width=width, tags=self.tags)

    def line(self, *coords, fill="#000000", width=1):
        flat = []
        for i in range(0, len(coords), 2):
            flat += self.pt(coords[i], coords[i + 1])
        return self.c.create_line(*flat, fill=fill, width=width, capstyle="round", tags=self.tags)

    def poly(self, points, fill="", outline="", width=1, smooth=False):
        flat = []
        for x, y in points:
            flat += self.pt(x, y)
        return self.c.create_polygon(*flat, fill=fill, outline=outline, width=width,
                                     smooth=smooth, tags=self.tags)

    def shadow(self, w, h, colour, oval=False):
        """A soft offset shadow under the item."""
        a, b = self.pt(-w / 2, -h / 2), self.pt(w / 2, h / 2)
        x1, x2 = sorted((a[0], b[0]))
        y1, y2 = sorted((a[1], b[1]))
        d = max(2, self.lw * 2)
        if oval:
            self.c.create_oval(x1 + d, y1 + d + 1, x2 + d, y2 + d + 1, fill=colour,
                               outline="", tags=self.tags)
        else:
            round_rect(self.c, x1 + d, y1 + d + 1, x2 + d, y2 + d + 1, min(x2 - x1, y2 - y1) * 0.12,
                       fill=colour, outline="", tags=self.tags)


# ---- one drawing function per kind of furniture --------------------------------
# p = Painter, w/h = size in pixels, c = main colour of the item
def art_chair(p, w, h, c):
    p.rect(-.42 * w, -.5 * h, .42 * w, -.12 * h, fill=shade(c, -.28), r=w * .12)
    p.rect(-.5 * w, -.3 * h, .5 * w, .5 * h, fill=c, outline=shade(c, -.3), width=p.lw, r=w * .16)
    p.rect(-.3 * w, -.1 * h, .3 * w, .32 * h, fill=shade(c, .25), r=w * .1)


def art_sofa(p, w, h, c, seats=3):
    arm = w * (.10 if seats > 1 else .16)
    back = h * .32
    dark = shade(c, -.25)
    p.rect(-w / 2, -h / 2, w / 2, h / 2, fill=dark, r=h * .2)                              # frame
    p.rect(-w / 2 + arm * .7, -h / 2 + h * .04, w / 2 - arm * .7, -h / 2 + back,
           fill=shade(c, -.1), r=h * .1)                                                   # backrest
    seat_w = (w - 2 * arm) / seats
    for i in range(seats):                                                                 # cushions
        x1 = -w / 2 + arm + i * seat_w
        p.rect(x1 + w * .008, -h / 2 + back * .85, x1 + seat_w - w * .008, h / 2 - h * .07,
               fill=shade(c, .12), outline=dark, width=1, r=h * .1)


def art_armchair(p, w, h, c):
    art_sofa(p, w, h, c, seats=1)


def art_table(p, w, h, c):
    p.rect(-w / 2, -h / 2, w / 2, h / 2, fill=shade(c, -.25), r=h * .12)
    p.rect(-w / 2 + .07 * h, -h / 2 + .07 * h, w / 2 - .07 * h, h / 2 - .07 * h, fill=c, r=h * .08)
    p.rect(-w * .36, -h * .26, w * .36, h * .26, outline=shade(c, .3), width=1, r=h * .06)
    r = h * .16
    p.oval(-r, -r, r, r, fill="#F28C38", outline="#C86A1E", width=1)                       # fruit bowl
    p.oval(-r * .5, -r * .65, r * .1, -r * .1, fill="#FFD08A")


def art_dining(p, w, h, c):
    tw, th = w * .70, h * .56
    cw, ch = w * .15, h * .17
    chair = shade(c, -.38)
    spots = [(fx * w, s * (th / 2 + ch * .55), 0, s) for fx in (-.2, .2) for s in (-1, 1)]
    for cx, cy, _, s in spots:                                                             # 4 long-side chairs
        p.rect(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2, fill=chair,
               outline=shade(chair, -.3), width=1, r=cw * .25)
        p.rect(cx - cw / 2, cy + s * ch * .28 - ch * .12, cx + cw / 2, cy + s * ch * .28 + ch * .12,
               fill=shade(chair, -.25), r=2)
    for s in (-1, 1):                                                                      # 2 end chairs
        cx = s * (tw / 2 + cw * .5)
        p.rect(cx - cw / 2, -ch / 2, cx + cw / 2, ch / 2, fill=chair, outline=shade(chair, -.3),
               width=1, r=cw * .25)
    p.rect(-tw / 2, -th / 2, tw / 2, th / 2, fill=shade(c, -.2), r=th * .1)
    p.rect(-tw / 2 + 3, -th / 2 + 3, tw / 2 - 3, th / 2 - 3, fill=c, r=th * .08)
    r = th * .2
    p.oval(-r, -r, r, r, fill="#F5C542", outline="#E08E0B", width=1)                       # flowers
    p.oval(-r * .4, -r * .4, r * .4, r * .4, fill="#E8643C")


def art_desk(p, w, h, c):
    dh = h * .58
    p.rect(-w / 2, -h / 2, w / 2, -h / 2 + dh, fill=shade(c, -.22), r=h * .06)
    p.rect(-w / 2 + 3, -h / 2 + 3, w / 2 - 3, -h / 2 + dh - 3, fill=c, r=h * .05)
    p.rect(-w * .16, -h * .30, w * .16, -h * .14, fill="#C9CED6", r=2)                     # laptop keys
    p.rect(-w * .16, -h * .44, w * .16, -h * .30, fill="#2B3038", r=2)                     # laptop screen
    p.oval(w * .27, -h * .34, w * .37, -h * .24, fill="#E5484D", outline="#B02A30")        # mug
    p.oval(-w * .42, -h * .40, -w * .28, -h * .26, fill="#F6D77A", outline="#C9A93E")      # desk lamp
    p.oval(-w * .15, h * .04, w * .15, h * .34, fill="#5B6475", outline="#3C4352", width=1)  # chair seat
    p.rect(-w * .15, h * .36, w * .15, h * .45, fill="#3C4352", r=3)                       # chair back


def art_bed(p, w, h, c):
    p.rect(-w / 2, -h / 2, w / 2, h / 2, fill="#8A5A38", r=w * .05)                        # frame + headboard
    p.rect(-w * .46, -h * .45, w * .46, h * .48, fill="#F4F5F7", r=w * .04)                # mattress
    for s in (-1, 1):                                                                      # two pillows
        x = s * w * .23
        p.rect(x - w * .19, -h * .42, x + w * .19, -h * .24, fill="#FFFFFF",
               outline="#C7CED8", width=1, r=w * .06)
    p.rect(-w * .46, -h * .10, w * .46, h * .48, fill=c, r=w * .04)                        # duvet
    p.rect(-w * .46, -h * .10, w * .46, -h * .02, fill=shade(c, .35), r=w * .03)           # folded edge
    p.line(0, -h * .02, 0, h * .46, fill=shade(c, -.15), width=1)


def art_wardrobe(p, w, h, c):
    p.rect(-w / 2, -h / 2, w / 2, h / 2, fill=shade(c, -.25), r=3)
    p.rect(-w / 2 + 4, -h / 2 + 4, w / 2 - 4, h / 2 - 4, fill=c, r=2)
    p.rect(-w / 2 + 9, -h / 2 + 9, -3, h / 2 - 9, outline=shade(c, .22), width=1)
    p.rect(3, -h / 2 + 9, w / 2 - 9, h / 2 - 9, outline=shade(c, .22), width=1)
    p.line(0, -h / 2 + 4, 0, h / 2 - 4, fill=shade(c, -.4), width=p.lw)
    for s in (-1, 1):
        p.oval(s * w * .04 - 2, h * .22, s * w * .04 + 2, h * .22 + 4, fill="#E8D9A8")     # knobs


def art_tvunit(p, w, h, c):
    p.rect(-w / 2, -h / 2, w / 2, h / 2, fill=shade(c, -.28), r=h * .12)
    p.rect(-w / 2 + 3, -h / 2 + 3, w / 2 - 3, h / 2 - 3, fill=c, r=h * .1)
    p.rect(-w * .34, -h * .40, w * .34, -h * .10, fill="#12151A", r=2)                     # TV
    p.line(-w * .28, -h * .32, -w * .14, -h * .32, fill="#5A6472", width=1)                # screen glare
    p.rect(-w * .05, -h * .10, w * .05, h * .02, fill="#2A2F36")                           # stand
    for fx in (-.33, 0, .33):
        p.rect(fx * w - w * .13, h * .12, fx * w + w * .13, h * .38, outline=shade(c, .25), width=1, r=2)


def art_bookshelf(p, w, h, c):
    p.rect(-w / 2, -h / 2, w / 2, h / 2, fill=shade(c, -.3), r=3)
    p.rect(-w / 2 + 3, -h / 2 + 3, w / 2 - 3, h / 2 - 3, fill=shade(c, -.55), r=2)
    colours = ["#E4572E", "#29A0B1", "#F2C14E", "#7B5EA7", "#4CAF77", "#E86A92"]
    x, i = -w / 2 + 5, 0
    while x < w / 2 - 9:
        bw = w * (.035 + ((i * 7) % 3) * .012)
        bh = (h - 8) * (.55 + ((i * 5) % 4) * .1)
        p.rect(x, h / 2 - 4 - bh, x + bw, h / 2 - 4, fill=colours[i % 6])
        x += bw + 1.5
        i += 1


def art_carpet(p, w, h, c):
    p.rect(-w / 2, -h / 2, w / 2, h / 2, fill=shade(c, -.2), r=h * .04)
    p.rect(-w / 2 + .05 * h, -h / 2 + .05 * h, w / 2 - .05 * h, h / 2 - .05 * h, fill=c,
           outline=shade(c, .35), width=p.lw, r=h * .03)
    p.rect(-w / 2 + .14 * h, -h / 2 + .14 * h, w / 2 - .14 * h, h / 2 - .14 * h,
           outline=shade(c, -.18), width=1)
    p.poly([(0, -h * .22), (w * .13, 0), (0, h * .22), (-w * .13, 0)], fill=shade(c, .2),
           outline=shade(c, -.1), width=1)


def art_rug(p, w, h, c):
    r = min(w, h) / 2
    p.oval(-r, -r, r, r, fill=shade(c, -.2))
    p.oval(-r * .88, -r * .88, r * .88, r * .88, fill=c)
    p.oval(-r * .62, -r * .62, r * .62, r * .62, fill=shade(c, .25))
    p.oval(-r * .36, -r * .36, r * .36, r * .36, fill=shade(c, -.05))
    p.oval(-r * .12, -r * .12, r * .12, r * .12, fill=shade(c, .4))


def art_plant(p, w, h, c):
    r = min(w, h) / 2
    p.oval(-r * .85, -r * .85, r * .85, r * .85, fill=shade(c, -.55))                      # soil / pot
    for layer, (length, tone) in enumerate(((1.0, 0.0), (.72, .25))):
        for i in range(9):
            a = math.radians(i * 40 + layer * 20)
            ca, sa = math.cos(a), math.sin(a)
            pxn, pyn = -sa, ca
            L, side = r * length, r * length * .27
            pts = [(0, 0), (ca * L * .5 + pxn * side, sa * L * .5 + pyn * side),
                   (ca * L, sa * L), (ca * L * .5 - pxn * side, sa * L * .5 - pyn * side)]
            p.poly(pts, fill=shade(c, tone + (-.1 if i % 2 else .05)), outline=shade(c, -.35),
                   width=1, smooth=True)
    p.oval(-r * .2, -r * .2, r * .2, r * .2, fill="#B8683B", outline="#8A4A26")


def art_lamp(p, w, h, c, big=False):
    r = min(w, h) / 2
    p.oval(-r, -r, r, r, fill=shade(c, -.15), outline=shade(c, -.4), width=1)
    if big:
        p.oval(-r * .86, -r * .86, r * .86, r * .86, outline=shade(c, .3), width=1)
    p.oval(-r * .72, -r * .72, r * .72, r * .72, fill=c)
    p.oval(-r * .38, -r * .38, r * .38, r * .38, fill=shade(c, .55))
    p.oval(-r * .14, -r * .14, r * .14, r * .14, fill="#FFFFFF")


def art_floorlamp(p, w, h, c):
    art_lamp(p, w, h, c, big=True)


def art_fridge(p, w, h, c):
    p.rect(-w / 2, -h / 2, w / 2, h / 2, fill=shade(c, -.28), r=w * .1)
    p.rect(-w / 2 + 3, -h / 2 + 3, w / 2 - 3, h / 2 - 3, fill=c, r=w * .08)
    p.line(-w / 2 + 3, -h * .08, w / 2 - 3, -h * .08, fill=shade(c, -.3), width=p.lw)       # door seam
    p.rect(-w * .3, h / 2 - 8, w * .3, h / 2 - 5, fill="#6B7785", r=2)                      # handle
    for i in range(4):                                                                     # top vents
        y = -h / 2 + 9 + i * 4
        p.line(-w * .25, y, w * .25, y, fill=shade(c, -.18), width=1)


def art_counter(p, w, h, c):
    p.rect(-w / 2, -h / 2, w / 2, h / 2, fill=shade(c, -.3), r=3)
    p.rect(-w / 2 + 3, -h / 2 + 3, w / 2 - 3, h / 2 - 3, fill=c, r=2)
    for i in (1, 2):
        x = -w / 2 + i * w / 3
        p.line(x, -h / 2 + 3, x, h / 2 - 3, fill=shade(c, -.32), width=1)
    for i in range(3):
        x = -w / 2 + (i + .5) * w / 3
        p.rect(x - 7, h / 2 - 8, x + 7, h / 2 - 5, fill="#D5D9DF", r=1)
    p.rect(w * .08, -h * .28, w * .24, h * .02, fill="#D9A768", r=3)                        # chopping board
    p.oval(-w * .3, -h * .26, -w * .2, -h * .06, fill="#E8643C", outline="#B8431F")        # fruit


def art_sink(p, w, h, c):
    p.rect(-w / 2, -h / 2, w / 2, h / 2, fill=shade(c, -.3), r=3)
    p.rect(-w / 2 + 3, -h / 2 + 3, w / 2 - 3, h / 2 - 3, fill=c, r=2)
    for s in (-1, 1):
        x1, x2 = (-w * .42, -w * .04) if s < 0 else (w * .04, w * .42)
        p.rect(x1, -h * .24, x2, h * .36, fill="#CFE2EC", outline="#8FA6B5", width=1, r=4)
        p.oval((x1 + x2) / 2 - 3, h * .05, (x1 + x2) / 2 + 3, h * .05 + 6, fill="#8FA6B5")
    p.rect(-w * .03, -h * .40, w * .03, -h * .24, fill="#B6C0C9", r=2)                      # tap
    p.oval(-w * .045, -h * .46, w * .045, -h * .38, fill="#9AA7B1")


def art_stove(p, w, h, c):
    p.rect(-w / 2, -h / 2, w / 2, h / 2, fill=shade(c, -.3), r=3)
    p.rect(-w / 2 + 3, -h / 2 + 3, w / 2 - 3, h / 2 - 3, fill=shade(c, .1), r=3)
    r = min(w, h) * .17
    for fx, fy in ((-.22, -.2), (.22, -.2), (-.22, .12), (.22, .12)):
        cx, cy = fx * w, fy * h
        p.oval(cx - r, cy - r, cx + r, cy + r, fill="#15181C", outline="#8A929B", width=1)
        p.oval(cx - r * .55, cy - r * .55, cx + r * .55, cy + r * .55, fill="#FF6B3D")
        p.oval(cx - r * .2, cy - r * .2, cx + r * .2, cy + r * .2, fill="#FFC24B")
    for fx in (-.3, -.1, .1, .3):
        p.oval(fx * w - 3, h * .36, fx * w + 3, h * .36 + 6, fill="#C9CED6")


def art_toilet(p, w, h, c):
    edge = shade(c, -.28)
    p.rect(-w * .42, -h / 2, w * .42, -h * .2, fill=c, outline=edge, width=p.lw, r=w * .1)  # tank
    p.oval(-w * .06, -h * .43, w * .06, -h * .33, fill="#9AA7B1")                           # flush button
    p.oval(-w / 2, -h * .28, w / 2, h / 2, fill=c, outline=edge, width=p.lw)                # bowl
    p.oval(-w * .36, -h * .18, w * .36, h * .40, fill=shade(c, -.07), outline=shade(c, -.2), width=1)
    p.oval(-w * .2, -h * .02, w * .2, h * .28, fill="#BFE3F0")                              # water


def art_basin(p, w, h, c):
    p.rect(-w / 2, -h / 2, w / 2, h / 2, fill=c, outline=shade(c, -.28), width=p.lw, r=w * .1)
    p.oval(-w * .32, -h * .28, w * .32, h * .4, fill="#D6ECF6", outline=shade(c, -.3), width=1)
    p.oval(-w * .04, h * .08, w * .04, h * .08 + 7, fill="#8F9BA6")                         # drain
    p.rect(-w * .04, -h * .44, w * .04, -h * .28, fill="#8F9BA6", r=2)                      # tap


def art_bathtub(p, w, h, c):
    p.rect(-w / 2, -h / 2, w / 2, h / 2, fill=c, outline=shade(c, -.28), width=p.lw, r=h * .3)
    p.rect(-w / 2 + .07 * h, -h / 2 + .1 * h, w / 2 - .07 * h, h / 2 - .1 * h, fill="#CBE8F3",
           outline=shade(c, -.3), width=1, r=h * .28)
    p.oval(-w * .44, -h * .12, -w * .38, h * .12, fill="#8F9BA6")                           # tap
    p.oval(w * .36, -h * .06, w * .40, h * .06, fill="#8F9BA6")                             # drain
    p.line(-w * .15, -h * .1, -w * .05, -h * .18, w * .05, -h * .1, w * .15, -h * .18, fill="#FFFFFF", width=1)


ART = {
    "chair": art_chair, "sofa": art_sofa, "armchair": art_armchair, "table": art_table,
    "dining": art_dining, "desk": art_desk, "bed": art_bed, "wardrobe": art_wardrobe,
    "tvunit": art_tvunit, "bookshelf": art_bookshelf, "carpet": art_carpet, "rug": art_rug,
    "plant": art_plant, "lamp": art_lamp, "floorlamp": art_floorlamp, "fridge": art_fridge,
    "counter": art_counter, "sink": art_sink, "stove": art_stove, "toilet": art_toilet,
    "basin": art_basin, "bathtub": art_bathtub,
}
OVAL_ART = ("plant", "lamp", "floorlamp", "rug")      # these get a round shadow


def draw_item_icon(canvas, kind, cx, cy, box_w, box_h, colour=None, tags=()):
    """Draws a small picture of a catalogue item that fits inside box_w x box_h pixels."""
    spec = CATALOG[kind]
    scale = min(box_w / spec["w"], box_h / spec["h"])
    painter = Painter(canvas, cx, cy, 0, tags, unit=max(1, scale / 22))
    ART[spec["art"]](painter, spec["w"] * scale, spec["h"] * scale, colour or spec["color"])


# =====================================================================
# 6. UI WIDGETS
# =====================================================================
def draw_icon(c, name, cx, cy, s, color, tag="icon"):
    """Draws a simple line icon (so we never depend on emoji fonts)."""
    h = s / 2
    w = max(1.6, s / 8)

    def L(*pts, **kw):
        return c.create_line(*pts, fill=color, width=kw.pop("width", w), capstyle="round",
                             joinstyle="round", tags=tag, **kw)

    if name == "plus":
        L(cx - h * .8, cy, cx + h * .8, cy)
        L(cx, cy - h * .8, cx, cy + h * .8)
    elif name == "minus":
        L(cx - h * .8, cy, cx + h * .8, cy)
    elif name == "menu":
        for dy in (-.6, 0, .6):
            L(cx - h * .85, cy + dy * h, cx + h * .85, cy + dy * h)
    elif name == "home":
        L(cx - h, cy, cx, cy - h, cx + h, cy)
        L(cx - h * .7, cy - h * .25, cx - h * .7, cy + h * .9, cx + h * .7, cy + h * .9, cx + h * .7, cy - h * .25)
        L(cx - h * .2, cy + h * .9, cx - h * .2, cy + h * .35, cx + h * .2, cy + h * .35, cx + h * .2, cy + h * .9)
    elif name == "save":
        L(cx - h * .85, cy - h * .85, cx + h * .55, cy - h * .85, cx + h * .85, cy - h * .55,
          cx + h * .85, cy + h * .85, cx - h * .85, cy + h * .85, cx - h * .85, cy - h * .85)
        L(cx - h * .45, cy - h * .85, cx - h * .45, cy - h * .3, cx + h * .4, cy - h * .3, cx + h * .4, cy - h * .85)
        L(cx - h * .5, cy + h * .85, cx - h * .5, cy + h * .25, cx + h * .5, cy + h * .25, cx + h * .5, cy + h * .85)
    elif name == "folder":
        L(cx - h, cy - h * .6, cx - h, cy + h * .75, cx + h, cy + h * .75, cx + h, cy - h * .35,
          cx + h * .1, cy - h * .35, cx - h * .15, cy - h * .6, cx - h, cy - h * .6)
    elif name == "gear":
        c.create_oval(cx - h * .38, cy - h * .38, cx + h * .38, cy + h * .38, outline=color, width=w, tags=tag)
        for i in range(8):
            a = math.radians(i * 45)
            L(cx + math.cos(a) * h * .62, cy + math.sin(a) * h * .62,
              cx + math.cos(a) * h * .98, cy + math.sin(a) * h * .98, width=w * 1.5)
    elif name == "pencil":
        dx, dy, px, py = .7071, -.7071, .7071, .7071
        tx, ty = cx - .85 * h, cy + .85 * h
        k = .26 * h
        pts = [tx, ty,
               tx + dx * .7 * h + px * k, ty + dy * .7 * h + py * k,
               tx + dx * 2.35 * h + px * k, ty + dy * 2.35 * h + py * k,
               tx + dx * 2.35 * h - px * k, ty + dy * 2.35 * h - py * k,
               tx + dx * .7 * h - px * k, ty + dy * .7 * h - py * k]
        c.create_polygon(pts, fill=color, outline="", tags=tag)
    elif name == "trash":
        L(cx - h * .85, cy - h * .55, cx + h * .85, cy - h * .55)
        L(cx - h * .3, cy - h * .55, cx - h * .3, cy - h * .9, cx + h * .3, cy - h * .9, cx + h * .3, cy - h * .55)
        L(cx - h * .6, cy - h * .3, cx - h * .5, cy + h * .9, cx + h * .5, cy + h * .9, cx + h * .6, cy - h * .3)
        L(cx - h * .15, cy - h * .05, cx - h * .15, cy + h * .6)
        L(cx + h * .15, cy - h * .05, cx + h * .15, cy + h * .6)
    elif name == "rotate":
        c.create_arc(cx - h * .8, cy - h * .8, cx + h * .8, cy + h * .8, start=60, extent=270,
                     style="arc", outline=color, width=w, tags=tag)
        ex, ey = cx + h * .8 * math.cos(math.radians(60)), cy - h * .8 * math.sin(math.radians(60))
        c.create_polygon(ex - h * .15, ey - h * .65, ex + h * .2, ey + h * .35, ex - h * .75, ey + h * .15,
                         fill=color, outline="", tags=tag)
    elif name == "copy":
        c.create_rectangle(cx - h * .85, cy - h * .45, cx + h * .2, cy + h * .9, outline=color, width=w, tags=tag)
        c.create_rectangle(cx - h * .2, cy - h * .9, cx + h * .85, cy + h * .45, outline=color, width=w, tags=tag)
    elif name == "fit":
        for sx in (-1, 1):
            for sy in (-1, 1):
                L(cx + sx * h, cy + sy * h * .35, cx + sx * h, cy + sy * h, cx + sx * h * .35, cy + sy * h)
    elif name == "search":
        c.create_oval(cx - h * .85, cy - h * .85, cx + h * .25, cy + h * .25, outline=color, width=w, tags=tag)
        L(cx + h * .1, cy + h * .1, cx + h * .9, cy + h * .9)
    elif name == "left":
        L(cx + h * .3, cy - h * .8, cx - h * .4, cy, cx + h * .3, cy + h * .8)
    elif name == "right":
        L(cx - h * .3, cy - h * .8, cx + h * .4, cy, cx - h * .3, cy + h * .8)
    elif name == "cursor":
        c.create_polygon(cx - h * .6, cy - h * .85, cx - h * .6, cy + h * .7, cx - h * .2, cy + h * .3,
                         cx + h * .1, cy + h * .95, cx + h * .38, cy + h * .82, cx + h * .08, cy + h * .2,
                         cx + h * .6, cy + h * .2, fill=color, outline="", tags=tag)
    elif name == "move":
        L(cx - h, cy, cx + h, cy)
        L(cx, cy - h, cx, cy + h)
        L(cx - h * .6, cy - h * .4, cx - h, cy, cx - h * .6, cy + h * .4)
        L(cx + h * .6, cy - h * .4, cx + h, cy, cx + h * .6, cy + h * .4)
        L(cx - h * .4, cy - h * .6, cx, cy - h, cx + h * .4, cy - h * .6)
        L(cx - h * .4, cy + h * .6, cx, cy + h, cx + h * .4, cy + h * .6)
    elif name == "check":
        L(cx - h * .8, cy, cx - h * .2, cy + h * .6, cx + h * .8, cy - h * .6)


class RoundButton(tk.Canvas):
    """A modern rounded button with hover and press effects."""

    def __init__(self, parent, text="", command=None, icon=None, bg=BLUE, hover=None, fg=TEXT,
                 width=None, height=36, radius=12, size=10):
        self.command = command
        self.bg = bg
        self.hover = hover or shade(bg, .18)
        self.press = shade(bg, -.15)
        font = F(size, True)
        measure = tkfont.Font(family=font[0], size=font[1], weight=font[2])
        tw = measure.measure(text) if text else 0
        iw = 18 if icon else 0
        gap = 8 if (icon and text) else 0
        w = width or (height if (icon and not text) else tw + iw + gap + 30)
        super().__init__(parent, width=w, height=height, bg=parent.cget("bg"),
                         highlightthickness=0, bd=0, cursor="hand2")
        self.shape = round_rect(self, 1, 1, w - 1, height - 1, radius, fill=bg, outline="")
        x0 = (w - (iw + gap + tw)) / 2
        if icon:
            draw_icon(self, icon, x0 + iw / 2, height / 2, 15, fg)
        if text:
            self.create_text(x0 + iw + gap, height / 2, text=text, anchor="w", fill=fg, font=font)
        self.bind("<Enter>", lambda e: self._paint(self.hover))
        self.bind("<Leave>", lambda e: self._paint(self.bg))
        self.bind("<ButtonPress-1>", lambda e: self._paint(self.press))
        self.bind("<ButtonRelease-1>", self._release)

    def _paint(self, colour):
        try:
            self.itemconfig(self.shape, fill=colour)
        except tk.TclError:
            pass

    def _release(self, event):
        self._paint(self.hover)
        if 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height() and self.command:
            self.command()

    def recolor(self, bg):
        self.bg, self.hover, self.press = bg, shade(bg, .18), shade(bg, -.15)
        self._paint(bg)


class IconButton(tk.Canvas):
    """A small icon-only button without a background (used for edit / delete)."""

    def __init__(self, parent, icon, color, command, size=26):
        super().__init__(parent, width=size, height=size, bg=parent.cget("bg"),
                         highlightthickness=0, cursor="hand2")
        self.icon, self.color, self.command, self.size = icon, color, command, size
        self._paint(color)
        self.bind("<Enter>", lambda e: self._paint(shade(color, .35)))
        self.bind("<Leave>", lambda e: self._paint(color))
        self.bind("<ButtonRelease-1>", lambda e: self.command())

    def _paint(self, colour):
        self.delete("all")
        draw_icon(self, self.icon, self.size / 2, self.size / 2, self.size * .58, colour)


class Stepper(tk.Frame):
    """[ - ]  18'  [ + ]  control used for room width / length."""

    def __init__(self, parent, value, lo, hi, command=None):
        super().__init__(parent, bg=parent.cget("bg"))
        self.value, self.lo, self.hi, self.command = value, lo, hi, command
        RoundButton(self, icon="minus", width=28, height=28, radius=9, bg=PANEL3,
                    command=lambda: self.step(-1)).pack(side="left")
        self.label = tk.Label(self, text=self._text(), width=6, bg=parent.cget("bg"), fg=TEXT, font=F(12, True))
        self.label.pack(side="left", padx=2)
        RoundButton(self, icon="plus", width=28, height=28, radius=9, bg=PANEL3,
                    command=lambda: self.step(1)).pack(side="left")

    def _text(self):
        return str(self.value) + " ft"

    def set(self, value):
        self.value = value
        self.label.config(text=self._text())

    def step(self, delta):
        new = max(self.lo, min(self.hi, self.value + delta))
        if new == self.value:
            return
        if self.command and self.command(new) is False:      # command may refuse (e.g. overlap)
            return
        self.set(new)


def bind_wheel(area, scroll):
    """Mouse-wheel scrolling while the pointer is over 'area'. scroll(step) is called with -1 / +1."""
    def on_wheel(event):
        up = event.num == 4 or getattr(event, "delta", 0) > 0
        scroll(-1 if up else 1)

    def on_enter(_):
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            area.bind_all(seq, on_wheel)

    def on_leave(_):
        try:
            x, y = area.winfo_pointerxy()
            inside = area.winfo_containing(x, y)
            if inside is not None and str(inside).startswith(str(area)):
                return
        except Exception:
            pass
        for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            area.unbind_all(seq)

    area.bind("<Enter>", on_enter, add="+")
    area.bind("<Leave>", on_leave, add="+")


class ScrollFrame(tk.Frame):
    """A frame whose content scrolls vertically with the mouse wheel."""

    def __init__(self, parent, bg):
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, yscrollincrement=18)
        self.canvas.pack(fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self._resize)
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.win, width=e.width))
        bind_wheel(self, self._scroll)

    def _resize(self, _=None):
        self.canvas.configure(scrollregion=(0, 0, self.inner.winfo_reqwidth(), self.inner.winfo_reqheight()))

    def _scroll(self, step):
        if self.inner.winfo_reqheight() > self.canvas.winfo_height():
            self.canvas.yview_scroll(step, "units")

    def rebuild(self, build):
        """Clears the content, calls build(inner_frame) and keeps the scroll position."""
        top = self.canvas.yview()[0]
        for widget in self.inner.winfo_children():
            widget.destroy()
        build(self.inner)
        self.update_idletasks()
        self._resize()
        self.canvas.yview_moveto(top)


# =====================================================================
# 7. DIALOGS (pop-up windows)
# =====================================================================
class Dialog(tk.Toplevel):
    """Base class for all pop-up windows: dark theme, centred, modal."""

    def __init__(self, app, title):
        super().__init__(app.root)
        self.app = app
        self.result = None
        self.withdraw()
        self.title(title)
        self.configure(bg=PANEL)
        self.resizable(False, False)
        self.transient(app.root)
        tk.Label(self, text=title.upper(), bg=PANEL, fg=TEXT, font=F(14, True)).pack(anchor="w", padx=24, pady=(20, 4))
        self.body = tk.Frame(self, bg=PANEL)
        self.body.pack(fill="both", expand=True, padx=24, pady=(6, 4))
        self.foot = tk.Frame(self, bg=PANEL)
        self.foot.pack(fill="x", padx=24, pady=(12, 20))
        self.bind("<Escape>", lambda e: self.destroy())

    def add_buttons(self, ok_command, ok_text="OK", ok_color=BLUE):
        RoundButton(self.foot, text=ok_text, command=ok_command, bg=ok_color).pack(side="right")
        RoundButton(self.foot, text="Cancel", command=self.destroy, bg=PANEL3).pack(side="right", padx=(0, 8))

    def finish(self, result):
        self.result = result
        self.destroy()

    def show(self):
        self.update_idletasks()
        root = self.app.root
        x = root.winfo_rootx() + (root.winfo_width() - self.winfo_reqwidth()) // 2
        y = root.winfo_rooty() + (root.winfo_height() - self.winfo_reqheight()) // 3
        self.geometry("+%d+%d" % (max(0, x), max(0, y)))
        self.deiconify()
        try:
            self.wait_visibility()
            self.grab_set()
        except tk.TclError:
            pass
        self.wait_window()
        return self.result


def make_entry(parent, var, width=28, show=""):
    return tk.Entry(parent, textvariable=var, width=width, show=show, bg=PANEL3, fg=TEXT,
                    insertbackground=TEXT, relief="flat", font=F(12),
                    highlightthickness=1, highlightbackground=LINE, highlightcolor=BLUE)


def caption(parent, text):
    return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=MUTED, font=F(10, True))


def ask_text(app, title, label, initial="", password=False):
    """Small dialog with one text box. Returns the text, or None if cancelled."""
    d = Dialog(app, title)
    caption(d.body, label).pack(anchor="w")
    var = tk.StringVar(value=initial)
    entry = make_entry(d.body, var, show="*" if password else "")
    entry.pack(fill="x", ipady=7, pady=(6, 0))
    entry.focus_set()
    entry.select_range(0, "end")
    ok = lambda: d.finish(var.get().strip())
    entry.bind("<Return>", lambda e: ok())
    d.add_buttons(ok)
    return d.show()


def room_dialog(app):
    """Add-room dialog. Returns (room_type, name, width, length) or None."""
    d = Dialog(app, "Add Room")
    state = {"type": "Bedroom", "w": ROOM_TYPES["Bedroom"]["w"], "h": ROOM_TYPES["Bedroom"]["h"]}
    name_var = tk.StringVar(value="Bedroom")

    caption(d.body, "Choose a room type").pack(anchor="w")
    grid = tk.Frame(d.body, bg=PANEL)
    grid.pack(pady=(6, 10))
    chips = {}

    def paint():
        for t, cv in chips.items():
            cv.delete("all")
            on = t == state["type"]
            accent = ROOM_TYPES[t]["accent"]
            round_rect(cv, 2, 2, 94, 78, 14, fill=PANEL3 if on else PANEL2, outline=accent if on else LINE,
                       width=2 if on else 1)
            round_rect(cv, 30, 8, 66, 44, 10, fill=accent, outline="")
            draw_item_icon(cv, ROOM_TYPES[t]["icon"], 48, 26, 28, 26, "#FFFFFF")
            cv.create_text(48, 62, text=t, fill=TEXT, font=F(8, True), width=88)

    def choose(t):
        old = state["type"]
        state["type"] = t
        if name_var.get().strip() in ("", old):
            name_var.set(t)
        info = ROOM_TYPES[t]
        state["w"], state["h"] = info["w"], info["h"]
        width_stepper.set(info["w"])
        length_stepper.set(info["h"])
        paint()

    for i, t in enumerate(ROOM_TYPES):
        cv = tk.Canvas(grid, width=96, height=80, bg=PANEL, highlightthickness=0, cursor="hand2")
        cv.grid(row=i // 4, column=i % 4, padx=3, pady=3)
        cv.bind("<Button-1>", lambda e, t=t: choose(t))
        chips[t] = cv

    caption(d.body, "Room name").pack(anchor="w")
    make_entry(d.body, name_var).pack(fill="x", ipady=6, pady=(4, 10))
    sizes = tk.Frame(d.body, bg=PANEL)
    sizes.pack(fill="x")
    caption(sizes, "Width").grid(row=0, column=0, sticky="w", padx=(0, 30))
    caption(sizes, "Length").grid(row=0, column=1, sticky="w")
    width_stepper = Stepper(sizes, state["w"], MIN_SIZE, MAX_SIZE, lambda v: state.update(w=v))
    width_stepper.grid(row=1, column=0, pady=4, padx=(0, 30))
    length_stepper = Stepper(sizes, state["h"], MIN_SIZE, MAX_SIZE, lambda v: state.update(h=v))
    length_stepper.grid(row=1, column=1, pady=4)
    paint()
    d.add_buttons(lambda: d.finish((state["type"], name_var.get().strip() or state["type"],
                                    state["w"], state["h"])), "Add Room")
    return d.show()


def item_dialog(app, item):
    """Edit-furniture dialog. Returns (name, price, colour) or None."""
    d = Dialog(app, "Edit Furniture")
    name_var = tk.StringVar(value=item.name)
    price_var = tk.StringVar(value=str(item.price))
    colour = {"value": item.color}
    caption(d.body, "Name").pack(anchor="w")
    make_entry(d.body, name_var).pack(fill="x", ipady=6, pady=(4, 10))
    caption(d.body, "Price (\u20b9)").pack(anchor="w")
    make_entry(d.body, price_var).pack(fill="x", ipady=6, pady=(4, 10))
    caption(d.body, "Colour").pack(anchor="w")
    swatch = tk.Canvas(d.body, width=120, height=34, bg=PANEL, highlightthickness=0, cursor="hand2")
    swatch.pack(anchor="w", pady=(4, 0))

    def paint():
        swatch.delete("all")
        round_rect(swatch, 1, 1, 119, 33, 10, fill=colour["value"], outline=LINE)
        swatch.create_text(60, 17, text="Change", fill="#FFFFFF" if sum(int(colour["value"][i:i + 2], 16)
                                                                       for i in (1, 3, 5)) < 380 else "#222222",
                           font=F(10, True))

    def pick(_):
        chosen = colorchooser.askcolor(color=colour["value"], parent=d, title="Furniture colour")[1]
        if chosen:
            colour["value"] = chosen
            paint()

    swatch.bind("<Button-1>", pick)
    paint()

    def ok():
        raw = price_var.get().replace(",", "").replace("\u20b9", "").strip()
        if not raw.isdigit():
            messagebox.showerror("Price", "Please enter the price as a whole number, e.g. 25000.", parent=d)
            return
        d.finish((name_var.get().strip() or item.kind, int(raw), colour["value"]))

    d.add_buttons(ok, "Save")
    return d.show()


def load_dialog(app, rows):
    """Lists saved projects. Returns the chosen project id, or None."""
    d = Dialog(app, "Load Project")
    tree = ttk.Treeview(d.body, columns=("id", "name", "rooms", "items", "saved"), show="headings",
                        height=9, selectmode="browse")
    for col, text, width, anchor in (("id", "ID", 46, "center"), ("name", "Project", 210, "w"),
                                     ("rooms", "Rooms", 60, "center"), ("items", "Items", 60, "center"),
                                     ("saved", "Saved on", 160, "w")):
        tree.heading(col, text=text)
        tree.column(col, width=width, anchor=anchor)
    tree.pack(fill="both", expand=True)
    for r in rows:
        saved = r[3].strftime("%d %b %Y, %I:%M %p") if hasattr(r[3], "strftime") else str(r[3])
        tree.insert("", "end", iid=str(r[0]), values=(r[0], r[1], r[4], r[5], saved))
    if rows:
        tree.selection_set(str(rows[0][0]))

    def chosen():
        sel = tree.selection()
        return int(sel[0]) if sel else None

    def open_it():
        if chosen() is not None:
            d.finish(chosen())

    def delete_it():
        pid = chosen()
        if pid is None:
            return
        name = tree.item(str(pid), "values")[1]
        if messagebox.askyesno("Delete project", "Permanently delete '%s' from the database?" % name, parent=d):
            try:
                app.db.delete_project(pid)
                tree.delete(str(pid))
                if app.project_id == pid:
                    app.project_id = None
            except mysql.connector.Error as err:
                messagebox.showerror("Database error", str(err), parent=d)

    tree.bind("<Double-1>", lambda e: open_it())
    RoundButton(d.foot, text="Delete", icon="trash", command=delete_it, bg=DARK_RED, fg="#FF9A91").pack(side="left")
    d.add_buttons(open_it, "Open")
    return d.show()


def settings_dialog(app):
    """Budget and display options."""
    d = Dialog(app, "Settings")
    budget_var = tk.StringVar(value=str(app.budget))
    snap_var = tk.BooleanVar(value=app.snap)
    grid_var = tk.BooleanVar(value=app.show_grid)
    caption(d.body, "Total budget (\u20b9)").pack(anchor="w")
    make_entry(d.body, budget_var).pack(fill="x", ipady=6, pady=(4, 12))
    for text, var in (("Snap furniture to a half-foot grid", snap_var), ("Show grid lines", grid_var)):
        tk.Checkbutton(d.body, text=text, variable=var, bg=PANEL, fg=TEXT, selectcolor=PANEL3,
                       activebackground=PANEL, activeforeground=TEXT, font=F(11), bd=0,
                       highlightthickness=0, anchor="w").pack(fill="x", pady=2)
    tips = ("Drag furniture to move it  \u2022  Right-click (or R) to rotate\n"
            "Delete key removes it  \u2022  Arrow keys nudge it  \u2022  Ctrl+D duplicates\n"
            "Drag an empty floor area to move a room  \u2022  Drag the round corner handle to resize\n"
            "Mouse wheel zooms  \u2022  Drag the background to pan  \u2022  Ctrl+S saves")
    tk.Label(d.body, text=tips, bg=PANEL, fg=MUTED, font=F(9), justify="left").pack(anchor="w", pady=(14, 0))

    def ok():
        raw = budget_var.get().replace(",", "").replace("\u20b9", "").strip()
        if not raw.isdigit() or int(raw) <= 0:
            messagebox.showerror("Budget", "Please enter the budget as a whole number, e.g. 1000000.", parent=d)
            return
        d.finish((int(raw), snap_var.get(), grid_var.get()))

    d.add_buttons(ok, "Apply")
    return d.show()


# =====================================================================
# 8. MAIN APPLICATION
# =====================================================================
class DreamHouseApp:
    """The whole application window.

    Coordinates:  rooms and furniture live in FEET.  to_screen() / to_model() convert between
    feet and canvas pixels using the zoom level and the pan offset (ox, oy)."""

    def __init__(self, root):
        self.root = root
        choose_font(root)
        root.title("Dream House Builder")
        root.configure(bg=BG)
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry("%dx%d+20+20" % (min(1440, sw - 40), min(900, sh - 90)))
        root.minsize(1100, 700)
        try:
            root.state("zoomed")
        except tk.TclError:
            try:
                root.attributes("-zoomed", True)
            except tk.TclError:
                pass

        # ---- application state ----
        self.db = None
        self.project_id = None
        self.project_name = "My Dream House"
        self.budget = DEFAULT_BUDGET
        self.rooms = []
        self.sel_room = None
        self.sel_item = None
        self.name_room = None            # room currently shown in the name box
        self.dirty = False
        self.zoom, self.ox, self.oy = 20.0, 40.0, 40.0
        self.snap, self.show_grid = True, True
        self.category = "All"
        self.drag = None                 # info about the drag in progress on the plan
        self.cat_drag = None             # drag started from a catalogue card
        self.toast_label = None
        self._resize_job = None
        self._fit_tries = 0

        self.setup_style()
        self.build_ui()
        self.bind_keys()
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.connect_database()
        self.build_default_house()
        self.refresh_all()
        root.after(150, self.fit_view)

    # -----------------------------------------------------------------
    # styling
    # -----------------------------------------------------------------
    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=PANEL3, background=PANEL3, foreground=TEXT,
                        arrowcolor=TEXT, bordercolor=LINE, lightcolor=PANEL3, darkcolor=PANEL3, padding=4)
        style.map("TCombobox", fieldbackground=[("readonly", PANEL3)], foreground=[("readonly", TEXT)],
                  selectbackground=[("readonly", PANEL3)], selectforeground=[("readonly", TEXT)])
        font_spec = "{%s} 10" % FONT_FAMILY
        self.root.option_add("*TCombobox*Listbox.background", PANEL2)
        self.root.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", BLUE)
        self.root.option_add("*TCombobox*Listbox.font", font_spec)
        style.configure("Treeview", background=PANEL2, fieldbackground=PANEL2, foreground=TEXT,
                        rowheight=30, borderwidth=0, font=F(10))
        style.configure("Treeview.Heading", background=PANEL3, foreground=TEXT, font=F(10, True), relief="flat")
        style.map("Treeview", background=[("selected", BLUE)])
        style.map("Treeview.Heading", background=[("active", PANEL3)])

    # -----------------------------------------------------------------
    # building the window
    # -----------------------------------------------------------------
    def build_ui(self):
        self.build_header()
        self.build_footer()
        self.build_catalog()
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=10, pady=(10, 6))
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)
        self.left = tk.Frame(body, bg=PANEL, width=236, highlightbackground=LINE, highlightthickness=1)
        self.left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.left.grid_propagate(False)
        self.left.pack_propagate(False)
        center = tk.Frame(body, bg=CANVAS_BG, highlightbackground=LINE, highlightthickness=1)
        center.grid(row=0, column=1, sticky="nsew")
        right = tk.Frame(body, bg=BG, width=312)
        right.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        right.grid_propagate(False)
        right.pack_propagate(False)
        self.build_left(self.left)
        self.build_plan(center)
        self.build_right(right)

    def build_header(self):
        bar = tk.Frame(self.root, bg=PANEL, height=66)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        IconButton(bar, "menu", TEXT, self.toggle_sidebar, size=36).pack(side="left", padx=(18, 8))
        self.title_cv = tk.Canvas(bar, height=66, width=500, bg=PANEL, highlightthickness=0, cursor="hand2")
        self.title_cv.pack(side="left")
        self.title_cv.bind("<Button-1>", lambda e: self.rename_project())
        RoundButton(bar, icon="gear", width=44, height=40, bg=PANEL3, command=self.open_settings).pack(
            side="right", padx=(6, 18), pady=13)
        RoundButton(bar, text="Load", icon="folder", bg=PANEL3, height=40, command=self.load_project).pack(
            side="right", padx=6, pady=13)
        RoundButton(bar, text="Save", icon="save", bg=BLUE, height=40, command=self.save_project).pack(
            side="right", padx=6, pady=13)
        RoundButton(bar, text="New Project", icon="plus", bg=PANEL3, height=40, command=self.new_project).pack(
            side="right", padx=6, pady=13)

    def build_footer(self):
        foot = tk.Frame(self.root, bg=PANEL, height=38)
        foot.pack(side="bottom", fill="x", padx=10, pady=(0, 10))
        foot.pack_propagate(False)
        for icon, text, colour in (("cursor", "Select Item", MUTED), ("move", "Drag to Place", MUTED),
                                   ("rotate", "Right Click to Rotate", MUTED), ("trash", "Delete Item", RED)):
            cell = tk.Frame(foot, bg=PANEL)
            cell.pack(side="left", padx=(20, 8))
            cv = tk.Canvas(cell, width=24, height=24, bg=PANEL, highlightthickness=0)
            cv.pack(side="left")
            draw_icon(cv, icon, 12, 12, 16, colour)
            tk.Label(cell, text=text, bg=PANEL, fg=colour, font=F(10)).pack(side="left", padx=(4, 0), pady=6)

    # ---- left sidebar: rooms + budget ----
    def build_left(self, left):
        tk.Label(left, text="ROOMS", bg=PANEL, fg=TEXT, font=F(14, True)).pack(side="top", anchor="w", padx=18, pady=(16, 6))
        budget = tk.Frame(left, bg=PANEL)
        budget.pack(side="bottom", fill="x", padx=18, pady=(0, 14))
        tk.Label(budget, text="BUDGET", bg=PANEL, fg=TEXT, font=F(14, True)).pack(anchor="w", pady=(0, 2))
        self.stat = {}
        for key, colour in (("Total Budget", GREEN), ("Total Cost", GOLD), ("Remaining", CYAN)):
            tk.Label(budget, text=key, bg=PANEL, fg=MUTED, font=F(10)).pack(anchor="w")
            label = tk.Label(budget, text="", bg=PANEL, fg=colour, font=F(19, True))
            label.pack(anchor="w", pady=(0, 3))
            self.stat[key] = label
        self.bar = tk.Canvas(budget, height=10, bg=PANEL, highlightthickness=0)
        self.bar.pack(fill="x", pady=(4, 4))
        self.bar.bind("<Configure>", lambda e: self.refresh_budget())
        self.bar_note = tk.Label(budget, text="", bg=PANEL, fg=MUTED, font=F(9))
        self.bar_note.pack(anchor="w")
        tk.Frame(left, bg=LINE, height=1).pack(side="bottom", fill="x", padx=16, pady=8)
        buttons = tk.Frame(left, bg=PANEL)
        buttons.pack(side="bottom", fill="x", padx=14)
        RoundButton(buttons, text="Delete Room", icon="trash", bg=DARK_RED, fg="#FF9A91", width=206,
                    command=self.delete_room).pack(side="bottom", pady=(6, 0))
        RoundButton(buttons, text="Add Room", icon="plus", bg=PANEL3, width=206,
                    command=self.add_room).pack(side="bottom")
        self.room_list = ScrollFrame(left, PANEL)
        self.room_list.pack(fill="both", expand=True, padx=(12, 6), pady=(0, 6))

    # ---- centre: the floor plan canvas ----
    def build_plan(self, center):
        self.plan = tk.Canvas(center, bg=CANVAS_BG, highlightthickness=0)
        self.plan.pack(fill="both", expand=True)
        self.plan.bind("<ButtonPress-1>", self.on_press)
        self.plan.bind("<B1-Motion>", self.on_drag)
        self.plan.bind("<ButtonRelease-1>", self.on_release)
        self.plan.bind("<Double-Button-1>", self.on_double)
        self.plan.bind("<Motion>", self.on_motion)
        self.plan.bind("<Configure>", self.on_resize)
        self.plan.bind("<MouseWheel>", self.on_wheel)
        self.plan.bind("<Button-4>", self.on_wheel)
        self.plan.bind("<Button-5>", self.on_wheel)
        if self.root.tk.call("tk", "windowingsystem") == "aqua":
            right_button, middle_button = "<Button-2>", "<Button-3>"
        else:
            right_button, middle_button = "<Button-3>", "<Button-2>"
        self.plan.bind(right_button, self.on_right_click)
        self.plan.bind(middle_button, self.on_pan_start)
        self.plan.bind("<B%s-Motion>" % middle_button[-2], self.on_pan_move)
        controls = tk.Frame(center, bg=CANVAS_BG)
        controls.place(relx=1, rely=1, x=-14, y=-14, anchor="se")
        RoundButton(controls, icon="minus", width=38, height=38, bg=PANEL3,
                    command=lambda: self.zoom_center(1 / 1.2)).pack(side="left", padx=3)
        RoundButton(controls, icon="plus", width=38, height=38, bg=PANEL3,
                    command=lambda: self.zoom_center(1.2)).pack(side="left", padx=3)
        RoundButton(controls, text="Fit", icon="fit", height=38, bg=PANEL3, command=self.fit_view).pack(
            side="left", padx=3)
        tk.Label(center, text="Wheel = zoom   \u2022   drag background = pan   \u2022   drag floor = move room   "
                              "\u2022   drag corner dot = resize", bg=CANVAS_BG, fg="#8896A5",
                 font=F(9)).place(relx=0, rely=1, x=14, y=-14, anchor="sw")

    # ---- right: room details + furniture list ----
    def build_right(self, right):
        card = tk.Frame(right, bg=PANEL, highlightbackground=LINE, highlightthickness=1)
        card.pack(side="top", fill="x")
        tk.Label(card, text="ROOM DETAILS", bg=PANEL, fg=TEXT, font=F(14, True)).pack(anchor="w", padx=16, pady=(14, 8))
        form = tk.Frame(card, bg=PANEL)
        form.pack(fill="x", padx=16, pady=(0, 14))
        form.grid_columnconfigure(1, weight=1)
        labels = ("Name", "Width", "Length", "Floor Type", "Wall Color", "Cost")
        for r, text in enumerate(labels):
            tk.Label(form, text=text, bg=PANEL, fg=MUTED, font=F(11)).grid(row=r, column=0, sticky="w", pady=5)
        self.name_var = tk.StringVar()
        self.name_entry = tk.Entry(form, textvariable=self.name_var, bg=PANEL3, fg=GREEN, relief="flat",
                                   insertbackground=TEXT, font=F(12, True), highlightthickness=1,
                                   highlightbackground=LINE, highlightcolor=BLUE, width=14)
        self.name_entry.grid(row=0, column=1, sticky="e", pady=5, ipady=4)
        self.name_entry.bind("<Return>", lambda e: self.apply_name())
        self.name_entry.bind("<FocusOut>", lambda e: self.apply_name())
        self.width_stepper = Stepper(form, 18, MIN_SIZE, MAX_SIZE, lambda v: self.resize_room_to(w=v))
        self.width_stepper.grid(row=1, column=1, sticky="e", pady=3)
        self.length_stepper = Stepper(form, 14, MIN_SIZE, MAX_SIZE, lambda v: self.resize_room_to(h=v))
        self.length_stepper.grid(row=2, column=1, sticky="e", pady=3)
        self.floor_var = tk.StringVar()
        self.floor_box = ttk.Combobox(form, textvariable=self.floor_var, values=list(FLOORS), state="readonly",
                                      width=13, font=F(10))
        self.floor_box.grid(row=3, column=1, sticky="e", pady=5)
        self.floor_box.bind("<<ComboboxSelected>>", self.change_floor)
        self.swatch = tk.Canvas(form, width=60, height=30, bg=PANEL, highlightthickness=0, cursor="hand2")
        self.swatch.grid(row=4, column=1, sticky="e", pady=5)
        self.swatch.bind("<Button-1>", lambda e: self.pick_wall_colour())
        self.cost_label = tk.Label(form, text="", bg=PANEL, fg=GREEN, font=F(14, True))
        self.cost_label.grid(row=5, column=1, sticky="e", pady=5)

        card2 = tk.Frame(right, bg=PANEL, highlightbackground=LINE, highlightthickness=1)
        card2.pack(side="top", fill="both", expand=True, pady=(10, 0))
        tk.Label(card2, text="FURNITURE IN ROOM", bg=PANEL, fg=TEXT, font=F(14, True)).pack(
            side="top", anchor="w", padx=16, pady=(14, 6))
        foot = tk.Frame(card2, bg=PANEL)
        foot.pack(side="bottom", fill="x", padx=14, pady=(4, 12))
        total_row = tk.Frame(foot, bg=PANEL)
        total_row.pack(fill="x", pady=(0, 8))
        tk.Label(total_row, text="Total", bg=PANEL, fg=TEXT, font=F(12, True)).pack(side="left")
        self.furn_total = tk.Label(total_row, text="", bg=PANEL, fg=GREEN, font=F(15, True))
        self.furn_total.pack(side="right")
        RoundButton(foot, text="Rotate", icon="rotate", bg=PANEL3, width=134, command=self.rotate_selected).pack(side="left")
        RoundButton(foot, text="Duplicate", icon="copy", bg=PANEL3, width=134, command=self.duplicate_selected).pack(side="right")
        self.furn_list = ScrollFrame(card2, PANEL)
        self.furn_list.pack(fill="both", expand=True, padx=(10, 6))

    # ---- bottom: furniture catalogue ----
    def build_catalog(self):
        cat = tk.Frame(self.root, bg=PANEL, height=214, highlightbackground=LINE, highlightthickness=1)
        cat.pack(side="bottom", fill="x", padx=10, pady=(0, 6))
        cat.pack_propagate(False)
        head = tk.Frame(cat, bg=PANEL)
        head.pack(fill="x", padx=16, pady=(10, 4))
        tk.Label(head, text="FURNITURE CATALOG", bg=PANEL, fg=TEXT, font=F(14, True)).pack(side="left", padx=(0, 14))
        self.tab_buttons = {}
        for name in CATEGORIES:
            btn = RoundButton(head, text=name, bg=BLUE if name == self.category else PANEL2, height=30,
                              radius=10, size=9, command=lambda n=name: self.set_category(n))
            btn.pack(side="left", padx=3)
            self.tab_buttons[name] = btn
        self.search_var = tk.StringVar()
        box = tk.Frame(head, bg=PANEL3)
        box.pack(side="right")
        icon = tk.Canvas(box, width=26, height=28, bg=PANEL3, highlightthickness=0)
        icon.pack(side="left", padx=(6, 0))
        draw_icon(icon, "search", 14, 14, 14, MUTED)
        entry = tk.Entry(box, textvariable=self.search_var, width=16, bg=PANEL3, fg=TEXT, relief="flat",
                         insertbackground=TEXT, font=F(10))
        entry.pack(side="left", ipady=5, padx=(0, 8))
        entry.bind("<KeyRelease>", lambda e: self.refresh_catalog())
        row = tk.Frame(cat, bg=PANEL)
        row.pack(fill="both", expand=True, padx=6, pady=(0, 8))
        IconButton(row, "left", MUTED, lambda: self.cat_canvas.xview_scroll(-3, "units"), size=30).pack(side="left")
        IconButton(row, "right", MUTED, lambda: self.cat_canvas.xview_scroll(3, "units"), size=30).pack(side="right")
        self.cat_canvas = tk.Canvas(row, bg=PANEL, highlightthickness=0, xscrollincrement=40)
        self.cat_canvas.pack(side="left", fill="both", expand=True)
        self.cat_inner = tk.Frame(self.cat_canvas, bg=PANEL)
        self.cat_canvas.create_window((0, 0), window=self.cat_inner, anchor="nw")
        self.cat_inner.bind("<Configure>", lambda e: self.cat_canvas.configure(scrollregion=self.cat_canvas.bbox("all")))
        bind_wheel(row, lambda step: self.cat_canvas.xview_scroll(step * 3, "units"))
        self.refresh_catalog()

    # -----------------------------------------------------------------
    # database connection
    # -----------------------------------------------------------------
    def connect_database(self):
        """Connects to MySQL. Asks for the password if the server refuses the login."""
        config = dict(DB_CONFIG)
        for _ in range(3):
            try:
                self.db = Database(config)
                DB_CONFIG["password"] = config["password"]
                return True
            except mysql.connector.Error as err:
                if getattr(err, "errno", None) == errorcode.ER_ACCESS_DENIED_ERROR:
                    pw = ask_text(self, "MySQL Password", "Enter the MySQL password for user '%s':" % config["user"],
                                  "", password=True)
                    if pw is None:
                        break
                    config["password"] = pw
                    continue
                messagebox.showwarning(
                    "MySQL not available",
                    "Could not connect to MySQL.\n\n%s\n\nYou can still design a house; "
                    "Save and Load need MySQL to be running." % err)
                break
        self.db = None
        return False

    def require_db(self):
        if self.db is None:
            self.connect_database()
        if self.db is None:
            self.toast("MySQL is not connected - check that the server is running", "err")
            return False
        return True

    # -----------------------------------------------------------------
    # coordinates and view
    # -----------------------------------------------------------------
    def to_screen(self, fx, fy):
        return self.ox + fx * self.zoom, self.oy + fy * self.zoom

    def to_model(self, sx, sy):
        return (sx - self.ox) / self.zoom, (sy - self.oy) / self.zoom

    def wall_px(self):
        return max(6.0, 0.6 * self.zoom)

    def fit_view(self):
        """Zoom and pan so that the whole house is visible."""
        cw, ch = self.plan.winfo_width(), self.plan.winfo_height()
        if (cw < 200 or ch < 150) and self._fit_tries < 20:
            self._fit_tries += 1
            self.root.after(100, self.fit_view)
            return
        self._fit_tries = 0
        if not self.rooms:
            return
        x1 = min(r.x for r in self.rooms) - 2
        y1 = min(r.y for r in self.rooms) - 2
        x2 = max(r.x + r.w for r in self.rooms) + 2
        y2 = max(r.y + r.h for r in self.rooms) + 2
        self.zoom = max(8.0, min(40.0, cw / (x2 - x1), ch / (y2 - y1)))
        self.ox = (cw - (x2 - x1) * self.zoom) / 2 - x1 * self.zoom
        self.oy = (ch - (y2 - y1) * self.zoom) / 2 - y1 * self.zoom
        self.draw_plan()

    def zoom_at(self, factor, sx, sy):
        mx, my = self.to_model(sx, sy)
        self.zoom = max(8.0, min(45.0, self.zoom * factor))
        self.ox, self.oy = sx - mx * self.zoom, sy - my * self.zoom
        self.draw_plan()

    def zoom_center(self, factor):
        self.zoom_at(factor, self.plan.winfo_width() / 2, self.plan.winfo_height() / 2)

    def on_wheel(self, event):
        up = event.num == 4 or getattr(event, "delta", 0) > 0
        self.zoom_at(1.12 if up else 1 / 1.12, event.x, event.y)

    def on_resize(self, event):
        if self._resize_job:
            self.root.after_cancel(self._resize_job)
        self._resize_job = self.root.after(40, self.draw_plan)

    def toggle_sidebar(self):
        if self.left.winfo_ismapped():
            self.left.grid_remove()
        else:
            self.left.grid()

    # -----------------------------------------------------------------
    # default house
    # -----------------------------------------------------------------
    def build_default_house(self):
        living = Room("Living Room", x=0, y=0)
        living.add_item("TV Unit", 1.3, 7, 3)
        living.add_item("Carpet", 8.0, 7, 1)
        living.add_item("Center Table", 8.0, 7, 1)
        living.add_item("Sofa", 12.2, 7, 1)
        living.add_item("Plant", 16.3, 1.7)
        bedroom = Room("Bedroom", x=18, y=0)
        bedroom.add_item("Bed", 12.2, 7, 1)
        bedroom.add_item("Wardrobe", 1.4, 3.5, 3)
        bedroom.add_item("Study Desk", 3.6, 12.0, 2)
        bedroom.add_item("Plant", 14.6, 12.4)
        bedroom.add_item("Lamp", 14.7, 2.2)
        kitchen = Room("Kitchen", x=0, y=14)
        kitchen.add_item("Refrigerator", 1.9, 1.9)
        kitchen.add_item("Sink", 5.6, 1.5)
        kitchen.add_item("Stove", 8.7, 1.5)
        kitchen.add_item("Kitchen Counter", 12.6, 6.0, 1)
        kitchen.add_item("Dining Table", 6.4, 6.6)
        bathroom = Room("Bathroom", x=14, y=14)
        bathroom.add_item("Toilet", 8.5, 2.6, 1)
        bathroom.add_item("Washbasin", 1.9, 6.6, 2)
        self.rooms = [living, bedroom, kitchen, bathroom]
        self.sel_room, self.sel_item = living, None
        self.project_id = None
        self.budget = DEFAULT_BUDGET
        self.dirty = False

    def new_project(self):
        if not self.confirm_discard():
            return
        name = ask_text(self, "New Project", "Name your dream house:", "My Dream House")
        if name is None:
            return
        self.build_default_house()
        self.project_name = name or "My Dream House"
        self.refresh_all()
        self.fit_view()
        self.toast("New project started")

    def rename_project(self):
        name = ask_text(self, "Rename Project", "Project name:", self.project_name)
        if name:
            self.project_name = name
            self.mark_dirty()

    def confirm_discard(self):
        if not self.dirty:
            return True
        return messagebox.askyesno("Unsaved changes", "You have unsaved changes. Continue and lose them?")

    # -----------------------------------------------------------------
    # refreshing the interface
    # -----------------------------------------------------------------
    def refresh_all(self):
        self.refresh_details()
        self.draw_plan()
        self.refresh_rooms()
        self.refresh_furniture()
        self.refresh_budget()
        self.update_title()

    def mark_dirty(self):
        self.dirty = True
        self.update_title()

    def update_title(self):
        cv = self.title_cv
        cv.delete("all")
        text = self.project_name.upper()
        font = F(22, True)
        width = tkfont.Font(family=font[0], size=font[1], weight=font[2]).measure(text)
        cv.create_text(6, 33, text=text, anchor="w", fill=TEXT, font=font)
        draw_icon(cv, "home", 6 + width + 30, 33, 26, "#F5A742")
        x = 6 + width + 56
        if self.dirty:
            round_rect(cv, x, 22, x + 92, 44, 11, fill="#4A3A12", outline="")
            cv.create_text(x + 46, 33, text="UNSAVED", fill=GOLD, font=F(9, True))
            x += 100
        cv.config(width=x + 10)
        self.root.title("Dream House Builder - %s%s" % (self.project_name, " *" if self.dirty else ""))

    def refresh_rooms(self):
        def build(parent):
            for room in self.rooms:
                self.make_room_row(parent, room)
        self.room_list.rebuild(build)

    def make_room_row(self, parent, room):
        active = room is self.sel_room
        cv = tk.Canvas(parent, width=206, height=48, bg=PANEL, highlightthickness=0, cursor="hand2")
        cv.pack(anchor="w", pady=2)
        round_rect(cv, 1, 1, 205, 47, 14, fill="#173A2E" if active else PANEL, outline="#2E7D57" if active else "")
        round_rect(cv, 9, 9, 39, 39, 9, fill=room.accent, outline="")
        draw_item_icon(cv, ROOM_TYPES[room.type]["icon"], 24, 24, 20, 20, "#FFFFFF")
        name = room.name if len(room.name) <= 16 else room.name[:15] + "..."
        cv.create_text(52, 24, text=name, anchor="w", fill=TEXT if active else "#D6E2EC", font=F(11, active))
        cv.bind("<Button-1>", lambda e, r=room: self.select_room(r))

    def select_room(self, room):
        self.sel_room, self.sel_item = room, None
        self.refresh_all()

    def room_of(self, item):
        return next((r for r in self.rooms if item in r.items), None)

    def select_item(self, item):
        room = self.room_of(item)
        if room is None:
            return
        self.sel_room, self.sel_item = room, item
        self.refresh_all()

    def deselect(self):
        self.sel_item = None
        self.refresh_all()

    def refresh_details(self):
        self.apply_name()                       # keep a name that was typed but not confirmed
        room = self.sel_room
        self.name_room = room
        if room is None:
            return
        self.name_var.set(room.name)
        self.width_stepper.set(room.w)
        self.length_stepper.set(room.h)
        self.floor_var.set(room.floor)
        self.cost_label.config(text=money(room.cost))
        self.swatch.delete("all")
        round_rect(self.swatch, 1, 1, 59, 29, 9, fill=room.wall, outline="#FFFFFF", width=2)

    def apply_name(self, _event=None):
        room = self.name_room
        if room is None or room not in self.rooms:
            return
        text = self.name_var.get().strip()
        if not text:
            self.name_var.set(room.name)
        elif text != room.name:
            room.name = text
            self.mark_dirty()
            self.draw_plan()
            self.refresh_rooms()

    def refresh_furniture(self):
        room = self.sel_room

        def build(parent):
            if room is None or not room.items:
                tk.Label(parent, text="No furniture yet.\nClick or drag items\nfrom the catalogue below.",
                         bg=PANEL, fg=MUTED, font=F(10), justify="left").pack(anchor="w", padx=8, pady=10)
                return
            for item in room.items:
                bg = PANEL3 if item is self.sel_item else PANEL
                row = tk.Frame(parent, bg=bg)
                row.pack(fill="x", pady=1)
                name = tk.Label(row, text=item.name, bg=bg, fg=TEXT, font=F(11), anchor="w")
                name.pack(side="left", padx=(8, 0), pady=3)
                IconButton(row, "trash", RED, lambda i=item: self.delete_item(i)).pack(side="right", padx=(0, 4))
                IconButton(row, "pencil", "#FFA94D", lambda i=item: self.edit_item(i)).pack(side="right")
                price = tk.Label(row, text=money(item.price), bg=bg, fg=GREEN, font=F(11, True))
                price.pack(side="right", padx=6)
                for widget in (row, name, price):
                    widget.bind("<Button-1>", lambda e, i=item: self.select_item(i))
        self.furn_list.rebuild(build)
        self.furn_total.config(text=money(room.furniture_total()) if room else money(0))

    def total_cost(self):
        return sum(r.total() for r in self.rooms)

    def refresh_budget(self):
        total = self.total_cost()
        remaining = self.budget - total
        self.stat["Total Budget"].config(text=money(self.budget))
        self.stat["Total Cost"].config(text=money(total))
        self.stat["Remaining"].config(text=money(remaining), fg=CYAN if remaining >= 0 else RED)
        fraction = min(1.0, total / self.budget) if self.budget else 0
        width = max(self.bar.winfo_width(), 120)
        self.bar.delete("all")
        round_rect(self.bar, 0, 0, width, 10, 5, fill=PANEL3, outline="")
        if fraction > 0:
            colour = GREEN if fraction < .8 else (GOLD if fraction < 1 else RED)
            round_rect(self.bar, 0, 0, max(10, width * fraction), 10, 5, fill=colour, outline="")
        if remaining < 0:
            self.bar_note.config(text="Over budget by " + money(-remaining), fg=RED)
        else:
            self.bar_note.config(text="%d%% of budget used" % round(fraction * 100), fg=MUTED)

    def toast(self, text, kind="ok"):
        """Short message that appears at the top of the plan and fades away."""
        colour = {"ok": GREEN, "warn": GOLD, "err": RED}[kind]
        if self.toast_label is not None:
            self.toast_label.destroy()
        label = tk.Label(self.plan.master, text=text, bg=PANEL, fg=colour, font=F(11, True), padx=18, pady=9,
                         highlightthickness=2, highlightbackground=colour)
        label.place(relx=0.5, y=14, anchor="n")
        self.toast_label = label
        self.root.after(2800, lambda: label.destroy() if label.winfo_exists() else None)

    # -----------------------------------------------------------------
    # room editing
    # -----------------------------------------------------------------
    def find_free_spot(self, w, h, rooms):
        """First position (scanning rows from the top-left) where a w x h room fits without overlap."""
        for y in range(0, 90):
            for x in range(0, 90):
                if not any(rects_overlap(x, y, w, h, r.x, r.y, r.w, r.h) for r in rooms):
                    return x, y
        return 0, 0

    def collides(self, room, x, y, w, h):
        return any(o is not room and rects_overlap(x, y, w, h, o.x, o.y, o.w, o.h) for o in self.rooms)

    def add_room(self):
        result = room_dialog(self)
        if not result:
            return
        rtype, name, w, h = result
        x, y = self.find_free_spot(w, h, self.rooms)
        room = Room(rtype, name, x, y, w, h)
        self.rooms.append(room)
        self.sel_room, self.sel_item = room, None
        self.mark_dirty()
        self.refresh_all()
        self.fit_view()
        self.toast("%s added" % room.name)

    def delete_room(self):
        room = self.sel_room
        if room is None:
            return
        if len(self.rooms) <= 1:
            self.toast("A house needs at least one room", "warn")
            return
        if room.items and not messagebox.askyesno(
                "Delete room", "Delete '%s' and its %d furniture item(s)?" % (room.name, len(room.items))):
            return
        index = self.rooms.index(room)
        self.rooms.remove(room)
        self.sel_room = self.rooms[min(index, len(self.rooms) - 1)]
        self.sel_item = None
        self.mark_dirty()
        self.refresh_all()

    def resize_room_to(self, w=None, h=None):
        """Called by the width / length steppers. Returns False if the new size would hit another room."""
        room = self.sel_room
        if room is None:
            return False
        w, h = w or room.w, h or room.h
        if self.collides(room, room.x, room.y, w, h):
            self.toast("Another room is in the way", "warn")
            return False
        self.apply_size(room, w, h)
        return True

    def apply_size(self, room, w, h):
        room.w, room.h = w, h
        room.recalc_cost()
        for item in room.items:
            item.clamp_into(room)
        self.mark_dirty()
        self.draw_plan()
        self.refresh_details()
        self.refresh_budget()

    def change_floor(self, _event=None):
        room = self.sel_room
        if room is None:
            return
        room.floor = self.floor_var.get()
        room.recalc_cost()
        self.mark_dirty()
        self.refresh_all()

    def pick_wall_colour(self):
        room = self.sel_room
        if room is None:
            return
        colour = colorchooser.askcolor(color=room.wall, parent=self.root, title="Wall colour")[1]
        if colour:
            room.wall = colour
            self.mark_dirty()
            self.refresh_all()

    # -----------------------------------------------------------------
    # furniture editing
    # -----------------------------------------------------------------
    def free_spot(self, room, kind):
        """Finds an empty place in the room (closest to the centre) for a new item."""
        spec = CATALOG[kind]
        w, h = spec["w"], spec["h"]
        cx, cy = room.w / 2, room.h / 2
        lo_x, hi_x = w / 2 + WALL_FT, room.w - w / 2 - WALL_FT
        lo_y, hi_y = h / 2 + WALL_FT, room.h - h / 2 - WALL_FT
        if hi_x < lo_x or hi_y < lo_y:
            return cx, cy
        spots, x = [], lo_x
        while x <= hi_x + 0.01:
            y = lo_y
            while y <= hi_y + 0.01:
                spots.append((x, y))
                y += 1
            x += 1
        spots.sort(key=lambda s: (s[0] - cx) ** 2 + (s[1] - cy) ** 2)
        for x, y in spots:
            clear = True
            for it in room.items:
                if (kind in LOW_LAYER) != (it.kind in LOW_LAYER):
                    continue                              # rugs and furniture may overlap
                if rects_overlap(x - w / 2, y - h / 2, w, h, it.x - it.w / 2, it.y - it.h / 2, it.w, it.h):
                    clear = False
                    break
            if clear:
                return x, y
        return cx, cy

    def add_item(self, room, kind, x, y, rot=0):
        item = room.add_item(kind, x, y, rot)
        self.sel_room, self.sel_item = room, item
        self.mark_dirty()
        self.refresh_all()
        if self.total_cost() > self.budget:
            self.toast("Over budget by " + money(self.total_cost() - self.budget), "warn")

    def add_to_selected_room(self, kind):
        room = self.sel_room
        if room is None:
            self.toast("Select a room first", "warn")
            return
        x, y = self.free_spot(room, kind)
        self.add_item(room, kind, x, y)

    def add_item_at(self, kind, sx, sy):
        """Used when furniture is dragged from the catalogue and dropped on the plan."""
        mx, my = self.to_model(sx, sy)
        room = self.find_room(mx, my)
        if room is None:
            self.toast("Drop the furniture inside a room", "warn")
            return
        x, y = mx - room.x, my - room.y
        if self.snap:
            x, y = round(x * 2) / 2, round(y * 2) / 2
        self.add_item(room, kind, x, y)

    def delete_item(self, item):
        room = self.room_of(item)
        if room is None:
            return
        room.items.remove(item)
        if self.sel_item is item:
            self.sel_item = None
        self.mark_dirty()
        self.refresh_all()

    def edit_item(self, item):
        result = item_dialog(self, item)
        if result:
            item.name, item.price, item.color = result
            self.mark_dirty()
            self.refresh_all()

    def rotate_item(self, item):
        room = self.room_of(item)
        if room is None:
            return
        item.rot = (item.rot + 1) % 4
        item.clamp_into(room)
        self.sel_room, self.sel_item = room, item
        self.mark_dirty()
        self.draw_plan()
        self.refresh_furniture()

    def rotate_selected(self):
        if self.sel_item is None:
            self.toast("Select a furniture item first", "warn")
        else:
            self.rotate_item(self.sel_item)

    def duplicate_selected(self):
        item = self.sel_item
        room = self.room_of(item) if item else None
        if room is None:
            self.toast("Select a furniture item first", "warn")
            return
        copy = Item(item.kind, item.x + 1, item.y + 1, item.rot, item.name, item.price, item.color)
        copy.clamp_into(room)
        room.items.append(copy)
        self.sel_item = copy
        self.mark_dirty()
        self.refresh_all()

    # -----------------------------------------------------------------
    # catalogue
    # -----------------------------------------------------------------
    def set_category(self, name):
        self.category = name
        for n, btn in self.tab_buttons.items():
            btn.recolor(BLUE if n == name else PANEL2)
        self.refresh_catalog()

    def refresh_catalog(self):
        for widget in self.cat_inner.winfo_children():
            widget.destroy()
        query = self.search_var.get().strip().lower()
        shown = [k for k, s in CATALOG.items()
                 if (self.category == "All" or s["cat"] == self.category) and query in k.lower()]
        for kind in shown:
            self.make_card(kind).pack(side="left", padx=5, pady=2)
        if not shown:
            tk.Label(self.cat_inner, text="No furniture found.", bg=PANEL, fg=MUTED, font=F(11)).pack(padx=20, pady=40)
        self.cat_canvas.xview_moveto(0)

    def make_card(self, kind):
        spec = CATALOG[kind]
        cv = tk.Canvas(self.cat_inner, width=114, height=146, bg=PANEL, highlightthickness=0, cursor="hand2")
        shape = round_rect(cv, 2, 2, 112, 144, 16, fill=PANEL2, outline=LINE)
        draw_item_icon(cv, kind, 57, 52, 84, 62)
        cv.create_text(57, 108, text=kind, fill=TEXT, font=F(10, True), width=104)
        cv.create_text(57, 129, text=money(spec["price"]), fill=GREEN, font=F(10, True))
        cv.bind("<Enter>", lambda e: cv.itemconfig(shape, fill=PANEL3))
        cv.bind("<Leave>", lambda e: cv.itemconfig(shape, fill=PANEL2))
        cv.bind("<ButtonPress-1>", lambda e, k=kind: self.card_press(e, k))
        cv.bind("<B1-Motion>", self.card_motion)
        cv.bind("<ButtonRelease-1>", self.card_release)
        return cv

    def card_press(self, event, kind):
        self.cat_drag = {"kind": kind, "x": event.x_root, "y": event.y_root, "ghost": None}

    def card_motion(self, event):
        d = self.cat_drag
        if not d:
            return
        if d["ghost"] is None and abs(event.x_root - d["x"]) + abs(event.y_root - d["y"]) > 10:
            ghost = tk.Toplevel(self.root)
            ghost.overrideredirect(True)
            try:
                ghost.attributes("-topmost", True)
            except tk.TclError:
                pass
            tk.Label(ghost, text=d["kind"], bg=BLUE, fg="white", font=F(11, True), padx=16, pady=7).pack()
            d["ghost"] = ghost
        if d["ghost"] is not None:
            d["ghost"].geometry("+%d+%d" % (event.x_root + 16, event.y_root + 16))

    def card_release(self, event):
        d, self.cat_drag = self.cat_drag, None
        if not d:
            return
        if d["ghost"] is None:                     # it was a simple click
            self.add_to_selected_room(d["kind"])
            return
        d["ghost"].destroy()
        try:
            target = self.root.winfo_containing(event.x_root, event.y_root)
        except Exception:
            target = None
        if target is self.plan:
            self.add_item_at(d["kind"], event.x_root - self.plan.winfo_rootx(),
                             event.y_root - self.plan.winfo_rooty())
        else:
            self.toast("Drop the furniture on a room in the plan", "warn")

    # -----------------------------------------------------------------
    # drawing the floor plan
    # -----------------------------------------------------------------
    def draw_plan(self):
        c = self.plan
        c.delete("all")
        cw, ch = c.winfo_width(), c.winfo_height()
        if self.show_grid:
            self.draw_grid(cw, ch)
        for room in self.rooms:
            self.draw_floor(room)
        for room in self.rooms:
            self.draw_walls(room)
        for room in self.rooms:
            self.draw_openings(room)
        for room in self.rooms:
            self.draw_label(room)
        for room in self.rooms:
            for item in room.ordered_items():
                self.draw_item(room, item)
        self.draw_selection()

    def draw_grid(self, cw, ch):
        c, z = self.plan, self.zoom
        step = 1 if z >= 14 else 2
        for k in range(int(math.floor(-self.ox / z)), int(math.ceil((cw - self.ox) / z)) + 1):
            if k % step == 0:
                x = self.ox + k * z
                c.create_line(x, 0, x, ch, fill=GRID_MAJOR if k % 5 == 0 else GRID)
        for k in range(int(math.floor(-self.oy / z)), int(math.ceil((ch - self.oy) / z)) + 1):
            if k % step == 0:
                y = self.oy + k * z
                c.create_line(0, y, cw, y, fill=GRID_MAJOR if k % 5 == 0 else GRID)

    def draw_floor(self, room):
        c, z = self.plan, self.zoom
        style = FLOORS[room.floor]
        x1, y1 = self.to_screen(room.x, room.y)
        x2, y2 = self.to_screen(room.x + room.w, room.y + room.h)
        tags = ("room", "g%d" % room.uid)
        c.create_rectangle(x1, y1, x2, y2, fill=style["base"], outline="", tags=tags)
        kind = style["kind"]
        if kind == "planks":
            row = 0.9 * z
            for i in range(int(room.h / 0.9) + 1):
                ya = y1 + i * row
                if ya >= y2:
                    break
                yb = min(ya + row, y2)
                tone = shade(style["base"], (-.04, .02, .05, -.01)[(i + room.uid) % 4])
                c.create_rectangle(x1, ya, x2, yb, fill=tone, outline=style["line"], tags=tags)
                seam = ((i * 1.7) + room.uid * 0.9) % 4.6
                while seam < room.w:
                    c.create_line(x1 + seam * z, ya, x1 + seam * z, yb, fill=style["line"], tags=tags)
                    seam += 4.6
        elif kind in ("tiles", "marble"):
            size = style["size"]
            k = 1
            while k * size < room.w:
                c.create_line(x1 + k * size * z, y1, x1 + k * size * z, y2, fill=style["line"], tags=tags)
                k += 1
            k = 1
            while k * size < room.h:
                c.create_line(x1, y1 + k * size * z, x2, y1 + k * size * z, fill=style["line"], tags=tags)
                k += 1
            if kind == "marble":
                rnd = random.Random(room.uid)
                for _ in range(7):
                    px, py = x1 + rnd.random() * (x2 - x1), y1 + rnd.random() * (y2 - y1)
                    pts = [px, py]
                    for _ in range(3):
                        px += rnd.uniform(10, 40) * z / 20
                        py += rnd.uniform(-20, 30) * z / 20
                        pts += [min(max(px, x1), x2), min(max(py, y1), y2)]
                    c.create_line(*pts, fill="#CDD1D6", smooth=True, tags=tags)
        elif kind == "carpet":
            m = 0.7 * z
            c.create_rectangle(x1 + m, y1 + m, x2 - m, y2 - m, outline=style["line"], width=max(2, z / 8), tags=tags)
            c.create_rectangle(x1 + m * 1.9, y1 + m * 1.9, x2 - m * 1.9, y2 - m * 1.9,
                               outline=shade(style["base"], .25), width=1, tags=tags)

    def draw_walls(self, room):
        c, T = self.plan, self.wall_px()
        x1, y1 = self.to_screen(room.x, room.y)
        x2, y2 = self.to_screen(room.x + room.w, room.y + room.h)
        tags = ("room", "g%d" % room.uid)
        c.create_rectangle(x1 - T / 2, y1 - T / 2, x2 + T / 2, y2 + T / 2, outline=WALL_EDGE, width=2, tags=tags)
        c.create_rectangle(x1, y1, x2, y2, outline=room.wall, width=T, tags=tags)
        c.create_rectangle(x1 + T / 2, y1 + T / 2, x2 - T / 2, y2 - T / 2, outline=WALL_EDGE, width=1, tags=tags)

    def room_above(self, room):
        """True if another room touches the top wall of this room."""
        return any(o is not room and o.y + o.h == room.y and o.x < room.x + room.w and room.x < o.x + o.w
                   for o in self.rooms)

    def draw_openings(self, room):
        """Windows on the top wall and a door (with its swing) on the bottom wall."""
        c, z, T = self.plan, self.zoom, self.wall_px()
        x1, y1 = self.to_screen(room.x, room.y)
        x2, y2 = self.to_screen(room.x + room.w, room.y + room.h)
        tags = ("room", "g%d" % room.uid)
        if room.type != "Balcony" and not self.room_above(room):
            count = 2 if room.w >= 12 else 1
            length = min(5.0, room.w * 0.28) * z
            for k in range(count):
                frac = 0.5 if count == 1 else (0.27 if k == 0 else 0.73)
                cx = x1 + room.w * frac * z
                c.create_rectangle(cx - length / 2, y1 - T / 2, cx + length / 2, y1 + T / 2, fill="#FFFFFF",
                                   outline=WALL_EDGE, tags=tags)
                c.create_line(cx - length / 2 + 3, y1, cx + length / 2 - 3, y1, fill="#6FC3E8",
                              width=max(2, T / 4), tags=tags)
                c.create_line(cx, y1 - T / 2, cx, y1 + T / 2, fill=WALL_EDGE, tags=tags)
        if room.w >= 6:
            dw = 3 * z
            left_hinge = room.uid % 2 == 0
            xa = x1 + max(1.0, room.w * 0.16) * z if left_hinge else x2 - max(1.0, room.w * 0.16) * z - dw
            xb = xa + dw
            c.create_rectangle(xa, y2 - T / 2 - 1, xb, y2 + T / 2 + 1, fill=FLOORS[room.floor]["base"],
                               outline="", tags=tags)
            for x in (xa, xb):
                c.create_line(x, y2 - T / 2, x, y2 + T / 2, fill=WALL_EDGE, width=2, tags=tags)
            hinge = xa if left_hinge else xb
            c.create_line(hinge, y2, hinge, y2 - dw, fill="#6B4A32", width=3, tags=tags)
            c.create_arc(hinge - dw, y2 - dw, hinge + dw, y2 + dw, start=0 if left_hinge else 90, extent=90,
                         style="arc", outline="#7B8794", dash=(4, 3), tags=tags)

    def draw_label(self, room):
        c, z = self.plan, self.zoom
        x1, y1 = self.to_screen(room.x, room.y)
        x2, y2 = self.to_screen(room.x + room.w, room.y + room.h)
        size = max(8, min(15, int(z * 0.5)))
        cx = (x1 + x2) / 2
        cy = y2 - 2.4 * z if room.h >= 10 else (y1 + y2) / 2
        tags = ("room", "g%d" % room.uid)
        c.create_text(cx, cy - size * 0.9, text=room.name.upper(), fill="#2B2F36", font=F(size, True),
                      width=max(40, x2 - x1 - 20), tags=tags)
        c.create_text(cx, cy + size * 0.9, text="%d' X %d'" % (room.w, room.h), fill="#3A4048",
                      font=F(size - 1, True), tags=tags)

    def draw_item(self, room, item):
        c, z = self.plan, self.zoom
        spec = CATALOG[item.kind]
        cx, cy = self.to_screen(room.x + item.x, room.y + item.y)
        w, h = spec["w"] * z, spec["h"] * z
        tags = ("item", "g%d" % room.uid, "i%d" % item.uid)
        painter = Painter(c, cx, cy, item.rot, tags, unit=z / 20)
        painter.shadow(w, h, shade(FLOORS[room.floor]["base"], -.28), oval=spec["art"] in OVAL_ART)
        ART[spec["art"]](painter, w, h, item.color)

    def pill(self, x, y, text, bg, fg, tags, anchor="center"):
        """Text on a small rounded background."""
        c = self.plan
        tid = c.create_text(x, y, text=text, fill=fg, font=F(10, True), anchor=anchor, tags=tags)
        bb = c.bbox(tid)
        back = round_rect(c, bb[0] - 9, bb[1] - 4, bb[2] + 9, bb[3] + 4, 10, fill=bg, outline="", tags=tags)
        c.tag_lower(back, tid)

    def handle_pos(self, room):
        return self.to_screen(room.x + room.w, room.y + room.h)

    def draw_selection(self):
        c, z = self.plan, self.zoom
        room = self.sel_room
        if room is None:
            return
        T = self.wall_px()
        x1, y1 = self.to_screen(room.x, room.y)
        x2, y2 = self.to_screen(room.x + room.w, room.y + room.h)
        tags = ("overlay", "g%d" % room.uid)
        c.create_rectangle(x1 - T / 2 - 3, y1 - T / 2 - 3, x2 + T / 2 + 3, y2 + T / 2 + 3,
                           outline=room.accent, width=3, tags=tags)
        c.create_oval(x2 - 9, y2 - 9, x2 + 9, y2 + 9, fill=room.accent, outline="#FFFFFF", width=2, tags=tags)
        self.pill(x2 + 16, y2 + 14, "%d' x %d'" % (room.w, room.h), room.accent, "#FFFFFF", tags, anchor="nw")
        item = self.sel_item
        if item is not None and item in room.items:
            cx, cy = self.to_screen(room.x + item.x, room.y + item.y)
            hw, hh = item.w * z / 2 + 4, item.h * z / 2 + 4
            itags = ("overlay", "g%d" % room.uid, "i%d" % item.uid)
            c.create_rectangle(cx - hw, cy - hh, cx + hw, cy + hh, outline="#FF9F1C", width=2, dash=(5, 3), tags=itags)
            self.pill(cx, cy - hh - 14, item.name, "#FF9F1C", "#2A1B00", itags, anchor="center")

    # -----------------------------------------------------------------
    # mouse interaction on the plan
    # -----------------------------------------------------------------
    def find_item(self, mx, my):
        for room in reversed(self.rooms):
            if room.contains(mx, my):
                for item in reversed(room.ordered_items()):
                    if item.contains(mx - room.x, my - room.y):
                        return room, item
        return None

    def find_room(self, mx, my):
        for room in self.rooms:
            if room.contains(mx, my):
                return room
        for room in self.rooms:                        # a click on the wall itself
            if room.x - WALL_FT <= mx <= room.x + room.w + WALL_FT and room.y - WALL_FT <= my <= room.y + room.h + WALL_FT:
                return room
        return None

    def on_handle(self, sx, sy):
        if self.sel_room is None:
            return False
        hx, hy = self.handle_pos(self.sel_room)
        return (sx - hx) ** 2 + (sy - hy) ** 2 <= 14 ** 2

    def on_motion(self, event):
        mx, my = self.to_model(event.x, event.y)
        if self.on_handle(event.x, event.y):
            cursor = "sizing"
        elif self.find_item(mx, my):
            cursor = "hand2"
        elif self.find_room(mx, my):
            cursor = "fleur"
        else:
            cursor = "arrow"
        try:
            self.plan.config(cursor=cursor)
        except tk.TclError:
            self.plan.config(cursor="arrow")

    def on_press(self, event):
        self.plan.focus_set()
        self.drag = None
        mx, my = self.to_model(event.x, event.y)
        if self.on_handle(event.x, event.y):
            self.drag = {"mode": "resize", "room": self.sel_room, "moved": False}
            return
        hit = self.find_item(mx, my)
        if hit:
            room, item = hit
            self.sel_room, self.sel_item = room, item
            self.drag = {"mode": "item", "room": room, "item": item, "moved": False,
                         "dx": room.x + item.x - mx, "dy": room.y + item.y - my}
            self.refresh_all()
            return
        room = self.find_room(mx, my)
        if room:
            self.sel_room, self.sel_item = room, None
            self.drag = {"mode": "room", "room": room, "start": (mx, my), "orig": (room.x, room.y), "moved": False}
            self.refresh_all()
            return
        self.sel_item = None
        self.drag = {"mode": "pan", "x": event.x, "y": event.y, "moved": False}
        self.refresh_all()

    def on_drag(self, event):
        d = self.drag
        if not d:
            return
        z = self.zoom
        mx, my = self.to_model(event.x, event.y)
        if d["mode"] == "item":
            room, item = d["room"], d["item"]
            nx, ny = mx + d["dx"] - room.x, my + d["dy"] - room.y
            if self.snap:
                nx, ny = round(nx * 2) / 2, round(ny * 2) / 2
            old = (item.x, item.y)
            item.x, item.y = nx, ny
            item.clamp_into(room)
            if (item.x, item.y) != old:
                self.plan.move("i%d" % item.uid, (item.x - old[0]) * z, (item.y - old[1]) * z)
                d["moved"] = True
        elif d["mode"] == "room":
            room = d["room"]
            nx = d["orig"][0] + round(mx - d["start"][0])
            ny = d["orig"][1] + round(my - d["start"][1])
            if (nx, ny) != (room.x, room.y) and not self.collides(room, nx, ny, room.w, room.h):
                self.plan.move("g%d" % room.uid, (nx - room.x) * z, (ny - room.y) * z)
                room.x, room.y = nx, ny
                d["moved"] = True
        elif d["mode"] == "resize":
            room = d["room"]
            nw = max(MIN_SIZE, min(MAX_SIZE, int(round(mx - room.x))))
            nh = max(MIN_SIZE, min(MAX_SIZE, int(round(my - room.y))))
            if (nw, nh) != (room.w, room.h) and not self.collides(room, room.x, room.y, nw, nh):
                self.apply_size(room, nw, nh)
                d["moved"] = True
        elif d["mode"] == "pan":
            dx, dy = event.x - d["x"], event.y - d["y"]
            self.plan.move("all", dx, dy)
            self.ox += dx
            self.oy += dy
            d["x"], d["y"] = event.x, event.y

    def on_release(self, event):
        d, self.drag = self.drag, None
        if not d:
            return
        if d["mode"] in ("item", "room") and d["moved"]:
            self.mark_dirty()
        self.draw_plan()

    def on_right_click(self, event):
        hit = self.find_item(*self.to_model(event.x, event.y))
        if hit:
            self.rotate_item(hit[1])

    def on_double(self, event):
        self.drag = None
        hit = self.find_item(*self.to_model(event.x, event.y))
        if hit:
            self.edit_item(hit[1])
        elif self.sel_room is not None:
            self.name_entry.focus_set()
            self.name_entry.select_range(0, "end")

    def on_pan_start(self, event):
        self.drag = {"mode": "pan", "x": event.x, "y": event.y, "moved": False}

    def on_pan_move(self, event):
        if self.drag and self.drag["mode"] == "pan":
            self.on_drag(event)

    # -----------------------------------------------------------------
    # keyboard shortcuts
    # -----------------------------------------------------------------
    def typing(self):
        try:
            return isinstance(self.root.focus_get(), (tk.Entry, ttk.Entry, ttk.Combobox))
        except Exception:
            return False

    def bind_keys(self):
        r = self.root
        r.bind("<Delete>", self.key_delete)
        r.bind("<BackSpace>", self.key_delete)
        r.bind("<r>", self.key_rotate)
        r.bind("<R>", self.key_rotate)
        for key, (dx, dy) in {"Left": (-.5, 0), "Right": (.5, 0), "Up": (0, -.5), "Down": (0, .5)}.items():
            r.bind("<%s>" % key, lambda e, dx=dx, dy=dy: self.key_nudge(dx, dy))
        r.bind("<Control-s>", lambda e: self.save_project())
        r.bind("<Control-o>", lambda e: self.load_project())
        r.bind("<Control-d>", lambda e: None if self.typing() else self.duplicate_selected())
        r.bind("<Escape>", lambda e: None if self.typing() else self.deselect())
        r.bind("<plus>", lambda e: None if self.typing() else self.zoom_center(1.2))
        r.bind("<equal>", lambda e: None if self.typing() else self.zoom_center(1.2))
        r.bind("<minus>", lambda e: None if self.typing() else self.zoom_center(1 / 1.2))

    def key_delete(self, event):
        if not self.typing() and self.sel_item is not None:
            self.delete_item(self.sel_item)

    def key_rotate(self, event):
        if not self.typing() and self.sel_item is not None:
            self.rotate_item(self.sel_item)

    def key_nudge(self, dx, dy):
        item = self.sel_item
        room = self.room_of(item) if item else None
        if self.typing() or room is None:
            return
        item.x += dx
        item.y += dy
        item.clamp_into(room)
        self.mark_dirty()
        self.draw_plan()

    # -----------------------------------------------------------------
    # settings, save, load
    # -----------------------------------------------------------------
    def open_settings(self):
        result = settings_dialog(self)
        if result:
            budget, self.snap, self.show_grid = result
            if budget != self.budget:
                self.budget = budget
                self.mark_dirty()
            self.refresh_all()

    def save_project(self):
        if not self.require_db():
            return False
        self.apply_name()
        try:
            self.project_id = self.db.save_project(self.project_id, self.project_name, self.budget, self.rooms)
        except mysql.connector.Error as err:
            messagebox.showerror("Database error", "Could not save the project.\n\n%s" % err)
            return False
        self.dirty = False
        self.update_title()
        self.toast("Project saved to MySQL")
        return True

    def load_project(self):
        if not self.require_db() or not self.confirm_discard():
            return
        try:
            rows = self.db.list_projects()
            if not rows:
                self.toast("No saved projects yet - press Save first", "warn")
                return
            project_id = load_dialog(self, rows)
            if project_id is None:
                return
            data = self.db.load_project(project_id)
        except mysql.connector.Error as err:
            messagebox.showerror("Database error", "Could not load the project.\n\n%s" % err)
            return
        if data is None:
            self.toast("That project no longer exists", "err")
            return
        self.apply_project(data)
        self.toast("Loaded '%s'" % self.project_name)

    def apply_project(self, data):
        """Turns the dictionary returned by Database.load_project() into Room and Item objects."""
        version = data["version"]
        rooms = []
        for rd in data["rooms"]:
            rtype = rd["type"]
            if version < 2 and rd["name"] in ROOM_TYPES:      # old saves had no room_type column
                rtype = rd["name"]
            w = max(MIN_SIZE, min(MAX_SIZE, rd["w"]))
            h = max(MIN_SIZE, min(MAX_SIZE, rd["h"]))
            if version >= 2:
                x, y = rd["x"], rd["y"]
            else:                                              # old save: arrange rooms automatically
                x, y = self.find_free_spot(w, h, rooms)
            room = Room(rtype, rd["name"], x, y, w, h, rd["floor"], rd["wall"], rd["cost"])
            for fd in rd["items"]:
                kind = fd["type"] if fd["type"] in CATALOG else (fd["name"] if fd["name"] in CATALOG else "Center Table")
                if version >= 2:
                    item = Item(kind, fd["x"] / 10.0, fd["y"] / 10.0, (fd["rot"] // 90) % 4,
                                fd["name"], fd["price"], fd["color"])
                else:                                          # old save: positions were in pixels
                    fx, fy = self.free_spot(room, kind)
                    item = Item(kind, fx, fy, fd["rot"] % 4, fd["name"], fd["price"], fd["color"])
                item.clamp_into(room)
                room.items.append(item)
            rooms.append(room)
        if not rooms:
            rooms = [Room("Living Room")]
        self.rooms = rooms
        self.project_id = data["id"]
        self.project_name = data["name"]
        self.budget = data["budget"]
        self.sel_room, self.sel_item = rooms[0], None
        self.dirty = False
        self.refresh_all()
        self.fit_view()

    def on_close(self):
        self.apply_name()
        if self.dirty:
            answer = messagebox.askyesnocancel("Unsaved changes", "Save the project before closing?")
            if answer is None:
                return
            if answer and self.db is not None and not self.save_project():
                return
        if self.db is not None:
            self.db.close()
        self.root.destroy()


# =====================================================================
# START THE PROGRAM
# =====================================================================
def main():
    load_private_fonts()           # must happen before the window is created
    root = tk.Tk()
    DreamHouseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
