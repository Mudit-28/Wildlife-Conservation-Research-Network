"""
Wildlife Sanctuary Management System  —  MySQL Edition
=======================================================
Requirements:
    pip install mysql-connector-python

Setup:
    1. Create the database in MySQL:
       CREATE DATABASE sanctuary CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

    2. Fill in your credentials in the DB_CONFIG block below.

    3. Run:
       python wildlife_sanctuary_mysql.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from datetime import datetime, date

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:
    import tkinter as _tk
    _tk.Tk().withdraw()
    import tkinter.messagebox as _mb
    _mb.showerror(
        "Missing Driver",
        "mysql-connector-python is not installed.\n\n"
        "Run:  pip install mysql-connector-python\n\nThen restart the app."
    )
    raise SystemExit(1)

# ─────────────────────────────────────────────
#  ★  EDIT THESE CREDENTIALS  ★
# ─────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",
    "password": "MySQL@12345",
    "database": "sanctuary",
}
# ─────────────────────────────────────────────

# ── Colour palette ──────────────────────────
BG_DARK   = "#1A2332"
BG_MID    = "#243447"
BG_CARD   = "#2D4059"
ACCENT    = "#4ECDC4"
ACCENT2   = "#FF6B6B"
ACCENT3   = "#FFE66D"
TEXT_MAIN = "#E8F4F8"
TEXT_SUB  = "#8BA7B8"
BTN_GREEN = "#27AE60"
BTN_RED   = "#E74C3C"
BTN_BLUE  = "#2980B9"
BTN_ORG   = "#E67E22"


# ════════════════════════════════════════════
#  DATABASE LAYER  (MySQL)
# ════════════════════════════════════════════
class Database:
    def __init__(self):
        try:
            self.conn = mysql.connector.connect(**DB_CONFIG)
        except MySQLError as e:
            messagebox.showerror(
                "Database Connection Failed",
                f"Could not connect to MySQL.\n\n"
                f"Host : {DB_CONFIG['host']}:{DB_CONFIG['port']}\n"
                f"DB   : {DB_CONFIG['database']}\n\n"
                f"Error: {e}\n\n"
                "Please check your credentials in DB_CONFIG and try again."
            )
            raise SystemExit(1)
        self._create_tables()

    # ── Placeholder conversion ───────────────
    @staticmethod
    def _q(sql: str) -> str:
        """Convert SQLite ? placeholders → MySQL %s placeholders."""
        return sql.replace("?", "%s")

    # ── Schema  (MySQL syntax) ───────────────
    def _create_tables(self):
        sql_statements = [
            """CREATE TABLE IF NOT EXISTS zones (
                id          INT PRIMARY KEY AUTO_INCREMENT,
                name        VARCHAR(120) NOT NULL UNIQUE,
                area_sqkm   DOUBLE,
                description TEXT,
                capacity    INT,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB""",

            """CREATE TABLE IF NOT EXISTS staff (
                id          INT PRIMARY KEY AUTO_INCREMENT,
                name        VARCHAR(150) NOT NULL,
                role        ENUM('Caretaker','Veterinarian','Ranger','Admin') NOT NULL,
                email       VARCHAR(200),
                phone       VARCHAR(50),
                speciality  VARCHAR(200),
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB""",

            """CREATE TABLE IF NOT EXISTS animals (
                id          INT PRIMARY KEY AUTO_INCREMENT,
                name        VARCHAR(120) NOT NULL,
                species     VARCHAR(150) NOT NULL,
                common_name VARCHAR(150),
                age         DOUBLE,
                gender      ENUM('Male','Female','Unknown') DEFAULT 'Unknown',
                weight_kg   DOUBLE,
                zone_id     INT,
                staff_id    INT,
                health      ENUM('Healthy','Sick','Critical','Recovering','Deceased') DEFAULT 'Healthy',
                notes       TEXT,
                arrived_on  DATE,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (zone_id)  REFERENCES zones(id)  ON DELETE SET NULL,
                FOREIGN KEY (staff_id) REFERENCES staff(id)  ON DELETE SET NULL
            ) ENGINE=InnoDB""",

            """CREATE TABLE IF NOT EXISTS health_records (
                id          INT PRIMARY KEY AUTO_INCREMENT,
                animal_id   INT NOT NULL,
                staff_id    INT,
                date        DATE NOT NULL,
                diagnosis   VARCHAR(300),
                symptoms    TEXT,
                status      VARCHAR(50),
                notes       TEXT,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (animal_id) REFERENCES animals(id) ON DELETE CASCADE,
                FOREIGN KEY (staff_id)  REFERENCES staff(id)   ON DELETE SET NULL
            ) ENGINE=InnoDB""",

            """CREATE TABLE IF NOT EXISTS medicines (
                id           INT PRIMARY KEY AUTO_INCREMENT,
                name         VARCHAR(150) NOT NULL UNIQUE,
                type         VARCHAR(100),
                unit         VARCHAR(30)  DEFAULT 'mg',
                stock        DOUBLE       DEFAULT 0,
                min_stock    DOUBLE       DEFAULT 10,
                expiry_date  DATE,
                supplier     VARCHAR(200),
                created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB""",

            """CREATE TABLE IF NOT EXISTS treatments (
                id          INT PRIMARY KEY AUTO_INCREMENT,
                animal_id   INT NOT NULL,
                medicine_id INT,
                staff_id    INT,
                date        DATE NOT NULL,
                dose        DOUBLE,
                duration    VARCHAR(100),
                purpose     VARCHAR(300),
                notes       TEXT,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (animal_id)   REFERENCES animals(id)   ON DELETE CASCADE,
                FOREIGN KEY (medicine_id) REFERENCES medicines(id) ON DELETE SET NULL,
                FOREIGN KEY (staff_id)    REFERENCES staff(id)     ON DELETE SET NULL
            ) ENGINE=InnoDB""",

            """CREATE TABLE IF NOT EXISTS feeding_schedules (
                id          INT PRIMARY KEY AUTO_INCREMENT,
                animal_id   INT NOT NULL,
                diet_type   VARCHAR(100),
                food_items  TEXT,
                quantity_kg DOUBLE,
                frequency   VARCHAR(100),
                time_slots  VARCHAR(200),
                notes       TEXT,
                created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (animal_id) REFERENCES animals(id) ON DELETE CASCADE
            ) ENGINE=InnoDB""",

            # ── Trigger log table ────────────────────
            """CREATE TABLE IF NOT EXISTS trigger_logs (
                id           INT PRIMARY KEY AUTO_INCREMENT,
                trigger_name VARCHAR(100) NOT NULL,
                event        VARCHAR(100) NOT NULL,
                animal_id    INT,
                details      TEXT,
                fired_at     DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB""",

            # ── Users / login table ───────────────────
            """CREATE TABLE IF NOT EXISTS users (
                id         INT PRIMARY KEY AUTO_INCREMENT,
                username   VARCHAR(80)  NOT NULL UNIQUE,
                password   VARCHAR(200) NOT NULL,
                role       ENUM('Admin','Healthcare','Caretaker','General') NOT NULL,
                full_name  VARCHAR(150),
                active     TINYINT DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB""",
        ]
        cur = self.conn.cursor()
        for sql in sql_statements:
            cur.execute(sql)
        self.conn.commit()
        cur.close()
        self._create_triggers()
        self._seed_users()

    def _seed_users(self):
        """Insert default accounts on first run."""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] == 0:
            cur.executemany(
                "INSERT INTO users (username,password,role,full_name) VALUES (%s,%s,%s,%s)",
                [
                    ("admin",      "admin123",   "Admin",       "System Administrator"),
                    ("drsmith",    "health123",  "Healthcare",  "Dr. Sarah Smith"),
                    ("john_care",  "care123",    "Caretaker",   "John Caretaker"),
                    ("guest",      "guest123",   "General",     "Wildlife Explorer"),
                ]
            )
            self.conn.commit()
        cur.close()

    def authenticate(self, username, password):
        """
        Return user dict if credentials match, else None.
        Tries multiple query forms in case the DB schema is partially
        migrated (e.g. active column may not exist yet).
        """
        # Try full query with active column first
        try:
            row = self.fetchone(
                "SELECT * FROM users WHERE username=? AND password=? AND active=1",
                (username, password)
            )
            if row:
                return row
        except Exception:
            pass

        # Fallback: without active column (handles partial schema)
        try:
            row = self.fetchone(
                "SELECT * FROM users WHERE username=? AND password=?",
                (username, password)
            )
            return row
        except Exception:
            return None

    def get_all_users(self):
        return self.fetchall("SELECT * FROM users ORDER BY role, username")

    def add_user(self, username, password, role, full_name):
        try:
            self.execute(
                "INSERT INTO users (username,password,role,full_name) VALUES (?,?,?,?)",
                (username, password, role, full_name)
            )
            return True, "User created successfully."
        except Exception as e:
            return False, str(e)

    def update_user(self, uid, username, password, role, full_name, active):
        try:
            self.execute(
                "UPDATE users SET username=?,password=?,role=?,full_name=?,active=? WHERE id=?",
                (username, password, role, full_name, active, uid)
            )
            return True, "User updated."
        except Exception as e:
            return False, str(e)

    def delete_user(self, uid):
        self.delete("DELETE FROM users WHERE id=?", (uid,))

    # ── Create Triggers ──────────────────────
    def _create_triggers(self):
        """
        Creates 5 database triggers:
          TRG1 trg_health_status_alert   AFTER UPDATE animals    → auto health_record + log
          TRG2 trg_medicine_low_stock    AFTER UPDATE medicines  → low stock alert log
          TRG3 trg_new_animal_zone_log   AFTER INSERT animals    → zone capacity check log
          TRG4 trg_treatment_audit       AFTER INSERT treatments → treatment audit log
          TRG5 trg_feeding_overdue_flag  AFTER UPDATE animals    → flag deceased feeding
        """
        errors = []
        TRIGGER_NAMES = [
            "trg_health_status_alert",
            "trg_medicine_low_stock",
            "trg_new_animal_zone_log",
            "trg_treatment_audit",
            "trg_feeding_overdue_flag",
        ]
        try:
            self.conn.autocommit = True
            cur = self.conn.cursor()

            for name in TRIGGER_NAMES:
                try:
                    cur.execute(f"DROP TRIGGER IF EXISTS {name}")
                except Exception as e:
                    errors.append(f"DROP {name}: {e}")

            # ── TRIGGER 1 ─────────────────────────────────────────────────
            # AFTER UPDATE ON animals
            # When health status changes → auto-insert health_records audit row
            # + write to trigger_logs
            try:
                cur.execute(
                    "CREATE TRIGGER trg_health_status_alert "
                    "AFTER UPDATE ON animals "
                    "FOR EACH ROW "
                    "BEGIN "
                    "  IF OLD.health <> NEW.health THEN "
                    "    INSERT INTO health_records "
                    "      (animal_id,staff_id,date,diagnosis,symptoms,status,notes) "
                    "    VALUES ("
                    "      NEW.id,NULL,CURDATE(),"
                    "      CONCAT('Auto-logged: ',OLD.health,' to ',NEW.health),"
                    "      'System detected health change',"
                    "      NEW.health,"
                    "      'Created by trg_health_status_alert'"
                    "    );"
                    "    INSERT INTO trigger_logs (trigger_name,event,animal_id,details) "
                    "    VALUES ("
                    "      'trg_health_status_alert',"
                    "      CONCAT('Health: ',OLD.health,' → ',NEW.health),"
                    "      NEW.id,"
                    "      CONCAT('Animal=',NEW.name,"
                    "             ' | Old=',OLD.health,"
                    "             ' | New=',NEW.health,"
                    "             ' | ',NOW())"
                    "    );"
                    "  END IF;"
                    "END"
                )
            except Exception as e:
                errors.append(f"TRG1 trg_health_status_alert: {e}")

            # ── TRIGGER 2 ─────────────────────────────────────────────────
            # AFTER UPDATE ON medicines
            # When stock drops to or below min_stock → LOW STOCK ALERT in trigger_logs
            try:
                cur.execute(
                    "CREATE TRIGGER trg_medicine_low_stock "
                    "AFTER UPDATE ON medicines "
                    "FOR EACH ROW "
                    "BEGIN "
                    "  IF NEW.stock <= NEW.min_stock AND OLD.stock > OLD.min_stock THEN "
                    "    INSERT INTO trigger_logs (trigger_name,event,animal_id,details) "
                    "    VALUES ("
                    "      'trg_medicine_low_stock',"
                    "      CONCAT('LOW STOCK: ',NEW.name),"
                    "      NULL,"
                    "      CONCAT('Medicine=',NEW.name,"
                    "             ' | Stock=',NEW.stock,"
                    "             ' | Min=',NEW.min_stock,"
                    "             ' | WasStock=',OLD.stock,"
                    "             ' | REORDER NOW | ',NOW())"
                    "    );"
                    "  END IF;"
                    "END"
                )
            except Exception as e:
                errors.append(f"TRG2 trg_medicine_low_stock: {e}")

            # ── TRIGGER 3 ─────────────────────────────────────────────────
            # AFTER INSERT ON animals
            # When a new animal is added → check zone capacity and log
            try:
                cur.execute(
                    "CREATE TRIGGER trg_new_animal_zone_log "
                    "AFTER INSERT ON animals "
                    "FOR EACH ROW "
                    "BEGIN "
                    "  INSERT INTO trigger_logs (trigger_name,event,animal_id,details) "
                    "  VALUES ("
                    "    'trg_new_animal_zone_log',"
                    "    CONCAT('New animal added: ',NEW.name),"
                    "    NEW.id,"
                    "    CONCAT('Animal=',NEW.name,"
                    "           ' | Species=',NEW.species,"
                    "           ' | ZoneID=',IFNULL(NEW.zone_id,'None'),"
                    "           ' | Health=',NEW.health,"
                    "           ' | ',NOW())"
                    "  );"
                    "END"
                )
            except Exception as e:
                errors.append(f"TRG3 trg_new_animal_zone_log: {e}")

            # ── TRIGGER 4 ─────────────────────────────────────────────────
            # AFTER INSERT ON treatments
            # When a treatment is logged → write a full audit entry to trigger_logs
            try:
                cur.execute(
                    "CREATE TRIGGER trg_treatment_audit "
                    "AFTER INSERT ON treatments "
                    "FOR EACH ROW "
                    "BEGIN "
                    "  INSERT INTO trigger_logs (trigger_name,event,animal_id,details) "
                    "  VALUES ("
                    "    'trg_treatment_audit',"
                    "    CONCAT('Treatment logged for Animal ID=',NEW.animal_id),"
                    "    NEW.animal_id,"
                    "    CONCAT('TreatmentID=',NEW.id,"
                    "           ' | MedicineID=',IFNULL(NEW.medicine_id,'None'),"
                    "           ' | Dose=',IFNULL(NEW.dose,'N/A'),"
                    "           ' | Purpose=',IFNULL(NEW.purpose,'N/A'),"
                    "           ' | Date=',NEW.date,"
                    "           ' | ',NOW())"
                    "  );"
                    "END"
                )
            except Exception as e:
                errors.append(f"TRG4 trg_treatment_audit: {e}")

            # ── TRIGGER 5 ─────────────────────────────────────────────────
            # AFTER UPDATE ON animals
            # When animal is marked Deceased → flag feeding schedules as inactive
            # by logging a warning in trigger_logs
            try:
                cur.execute(
                    "CREATE TRIGGER trg_feeding_overdue_flag "
                    "AFTER UPDATE ON animals "
                    "FOR EACH ROW "
                    "BEGIN "
                    "  IF NEW.health = 'Deceased' AND OLD.health <> 'Deceased' THEN "
                    "    INSERT INTO trigger_logs (trigger_name,event,animal_id,details) "
                    "    VALUES ("
                    "      'trg_feeding_overdue_flag',"
                    "      CONCAT('DECEASED FLAG: ',NEW.name),"
                    "      NEW.id,"
                    "      CONCAT('Animal ',NEW.name,' marked Deceased.',"
                    "             ' | Feeding schedules should be reviewed.',"
                    "             ' | Zone=',IFNULL(NEW.zone_id,'None'),"
                    "             ' | ',NOW())"
                    "    );"
                    "  END IF;"
                    "END"
                )
            except Exception as e:
                errors.append(f"TRG5 trg_feeding_overdue_flag: {e}")

            cur.close()
            self.conn.autocommit = False

        except Exception as e:
            errors.append(f"Connection error: {e}")

        if errors:
            return False, "\n".join(errors)
        return True, "All 5 triggers created successfully."

    def reset_conn(self):
        """Safely reset the connection — rollback any open transaction,
        then set autocommit=False so we start clean."""
        try:
            self.conn.rollback()
        except Exception:
            pass
        try:
            self.conn.autocommit = False
        except Exception:
            pass
        # If connection is dead, reconnect
        try:
            self.conn.ping(reconnect=True, attempts=3, delay=1)
        except Exception:
            self.conn = mysql.connector.connect(**DB_CONFIG)
            self.conn.autocommit = False

    def verify_triggers(self):
        """Returns list of trigger names actually in the DB."""
        try:
            cur = self._cursor(dictionary=True)
            cur.execute(
                "SELECT TRIGGER_NAME FROM information_schema.TRIGGERS "
                "WHERE TRIGGER_SCHEMA = %s",
                (DB_CONFIG["database"],)
            )
            rows = cur.fetchall()
            cur.close()
            return [r["TRIGGER_NAME"] for r in rows]
        except Exception:
            return []

    def get_latest_log_id(self):
        """Returns the highest trigger_log id currently in the table."""
        try:
            r = self.fetchone("SELECT MAX(id) AS mid FROM trigger_logs")
            return r["mid"] if r and r["mid"] else 0
        except Exception:
            return 0

    def get_new_logs_since(self, last_id):
        """Returns trigger_log rows with id > last_id."""
        try:
            return self.fetchall(
                "SELECT * FROM trigger_logs WHERE id > ? ORDER BY id ASC",
                (last_id,)
            )
        except Exception:
            return []

    # ── Reconnect on timeout ─────────────────
    def _cursor(self, dictionary=True):
        try:
            self.conn.ping(reconnect=True, attempts=3, delay=1)
        except MySQLError:
            self.conn = mysql.connector.connect(**DB_CONFIG)
        return self.conn.cursor(dictionary=dictionary)

    # ── Generic helpers ──────────────────────
    def fetchall(self, sql, params=()):
        cur = self._cursor(dictionary=True)
        cur.execute(self._q(sql), params)
        rows = cur.fetchall()
        cur.close()
        return rows

    def fetchone(self, sql, params=()):
        cur = self._cursor(dictionary=True)
        cur.execute(self._q(sql), params)
        row = cur.fetchone()
        cur.close()
        return row

    def execute(self, sql, params=()):
        cur = self._cursor(dictionary=False)
        cur.execute(self._q(sql), params)
        self.conn.commit()
        last_id = cur.lastrowid
        cur.close()
        return last_id

    def delete(self, sql, params=()):
        cur = self._cursor(dictionary=False)
        cur.execute(self._q(sql), params)
        self.conn.commit()
        cur.close()

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass


# ════════════════════════════════════════════
#  REUSABLE UI WIDGETS
# ════════════════════════════════════════════
class StyledButton(tk.Button):
    def __init__(self, parent, text, command=None, color=BTN_GREEN, **kwargs):
        super().__init__(
            parent, text=text, command=command,
            bg=color, fg="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat", bd=0, padx=12, pady=6,
            activebackground=color, activeforeground="white",
            cursor="hand2", **kwargs
        )
        self.bind("<Enter>", lambda e: self.config(bg=self._darken(color)))
        self.bind("<Leave>", lambda e: self.config(bg=color))

    @staticmethod
    def _darken(hex_color):
        r = max(0, int(hex_color[1:3], 16) - 30)
        g = max(0, int(hex_color[3:5], 16) - 30)
        b = max(0, int(hex_color[5:7], 16) - 30)
        return f"#{r:02x}{g:02x}{b:02x}"


def make_label(parent, text, size=10, color=TEXT_MAIN, bold=False, **kwargs):
    weight = "bold" if bold else "normal"
    kwargs.setdefault("bg", BG_MID)
    return tk.Label(parent, text=text, fg=color,
                    font=("Segoe UI", size, weight), **kwargs)


def make_entry(parent, width=24):
    return tk.Entry(parent, bg=BG_CARD, fg=TEXT_MAIN,
                    insertbackground=TEXT_MAIN, relief="flat",
                    font=("Segoe UI", 10), width=width, bd=4)


def make_combo(parent, values, width=22):
    cb = ttk.Combobox(parent, values=values, width=width,
                      state="readonly", font=("Segoe UI", 10))
    cb.configure(style="Dark.TCombobox")
    return cb


def make_tree(parent, columns, headings, col_widths=None):
    frame = tk.Frame(parent, bg=BG_MID)
    frame.pack(fill="both", expand=True, padx=4, pady=4)

    scroll_y = ttk.Scrollbar(frame, orient="vertical")
    scroll_x = ttk.Scrollbar(frame, orient="horizontal")
    scroll_y.pack(side="right",  fill="y")
    scroll_x.pack(side="bottom", fill="x")

    tree = ttk.Treeview(frame, columns=columns, show="headings",
                        yscrollcommand=scroll_y.set,
                        xscrollcommand=scroll_x.set,
                        style="Dark.Treeview")
    scroll_y.config(command=tree.yview)
    scroll_x.config(command=tree.xview)

    for i, (col, head) in enumerate(zip(columns, headings)):
        tree.heading(col, text=head)
        w = col_widths[i] if col_widths else 120
        tree.column(col, width=w, minwidth=60, anchor="center")

    tree.pack(fill="both", expand=True)
    return tree


# ════════════════════════════════════════════
#  DIALOG BASE
# ════════════════════════════════════════════
class BaseDialog(tk.Toplevel):
    def __init__(self, parent, title, width=460, height=520):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=BG_MID)
        self.resizable(False, False)
        x = parent.winfo_rootx() + 100
        y = parent.winfo_rooty() + 60
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.grab_set()
        self.result = None

        self.body_frame = tk.Frame(self, bg=BG_MID, padx=20, pady=10)
        self.body_frame.pack(fill="both", expand=True)

    def _row(self, label, widget, row):
        make_label(self.body_frame, label, size=9, color=TEXT_SUB).grid(
            row=row, column=0, sticky="w", pady=4, padx=4)
        widget.grid(row=row, column=1, sticky="ew", pady=4, padx=4)

    def _btn_row(self, ok_text="Save", ok_cmd=None, cancel_cmd=None):
        f = tk.Frame(self, bg=BG_MID, pady=10)
        f.pack(fill="x", padx=20)
        StyledButton(f, ok_text, ok_cmd or self.destroy, color=BTN_GREEN).pack(side="left", padx=4)
        StyledButton(f, "Cancel", cancel_cmd or self.destroy, color=BTN_RED).pack(side="left", padx=4)


# ════════════════════════════════════════════
#  PANELS
# ════════════════════════════════════════════

# ── Animals Panel ───────────────────────────
class AnimalsPanel(tk.Frame):
    COLS   = ("id","name","species","age","gender","weight","zone","health","caretaker")
    HEADS  = ("ID","Name","Species","Age","Gender","Weight(kg)","Zone","Health","Caretaker")
    WIDTHS = (40,110,120,50,70,80,100,90,110)

    def __init__(self, parent, db, readonly=False):
        super().__init__(parent, bg=BG_MID)
        self.db = db
        self.readonly = readonly
        self._build()

    def _build(self):
        tb = tk.Frame(self, bg=BG_DARK, pady=6, padx=10)
        tb.pack(fill="x")
        if self.readonly:
            ro_bar = tk.Frame(self, bg="#2C3E50", pady=3)
            ro_bar.pack(fill="x")
            tk.Label(ro_bar, text="  👁  VIEW ONLY — You do not have permission to add, edit or delete records.",
                     bg="#2C3E50", fg=ACCENT3,
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(side="left", padx=6)
        make_label(tb, "🐾  Animals", size=13, bold=True, bg=BG_DARK).pack(side="left")
        StyledButton(tb, "🔄 Refresh", self.refresh, BTN_ORG).pack(side="right", padx=4)
        if not self.readonly:
            StyledButton(tb, "+ Add Animal", self._add,    BTN_GREEN).pack(side="right", padx=4)
            StyledButton(tb, "✏ Edit",       self._edit,   BTN_BLUE ).pack(side="right", padx=4)
            StyledButton(tb, "🗑 Delete",    self._delete, BTN_RED  ).pack(side="right", padx=4)

        sf = tk.Frame(self, bg=BG_MID, pady=4, padx=10)
        sf.pack(fill="x")
        make_label(sf, "Search:", size=9, color=TEXT_SUB).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self.refresh())
        e = make_entry(sf, 30)
        e.config(textvariable=self.search_var)
        e.pack(side="left", padx=6)

        make_label(sf, "Health:", size=9, color=TEXT_SUB).pack(side="left", padx=(10,0))
        self.health_filter = tk.StringVar(value="All")
        cb = make_combo(sf, ["All","Healthy","Sick","Critical","Recovering","Deceased"], 12)
        cb.config(textvariable=self.health_filter)
        cb.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        cb.pack(side="left", padx=4)

        self.tree = make_tree(self, self.COLS, self.HEADS, self.WIDTHS)
        self._tag_colors()
        self.refresh()

    def _tag_colors(self):
        self.tree.tag_configure("Healthy",    foreground="#2ECC71")
        self.tree.tag_configure("Sick",       foreground="#E67E22")
        self.tree.tag_configure("Critical",   foreground="#E74C3C")
        self.tree.tag_configure("Recovering", foreground="#3498DB")
        self.tree.tag_configure("Deceased",   foreground=TEXT_SUB)

    def refresh(self, *_):
        for row in self.tree.get_children():
            self.tree.delete(row)
        q  = self.search_var.get().strip()
        hf = self.health_filter.get()
        sql = """
            SELECT a.id, a.name, a.species, a.age, a.gender, a.weight_kg,
                   z.name AS zone, a.health, s.name AS caretaker
            FROM   animals a
            LEFT JOIN zones z ON z.id = a.zone_id
            LEFT JOIN staff s ON s.id = a.staff_id
            WHERE  (a.name LIKE ? OR a.species LIKE ?)
        """
        params = [f"%{q}%", f"%{q}%"]
        if hf != "All":
            sql += " AND a.health = ?"
            params.append(hf)
        sql += " ORDER BY a.name"
        for r in self.db.fetchall(sql, params):
            vals = tuple(r.get(c, "") or "" for c in self.COLS)
            tag  = r.get("health") or "Healthy"
            self.tree.insert("", "end", values=vals, tags=(tag,))

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select an animal first.")
            return None
        return self.tree.item(sel[0])["values"][0]

    def _add(self):
        dlg = AnimalDialog(self, self.db)
        self.wait_window(dlg); self.refresh()

    def _edit(self):
        aid = self._selected_id()
        if aid is None: return
        dlg = AnimalDialog(self, self.db, animal_id=aid)
        self.wait_window(dlg); self.refresh()

    def _delete(self):
        aid = self._selected_id()
        if aid is None: return
        if messagebox.askyesno("Confirm", "Delete this animal and all related records?"):
            self.db.delete("DELETE FROM animals WHERE id=?", (aid,))
            self.refresh()


class AnimalDialog(BaseDialog):
    def __init__(self, parent, db, animal_id=None):
        super().__init__(parent, "Add Animal" if not animal_id else "Edit Animal")
        self.db = db
        self.animal_id = animal_id
        self._build()
        if animal_id:
            self._load()

    def _build(self):
        f = self.body_frame
        f.columnconfigure(1, weight=1)

        self.name_e     = make_entry(f)
        self.species_e  = make_entry(f)
        self.common_e   = make_entry(f)
        self.age_e      = make_entry(f)
        self.gender_cb  = make_combo(f, ["Male","Female","Unknown"])
        self.weight_e   = make_entry(f)
        self.health_cb  = make_combo(f, ["Healthy","Sick","Critical","Recovering","Deceased"])
        self.arrived_e  = make_entry(f)
        self.arrived_e.insert(0, str(date.today()))

        zones  = [f"{z['id']}: {z['name']}" for z in self.db.fetchall("SELECT id,name FROM zones ORDER BY name")]
        staffs = [f"{s['id']}: {s['name']}" for s in self.db.fetchall("SELECT id,name FROM staff ORDER BY name")]
        self.zone_cb  = make_combo(f, zones)
        self.staff_cb = make_combo(f, staffs)
        self.notes_e  = make_entry(f, 28)

        for i, (lbl, w) in enumerate([
            ("Name *",       self.name_e),
            ("Species *",    self.species_e),
            ("Common Name",  self.common_e),
            ("Age (years)",  self.age_e),
            ("Gender",       self.gender_cb),
            ("Weight (kg)",  self.weight_e),
            ("Health",       self.health_cb),
            ("Zone",         self.zone_cb),
            ("Caretaker",    self.staff_cb),
            ("Arrived On",   self.arrived_e),
            ("Notes",        self.notes_e),
        ]):
            self._row(lbl, w, i)

        self._btn_row("Save", self._save)

    def _load(self):
        r = self.db.fetchone("SELECT * FROM animals WHERE id=?", (self.animal_id,))
        if not r: return
        self.name_e.insert(0,    r.get("name") or "")
        self.species_e.insert(0, r.get("species") or "")
        self.common_e.insert(0,  r.get("common_name") or "")
        self.age_e.insert(0,     str(r.get("age") or ""))
        self.weight_e.insert(0,  str(r.get("weight_kg") or ""))
        self.notes_e.insert(0,   r.get("notes") or "")
        self.arrived_e.delete(0, "end")
        self.arrived_e.insert(0, str(r.get("arrived_on") or ""))
        if r.get("gender"):   self.gender_cb.set(r["gender"])
        if r.get("health"):   self.health_cb.set(r["health"])
        if r.get("zone_id"):
            for z in self.db.fetchall("SELECT id,name FROM zones"):
                if z["id"] == r["zone_id"]:
                    self.zone_cb.set(f"{z['id']}: {z['name']}"); break
        if r.get("staff_id"):
            for s in self.db.fetchall("SELECT id,name FROM staff"):
                if s["id"] == r["staff_id"]:
                    self.staff_cb.set(f"{s['id']}: {s['name']}"); break

    def _save(self):
        name = self.name_e.get().strip()
        spc  = self.species_e.get().strip()
        if not name or not spc:
            messagebox.showwarning("Required", "Name and Species are required."); return
        try:
            age    = float(self.age_e.get()) if self.age_e.get() else None
            weight = float(self.weight_e.get()) if self.weight_e.get() else None
        except ValueError:
            messagebox.showerror("Input Error", "Age and Weight must be numbers."); return

        zone_id  = int(self.zone_cb.get().split(":")[0]) if self.zone_cb.get() else None
        staff_id = int(self.staff_cb.get().split(":")[0]) if self.staff_cb.get() else None
        health   = self.health_cb.get() or "Healthy"
        gender   = self.gender_cb.get() or "Unknown"
        arrived  = self.arrived_e.get() or None

        if self.animal_id:
            self.db.execute("""UPDATE animals SET name=?,species=?,common_name=?,age=?,gender=?,
                               weight_kg=?,zone_id=?,staff_id=?,health=?,arrived_on=?,notes=?
                               WHERE id=?""",
                (name, spc, self.common_e.get(), age, gender, weight,
                 zone_id, staff_id, health, arrived, self.notes_e.get(), self.animal_id))
        else:
            self.db.execute("""INSERT INTO animals
                (name,species,common_name,age,gender,weight_kg,zone_id,staff_id,health,arrived_on,notes)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (name, spc, self.common_e.get(), age, gender, weight,
                 zone_id, staff_id, health, arrived, self.notes_e.get()))
        self.destroy()


# ── Health Records Panel ─────────────────────
class HealthPanel(tk.Frame):
    COLS   = ("id","animal","date","diagnosis","symptoms","status","vet")
    HEADS  = ("ID","Animal","Date","Diagnosis","Symptoms","Status","Veterinarian")
    WIDTHS = (40,120,90,150,140,90,120)

    def __init__(self, parent, db, readonly=False):
        super().__init__(parent, bg=BG_MID)
        self.db = db; self.readonly = readonly; self._build()

    def _build(self):
        tb = tk.Frame(self, bg=BG_DARK, pady=6, padx=10)
        tb.pack(fill="x")
        if self.readonly:
            ro_bar = tk.Frame(self, bg="#2C3E50", pady=3)
            ro_bar.pack(fill="x")
            tk.Label(ro_bar, text="  👁  VIEW ONLY — You do not have permission to add, edit or delete records.",
                     bg="#2C3E50", fg=ACCENT3,
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(side="left", padx=6)
        make_label(tb, "🏥  Health Records", size=13, bold=True, bg=BG_DARK).pack(side="left")
        StyledButton(tb, "🔄 Refresh", self.refresh, BTN_ORG).pack(side="right", padx=4)
        if not self.readonly:
            StyledButton(tb, "+ Log Record", self._add,    BTN_GREEN).pack(side="right", padx=4)
            StyledButton(tb, "🗑 Delete",    self._delete, BTN_RED  ).pack(side="right", padx=4)

        sf = tk.Frame(self, bg=BG_MID, pady=4, padx=10)
        sf.pack(fill="x")
        make_label(sf, "Filter Animal:", size=9, color=TEXT_SUB).pack(side="left")
        self.filter_var = tk.StringVar()
        self.filter_var.trace("w", lambda *a: self.refresh())
        e = make_entry(sf, 26)
        e.config(textvariable=self.filter_var)
        e.pack(side="left", padx=6)

        self.tree = make_tree(self, self.COLS, self.HEADS, self.WIDTHS)
        self.refresh()

    def refresh(self, *_):
        for r in self.tree.get_children(): self.tree.delete(r)
        q = self.filter_var.get().strip()
        for r in self.db.fetchall("""
            SELECT hr.id, a.name AS animal, hr.date, hr.diagnosis,
                   hr.symptoms, hr.status, s.name AS vet
            FROM   health_records hr
            JOIN   animals a ON a.id = hr.animal_id
            LEFT JOIN staff s ON s.id = hr.staff_id
            WHERE  a.name LIKE ?
            ORDER  BY hr.date DESC
        """, (f"%{q}%",)):
            self.tree.insert("", "end", values=tuple(r.get(c, "") or "" for c in self.COLS))

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a record first."); return None
        return self.tree.item(sel[0])["values"][0]

    def _add(self):
        dlg = HealthDialog(self, self.db)
        self.wait_window(dlg); self.refresh()

    def _delete(self):
        rid = self._selected_id()
        if rid and messagebox.askyesno("Confirm", "Delete this record?"):
            self.db.delete("DELETE FROM health_records WHERE id=?", (rid,))
            self.refresh()


class HealthDialog(BaseDialog):
    def __init__(self, parent, db):
        super().__init__(parent, "Log Health Record", height=460)
        self.db = db; self._build()

    def _build(self):
        f = self.body_frame; f.columnconfigure(1, weight=1)

        animals = [f"{a['id']}: {a['name']}" for a in self.db.fetchall("SELECT id,name FROM animals ORDER BY name")]
        vets    = [f"{s['id']}: {s['name']}" for s in
                   self.db.fetchall("SELECT id,name FROM staff WHERE role='Veterinarian' ORDER BY name")]

        self.animal_cb = make_combo(f, animals)
        self.vet_cb    = make_combo(f, vets)
        self.date_e    = make_entry(f); self.date_e.insert(0, str(date.today()))
        self.diag_e    = make_entry(f)
        self.symp_e    = make_entry(f)
        self.status_cb = make_combo(f, ["Healthy","Sick","Critical","Recovering","Deceased"])
        self.notes_e   = make_entry(f)

        for i, (lbl, w) in enumerate([
            ("Animal *",    self.animal_cb),
            ("Veterinarian",self.vet_cb),
            ("Date *",      self.date_e),
            ("Diagnosis",   self.diag_e),
            ("Symptoms",    self.symp_e),
            ("Status",      self.status_cb),
            ("Notes",       self.notes_e),
        ]):
            self._row(lbl, w, i)

        self._btn_row("Save", self._save)

    def _save(self):
        if not self.animal_cb.get():
            messagebox.showwarning("Required", "Select an animal."); return
        animal_id = int(self.animal_cb.get().split(":")[0])
        staff_id  = int(self.vet_cb.get().split(":")[0]) if self.vet_cb.get() else None
        status    = self.status_cb.get() or None

        self.db.execute("""INSERT INTO health_records
            (animal_id, staff_id, date, diagnosis, symptoms, status, notes)
            VALUES (?,?,?,?,?,?,?)""",
            (animal_id, staff_id, self.date_e.get(),
             self.diag_e.get(), self.symp_e.get(), status, self.notes_e.get()))

        if status:
            self.db.execute("UPDATE animals SET health=? WHERE id=?", (status, animal_id))
        self.destroy()


# ── Medicine Panel ───────────────────────────
class MedicinePanel(tk.Frame):
    COLS   = ("id","name","type","unit","stock","min_stock","expiry","supplier")
    HEADS  = ("ID","Name","Type","Unit","Stock","Min Stock","Expiry","Supplier")
    WIDTHS = (40,140,100,60,70,80,100,120)

    def __init__(self, parent, db, readonly=False):
        super().__init__(parent, bg=BG_MID)
        self.db = db; self.readonly = readonly; self._build()

    def _build(self):
        tb = tk.Frame(self, bg=BG_DARK, pady=6, padx=10)
        tb.pack(fill="x")
        if self.readonly:
            ro_bar = tk.Frame(self, bg="#2C3E50", pady=3)
            ro_bar.pack(fill="x")
            tk.Label(ro_bar, text="  👁  VIEW ONLY — You do not have permission to add, edit or delete records.",
                     bg="#2C3E50", fg=ACCENT3,
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(side="left", padx=6)
        make_label(tb, "💊  Medicine Inventory", size=13, bold=True, bg=BG_DARK).pack(side="left")
        StyledButton(tb, "🔄 Refresh", self.refresh, BTN_ORG).pack(side="right", padx=4)
        if not self.readonly:
            StyledButton(tb, "+ Add",    self._add,    BTN_GREEN).pack(side="right", padx=4)
            StyledButton(tb, "✏ Edit",   self._edit,   BTN_BLUE ).pack(side="right", padx=4)
            StyledButton(tb, "🗑 Delete",self._delete, BTN_RED  ).pack(side="right", padx=4)

        self.tree = make_tree(self, self.COLS, self.HEADS, self.WIDTHS)
        self.tree.tag_configure("low",    foreground=ACCENT2)
        self.tree.tag_configure("expiry", foreground=ACCENT3)
        self.refresh()

    def refresh(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        today = str(date.today())
        for r in self.db.fetchall("SELECT * FROM medicines ORDER BY name"):
            vals = tuple(r.get(c, "") or "" for c in self.COLS)
            tag  = ()
            stk  = r.get("stock")
            minstk = r.get("min_stock")
            exp  = str(r.get("expiry_date") or "")
            if stk is not None and minstk is not None and stk <= minstk:
                tag = ("low",)
            elif exp and exp <= today:
                tag = ("expiry",)
            self.tree.insert("", "end", values=vals, tags=tag)

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a medicine first."); return None
        return self.tree.item(sel[0])["values"][0]

    def _add(self):
        dlg = MedicineDialog(self, self.db)
        self.wait_window(dlg); self.refresh()

    def _edit(self):
        mid = self._selected_id()
        if mid:
            dlg = MedicineDialog(self, self.db, med_id=mid)
            self.wait_window(dlg); self.refresh()

    def _delete(self):
        mid = self._selected_id()
        if mid and messagebox.askyesno("Confirm", "Delete medicine?"):
            self.db.delete("DELETE FROM medicines WHERE id=?", (mid,))
            self.refresh()


class MedicineDialog(BaseDialog):
    def __init__(self, parent, db, med_id=None):
        super().__init__(parent, "Add Medicine" if not med_id else "Edit Medicine", height=420)
        self.db = db; self.med_id = med_id
        self._build()
        if med_id: self._load()

    def _build(self):
        f = self.body_frame; f.columnconfigure(1, weight=1)
        self.name_e     = make_entry(f)
        self.type_e     = make_entry(f)
        self.unit_e     = make_entry(f); self.unit_e.insert(0, "mg")
        self.stock_e    = make_entry(f); self.stock_e.insert(0, "0")
        self.min_e      = make_entry(f); self.min_e.insert(0, "10")
        self.expiry_e   = make_entry(f)
        self.supplier_e = make_entry(f)

        for i, (lbl, w) in enumerate([
            ("Name *",      self.name_e),
            ("Type",        self.type_e),
            ("Unit",        self.unit_e),
            ("Stock",       self.stock_e),
            ("Min Stock",   self.min_e),
            ("Expiry Date (YYYY-MM-DD)", self.expiry_e),
            ("Supplier",    self.supplier_e),
        ]):
            self._row(lbl, w, i)
        self._btn_row("Save", self._save)

    def _load(self):
        r = self.db.fetchone("SELECT * FROM medicines WHERE id=?", (self.med_id,))
        if not r: return
        for e, key in [(self.name_e,"name"),(self.type_e,"type"),(self.unit_e,"unit"),
                       (self.stock_e,"stock"),(self.min_e,"min_stock"),
                       (self.expiry_e,"expiry_date"),(self.supplier_e,"supplier")]:
            e.delete(0,"end"); e.insert(0, str(r.get(key) or ""))

    def _save(self):
        name = self.name_e.get().strip()
        if not name:
            messagebox.showwarning("Required", "Name is required."); return
        try:
            stock = float(self.stock_e.get() or 0)
            minst = float(self.min_e.get() or 0)
        except ValueError:
            messagebox.showerror("Input", "Stock values must be numbers."); return
        expiry = self.expiry_e.get().strip() or None

        if self.med_id:
            self.db.execute("""UPDATE medicines SET name=?,type=?,unit=?,stock=?,
                min_stock=?,expiry_date=?,supplier=? WHERE id=?""",
                (name, self.type_e.get(), self.unit_e.get(), stock, minst,
                 expiry, self.supplier_e.get(), self.med_id))
        else:
            self.db.execute("""INSERT INTO medicines (name,type,unit,stock,min_stock,expiry_date,supplier)
                VALUES (?,?,?,?,?,?,?)""",
                (name, self.type_e.get(), self.unit_e.get(), stock, minst,
                 expiry, self.supplier_e.get()))
        self.destroy()


# ── Treatments Panel ─────────────────────────
class TreatmentPanel(tk.Frame):
    COLS   = ("id","animal","date","medicine","dose","duration","purpose","vet")
    HEADS  = ("ID","Animal","Date","Medicine","Dose","Duration","Purpose","Veterinarian")
    WIDTHS = (40,120,90,130,60,80,130,120)

    def __init__(self, parent, db, readonly=False):
        super().__init__(parent, bg=BG_MID)
        self.db = db; self.readonly = readonly; self._build()

    def _build(self):
        tb = tk.Frame(self, bg=BG_DARK, pady=6, padx=10)
        tb.pack(fill="x")
        if self.readonly:
            ro_bar = tk.Frame(self, bg="#2C3E50", pady=3)
            ro_bar.pack(fill="x")
            tk.Label(ro_bar, text="  👁  VIEW ONLY — You do not have permission to add, edit or delete records.",
                     bg="#2C3E50", fg=ACCENT3,
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(side="left", padx=6)
        make_label(tb, "💉  Treatment Records", size=13, bold=True, bg=BG_DARK).pack(side="left")
        StyledButton(tb, "🔄 Refresh", self.refresh, BTN_ORG).pack(side="right", padx=4)
        if not self.readonly:
            StyledButton(tb, "+ Log Treatment", self._add,    BTN_GREEN).pack(side="right", padx=4)
            StyledButton(tb, "🗑 Delete",       self._delete, BTN_RED  ).pack(side="right", padx=4)

        self.tree = make_tree(self, self.COLS, self.HEADS, self.WIDTHS)
        self.refresh()

    def refresh(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        for r in self.db.fetchall("""
            SELECT t.id, a.name AS animal, t.date, m.name AS medicine,
                   t.dose, t.duration, t.purpose, s.name AS vet
            FROM   treatments t
            JOIN   animals a ON a.id = t.animal_id
            LEFT JOIN medicines m ON m.id = t.medicine_id
            LEFT JOIN staff s ON s.id = t.staff_id
            ORDER  BY t.date DESC
        """):
            self.tree.insert("", "end", values=tuple(r.get(c, "") or "" for c in self.COLS))

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select","Select a record first."); return None
        return self.tree.item(sel[0])["values"][0]

    def _add(self):
        dlg = TreatmentDialog(self, self.db)
        self.wait_window(dlg); self.refresh()

    def _delete(self):
        tid = self._selected_id()
        if tid and messagebox.askyesno("Confirm", "Delete this treatment record?"):
            self.db.delete("DELETE FROM treatments WHERE id=?", (tid,))
            self.refresh()


class TreatmentDialog(BaseDialog):
    def __init__(self, parent, db):
        super().__init__(parent, "Log Treatment", height=480)
        self.db = db; self._build()

    def _build(self):
        f = self.body_frame; f.columnconfigure(1, weight=1)
        animals = [f"{a['id']}: {a['name']}" for a in self.db.fetchall("SELECT id,name FROM animals ORDER BY name")]
        meds    = [f"{m['id']}: {m['name']}" for m in self.db.fetchall("SELECT id,name FROM medicines ORDER BY name")]
        vets    = [f"{s['id']}: {s['name']}" for s in
                   self.db.fetchall("SELECT id,name FROM staff WHERE role='Veterinarian' ORDER BY name")]

        self.animal_cb = make_combo(f, animals)
        self.med_cb    = make_combo(f, meds)
        self.vet_cb    = make_combo(f, vets)
        self.date_e    = make_entry(f); self.date_e.insert(0, str(date.today()))
        self.dose_e    = make_entry(f)
        self.dur_e     = make_entry(f)
        self.purp_e    = make_entry(f)
        self.notes_e   = make_entry(f)

        for i, (lbl, w) in enumerate([
            ("Animal *",     self.animal_cb),
            ("Medicine",     self.med_cb),
            ("Veterinarian", self.vet_cb),
            ("Date",         self.date_e),
            ("Dose",         self.dose_e),
            ("Duration",     self.dur_e),
            ("Purpose",      self.purp_e),
            ("Notes",        self.notes_e),
        ]):
            self._row(lbl, w, i)
        self._btn_row("Save", self._save)

    def _save(self):
        if not self.animal_cb.get():
            messagebox.showwarning("Required","Select an animal."); return
        animal_id = int(self.animal_cb.get().split(":")[0])
        med_id    = int(self.med_cb.get().split(":")[0]) if self.med_cb.get() else None
        staff_id  = int(self.vet_cb.get().split(":")[0]) if self.vet_cb.get() else None
        try:
            dose = float(self.dose_e.get()) if self.dose_e.get() else None
        except ValueError:
            dose = None

        # Insert treatment record first
        self.db.execute("""INSERT INTO treatments
            (animal_id, medicine_id, staff_id, date, dose, duration, purpose, notes)
            VALUES (?,?,?,?,?,?,?,?)""",
            (animal_id, med_id, staff_id, self.date_e.get(),
             dose, self.dur_e.get(), self.purp_e.get(), self.notes_e.get()))

        # Deduct stock — trg_medicine_low_stock fires on this UPDATE
        # if stock drops to or below min_stock
        if med_id and dose:
            self.db.execute(
                "UPDATE medicines SET stock = GREATEST(0, stock - ?) WHERE id = ?",
                (dose, med_id)
            )

        self.destroy()


# ── Feeding Panel ────────────────────────────
class FeedingPanel(tk.Frame):
    COLS   = ("id","animal","diet","foods","qty","freq","times")
    HEADS  = ("ID","Animal","Diet Type","Food Items","Qty(kg)","Frequency","Time Slots")
    WIDTHS = (40,120,100,160,60,100,120)

    def __init__(self, parent, db, readonly=False):
        super().__init__(parent, bg=BG_MID)
        self.db = db; self.readonly = readonly; self._build()

    def _build(self):
        tb = tk.Frame(self, bg=BG_DARK, pady=6, padx=10)
        tb.pack(fill="x")
        if self.readonly:
            ro_bar = tk.Frame(self, bg="#2C3E50", pady=3)
            ro_bar.pack(fill="x")
            tk.Label(ro_bar, text="  👁  VIEW ONLY — You do not have permission to add, edit or delete records.",
                     bg="#2C3E50", fg=ACCENT3,
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(side="left", padx=6)
        make_label(tb, "🍖  Feeding Schedules", size=13, bold=True, bg=BG_DARK).pack(side="left")
        StyledButton(tb, "🔄 Refresh", self.refresh, BTN_ORG).pack(side="right", padx=4)
        if not self.readonly:
            StyledButton(tb, "+ Add",    self._add,    BTN_GREEN).pack(side="right", padx=4)
            StyledButton(tb, "✏ Edit",   self._edit,   BTN_BLUE ).pack(side="right", padx=4)
            StyledButton(tb, "🗑 Delete",self._delete, BTN_RED  ).pack(side="right", padx=4)

        self.tree = make_tree(self, self.COLS, self.HEADS, self.WIDTHS)
        self.refresh()

    def refresh(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        for r in self.db.fetchall("""
            SELECT fs.id, a.name AS animal, fs.diet_type AS diet, fs.food_items AS foods,
                   fs.quantity_kg AS qty, fs.frequency AS freq, fs.time_slots AS times
            FROM   feeding_schedules fs
            JOIN   animals a ON a.id = fs.animal_id ORDER BY a.name
        """):
            self.tree.insert("", "end", values=tuple(r.get(c, "") or "" for c in self.COLS))

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select","Select a schedule."); return None
        return self.tree.item(sel[0])["values"][0]

    def _add(self):
        dlg = FeedingDialog(self, self.db)
        self.wait_window(dlg); self.refresh()

    def _edit(self):
        fid = self._selected_id()
        if fid:
            dlg = FeedingDialog(self, self.db, feed_id=fid)
            self.wait_window(dlg); self.refresh()

    def _delete(self):
        fid = self._selected_id()
        if fid and messagebox.askyesno("Confirm","Delete this schedule?"):
            self.db.delete("DELETE FROM feeding_schedules WHERE id=?", (fid,))
            self.refresh()


class FeedingDialog(BaseDialog):
    def __init__(self, parent, db, feed_id=None):
        super().__init__(parent, "Feeding Schedule", height=440)
        self.db = db; self.feed_id = feed_id
        self._build()
        if feed_id: self._load()

    def _build(self):
        f = self.body_frame; f.columnconfigure(1, weight=1)
        animals = [f"{a['id']}: {a['name']}" for a in self.db.fetchall("SELECT id,name FROM animals ORDER BY name")]
        self.animal_cb = make_combo(f, animals)
        self.diet_e    = make_entry(f)
        self.foods_e   = make_entry(f)
        self.qty_e     = make_entry(f)
        self.freq_cb   = make_combo(f, ["Daily","Twice Daily","Weekly","Bi-weekly","Monthly","On Demand"])
        self.times_e   = make_entry(f)
        self.notes_e   = make_entry(f)

        for i, (lbl, w) in enumerate([
            ("Animal *",     self.animal_cb),
            ("Diet Type",    self.diet_e),
            ("Food Items",   self.foods_e),
            ("Quantity(kg)", self.qty_e),
            ("Frequency",    self.freq_cb),
            ("Time Slots",   self.times_e),
            ("Notes",        self.notes_e),
        ]):
            self._row(lbl, w, i)
        self._btn_row("Save", self._save)

    def _load(self):
        r = self.db.fetchone("SELECT * FROM feeding_schedules WHERE id=?", (self.feed_id,))
        if not r: return
        a = self.db.fetchone("SELECT id,name FROM animals WHERE id=?", (r["animal_id"],))
        if a: self.animal_cb.set(f"{a['id']}: {a['name']}")
        for e, key in [(self.diet_e,"diet_type"),(self.foods_e,"food_items"),
                       (self.qty_e,"quantity_kg"),(self.times_e,"time_slots"),(self.notes_e,"notes")]:
            e.delete(0,"end"); e.insert(0, str(r.get(key) or ""))
        if r.get("frequency"): self.freq_cb.set(r["frequency"])

    def _save(self):
        if not self.animal_cb.get():
            messagebox.showwarning("Required","Select an animal."); return
        animal_id = int(self.animal_cb.get().split(":")[0])
        try:
            qty = float(self.qty_e.get()) if self.qty_e.get() else None
        except ValueError:
            qty = None

        if self.feed_id:
            self.db.execute("""UPDATE feeding_schedules SET animal_id=?,diet_type=?,food_items=?,
                quantity_kg=?,frequency=?,time_slots=?,notes=? WHERE id=?""",
                (animal_id, self.diet_e.get(), self.foods_e.get(), qty,
                 self.freq_cb.get(), self.times_e.get(), self.notes_e.get(), self.feed_id))
        else:
            self.db.execute("""INSERT INTO feeding_schedules
                (animal_id,diet_type,food_items,quantity_kg,frequency,time_slots,notes)
                VALUES (?,?,?,?,?,?,?)""",
                (animal_id, self.diet_e.get(), self.foods_e.get(), qty,
                 self.freq_cb.get(), self.times_e.get(), self.notes_e.get()))
        self.destroy()


# ── Zones Panel ──────────────────────────────
class ZonesPanel(tk.Frame):
    COLS   = ("id","name","area","capacity","description","animals")
    HEADS  = ("ID","Zone Name","Area (km²)","Capacity","Description","Animals")
    WIDTHS = (40,130,90,80,200,70)

    def __init__(self, parent, db, readonly=False):
        super().__init__(parent, bg=BG_MID)
        self.db = db; self.readonly = readonly; self._build()

    def _build(self):
        tb = tk.Frame(self, bg=BG_DARK, pady=6, padx=10)
        tb.pack(fill="x")
        if self.readonly:
            ro_bar = tk.Frame(self, bg="#2C3E50", pady=3)
            ro_bar.pack(fill="x")
            tk.Label(ro_bar, text="  👁  VIEW ONLY — You do not have permission to add, edit or delete records.",
                     bg="#2C3E50", fg=ACCENT3,
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(side="left", padx=6)
        make_label(tb, "🗺  Habitat Zones", size=13, bold=True, bg=BG_DARK).pack(side="left")
        StyledButton(tb, "🔄 Refresh", self.refresh, BTN_ORG).pack(side="right", padx=4)
        if not self.readonly:
            StyledButton(tb, "+ Add",    self._add,    BTN_GREEN).pack(side="right", padx=4)
            StyledButton(tb, "✏ Edit",   self._edit,   BTN_BLUE ).pack(side="right", padx=4)
            StyledButton(tb, "🗑 Delete",self._delete, BTN_RED  ).pack(side="right", padx=4)

        self.tree = make_tree(self, self.COLS, self.HEADS, self.WIDTHS)
        self.refresh()

    def refresh(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        for r in self.db.fetchall("""
            SELECT z.id, z.name, z.area_sqkm AS area, z.capacity,
                   z.description, COUNT(a.id) AS animals
            FROM zones z LEFT JOIN animals a ON a.zone_id = z.id
            GROUP BY z.id, z.name, z.area_sqkm, z.capacity, z.description
            ORDER BY z.name
        """):
            self.tree.insert("", "end", values=tuple(r.get(c, "") or "" for c in self.COLS))

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select","Select a zone first."); return None
        return self.tree.item(sel[0])["values"][0]

    def _add(self):
        dlg = ZoneDialog(self, self.db)
        self.wait_window(dlg); self.refresh()

    def _edit(self):
        zid = self._selected_id()
        if zid:
            dlg = ZoneDialog(self, self.db, zone_id=zid)
            self.wait_window(dlg); self.refresh()

    def _delete(self):
        zid = self._selected_id()
        if zid and messagebox.askyesno("Confirm","Delete zone? Animals will be unassigned."):
            self.db.delete("DELETE FROM zones WHERE id=?", (zid,))
            self.refresh()


class ZoneDialog(BaseDialog):
    def __init__(self, parent, db, zone_id=None):
        super().__init__(parent, "Zone", height=360)
        self.db = db; self.zone_id = zone_id
        self._build()
        if zone_id: self._load()

    def _build(self):
        f = self.body_frame; f.columnconfigure(1, weight=1)
        self.name_e = make_entry(f)
        self.area_e = make_entry(f)
        self.cap_e  = make_entry(f)
        self.desc_e = make_entry(f, 28)

        for i, (lbl, w) in enumerate([
            ("Zone Name *", self.name_e),
            ("Area (km²)",  self.area_e),
            ("Capacity",    self.cap_e),
            ("Description", self.desc_e),
        ]):
            self._row(lbl, w, i)
        self._btn_row("Save", self._save)

    def _load(self):
        r = self.db.fetchone("SELECT * FROM zones WHERE id=?", (self.zone_id,))
        if not r: return
        for e, k in [(self.name_e,"name"),(self.area_e,"area_sqkm"),
                     (self.cap_e,"capacity"),(self.desc_e,"description")]:
            e.delete(0,"end"); e.insert(0, str(r.get(k) or ""))

    def _save(self):
        name = self.name_e.get().strip()
        if not name:
            messagebox.showwarning("Required","Zone name is required."); return
        try:
            area = float(self.area_e.get()) if self.area_e.get() else None
            cap  = int(self.cap_e.get()) if self.cap_e.get() else None
        except ValueError:
            messagebox.showerror("Input","Area and Capacity must be numbers."); return

        if self.zone_id:
            self.db.execute("UPDATE zones SET name=?,area_sqkm=?,capacity=?,description=? WHERE id=?",
                (name, area, cap, self.desc_e.get(), self.zone_id))
        else:
            self.db.execute("INSERT INTO zones (name,area_sqkm,capacity,description) VALUES (?,?,?,?)",
                (name, area, cap, self.desc_e.get()))
        self.destroy()


# ── Staff Panel ──────────────────────────────
class StaffPanel(tk.Frame):
    COLS   = ("id","name","role","email","phone","speciality")
    HEADS  = ("ID","Name","Role","Email","Phone","Speciality")
    WIDTHS = (40,140,110,160,110,140)

    def __init__(self, parent, db, readonly=False):
        super().__init__(parent, bg=BG_MID)
        self.db = db; self.readonly = readonly; self._build()

    def _build(self):
        tb = tk.Frame(self, bg=BG_DARK, pady=6, padx=10)
        tb.pack(fill="x")
        if self.readonly:
            ro_bar = tk.Frame(self, bg="#2C3E50", pady=3)
            ro_bar.pack(fill="x")
            tk.Label(ro_bar, text="  👁  VIEW ONLY — You do not have permission to add, edit or delete records.",
                     bg="#2C3E50", fg=ACCENT3,
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(side="left", padx=6)
        make_label(tb, "👤  Staff & Veterinarians", size=13, bold=True, bg=BG_DARK).pack(side="left")
        StyledButton(tb, "🔄 Refresh", self.refresh, BTN_ORG).pack(side="right", padx=4)
        if not self.readonly:
            StyledButton(tb, "+ Add",    self._add,    BTN_GREEN).pack(side="right", padx=4)
            StyledButton(tb, "✏ Edit",   self._edit,   BTN_BLUE ).pack(side="right", padx=4)
            StyledButton(tb, "🗑 Delete",self._delete, BTN_RED  ).pack(side="right", padx=4)

        self.tree = make_tree(self, self.COLS, self.HEADS, self.WIDTHS)
        self.refresh()

    def refresh(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        for r in self.db.fetchall("SELECT * FROM staff ORDER BY name"):
            self.tree.insert("", "end", values=tuple(r.get(c, "") or "" for c in self.COLS))

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select","Select a staff member."); return None
        return self.tree.item(sel[0])["values"][0]

    def _add(self):
        dlg = StaffDialog(self, self.db)
        self.wait_window(dlg); self.refresh()

    def _edit(self):
        sid = self._selected_id()
        if sid:
            dlg = StaffDialog(self, self.db, staff_id=sid)
            self.wait_window(dlg); self.refresh()

    def _delete(self):
        sid = self._selected_id()
        if sid and messagebox.askyesno("Confirm","Delete staff member?"):
            self.db.delete("DELETE FROM staff WHERE id=?", (sid,))
            self.refresh()


class StaffDialog(BaseDialog):
    def __init__(self, parent, db, staff_id=None):
        super().__init__(parent, "Staff Member", height=400)
        self.db = db; self.staff_id = staff_id
        self._build()
        if staff_id: self._load()

    def _build(self):
        f = self.body_frame; f.columnconfigure(1, weight=1)
        self.name_e  = make_entry(f)
        self.role_cb = make_combo(f, ["Caretaker","Veterinarian","Ranger","Admin"])
        self.email_e = make_entry(f)
        self.phone_e = make_entry(f)
        self.spec_e  = make_entry(f)

        for i, (lbl, w) in enumerate([
            ("Full Name *", self.name_e),
            ("Role *",      self.role_cb),
            ("Email",       self.email_e),
            ("Phone",       self.phone_e),
            ("Speciality",  self.spec_e),
        ]):
            self._row(lbl, w, i)
        self._btn_row("Save", self._save)

    def _load(self):
        r = self.db.fetchone("SELECT * FROM staff WHERE id=?", (self.staff_id,))
        if not r: return
        for e, k in [(self.name_e,"name"),(self.email_e,"email"),
                     (self.phone_e,"phone"),(self.spec_e,"speciality")]:
            e.delete(0,"end"); e.insert(0, str(r.get(k) or ""))
        if r.get("role"): self.role_cb.set(r["role"])

    def _save(self):
        name = self.name_e.get().strip()
        role = self.role_cb.get()
        if not name or not role:
            messagebox.showwarning("Required","Name and Role are required."); return

        if self.staff_id:
            self.db.execute("UPDATE staff SET name=?,role=?,email=?,phone=?,speciality=? WHERE id=?",
                (name, role, self.email_e.get(), self.phone_e.get(), self.spec_e.get(), self.staff_id))
        else:
            self.db.execute("INSERT INTO staff (name,role,email,phone,speciality) VALUES (?,?,?,?,?)",
                (name, role, self.email_e.get(), self.phone_e.get(), self.spec_e.get()))
        self.destroy()


# ── Reports Panel ────────────────────────────
class ReportsPanel(tk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, bg=BG_MID)
        self.db = db; self._build()

    def _build(self):
        tb = tk.Frame(self, bg=BG_DARK, pady=6, padx=10)
        tb.pack(fill="x")
        make_label(tb, "📊  Reports & Analysis", size=13, bold=True, bg=BG_DARK).pack(side="left")
        StyledButton(tb, "🔄 Refresh", self.refresh, BTN_ORG).pack(side="right", padx=4)

        col_frame = tk.Frame(self, bg=BG_MID)
        col_frame.pack(fill="both", expand=True, padx=10, pady=10)
        col_frame.columnconfigure(0, weight=1)
        col_frame.columnconfigure(1, weight=1)

        self.cards = {}
        for label, row, col in [
            ("summary",      0, 0),
            ("sick_animals", 0, 1),
            ("low_stock",    1, 0),
            ("zone_counts",  1, 1),
        ]:
            f = tk.Frame(col_frame, bg=BG_CARD, bd=0, relief="flat")
            f.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
            col_frame.rowconfigure(row, weight=1)
            self.cards[label] = f

        self.refresh()

    def _card_title(self, frame, title):
        for w in frame.winfo_children(): w.destroy()
        tk.Label(frame, text=title, bg=BG_CARD, fg=ACCENT,
                 font=("Segoe UI", 11, "bold"), pady=8).pack(fill="x", padx=10)
        ttk.Separator(frame, orient="horizontal").pack(fill="x", padx=10)

    def refresh(self):
        # Summary card
        f = self.cards["summary"]
        self._card_title(f, "🐾 Sanctuary Summary")
        for label, sql in [
            ("Total Animals",     "SELECT COUNT(*) AS n FROM animals"),
            ("Zones",             "SELECT COUNT(*) AS n FROM zones"),
            ("Staff Members",     "SELECT COUNT(*) AS n FROM staff"),
            ("Medicines",         "SELECT COUNT(*) AS n FROM medicines"),
            ("Health Records",    "SELECT COUNT(*) AS n FROM health_records"),
            ("Treatments Logged", "SELECT COUNT(*) AS n FROM treatments"),
        ]:
            val = (self.db.fetchone(sql) or {}).get("n", 0)
            row = tk.Frame(f, bg=BG_CARD)
            row.pack(fill="x", padx=14, pady=2)
            tk.Label(row, text=label, bg=BG_CARD, fg=TEXT_SUB,
                     font=("Segoe UI", 9), anchor="w").pack(side="left")
            tk.Label(row, text=str(val), bg=BG_CARD, fg=ACCENT3,
                     font=("Segoe UI", 10, "bold")).pack(side="right")

        # Sick animals card
        f = self.cards["sick_animals"]
        self._card_title(f, "🏥 Animals Needing Attention")
        rows = self.db.fetchall("""
            SELECT a.name, a.species, a.health, z.name AS zone
            FROM   animals a LEFT JOIN zones z ON z.id = a.zone_id
            WHERE  a.health IN ('Sick','Critical','Recovering')
            ORDER  BY FIELD(a.health,'Critical','Sick','Recovering')
        """)
        if not rows:
            tk.Label(f, text="✅  All animals are healthy!", bg=BG_CARD,
                     fg=BTN_GREEN, font=("Segoe UI", 10), pady=10).pack()
        for r in rows:
            color = {"Critical": ACCENT2, "Sick": ACCENT3, "Recovering": ACCENT}.get(r.get("health",""), TEXT_MAIN)
            tk.Label(f, text=f"  {str(r.get('health','')).upper():12} {r.get('name','')} ({r.get('species','')})",
                     bg=BG_CARD, fg=color, font=("Segoe UI", 9), anchor="w").pack(fill="x", padx=10, pady=1)

        # Low stock card
        f = self.cards["low_stock"]
        self._card_title(f, "⚠️  Low Medicine Stock")
        rows = self.db.fetchall("SELECT name, stock, min_stock, unit FROM medicines WHERE stock <= min_stock ORDER BY stock")
        if not rows:
            tk.Label(f, text="✅  All medicines well-stocked!", bg=BG_CARD,
                     fg=BTN_GREEN, font=("Segoe UI", 10), pady=10).pack()
        for r in rows:
            tk.Label(f, text=f"  {r.get('name','')}: {r.get('stock',0)} {r.get('unit','')} (min {r.get('min_stock',0)})",
                     bg=BG_CARD, fg=ACCENT2, font=("Segoe UI", 9), anchor="w").pack(fill="x", padx=10, pady=1)

        # Zone counts card
        f = self.cards["zone_counts"]
        self._card_title(f, "🗺  Animals per Zone")
        rows = self.db.fetchall("""
            SELECT z.name, COUNT(a.id) AS cnt, z.capacity
            FROM   zones z LEFT JOIN animals a ON a.zone_id = z.id
            GROUP  BY z.id, z.name, z.capacity ORDER BY cnt DESC
        """)
        if not rows:
            tk.Label(f, text="No zones defined yet.", bg=BG_CARD,
                     fg=TEXT_SUB, font=("Segoe UI", 9), pady=10).pack()
        for r in rows:
            cap = r.get("capacity") or "∞"
            row = tk.Frame(f, bg=BG_CARD)
            row.pack(fill="x", padx=14, pady=2)
            tk.Label(row, text=r.get("name",""), bg=BG_CARD, fg=TEXT_MAIN,
                     font=("Segoe UI", 9), anchor="w").pack(side="left")
            tk.Label(row, text=f"({r.get('cnt',0)}/{cap})", bg=BG_CARD, fg=ACCENT,
                     font=("Segoe UI", 9, "bold")).pack(side="right")


# ── Triggers Panel ──────────────────────────
class TriggersPanel(tk.Frame):
    """
    Demonstrates both database triggers:
      • trg_health_status_alert  – fires on animal health change
      • trg_medicine_low_stock   – fires when medicine stock is low
    Shows the trigger source code and a live log of every firing.
    """

    TRIGGER1_SQL = """\
TRIGGER: trg_health_status_alert
EVENT   : AFTER UPDATE ON animals
PURPOSE : When an animal's health status changes, this trigger
          automatically:
            1. Inserts an audit row into health_records
               (diagnosis = 'Auto-logged: health changed from X to Y')
            2. Logs the event in trigger_logs with full details

-- ── SQL Definition ──────────────────────────────────
CREATE TRIGGER trg_health_status_alert
AFTER UPDATE ON animals
FOR EACH ROW
BEGIN
    IF OLD.health <> NEW.health THEN

        -- Auto audit row in health_records
        INSERT INTO health_records
            (animal_id, staff_id, date, diagnosis, symptoms, status, notes)
        VALUES (
            NEW.id, NULL, CURDATE(),
            CONCAT('Auto-logged: health changed from ',
                    OLD.health, ' to ', NEW.health),
            'System detected status change',
            NEW.health,
            'Created automatically by trg_health_status_alert'
        );

        -- Log to trigger_logs
        INSERT INTO trigger_logs (trigger_name, event, animal_id, details)
        VALUES (
            'trg_health_status_alert',
            CONCAT('Health changed: ', OLD.health, ' to ', NEW.health),
            NEW.id,
            CONCAT('Animal ID=', NEW.id,
                   ' | Name=', NEW.name,
                   ' | Previous=', OLD.health,
                   ' | New=', NEW.health,
                   ' | Logged at=', NOW())
        );
    END IF;
END"""

    TRIGGER2_SQL = """\
TRIGGER: trg_medicine_low_stock
EVENT   : AFTER UPDATE ON medicines
PURPOSE : When medicine stock is updated (e.g. after a treatment is
          logged and stock is deducted), this trigger automatically
          checks if the new stock level has dropped to or below the
          minimum threshold. If so, it logs a LOW STOCK ALERT into
          trigger_logs so staff know to reorder immediately.

-- ── SQL Definition ──────────────────────────────────
CREATE TRIGGER trg_medicine_low_stock
AFTER UPDATE ON medicines
FOR EACH ROW
BEGIN
    -- Only fire when stock crosses the minimum boundary
    IF NEW.stock <= NEW.min_stock AND OLD.stock > OLD.min_stock THEN
        INSERT INTO trigger_logs (trigger_name, event, animal_id, details)
        VALUES (
            'trg_medicine_low_stock',
            CONCAT('LOW STOCK ALERT: ', NEW.name),
            NULL,
            CONCAT('Medicine: ', NEW.name,
                   ' | Stock dropped to: ', NEW.stock,
                   ' | Minimum required: ', NEW.min_stock,
                   ' | Previous stock: ', OLD.stock,
                   ' | REORDER IMMEDIATELY | ', NOW())
        );
    END IF;
END"""

    LOG_COLS   = ("id", "trigger_name", "event", "animal_id", "details", "fired_at")
    LOG_HEADS  = ("ID", "Trigger Name", "Event", "Animal ID", "Details", "Fired At")
    LOG_WIDTHS = (40, 180, 200, 75, 340, 150)

    def __init__(self, parent, db):
        super().__init__(parent, bg=BG_MID)
        self.db = db
        self._last_log_id = db.get_latest_log_id()
        self._poll_job    = None
        self._build()
        self._start_polling()   # begin live auto-refresh every 3 s

    def _build(self):
        # ── Toolbar ──────────────────────────
        tb = tk.Frame(self, bg=BG_DARK, pady=6, padx=10)
        tb.pack(fill="x")
        make_label(tb, "⚡  Database Triggers", size=13, bold=True, bg=BG_DARK).pack(side="left")
        StyledButton(tb, "🔄 Refresh Logs",      self._refresh_logs,    BTN_ORG  ).pack(side="right", padx=4)
        StyledButton(tb, "🧪 Test Trigger 1",    self._test_trigger1,   BTN_BLUE ).pack(side="right", padx=4)
        StyledButton(tb, "🧪 Test Trigger 2",    self._test_trigger2,   BTN_GREEN).pack(side="right", padx=4)
        StyledButton(tb, "🗑 Clear Logs",         self._clear_logs,      BTN_RED  ).pack(side="right", padx=4)
        StyledButton(tb, "🔧 Recreate Triggers",  self._recreate,        BTN_ORG  ).pack(side="right", padx=4)

        # ── Trigger status bar ────────────────
        self.status_frame = tk.Frame(self, bg=BG_CARD, pady=6, padx=14)
        self.status_frame.pack(fill="x", padx=6, pady=(4,0))
        self.t1_var = tk.StringVar(value="⏳ Checking...")
        self.t2_var = tk.StringVar(value="⏳ Checking...")
        self.trg_count_var = tk.StringVar(value="")
        make_label(self.status_frame, "Trigger 1 (Health Alert):",
                   size=9, color=TEXT_SUB, bg=BG_CARD).pack(side="left", padx=(0,4))
        self.t1_lbl = tk.Label(self.status_frame, textvariable=self.t1_var,
                               bg=BG_CARD, font=("Segoe UI", 9, "bold"))
        self.t1_lbl.pack(side="left", padx=(0,14))
        make_label(self.status_frame, "Trigger 2 (Low Stock):",
                   size=9, color=TEXT_SUB, bg=BG_CARD).pack(side="left", padx=(0,4))
        self.t2_lbl = tk.Label(self.status_frame, textvariable=self.t2_var,
                               bg=BG_CARD, font=("Segoe UI", 9, "bold"))
        self.t2_lbl.pack(side="left", padx=(0,14))
        tk.Label(self.status_frame, textvariable=self.trg_count_var,
                 bg=BG_CARD, fg=ACCENT3,
                 font=("Segoe UI", 9, "bold")).pack(side="right", padx=6)
        self._update_status()

        # ── Split: left = definitions, right = live log ──
        pane = tk.PanedWindow(self, orient="horizontal", bg=BG_MID,
                              sashwidth=6, sashrelief="flat")
        pane.pack(fill="both", expand=True, padx=6, pady=6)

        # Left — trigger definitions
        left = tk.Frame(pane, bg=BG_MID)
        pane.add(left, minsize=360)

        make_label(left, "📋  Trigger Definitions", size=10, bold=True,
                   color=ACCENT).pack(anchor="w", padx=6, pady=(6,2))

        nb = ttk.Notebook(left, style="TNotebook")
        nb.pack(fill="both", expand=True, padx=4, pady=4)

        for title, sql in [
            ("Trigger 1 — Health Alert",  self.TRIGGER1_SQL),
            ("Trigger 2 — Low Stock",     self.TRIGGER2_SQL),
        ]:
            frame = tk.Frame(nb, bg=BG_CARD)
            nb.add(frame, text=f"  {title}  ")
            txt = tk.Text(frame, bg=BG_CARD, fg=TEXT_MAIN,
                          font=("Courier New", 8), wrap="none",
                          relief="flat", bd=6,
                          insertbackground=TEXT_MAIN)
            sy = ttk.Scrollbar(frame, orient="vertical",   command=txt.yview)
            sx = ttk.Scrollbar(frame, orient="horizontal", command=txt.xview)
            txt.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
            sy.pack(side="right",  fill="y")
            sx.pack(side="bottom", fill="x")
            txt.pack(fill="both", expand=True)
            txt.insert("1.0", sql)
            txt.config(state="disabled")
            for kw in ("CREATE","TRIGGER","AFTER","UPDATE","INSERT","ON",
                       "FOR","EACH","ROW","BEGIN","END","IF","THEN",
                       "DECLARE","DEFAULT","SELECT","INTO","WHERE","VALUES",
                       "CONCAT","CURDATE","NOW","IFNULL"):
                self._highlight(txt, kw)

        # Right — live log
        right = tk.Frame(pane, bg=BG_MID)
        pane.add(right, minsize=400)

        hdr = tk.Frame(right, bg=BG_MID)
        hdr.pack(fill="x", padx=4, pady=(6,2))
        make_label(hdr, "📡  Live Trigger Logs", size=10, bold=True,
                   color=ACCENT).pack(side="left")

        self.stats_var = tk.StringVar(value="")
        tk.Label(hdr, textvariable=self.stats_var, bg=BG_MID,
                 fg=TEXT_SUB, font=("Segoe UI", 8)).pack(side="right", padx=6)

        self.log_tree = make_tree(right, self.LOG_COLS, self.LOG_HEADS, self.LOG_WIDTHS)
        self.log_tree.tag_configure("health", foreground=ACCENT3)
        self.log_tree.tag_configure("stock",  foreground=ACCENT2)

        self._refresh_logs()

    # ── Trigger status check ─────────────────
    def _update_status(self):
        existing = self.db.verify_triggers()
        all_5 = [
            "trg_health_status_alert",
            "trg_medicine_low_stock",
            "trg_new_animal_zone_log",
            "trg_treatment_audit",
            "trg_feeding_overdue_flag",
        ]
        found = [t for t in all_5 if t in existing]
        missing = [t for t in all_5 if t not in existing]
        # Update t1/t2 status labels for display
        for var, lbl, name in [
            (self.t1_var, self.t1_lbl, "trg_health_status_alert"),
            (self.t2_var, self.t2_lbl, "trg_medicine_low_stock"),
        ]:
            if name in existing:
                var.set("✅ ACTIVE")
                lbl.config(fg="#2ECC71")
            else:
                var.set("❌ NOT FOUND")
                lbl.config(fg=ACCENT2)
        # Show count
        if hasattr(self, "trg_count_var"):
            self.trg_count_var.set(
                str(len(found))+"/5 triggers active"
                +(("  |  Missing: "+", ".join(missing)) if missing else "")
            )

    # ── Recreate triggers ────────────────────
    def _recreate(self):
        ok, msg = self.db._create_triggers()
        self._update_status()
        if ok:
            messagebox.showinfo("Success ✅", msg)
        else:
            messagebox.showerror(
                "Trigger Creation Failed",
                f"Error details:\n\n{msg}\n\n"
                "Try running the SQL manually in MySQL Workbench instead.\n"
                "See the SQL definitions in the left panel."
            )

    # ── Syntax highlighter ───────────────────
    @staticmethod
    def _highlight(txt_widget, keyword):
        txt_widget.config(state="normal")
        start = "1.0"
        while True:
            pos = txt_widget.search(r'\m' + keyword + r'\M', start,
                                    stopindex="end", regexp=True)
            if not pos:
                break
            end = f"{pos}+{len(keyword)}c"
            txt_widget.tag_add(keyword, pos, end)
            txt_widget.tag_config(keyword, foreground=ACCENT)
            start = end
        txt_widget.config(state="disabled")

    # ── Refresh log tree ─────────────────────
    def _refresh_logs(self):
        for r in self.log_tree.get_children():
            self.log_tree.delete(r)

        rows = self.db.fetchall("""
            SELECT id, trigger_name, event, animal_id, details, fired_at
            FROM   trigger_logs
            ORDER  BY fired_at DESC
            LIMIT  200
        """)

        t1 = t2 = 0
        for r in rows:
            tag = "health" if "health_status" in (r.get("trigger_name") or "") else "stock"
            if tag == "health": t1 += 1
            else:               t2 += 1
            self.log_tree.insert("", "end",
                values=(
                    r.get("id",""),
                    r.get("trigger_name",""),
                    r.get("event",""),
                    r.get("animal_id",""),
                    r.get("details",""),
                    str(r.get("fired_at",""))
                ), tags=(tag,))

        total = t1 + t2
        self.stats_var.set(
            f"Total: {total}  |  Health alerts: {t1}  |  Stock alerts: {t2}"
        )

    # ── Test Trigger 1 ───────────────────────
    def _test_trigger1(self):
        """Pick first available animal and toggle its health to fire the trigger."""
        animal = self.db.fetchone(
            "SELECT id, name, health FROM animals LIMIT 1"
        )
        if not animal:
            messagebox.showwarning("No Data", "Add at least one animal first.")
            return

        aid     = animal["id"]
        name    = animal["name"]
        current = animal["health"] or "Healthy"
        new_h   = "Sick" if current == "Healthy" else "Healthy"

        self.db.execute(
            "UPDATE animals SET health=%s WHERE id=%s", (new_h, aid)
        )
        messagebox.showinfo(
            "Trigger 1 Fired ✅",
            f"Animal: {name}\n"
            f"Health changed: {current}  →  {new_h}\n\n"
            f"trg_health_status_alert fired!\n"
            f"• A health_records row was auto-inserted\n"
            f"• A trigger_log row was written\n\n"
            f"Check the Live Trigger Logs below."
        )
        self._refresh_logs()

    # ── Test Trigger 2 ───────────────────────
    def _test_trigger2(self):
        """Update a medicine stock to just below min_stock to fire the trigger."""
        med = self.db.fetchone(
            "SELECT id, name, stock, min_stock FROM medicines ORDER BY id LIMIT 1"
        )
        if not med:
            messagebox.showwarning("No Data", "Add at least one medicine first.")
            return

        med_id    = med["id"]
        med_name  = med["name"]
        min_stock = float(med["min_stock"] or 10)
        old_stock = float(med["stock"] or 0)

        # Set stock just above min first (so OLD.stock > OLD.min_stock)
        # then drop it below — this crosses the boundary and fires the trigger
        self.db.execute(
            "UPDATE medicines SET stock = ? WHERE id = ?",
            (min_stock + 5, med_id)
        )
        # Now drop below min — trigger fires on THIS update
        new_stock = max(0, min_stock - 1)
        self.db.execute(
            "UPDATE medicines SET stock = ? WHERE id = ?",
            (new_stock, med_id)
        )
        messagebox.showinfo(
            "Trigger 2 Test Sent",
            "Medicine : " + med_name + "\n"
            "Stock set: " + str(min_stock + 5) + " to " + str(new_stock) + " (min=" + str(min_stock) + ")\n\n"
            "trg_medicine_low_stock should have fired!\n"
            "Check the Live Trigger Logs below."
        )
        self._refresh_logs()

    # ── Auto-polling (every 3 seconds) ──────
    # ── Auto-polling (every 3 seconds) ──────
    def _start_polling(self):
        """Poll trigger_logs every 3s. Show popup if new rows appeared."""
        try:
            new_rows = self.db.get_new_logs_since(self._last_log_id)
            if new_rows:
                for r in new_rows:
                    self._last_log_id = max(self._last_log_id, r.get("id", 0))
                self._refresh_logs()
                self._update_status()
                for r in new_rows:
                    tname    = r.get("trigger_name", "")
                    event    = r.get("event", "")
                    details  = r.get("details", "")
                    fired_at = str(r.get("fired_at", ""))
                    if "health_status" in tname:
                        messagebox.showinfo(
                            "Trigger 1 Fired!",
                            "TRIGGER: trg_health_status_alert\n\n"
                            "Event   : " + event + "\n"
                            "Details : " + details + "\n"
                            "Fired at: " + fired_at + "\n\n"
                            "Health record auto-inserted into health_records.\n"
                            "Log row written to trigger_logs."
                        )
                    elif "low_stock" in tname:
                        messagebox.showwarning(
                            "Trigger 2 Fired!",
                            "TRIGGER: trg_medicine_low_stock\n\n"
                            "Event   : " + event + "\n"
                            "Details : " + details + "\n"
                            "Fired at: " + fired_at + "\n\n"
                            "Medicine stock is critically low!\n"
                            "Alert written to trigger_logs."
                        )
        except Exception:
            pass
        self._poll_job = self.after(3000, self._start_polling)

    def _stop_polling(self):
        if self._poll_job:
            self.after_cancel(self._poll_job)
            self._poll_job = None

    # ── Clear logs ───────────────────────────
    def _clear_logs(self):
        if messagebox.askyesno("Confirm", "Clear all trigger log entries?"):
            self.db.delete("DELETE FROM trigger_logs")
            self._last_log_id = 0
            self._refresh_logs()



# ════════════════════════════════════════════
#  TRANSACTIONS PANEL  (Task 6)
# ════════════════════════════════════════════
# ════════════════════════════════════════════
#  TRANSACTIONS PANEL  (Task 6)
# ════════════════════════════════════════════
class TransactionsPanel(tk.Frame):
    """
    5 Live DB transaction demos with real-time DB effects viewer:
      T1 – Animal + Health Record COMMIT   (multi-table, both or nothing)
      T2 – Medicine Stock ROLLBACK         (undo deduction if error detected)
      T3 – Conflicting Txns (DEADLOCK SIM) (two sessions fight over same row)
      T4 – SAVEPOINT partial rollback      (keep step 1, undo step 2)
      T5 – Cascading ROLLBACK              (3 steps, error mid-way, all undone)
    Right panel shows BEFORE/AFTER DB state for every demo.
    """

    TXNS = {
        "T1 – Animal Transfer (COMMIT)": (
            "START TRANSACTION;\n"
            "  -- Move animal to new zone\n"
            "  UPDATE animals SET zone_id=<NEW_ZONE> WHERE id=<ID>;\n\n"
            "  -- Log the transfer\n"
            "  INSERT INTO health_records\n"
            "    (animal_id,date,diagnosis,status,notes)\n"
            "  VALUES(<ID>,CURDATE(),'Zone transfer','Healthy','via T1');\n\n"
            "COMMIT; -- Both rows permanent"
        ),
        "T2 – Medicine Rollback (ROLLBACK)": (
            "START TRANSACTION;\n"
            "  UPDATE medicines SET stock=stock-50 WHERE id=<ID>;\n"
            "  -- Mid-txn SELECT shows deducted value\n"
            "  SELECT stock FROM medicines WHERE id=<ID>;\n"
            "  -- Mistake detected!\n"
            "ROLLBACK; -- Stock restored to original"
        ),
        "T3 – Conflicting Transactions": (
            "-- SESSION A locks the row:\n"
            "START TRANSACTION;\n"
            "  UPDATE animals SET health='Sick' WHERE id=<ID>;\n"
            "  -- Row is now LOCKED by Session A\n\n"
            "-- SESSION B tries same row (BLOCKED):\n"
            "START TRANSACTION;\n"
            "  SET innodb_lock_wait_timeout=3;\n"
            "  UPDATE animals SET health='Critical' WHERE id=<ID>;\n"
            "  -- ERROR 1205: Lock wait timeout exceeded\n\n"
            "-- Session A commits, lock released:\n"
            "COMMIT;"
        ),
        "T4 – Savepoint (Partial Rollback)": (
            "START TRANSACTION;\n"
            "  INSERT INTO health_records(...) VALUES(...);\n"
            "  SAVEPOINT sp1;  -- checkpoint\n\n"
            "  UPDATE animals SET weight_kg=9999 WHERE id=<ID>;\n"
            "  -- Oops! Wrong value\n"
            "  ROLLBACK TO SAVEPOINT sp1;\n"
            "  -- weight_kg change undone, health_record kept\n\n"
            "COMMIT; -- Only INSERT committed"
        ),
        "T5 – Cascading Rollback (3-step)": (
            "START TRANSACTION;\n"
            "  -- Step 1: Update animal zone\n"
            "  UPDATE animals SET zone_id=<Z2> WHERE id=<ID>;\n\n"
            "  -- Step 2: Deduct medicine stock\n"
            "  UPDATE medicines SET stock=stock-10 WHERE id=<MID>;\n\n"
            "  -- Step 3: Insert feeding note\n"
            "  INSERT INTO health_records(...) VALUES(...);\n\n"
            "  -- Error detected mid-way!\n"
            "ROLLBACK; -- ALL 3 steps undone atomically"
        ),
    }

    LOG_COLS   = ("no","txn","action","detail","result","time")
    LOG_HEADS  = ("#","Transaction","Action","Detail","Result","Time")
    LOG_WIDTHS = (30,155,130,260,95,100)

    def __init__(self, parent, db):
        super().__init__(parent, bg=BG_MID)
        self.db = db
        self._log_rows = []
        self._build()

    # ── UI ──────────────────────────────────────────────────────────
    def _build(self):
        tb = tk.Frame(self, bg=BG_DARK, pady=6, padx=10)
        tb.pack(fill="x")
        make_label(tb, "🔄  DB Transactions & Effects (Task 6)",
                   size=13, bold=True, bg=BG_DARK).pack(side="left")
        StyledButton(tb, "🗑 Clear Log",    self._clear_log,   BTN_RED ).pack(side="right", padx=4)
        StyledButton(tb, "🔄 Refresh View", self._refresh_db_view, BTN_ORG).pack(side="right", padx=4)

        # ── Three-column layout ───────────────────────────────────────
        main = tk.Frame(self, bg=BG_MID)
        main.pack(fill="both", expand=True, padx=6, pady=6)
        main.columnconfigure(0, weight=2)  # buttons + SQL
        main.columnconfigure(1, weight=3)  # execution log
        main.columnconfigure(2, weight=2)  # DB effects
        main.rowconfigure(0, weight=1)

        # ── Column 0: demo buttons + SQL viewer ──────────────────────
        left = tk.Frame(main, bg=BG_MID)
        left.grid(row=0, column=0, sticky="nsew", padx=(0,4))

        make_label(left, "  Transaction Demos", size=10,
                   bold=True, color=ACCENT).pack(anchor="w", pady=(0,4))

        bf = tk.Frame(left, bg=BG_MID)
        bf.pack(fill="x")
        bf.columnconfigure(0, weight=1)
        bf.columnconfigure(1, weight=1)

        demos = [
            ("T1\nAnimal Transfer\n(COMMIT)",       self._run_t1, BTN_GREEN),
            ("T2\nMedicine Stock\n(ROLLBACK)",       self._run_t2, BTN_RED),
            ("T3\nConflicting\nTransactions",        self._run_t3, BTN_ORG),
            ("T4\nSavepoint\n(Partial Rollback)",    self._run_t4, BTN_BLUE),
            ("T5\nCascading\nRollback (3-step)",     self._run_t5, "#8E44AD"),
        ]
        for i, (lbl, cmd, color) in enumerate(demos):
            r, c = divmod(i, 2)
            bf.rowconfigure(r, weight=1)
            tk.Button(bf, text=lbl, command=cmd,
                      bg=color, fg="white",
                      font=("Segoe UI", 8, "bold"),
                      relief="flat", bd=0, padx=6, pady=10,
                      cursor="hand2", wraplength=130, justify="center"
                      ).grid(row=r, column=c, padx=3, pady=3, sticky="nsew")

        make_label(left, "  SQL Preview", size=9,
                   bold=True, color=TEXT_SUB).pack(anchor="w", pady=(8,2))
        self.sql_sel = make_combo(left, list(self.TXNS.keys()), width=36)
        self.sql_sel.pack(fill="x", pady=(0,3))
        self.sql_sel.bind("<<ComboboxSelected>>", self._update_sql)
        self.sql_sel.current(0)

        sf = tk.Frame(left, bg=BG_CARD)
        sf.pack(fill="both", expand=True)
        self.sql_txt = tk.Text(sf, bg=BG_CARD, fg=TEXT_MAIN,
                               font=("Courier New", 8), wrap="none",
                               relief="flat", bd=4)
        sy = ttk.Scrollbar(sf, orient="vertical",   command=self.sql_txt.yview)
        sx = ttk.Scrollbar(sf, orient="horizontal", command=self.sql_txt.xview)
        self.sql_txt.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        sy.pack(side="right", fill="y"); sx.pack(side="bottom", fill="x")
        self.sql_txt.pack(fill="both", expand=True)
        self._update_sql()

        # ── Column 1: execution log ───────────────────────────────────
        mid = tk.Frame(main, bg=BG_MID)
        mid.grid(row=0, column=1, sticky="nsew", padx=4)

        mhdr = tk.Frame(mid, bg=BG_MID)
        mhdr.pack(fill="x")
        make_label(mhdr, "  Execution Log", size=10,
                   bold=True, color=ACCENT).pack(side="left")
        self.summary_var = tk.StringVar(value="")
        tk.Label(mhdr, textvariable=self.summary_var, bg=BG_MID,
                 fg=TEXT_SUB, font=("Segoe UI", 8)).pack(side="right")

        self.log_tree = make_tree(mid, self.LOG_COLS, self.LOG_HEADS, self.LOG_WIDTHS)
        self.log_tree.tag_configure("COMMITTED",   foreground="#2ECC71")
        self.log_tree.tag_configure("ROLLED BACK", foreground=ACCENT2)
        self.log_tree.tag_configure("CONFLICT",    foreground=ACCENT3)
        self.log_tree.tag_configure("SAVEPOINT",   foreground=ACCENT)
        self.log_tree.tag_configure("ERROR",       foreground=ACCENT2)
        self.log_tree.tag_configure("STEP OK",     foreground=TEXT_SUB)

        # ── Column 2: DB effects (BEFORE / AFTER) ───────────────────
        right = tk.Frame(main, bg=BG_MID)
        right.grid(row=0, column=2, sticky="nsew", padx=(4,0))

        make_label(right, "  DB Effects (Before / After)", size=10,
                   bold=True, color=ACCENT).pack(anchor="w", pady=(0,4))

        self.effects_txt = tk.Text(right, bg=BG_CARD, fg=TEXT_MAIN,
                                   font=("Courier New", 8), wrap="none",
                                   relief="flat", bd=6)
        sey = ttk.Scrollbar(right, orient="vertical",   command=self.effects_txt.yview)
        sex = ttk.Scrollbar(right, orient="horizontal", command=self.effects_txt.xview)
        self.effects_txt.configure(yscrollcommand=sey.set, xscrollcommand=sex.set)
        sey.pack(side="right", fill="y"); sex.pack(side="bottom", fill="x")
        self.effects_txt.pack(fill="both", expand=True)
        self.effects_txt.insert("1.0",
            "Run a transaction demo\nto see BEFORE / AFTER\nDB state here.")
        self.effects_txt.config(state="disabled")

    # ── Helpers ─────────────────────────────────────────────────────
    def _update_sql(self, *_):
        sql = self.TXNS.get(self.sql_sel.get(), "")
        self.sql_txt.config(state="normal")
        self.sql_txt.delete("1.0","end")
        self.sql_txt.insert("1.0", sql)
        for kw,col in [("START TRANSACTION",ACCENT),("COMMIT","#2ECC71"),
                        ("ROLLBACK",ACCENT2),("SAVEPOINT",ACCENT3),
                        ("UPDATE","#3498DB"),("INSERT","#9B59B6"),
                        ("SELECT","#1ABC9C")]:
            pos = "1.0"
            while True:
                p = self.sql_txt.search(kw, pos, stopindex="end")
                if not p: break
                e = p+"+"+str(len(kw))+"c"
                self.sql_txt.tag_add(kw,p,e)
                self.sql_txt.tag_config(kw,foreground=col,
                                        font=("Courier New",8,"bold"))
                pos = e
        self.sql_txt.config(state="disabled")

    def _log(self, txn, action, detail, status):
        n = len(self._log_rows)+1
        t = datetime.now().strftime("%H:%M:%S")
        self._log_rows.append((n,txn,action,detail,status,t))
        self.log_tree.insert("","0",values=(n,txn,action,detail,status,t),tags=(status,))
        c = sum(1 for r in self._log_rows if r[4]=="COMMITTED")
        rb= sum(1 for r in self._log_rows if r[4]=="ROLLED BACK")
        self.summary_var.set("Total:"+str(len(self._log_rows))
                             +"  Committed:"+str(c)+"  Rolled:"+str(rb))

    def _clear_log(self):
        self._log_rows.clear()
        for r in self.log_tree.get_children(): self.log_tree.delete(r)
        self.summary_var.set("")

    def _show_effects(self, text):
        self.effects_txt.config(state="normal")
        self.effects_txt.delete("1.0","end")
        self.effects_txt.insert("1.0", text)
        self.effects_txt.config(state="disabled")

    def _refresh_db_view(self):
        try:
            animals  = self.db.fetchall(
                "SELECT id,name,health,zone_id FROM animals ORDER BY id LIMIT 6")
            meds     = self.db.fetchall(
                "SELECT id,name,stock,min_stock FROM medicines ORDER BY id LIMIT 6")
            out = "=== CURRENT DB STATE ===\n\n"
            out += "-- animals (id|name|health|zone)\n"
            for r in animals:
                out += ("  "+str(r.get("id",""))+" | "+str(r.get("name",""))
                        +" | "+str(r.get("health",""))+" | "+str(r.get("zone_id",""))+"\n")
            out += "\n-- medicines (id|name|stock|min)\n"
            for r in meds:
                out += ("  "+str(r.get("id",""))+" | "+str(r.get("name",""))
                        +" | "+str(r.get("stock",""))+" | "+str(r.get("min_stock",""))+"\n")
            self._show_effects(out)
        except Exception as e:
            self._show_effects("Error reading DB:\n"+str(e))

    def _snapshot(self, animal_id=None, med_id=None):
        """Take a snapshot of key rows for BEFORE/AFTER display."""
        snap = {}
        if animal_id:
            r = self.db.fetchone(
                "SELECT id,name,health,zone_id,weight_kg FROM animals WHERE id=?",
                (animal_id,))
            snap["animal"] = dict(r) if r else {}
        if med_id:
            r = self.db.fetchone(
                "SELECT id,name,stock,min_stock FROM medicines WHERE id=?", (med_id,))
            snap["medicine"] = dict(r) if r else {}
        return snap

    def _fmt_snap(self, label, snap):
        lines = [label]
        if "animal" in snap:
            a = snap["animal"]
            lines.append("  Animal: "+str(a.get("name",""))
                         +" | health="+str(a.get("health",""))
                         +" | zone="+str(a.get("zone_id",""))
                         +" | weight="+str(a.get("weight_kg","")))
        if "medicine" in snap:
            m = snap["medicine"]
            lines.append("  Medicine: "+str(m.get("name",""))
                         +" | stock="+str(m.get("stock",""))
                         +" | min="+str(m.get("min_stock","")))
        return "\n".join(lines)

    # ── T1: Multi-table COMMIT ───────────────────────────────────────
    def _run_t1(self):
        animal = self.db.fetchone("SELECT id,name,zone_id,health FROM animals LIMIT 1")
        zones  = self.db.fetchall("SELECT id FROM zones LIMIT 2")
        if not animal or len(zones) < 2:
            messagebox.showwarning("No Data","Need 1+ animals and 2+ zones."); return

        aid      = animal["id"]
        aname    = animal["name"]
        old_zone = animal["zone_id"]
        new_zone = zones[1]["id"] if zones[0]["id"]==old_zone else zones[0]["id"]

        before = self._snapshot(animal_id=aid)
        self.db.reset_conn()
        conn = self.db.conn
        try:
            conn.start_transaction()
            cur = conn.cursor()

            cur.execute("UPDATE animals SET zone_id=%s WHERE id=%s",(new_zone,aid))
            self._log("T1 COMMIT","UPDATE animals",
                      "zone "+str(old_zone)+" → "+str(new_zone),"STEP OK")

            cur.execute(
                "INSERT INTO health_records"
                " (animal_id,staff_id,date,diagnosis,status,notes)"
                " VALUES(%s,NULL,CURDATE(),'Zone transfer','Healthy',%s)",
                (aid,"T1: moved zone "+str(old_zone)+" to "+str(new_zone)))
            self._log("T1 COMMIT","INSERT health_records",
                      "audit row for animal "+str(aid),"STEP OK")

            conn.commit(); cur.close()
            self._log("T1 COMMIT","COMMIT","Both steps permanent","COMMITTED")

            after = self._snapshot(animal_id=aid)
            self._show_effects(
                self._fmt_snap("BEFORE T1:",before)+"\n\n"
                +self._fmt_snap("AFTER  T1:",after)+"\n\n"
                +"Effect: zone_id changed from "+str(old_zone)+" to "
                +str(new_zone)+"\nHealth record auto-inserted."
            )
            messagebox.showinfo("T1 Committed",
                aname+" moved zone "+str(old_zone)+" → "+str(new_zone)
                +"\nUPDATE + INSERT both committed permanently.")
        except Exception as e:
            try: conn.rollback()
            except Exception: pass
            self._log("T1 COMMIT","ROLLBACK(err)",str(e)[:60],"ERROR")
            messagebox.showerror("T1 Error",str(e))

    # ── T2: Deliberate ROLLBACK ──────────────────────────────────────
    def _run_t2(self):
        med = self.db.fetchone(
            "SELECT id,name,stock FROM medicines WHERE stock>10 LIMIT 1")
        if not med:
            messagebox.showwarning("No Data","Need a medicine with stock>10."); return

        mid  = med["id"]; mname = med["name"]; orig = float(med["stock"])
        dose = 50.0
        before = self._snapshot(med_id=mid)
        self.db.reset_conn(); conn = self.db.conn
        try:
            conn.start_transaction()
            cur = conn.cursor(dictionary=True)
            cur.execute("UPDATE medicines SET stock=stock-%s WHERE id=%s",(dose,mid))
            self._log("T2 ROLLBACK","UPDATE medicines",
                      mname+": "+str(orig)+" - "+str(dose)+" = "+str(orig-dose),"STEP OK")
            cur.execute("SELECT stock FROM medicines WHERE id=%s",(mid,))
            mid_val = cur.fetchone()["stock"]
            self._log("T2 ROLLBACK","SELECT (mid-txn)",
                      "stock visible inside txn = "+str(mid_val),"STEP OK")
            conn.rollback(); cur.close()
            self._log("T2 ROLLBACK","ROLLBACK","All changes undone","ROLLED BACK")
            after = self._snapshot(med_id=mid)
            self._show_effects(
                self._fmt_snap("BEFORE T2:",before)+"\n\n"
                +"DURING TXN (not committed):\n"
                +"  stock was temporarily = "+str(mid_val)+"\n\n"
                +self._fmt_snap("AFTER  T2 (post ROLLBACK):",after)+"\n\n"
                +"Effect: stock is UNCHANGED at "+str(orig)
                +"\nROLLBACK fully undid the deduction."
            )
            messagebox.showinfo("T2 Rolled Back",
                mname+" stock:\n  Before: "+str(orig)
                +"\n  Mid-txn: "+str(mid_val)+" (deducted but NOT committed)"
                +"\n  After ROLLBACK: "+str(after.get("medicine",{}).get("stock",orig))
                +"\n\nROLLBACK restored original value.")
        except Exception as e:
            try: conn.rollback()
            except Exception: pass
            self._log("T2 ROLLBACK","ERROR",str(e)[:60],"ERROR")
            messagebox.showerror("T2 Error",str(e))

    # ── T3: Conflicting Transactions (Lock Conflict) ─────────────────
    def _run_t3(self):
        animal = self.db.fetchone(
            "SELECT id,name,health FROM animals LIMIT 1")
        if not animal:
            messagebox.showwarning("No Data","Need at least 1 animal."); return

        aid = animal["id"]; aname = animal["name"]; orig_h = animal["health"]
        before = self._snapshot(animal_id=aid)
        conn_b = None
        self.db.reset_conn(); conn_a = self.db.conn
        conflict_result = "Not tested"
        try:
            # Session A: lock the row
            conn_a.start_transaction()
            cur_a = conn_a.cursor()
            cur_a.execute("UPDATE animals SET health='Sick' WHERE id=%s",(aid,))
            self._log("T3 CONFLICT","SESSION A: UPDATE",
                      "health=Sick for id="+str(aid)+" — ROW LOCKED","CONFLICT")

            # Session B: try same row with short timeout
            conn_b = mysql.connector.connect(**DB_CONFIG)
            conn_b.autocommit = False
            conn_b.start_transaction()
            cur_b = conn_b.cursor()
            cur_b.execute("SET innodb_lock_wait_timeout=3")
            self._log("T3 CONFLICT","SESSION B: attempt",
                      "health=Critical for id="+str(aid)+" — WILL BLOCK","CONFLICT")
            try:
                cur_b.execute(
                    "UPDATE animals SET health='Critical' WHERE id=%s",(aid,))
                conn_b.commit()
                conflict_result = "Session B succeeded (lock released fast)"
            except Exception as lock_err:
                conn_b.rollback()
                conflict_result = "SESSION B BLOCKED/TIMED OUT: "+str(lock_err)[:60]
                self._log("T3 CONFLICT","SESSION B: BLOCKED",conflict_result,"CONFLICT")

            # Session A commits
            conn_a.commit(); cur_a.close()
            self._log("T3 CONFLICT","SESSION A: COMMIT",
                      "health=Sick committed","COMMITTED")

            after_conflict = self._snapshot(animal_id=aid)
            # Restore original health
            self.db.execute("UPDATE animals SET health=? WHERE id=?",(orig_h,aid))
            self._log("T3 CONFLICT","RESTORE",
                      "health restored to "+orig_h,"COMMITTED")
            after = self._snapshot(animal_id=aid)
            self._show_effects(
                self._fmt_snap("BEFORE T3:",before)+"\n\n"
                +"AFTER Session A committed:\n"
                +"  health = "+str(after_conflict.get("animal",{}).get("health","?"))+"\n\n"
                +"Session B result:\n  "+conflict_result+"\n\n"
                +self._fmt_snap("AFTER restore:",after)+"\n\n"
                +"Effect: InnoDB row-level locking prevented\n"
                +"concurrent conflicting writes."
            )
            messagebox.showinfo("T3 Conflict Demo",
                "Animal: "+aname+"\n"
                +"Session A: SET health=Sick → LOCKED ROW → COMMITTED\n"
                +"Session B: "+conflict_result+"\n\n"
                +"MySQL InnoDB handled the conflict via row-level locking.\n"
                +"Health restored to: "+orig_h)
        except Exception as e:
            try: conn_a.rollback()
            except Exception: pass
            self._log("T3 CONFLICT","ERROR",str(e)[:60],"ERROR")
            messagebox.showerror("T3 Error",str(e))
        finally:
            if conn_b:
                try: conn_b.close()
                except Exception: pass

    # ── T4: SAVEPOINT – Partial Rollback ────────────────────────────
    def _run_t4(self):
        animal = self.db.fetchone(
            "SELECT id,name,weight_kg,health FROM animals LIMIT 1")
        if not animal:
            messagebox.showwarning("No Data","Need at least 1 animal."); return

        aid   = animal["id"]; aname = animal["name"]; orig_w = animal["weight_kg"]
        before = self._snapshot(animal_id=aid)
        self.db.reset_conn(); conn = self.db.conn
        try:
            conn.start_transaction()
            cur = conn.cursor(dictionary=True)

            # Step 1: INSERT health record (KEEP)
            cur.execute(
                "INSERT INTO health_records"
                " (animal_id,staff_id,date,diagnosis,status,notes)"
                " VALUES(%s,NULL,CURDATE(),'Routine check','Healthy','T4 savepoint demo')",
                (aid,))
            self._log("T4 SAVEPOINT","INSERT health_records",
                      "animal_id="+str(aid)+" — health record added","STEP OK")

            cur.execute("SAVEPOINT sp_after_health")
            self._log("T4 SAVEPOINT","SAVEPOINT sp_after_health",
                      "Step 1 protected","SAVEPOINT")

            # Step 2: Bad weight (UNDO)
            cur.execute("UPDATE animals SET weight_kg=9999 WHERE id=%s",(aid,))
            cur.execute("SELECT weight_kg FROM animals WHERE id=%s",(aid,))
            bad_w = cur.fetchone()["weight_kg"]
            self._log("T4 SAVEPOINT","UPDATE weight (BAD)",
                      "weight="+str(bad_w)+" (mistake)","STEP OK")

            cur.execute("ROLLBACK TO SAVEPOINT sp_after_health")
            self._log("T4 SAVEPOINT","ROLLBACK TO SAVEPOINT",
                      "weight change undone","ROLLED BACK")

            conn.commit(); cur.close()
            self._log("T4 SAVEPOINT","COMMIT","Step 1 (health rec) kept","COMMITTED")

            after = self._snapshot(animal_id=aid)
            hr = self.db.fetchone(
                "SELECT id FROM health_records"
                " WHERE animal_id=? AND notes='T4 savepoint demo'",
                (aid,))
            self._show_effects(
                self._fmt_snap("BEFORE T4:",before)+"\n\n"
                +"DURING TXN (not yet committed):\n"
                +"  weight was temporarily = "+str(bad_w)+"\n\n"
                +self._fmt_snap("AFTER  T4:",after)+"\n\n"
                +"Effect: weight_kg = "+str(after.get("animal",{}).get("weight_kg","?"))
                +" (original preserved)\n"
                +"health_records row id="+str(hr["id"] if hr else "?")+
                " was committed.\nBad weight undone via SAVEPOINT."
            )
            messagebox.showinfo("T4 Savepoint",
                "Animal: "+aname+"\n"
                +"Step 1 (INSERT health_records) → COMMITTED\n"
                +"Step 2 (weight=9999)           → ROLLED BACK via SAVEPOINT\n\n"
                +"Final weight: "+str(after.get("animal",{}).get("weight_kg",orig_w))
                +" (original preserved)")
        except Exception as e:
            try: conn.rollback()
            except Exception: pass
            self._log("T4 SAVEPOINT","ERROR",str(e)[:60],"ERROR")
            messagebox.showerror("T4 Error",str(e))

    # ── T5: 3-step Cascading ROLLBACK ───────────────────────────────
    def _run_t5(self):
        animal = self.db.fetchone("SELECT id,name,zone_id,health FROM animals LIMIT 1")
        med    = self.db.fetchone("SELECT id,name,stock FROM medicines WHERE stock>15 LIMIT 1")
        zones  = self.db.fetchall("SELECT id FROM zones LIMIT 2")
        if not animal or not med or len(zones)<2:
            messagebox.showwarning("No Data",
                "Need 1+ animals, 2+ zones, 1+ medicine with stock>15."); return

        aid      = animal["id"]; aname = animal["name"]; orig_zone = animal["zone_id"]
        mid      = med["id"];  mname = med["name"];  orig_stock = float(med["stock"])
        new_zone = zones[1]["id"] if zones[0]["id"]==orig_zone else zones[0]["id"]

        before_a = self._snapshot(animal_id=aid)
        before_m = self._snapshot(med_id=mid)
        self.db.reset_conn(); conn = self.db.conn
        try:
            conn.start_transaction()
            cur = conn.cursor(dictionary=True)

            # Step 1
            cur.execute("UPDATE animals SET zone_id=%s WHERE id=%s",(new_zone,aid))
            self._log("T5 CASCADE","STEP 1: UPDATE animals",
                      "zone "+str(orig_zone)+"→"+str(new_zone),"STEP OK")

            # Step 2
            cur.execute("UPDATE medicines SET stock=stock-10 WHERE id=%s",(mid,))
            cur.execute("SELECT stock FROM medicines WHERE id=%s",(mid,))
            mid_stock = cur.fetchone()["stock"]
            self._log("T5 CASCADE","STEP 2: UPDATE medicines",
                      mname+" stock: "+str(orig_stock)+"→"+str(mid_stock),"STEP OK")

            # Step 3: Insert health note
            cur.execute(
                "INSERT INTO health_records"
                " (animal_id,staff_id,date,diagnosis,status,notes)"
                " VALUES(%s,NULL,CURDATE(),'T5 cascade test','Healthy','Step 3 of T5')",
                (aid,))
            self._log("T5 CASCADE","STEP 3: INSERT health_records",
                      "audit row for animal "+str(aid),"STEP OK")

            # Simulate error — force rollback of ALL 3 steps
            self._log("T5 CASCADE","ERROR DETECTED",
                      "Simulated error mid-transaction","ERROR")
            conn.rollback(); cur.close()
            self._log("T5 CASCADE","ROLLBACK (all 3 steps)",
                      "Zone, stock, health_record ALL undone","ROLLED BACK")

            after_a = self._snapshot(animal_id=aid)
            after_m = self._snapshot(med_id=mid)
            self._show_effects(
                "=== T5 CASCADE ROLLBACK ===\n\n"
                +self._fmt_snap("ANIMAL BEFORE:",before_a)+"\n"
                +self._fmt_snap("ANIMAL AFTER: ",after_a)+"\n"
                +"→ zone_id unchanged: "+str(after_a.get("animal",{}).get("zone_id","?"))+"\n\n"
                +self._fmt_snap("MEDICINE BEFORE:",before_m)+"\n"
                +self._fmt_snap("MEDICINE AFTER: ",after_m)+"\n"
                +"→ stock unchanged: "+str(after_m.get("medicine",{}).get("stock","?"))+"\n\n"
                +"health_records INSERT → UNDONE\n\n"
                +"ALL 3 steps rolled back atomically.\n"
                +"DB is exactly as it was before T5."
            )
            messagebox.showinfo("T5 Cascading Rollback",
                "3 steps executed inside one transaction:\n"
                "  Step 1: UPDATE animals zone\n"
                "  Step 2: UPDATE medicines stock\n"
                "  Step 3: INSERT health_records\n\n"
                "Error detected → ROLLBACK\n\n"
                "All 3 steps UNDONE atomically.\n"
                "Check DB Effects panel to verify.")
        except Exception as e:
            try: conn.rollback()
            except Exception: pass
            self._log("T5 CASCADE","ERROR",str(e)[:60],"ERROR")
            messagebox.showerror("T5 Error",str(e))


# ════════════════════════════════════════════
#  ROLE-BASED ACCESS CONTROL
# ════════════════════════════════════════════
# ── Per-role tab access ──────────────────────────────────────────────────────
# General     : read-only explorer — can VIEW animals, zones, reports, feeding
# Healthcare  : medical staff  — can manage health, medicines, treatments
# Caretaker   : field staff    — can manage animals, zones, feeding, movements
# Admin       : full access    — everything including users, triggers, transactions
# ─────────────────────────────────────────────────────────────────────────────
ROLE_TABS = {
    "Admin": [
        "🐾  Animals", "🏥  Health", "💊  Medicines",
        "💉  Treatments", "🍖  Feeding", "🗺  Zones",
        "👤  Staff", "📊  Reports", "⚡  Triggers",
        "🔄  Transactions", "👥  Users",
    ],
    "Healthcare": [
        "🐾  Animals", "🏥  Health", "💊  Medicines",
        "💉  Treatments", "📊  Reports",
    ],
    "Caretaker": [
        "🐾  Animals", "🍖  Feeding", "🗺  Zones",
        "👤  Staff", "📊  Reports",
    ],
    "General": [
        "🐾  Animals", "🍖  Feeding", "🗺  Zones", "📊  Reports",
    ],
}

# Tabs that are READ-ONLY for certain roles (no Add/Edit/Delete buttons shown)
ROLE_READONLY = {
    "General":    ["🐾  Animals", "🍖  Feeding", "🗺  Zones", "📊  Reports"],
    "Healthcare": [],
    "Caretaker":  [],
    "Admin":      [],
}

ROLE_COLORS = {
    "Admin":      "#9B59B6",   # purple
    "Healthcare": "#2980B9",   # blue
    "Caretaker":  "#27AE60",   # green
    "General":    "#7F8C8D",   # grey
}

ROLE_DESCRIPTIONS = {
    "Admin":      "Full system access — manage everything including users & triggers",
    "Healthcare": "Medical access — health records, medicines, treatments",
    "Caretaker":  "Field access — animal care, zones, feeding, staff assignments",
    "General":    "Read-only explorer — browse wildlife data, no editing allowed",
}


# ════════════════════════════════════════════
#  LOGIN WINDOW
# ════════════════════════════════════════════
class LoginWindow(tk.Toplevel):
    def __init__(self, parent, db, on_success):
        super().__init__(parent)
        self.db         = db
        self.on_success = on_success
        self.title("Wildlife Sanctuary — Login")
        self.geometry("420x500")
        self.resizable(False, False)
        self.configure(bg=BG_DARK)
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 420) // 2
        y = (self.winfo_screenheight() - 500) // 2
        self.geometry(f"420x500+{x}+{y}")
        self.grab_set()
        self._build()

    def _build(self):
        # ── Logo / header ─────────────────────
        hdr = tk.Frame(self, bg=BG_DARK, pady=28)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🌿", bg=BG_DARK, fg=ACCENT,
                 font=("Segoe UI", 38)).pack()
        tk.Label(hdr, text="Wildlife Sanctuary", bg=BG_DARK, fg=ACCENT,
                 font=("Segoe UI", 18, "bold")).pack()
        tk.Label(hdr, text="Management System", bg=BG_DARK, fg=TEXT_SUB,
                 font=("Segoe UI", 10)).pack()

        # ── Login card ────────────────────────
        card = tk.Frame(self, bg=BG_MID, padx=30, pady=22)
        card.pack(fill="x", padx=30)

        tk.Label(card, text="Username", bg=BG_MID, fg=TEXT_SUB,
                 font=("Segoe UI", 9), anchor="w").pack(fill="x")
        self.user_e = tk.Entry(card, bg=BG_CARD, fg=TEXT_MAIN,
                               insertbackground=TEXT_MAIN,
                               font=("Segoe UI", 11), relief="flat", bd=6)
        self.user_e.pack(fill="x", pady=(2, 12))
        self.user_e.insert(0, "admin")

        tk.Label(card, text="Password", bg=BG_MID, fg=TEXT_SUB,
                 font=("Segoe UI", 9), anchor="w").pack(fill="x")
        self.pass_e = tk.Entry(card, bg=BG_CARD, fg=TEXT_MAIN,
                               insertbackground=TEXT_MAIN,
                               font=("Segoe UI", 11), relief="flat", bd=6,
                               show="●")
        self.pass_e.pack(fill="x", pady=(2, 4))

        self.err_var = tk.StringVar()
        tk.Label(card, textvariable=self.err_var, bg=BG_MID, fg=ACCENT2,
                 font=("Segoe UI", 9)).pack(fill="x", pady=(0, 10))

        tk.Button(card, text="  Login  ", command=self._login,
                  bg=ACCENT, fg=BG_DARK,
                  font=("Segoe UI", 11, "bold"),
                  relief="flat", bd=0, pady=10,
                  cursor="hand2").pack(fill="x")

        # ── Default accounts with role descriptions ──
        hint = tk.Frame(self, bg=BG_DARK, pady=10)
        hint.pack(fill="x", padx=30)
        tk.Label(hint, text="Default accounts & roles:",
                 bg=BG_DARK, fg=TEXT_SUB,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0,4))

        accounts = [
            ("admin",     "admin123",  "Admin",      "Full access — manage everything"),
            ("drsmith",   "health123", "Healthcare", "Medicines, treatments, health records"),
            ("john_care", "care123",   "Caretaker",  "Animals, zones, feeding, movements"),
            ("guest",     "guest123",  "General",    "View-only — browse wildlife data"),
        ]
        for uname, pwd, role, desc in accounts:
            color = ROLE_COLORS.get(role, TEXT_SUB)
            row = tk.Frame(hint, bg=BG_CARD, pady=3)
            row.pack(fill="x", pady=1)
            # Role badge
            tk.Label(row, text=" "+role+" ", bg=color, fg="white",
                     font=("Segoe UI", 7, "bold"), padx=4).pack(side="left", padx=(4,6))
            # Credentials
            tk.Label(row, text=uname+"/"+pwd,
                     bg=BG_CARD, fg=TEXT_MAIN,
                     font=("Courier New", 8)).pack(side="left")
            # Description
            tk.Label(row, text=desc+"  ",
                     bg=BG_CARD, fg=TEXT_SUB,
                     font=("Segoe UI", 7)).pack(side="right")

        self.user_e.bind("<Return>", lambda e: self.pass_e.focus())
        self.pass_e.bind("<Return>", lambda e: self._login())

    def _login(self):
        username = self.user_e.get().strip()
        password = self.pass_e.get().strip()
        if not username or not password:
            self.err_var.set("Please enter username and password.")
            return
        user = self.db.authenticate(username, password)
        if user:
            self.destroy()
            self.on_success(user)
        else:
            # Check if username exists at all (to give clearer feedback)
            try:
                exists = self.db.fetchone(
                    "SELECT id FROM users WHERE username=?", (username,))
            except Exception:
                exists = None
            if exists:
                self.err_var.set("Wrong password for " + username + ".")
            else:
                self.err_var.set("User '" + username + "' not found in database.")
            self.pass_e.delete(0, "end")

    def _cancel(self):
        self.master.destroy()


# ════════════════════════════════════════════
#  USER MANAGEMENT PANEL  (Admin only)
# ════════════════════════════════════════════
class UsersPanel(tk.Frame):
    COLS   = ("id", "username", "role", "full_name", "active", "created_at")
    HEADS  = ("ID", "Username", "Role", "Full Name", "Active", "Created At")
    WIDTHS = (40, 120, 110, 160, 60, 140)

    def __init__(self, parent, db):
        super().__init__(parent, bg=BG_MID)
        self.db = db
        self._build()

    def _build(self):
        tb = tk.Frame(self, bg=BG_DARK, pady=6, padx=10)
        tb.pack(fill="x")
        make_label(tb, "👥  User Management", size=13,
                   bold=True, bg=BG_DARK).pack(side="left")
        StyledButton(tb, "+ Add User",  self._add,    BTN_GREEN).pack(side="right", padx=4)
        StyledButton(tb, "✏ Edit",      self._edit,   BTN_BLUE ).pack(side="right", padx=4)
        StyledButton(tb, "🗑 Delete",   self._delete, BTN_RED  ).pack(side="right", padx=4)
        StyledButton(tb, "🔄 Refresh",  self.refresh, BTN_ORG  ).pack(side="right", padx=4)

        # Role access legend
        leg = tk.Frame(self, bg=BG_MID, pady=6, padx=14)
        leg.pack(fill="x")
        for role, desc in ROLE_DESCRIPTIONS.items():
            color = ROLE_COLORS.get(role, TEXT_SUB)
            tabs  = ROLE_TABS.get(role, [])
            ro    = ROLE_READONLY.get(role, [])
            row   = tk.Frame(leg, bg=BG_CARD, pady=3, padx=8)
            row.pack(side="left", padx=(0,6))
            tk.Label(row, text=" "+role+" ", bg=color, fg="white",
                     font=("Segoe UI", 8, "bold")).pack(side="left", padx=(0,6))
            access = "READ-ONLY" if ro else str(len(tabs))+" tabs (edit)"
            tk.Label(row, text=access, bg=BG_CARD, fg=TEXT_SUB,
                     font=("Segoe UI", 8)).pack(side="left")

        self.tree = make_tree(self, self.COLS, self.HEADS, self.WIDTHS)
        for role, color in ROLE_COLORS.items():
            self.tree.tag_configure(role, foreground=color)
        self.refresh()

    def refresh(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        for r in self.db.get_all_users():
            role   = r.get("role", "")
            active = "Yes" if r.get("active") else "No"
            self.tree.insert("", "end",
                values=(r.get("id",""), r.get("username",""), role,
                        r.get("full_name","") or "", active,
                        str(r.get("created_at",""))),
                tags=(role,))

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a user first.")
            return None
        return self.tree.item(sel[0])["values"][0]

    def _add(self):
        dlg = UserDialog(self, self.db)
        self.wait_window(dlg)
        self.refresh()

    def _edit(self):
        uid = self._selected_id()
        if uid:
            dlg = UserDialog(self, self.db, user_id=uid)
            self.wait_window(dlg)
            self.refresh()

    def _delete(self):
        uid = self._selected_id()
        if uid is None:
            return
        uname = self.tree.item(self.tree.selection()[0])["values"][1]
        if str(uname) == "admin":
            messagebox.showwarning("Protected", "Cannot delete the admin account.")
            return
        if messagebox.askyesno("Confirm", "Delete this user account?"):
            self.db.delete_user(uid)
            self.refresh()


class UserDialog(BaseDialog):
    def __init__(self, parent, db, user_id=None):
        super().__init__(parent,
                         "Add User" if not user_id else "Edit User",
                         height=400)
        self.db      = db
        self.user_id = user_id
        self._build()
        if user_id:
            self._load()

    def _build(self):
        f = self.body_frame
        f.columnconfigure(1, weight=1)
        self.uname_e    = make_entry(f)
        self.pass_e     = make_entry(f)
        self.fname_e    = make_entry(f)
        self.role_cb    = make_combo(f, ["Admin","Healthcare","Caretaker","General"])
        self.active_var = tk.IntVar(value=1)
        active_chk = tk.Checkbutton(
            f, text="Active", variable=self.active_var,
            bg=BG_MID, fg=TEXT_MAIN,
            selectcolor=BG_CARD, activebackground=BG_MID,
            font=("Segoe UI", 9))

        for i, (lbl, w) in enumerate([
            ("Username *", self.uname_e),
            ("Password *", self.pass_e),
            ("Full Name",  self.fname_e),
            ("Role *",     self.role_cb),
            ("Status",     active_chk),
        ]):
            self._row(lbl, w, i)
        self._btn_row("Save", self._save)

    def _load(self):
        r = self.db.fetchone("SELECT * FROM users WHERE id=?", (self.user_id,))
        if not r:
            return
        self.uname_e.insert(0, r.get("username", ""))
        self.pass_e.insert(0,  r.get("password", ""))
        self.fname_e.insert(0, r.get("full_name", "") or "")
        if r.get("role"):
            self.role_cb.set(r["role"])
        self.active_var.set(1 if r.get("active") else 0)

    def _save(self):
        username  = self.uname_e.get().strip()
        password  = self.pass_e.get().strip()
        full_name = self.fname_e.get().strip()
        role      = self.role_cb.get()
        active    = self.active_var.get()

        if not username or not password or not role:
            messagebox.showwarning(
                "Required", "Username, Password and Role are required.")
            return

        if self.user_id:
            ok, msg = self.db.update_user(
                self.user_id, username, password, role, full_name, active)
        else:
            ok, msg = self.db.add_user(username, password, role, full_name)

        if ok:
            self.destroy()
        else:
            messagebox.showerror("Error", msg)


class SanctuaryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🌿 Wildlife Sanctuary Management System")
        self.geometry("1200x750")
        self.minsize(900, 600)
        self.configure(bg=BG_DARK)
        self.withdraw()          # hide until login succeeds

        self.db           = Database()
        self.current_user = None
        self._setup_styles()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        LoginWindow(self, self.db, self._on_login_success)

    def _on_login_success(self, user):
        self.current_user = user
        self._build_ui()
        self.deiconify()

    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("Dark.Treeview",
            background=BG_CARD, foreground=TEXT_MAIN,
            rowheight=28, fieldbackground=BG_CARD,
            borderwidth=0, font=("Segoe UI", 9))
        style.configure("Dark.Treeview.Heading",
            background=BG_DARK, foreground=ACCENT,
            font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Dark.Treeview",
            background=[("selected", BG_MID)],
            foreground=[("selected", ACCENT)])
        style.map("Dark.Treeview.Heading",
            background=[("active", BG_MID)])

        style.configure("Dark.TCombobox",
            fieldbackground=BG_CARD, background=BG_CARD,
            foreground=TEXT_MAIN, selectbackground=BG_MID,
            arrowcolor=ACCENT)
        style.map("Dark.TCombobox",
            fieldbackground=[("readonly", BG_CARD)],
            foreground=[("readonly", TEXT_MAIN)])

        style.configure("TNotebook", background=BG_DARK, borderwidth=0)
        style.configure("TNotebook.Tab",
            background=BG_MID, foreground=TEXT_SUB,
            font=("Segoe UI", 10), padding=(14, 8), borderwidth=0)
        style.map("TNotebook.Tab",
            background=[("selected", BG_DARK)],
            foreground=[("selected", ACCENT)],
            expand=[("selected", [1, 1, 1, 0])])

        style.configure("TSeparator", background=BG_CARD)

    def _build_ui(self):
        role      = self.current_user.get("role", "")
        full_name = (self.current_user.get("full_name") or
                     self.current_user.get("username", ""))

        # ── Legacy role name fallback ─────────────────────────────
        # If the DB still has old role names (Veterinarian / Ranger)
        # because the ENUM migration hasn't been run yet, remap them
        # so the user still gets access to the correct tabs.
        ROLE_LEGACY = {
            "Veterinarian": "Healthcare",
            "Ranger":        "Caretaker",
        }
        if role in ROLE_LEGACY:
            role = ROLE_LEGACY[role]

        role_color = ROLE_COLORS.get(role, TEXT_SUB)

        # ── Header ───────────────────────────────
        header = tk.Frame(self, bg=BG_DARK, pady=10, padx=20)
        header.pack(fill="x")
        tk.Label(header, text="🌿  Wildlife Sanctuary Management System",
                 bg=BG_DARK, fg=ACCENT,
                 font=("Segoe UI", 15, "bold")).pack(side="left")
        tk.Label(header,
                 text="  " + datetime.now().strftime("%B %d, %Y"),
                 bg=BG_DARK, fg=TEXT_SUB,
                 font=("Segoe UI", 9)).pack(side="left")

        # User badge + logout (right side)
        uf = tk.Frame(header, bg=BG_DARK)
        uf.pack(side="right")
        tk.Label(uf, text=full_name, bg=BG_DARK, fg=TEXT_MAIN,
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 6))
        tk.Label(uf, text="[" + role + "]",
                 bg=role_color, fg="white",
                 font=("Segoe UI", 8, "bold"),
                 padx=8, pady=2).pack(side="left", padx=(0, 10))
        tk.Button(uf, text="⏻ Logout",
                  command=self._logout,
                  bg=BTN_RED, fg="white",
                  font=("Segoe UI", 8, "bold"),
                  relief="flat", bd=0, padx=8, pady=4,
                  cursor="hand2").pack(side="left")

        ttk.Separator(self, orient="horizontal").pack(fill="x")

        # ── Role-filtered tabs ────────────────────
        nb = ttk.Notebook(self, style="TNotebook")
        nb.pack(fill="both", expand=True)

        all_tabs = [
            ("🐾  Animals",      AnimalsPanel),
            ("🏥  Health",       HealthPanel),
            ("💊  Medicines",    MedicinePanel),
            ("💉  Treatments",   TreatmentPanel),
            ("🍖  Feeding",      FeedingPanel),
            ("🗺  Zones",        ZonesPanel),
            ("👤  Staff",        StaffPanel),
            ("📊  Reports",      ReportsPanel),
            ("⚡  Triggers",     TriggersPanel),
            ("🔄  Transactions", TransactionsPanel),
            ("👥  Users",        UsersPanel),
        ]
        allowed  = ROLE_TABS.get(role, [])
        readonly = ROLE_READONLY.get(role, [])
        for label, cls in all_tabs:
            if label.strip() in allowed:
                is_ro = label.strip() in readonly
                try:
                    panel = cls(nb, self.db, readonly=is_ro)
                except TypeError:
                    panel = cls(nb, self.db)
                nb.add(panel, text="  " + label + "  ")

        # ── Status bar ────────────────────────────
        db_info = (DB_CONFIG["user"] + "@" + DB_CONFIG["host"] +
                   ":" + str(DB_CONFIG["port"]) + "/" + DB_CONFIG["database"])
        tk.Label(self,
                 text="Connected  •  MySQL  •  " + db_info +
                      "  •  " + full_name + " (" + role + ")",
                 bg=BG_DARK, fg=TEXT_SUB,
                 font=("Segoe UI", 8), anchor="w", pady=4, padx=10
                 ).pack(fill="x", side="bottom")

    def _logout(self):
        if not messagebox.askyesno("Logout", "Log out and return to login screen?"):
            return
        for widget in self.winfo_children():
            self._stop_polling_recursive(widget)
            widget.destroy()
        self.current_user = None
        LoginWindow(self, self.db, self._on_login_success)

    def _on_close(self):
        # Stop all polling loops before closing
        for widget in self.winfo_children():
            self._stop_polling_recursive(widget)
        self.db.close()
        self.destroy()

    def _stop_polling_recursive(self, widget):
        if hasattr(widget, "_stop_polling"):
            widget._stop_polling()
        for child in widget.winfo_children():
            self._stop_polling_recursive(child)


# ════════════════════════════════════════════
#  ENTRY POINT
# ════════════════════════════════════════════
if __name__ == "__main__":
    app = SanctuaryApp()
    app.mainloop()
