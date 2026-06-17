import tkinter as tk
from tkinter import messagebox
import cv2
import face_recognition
import pickle
import numpy as np
from datetime import datetime
from db_config import get_connection
from PIL import Image, ImageTk
import threading

BG      = "#1a1a2e"
CARD    = "#16213e"
GREEN   = "#00b894"
ORANGE  = "#e17055"
BLUE    = "#0984e3"
WHITE   = "#ffffff"
GRAY    = "#636e72"
RED     = "#d63031"
YELLOW  = "#fdcb6e"

FONT_TITLE  = ("Arial", 28, "bold")
FONT_BTN    = ("Arial", 16, "bold")
FONT_STATUS = ("Arial", 15)
FONT_SMALL  = ("Arial", 11)
FONT_INFO   = ("Arial", 13, "bold")

def open_camera():
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cam.isOpened():
        cam = cv2.VideoCapture(1, cv2.CAP_DSHOW)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cam.set(cv2.CAP_PROP_FPS, 30)
    return cam

def load_known_faces():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, face_encoding
        FROM employees
        WHERE face_encoding IS NOT NULL AND is_active = 1
    """)
    rows = cursor.fetchall()
    conn.close()
    encodings, info = [], []
    for emp_id, name, blob in rows:
        encodings.append(pickle.loads(blob))
        info.append((emp_id, name))
    return encodings, info

class AttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Nivesh Mangal Attendance System")
        self.root.configure(bg=BG)
        self.root.attributes('-fullscreen', True)
        self.root.bind('<Escape>', lambda e: self.root.attributes('-fullscreen', False))
        self.root.bind('<F11>',    lambda e: self.root.attributes('-fullscreen', True))

        self.mode          = None
        self.cam           = None
        self.running       = False
        self.marked        = set()
        self.known_enc     = []
        self.known_info    = []
        self.enroll_list   = []
        self.enroll_idx    = 0
        self._loading_dots = 0
        self._keys_bound   = False

        self.status_var = tk.StringVar(value="Mode chuno — Checkin ya Checkout")
        self.info_var   = tk.StringVar(value="")

        self.build_ui()

    def build_ui(self):
        self.left = tk.Frame(self.root, bg=BG)
        self.left.pack(side="left", fill="both", expand=True, padx=(30, 10), pady=30)

        tk.Label(self.left, text="🏢  FACE ATTENDANCE SYSTEM",
                 font=FONT_TITLE, bg=BG, fg=WHITE).pack(anchor="w", pady=(0, 6))

        date_str = datetime.now().strftime("%A, %d %B %Y")
        tk.Label(self.left, text=date_str,
                 font=FONT_SMALL, bg=BG, fg=GRAY).pack(anchor="w", pady=(0, 10))

        self.canvas = tk.Canvas(self.left, bg="#0d0d1a",
                                highlightthickness=2,
                                highlightbackground=BLUE)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_text(320, 240,
            text="📷  Camera yahan dikhega\nCheckin / Checkout button dabao",
            fill=GRAY, font=("Arial", 16), justify="center")

        self.right = tk.Frame(self.root, bg=CARD, width=320)
        self.right.pack(side="right", fill="y", padx=(10, 30), pady=30)
        self.right.pack_propagate(False)

        self.clock_var = tk.StringVar()
        tk.Label(self.right, textvariable=self.clock_var,
                 font=("Arial", 32, "bold"), bg=CARD, fg=WHITE).pack(pady=(25, 0))
        self.update_clock()

        tk.Frame(self.right, bg=BLUE, height=2).pack(fill="x", padx=20, pady=12)

        tk.Label(self.right, text="STATUS", font=FONT_SMALL, bg=CARD, fg=GRAY).pack()
        self.status_label = tk.Label(self.right, textvariable=self.status_var,
                                     font=FONT_STATUS, bg=CARD, fg=WHITE,
                                     wraplength=270, justify="center")
        self.status_label.pack(pady=(4, 0))

        tk.Frame(self.right, bg=GRAY, height=1).pack(fill="x", padx=20, pady=12)

        tk.Label(self.right, text="LAST ACTION", font=FONT_SMALL, bg=CARD, fg=GRAY).pack()
        tk.Label(self.right, textvariable=self.info_var,
                 font=FONT_INFO, bg=CARD, fg=GREEN,
                 wraplength=270, justify="center").pack(pady=(4, 0))

        tk.Frame(self.right, bg=GRAY, height=1).pack(fill="x", padx=20, pady=16)

        self.make_btn(self.right, "✅  CHECKIN",     GREEN,  lambda: self.activate("checkin"))
        self.make_btn(self.right, "🚪  CHECKOUT",    ORANGE, lambda: self.activate("checkout"))
        self.make_btn(self.right, "➕  ENROLL",      BLUE,   lambda: self.activate("enroll"))

        tk.Frame(self.right, bg=GRAY, height=1).pack(fill="x", padx=20, pady=16)

        self.make_btn(self.right, "⏹  STOP CAMERA", GRAY, self.stop_camera)
        self.make_btn(self.right, "❌  EXIT",        RED,  self.confirm_exit)

    def make_btn(self, parent, text, color, cmd):
        btn = tk.Button(parent, text=text, font=FONT_BTN,
                        bg=color, fg=WHITE,
                        activebackground=color, activeforeground=WHITE,
                        relief="flat", cursor="hand2",
                        width=18, height=2, command=cmd)
        btn.pack(pady=6, padx=20)
        btn.bind("<Enter>", lambda e, b=btn, c=color: b.configure(bg=self.dk(c)))
        btn.bind("<Leave>", lambda e, b=btn, c=color: b.configure(bg=c))

    def dk(self, h):
        r = max(0, int(h[1:3], 16) - 25)
        g = max(0, int(h[3:5], 16) - 25)
        b = max(0, int(h[5:7], 16) - 25)
        return f"#{r:02x}{g:02x}{b:02x}"

    def update_clock(self):
        now = datetime.now()
        time_str = now.strftime("%I:%M:%S %p")  # 12-hour format with AM/PM
        self.clock_var.set(time_str)
        self.root.after(1000, self.update_clock)

    def set_status(self, msg, color=WHITE):
        self.status_var.set(msg)
        self.status_label.configure(fg=color)

    def _unbind_keys(self):
        self.root.unbind('s')
        self.root.unbind('k')
        self.root.unbind('q')
        self._keys_bound = False

    def _bind_keys(self):
        if not self._keys_bound:
            self.root.bind('s', lambda e: self._enroll_save())
            self.root.bind('k', lambda e: self._enroll_skip())
            self.root.bind('q', lambda e: self.stop_camera())
            self._keys_bound = True

    # ══════════════════════════════════════════════
    #  ACTIVATE
    # ══════════════════════════════════════════════
    def activate(self, mode):
        self.stop_camera()
        self.mode          = mode
        self.marked        = set()
        self.running       = True
        self.cam           = None
        self._loading_dots = 0

        if mode in ("checkin", "checkout"):
            self.set_status("Camera load ho raha hai...", BLUE)
            threading.Thread(target=self._load_and_start, daemon=True).start()
        else:
            self._start_enroll()

    def _load_and_start(self):
        self.root.after(0, self._show_loading)
        self.known_enc, self.known_info = load_known_faces()
        if not self.known_enc:
            self.set_status("Koi enrolled employee nahi!", RED)
            self.running = False
            return
        lbl = "CHECKIN" if self.mode == "checkin" else "CHECKOUT"
        self.set_status(f"{lbl} MODE — Camera chal raha hai",
                        GREEN if self.mode == "checkin" else ORANGE)
        self.cam = open_camera()
        self.root.after(0, self._camera_loop)

    def _show_loading(self):
        if not self.running:
            return
        self._loading_dots = (self._loading_dots + 1) % 4
        dot_str = "●" * self._loading_dots + "○" * (3 - self._loading_dots)
        cw = self.canvas.winfo_width() or 640
        ch = self.canvas.winfo_height() or 480
        cx, cy = cw // 2, ch // 2
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, cw, ch, fill="#0d0d1a", outline="")
        self.canvas.create_oval(cx-50, cy-50, cx+50, cy+50, outline="#6366f1", width=3)
        self.canvas.create_text(cx, cy, text=dot_str, fill="#6366f1", font=("Arial", 20))
        self.canvas.create_text(cx, cy+80, text="📷  Camera load ho raha hai...",
                                fill="#ffffff", font=("Arial", 14))
        self.canvas.create_text(cx, cy+110, text="Please wait",
                                fill="#94a3b8", font=("Arial", 11))
        if self.running and self.cam is None:
            self.root.after(300, self._show_loading)

    # ══════════════════════════════════════════════
    #  CAMERA LOOP
    # ══════════════════════════════════════════════
    def _camera_loop(self):
        if not self.running or self.cam is None:
            return
        ret, frame = self.cam.read()
        if not ret:
            self.root.after(30, self._camera_loop)
            return
        if self.mode in ("checkin", "checkout"):
            frame = self._process_frame(frame)
        else:
            frame = self._process_enroll_frame(frame)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw > 10 and ch > 10:
            img = img.resize((cw, ch), Image.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=imgtk)
        self.canvas._img = imgtk
        self.root.after(15, self._camera_loop)

    # ══════════════════════════════════════════════
    #  CHECKIN / CHECKOUT
    # ══════════════════════════════════════════════
    def _process_frame(self, frame):
        small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb   = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, locations)
        color_cv  = (0, 200, 100) if self.mode == "checkin" else (0, 140, 255)

        for enc, loc in zip(encodings, locations):
            top, right, bottom, left = [v * 2 for v in loc]
            matches   = face_recognition.compare_faces(self.known_enc, enc, tolerance=0.5)
            distances = face_recognition.face_distance(self.known_enc, enc)
            label, color, status = "Unknown", (0, 0, 220), ""

            if True in matches:
                best = np.argmin(distances)
                if matches[best]:
                    emp_id, name = self.known_info[best]
                    label, color = name, color_cv
                    if emp_id not in self.marked:
                        result = self._do_attendance(emp_id, name)
                        if result:
                            self.info_var.set(result)
                        self.marked.add(emp_id)
                    else:
                        status = "✓ Done"

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom-30), (right, bottom), color, -1)
            cv2.putText(frame, label, (left+5, bottom-8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
            if status:
                cv2.putText(frame, status, (left, top-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        mode_text  = "✅ CHECKIN MODE" if self.mode == "checkin" else "🚪 CHECKOUT MODE"
        text_color = (0, 220, 100) if self.mode == "checkin" else (0, 140, 255)
        cv2.putText(frame, mode_text, (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.9, text_color, 2)
        return frame

    def _do_attendance(self, emp_id, name):
        today    = datetime.now().strftime('%Y-%m-%d')
        now_time = datetime.now().strftime('%I:%M%p').lower()
        conn     = get_connection()
        cursor   = conn.cursor()
        result   = ""
        if self.mode == "checkin":
            cursor.execute("SELECT id FROM attendances WHERE employee_id=%s AND date=%s",
                           (emp_id, today))
            if cursor.fetchone():
                self.set_status(f"{name} pehle se checkin hai!", YELLOW)
            else:
                cursor.execute("""
                    INSERT INTO attendances (date, employee_id, checkin, status, type,note)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (today, emp_id, now_time, 1, 'Present','face_recognition'))
                conn.commit()
                result = f"✅ {name}\nCheckin: {now_time}"
                self.set_status(f"✅ {name} — Checkin: {now_time}", GREEN)
        else:
            cursor.execute("""
                SELECT id, checkin, checkout FROM attendances
                WHERE employee_id=%s AND date=%s
            """, (emp_id, today))
            record = cursor.fetchone()
            if not record:
                self.set_status(f"{name} ka checkin nahi hua!", RED)
            elif record[2]:
                self.set_status(f"{name} checkout ho chuka!", YELLOW)
            else:
                checkin_str = record[1]
                now_dt      = datetime.now()

                try:
                    parsed     = datetime.strptime(checkin_str.upper(), '%I:%M%p')
                    checkin_dt = parsed.replace(year=now_dt.year, month=now_dt.month, day=now_dt.day)
                    diff       = now_dt - checkin_dt
                    hours      = diff.total_seconds() / 3600.0
                except Exception:
                    hours = 0.0

                # ── Type logic ──────────────────────────────
                if hours < 2:
                    type_val = 'Came Late/ Left Early'
                elif 2 <= hours < 3:
                    type_val = 'Came Late/ Left Early'
                elif 3 <= hours < 5:
                    try:
                        checkin_hour = datetime.strptime(checkin_str.upper(), '%I:%M%p').hour
                        if checkin_hour < 14:      # 2 baje se pehle → First Half
                            type_val = 'First Half'
                        else:                      # 2 baje ke baad  → Second Half
                            type_val = 'Second Half'
                    except Exception:
                        type_val = 'First Half'
                elif 5 <= hours < 7:
                    type_val = 'Other'
                else:                              # 7+ hours
                    type_val = 'Present'
                # ────────────────────────────────────────────

                hrs  = int(hours)
                mins = int((hours - hrs) * 60)

                cursor.execute(
                    "UPDATE attendances SET checkout=%s, type=%s, note=%s WHERE id=%s",
                    (now_time, type_val, 'face_recognition', record[0])
                )
                conn.commit()
                result = f"🚪 {name}\nCheckout: {now_time}\nType: {type_val}\nHours: {hrs}h {mins}m"
                self.set_status(f"🚪 {name} — {type_val} ({hrs}h {mins}m)", ORANGE)
        conn.close()
        return result

    # ══════════════════════════════════════════════
    #  ENROLL
    # ══════════════════════════════════════════════
    def _start_enroll(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name FROM employees
            WHERE face_encoding IS NULL AND is_active = 1
        """)
        self.enroll_list = cursor.fetchall()
        conn.close()
        if not self.enroll_list:
            self.set_status("Sabka face enrolled hai!", GREEN)
            self.running = False
            return
        self.enroll_idx  = 0
        self._keys_bound = False
        self.cam = open_camera()
        self._next_enroll()

    def _next_enroll(self):
        if self.enroll_idx >= len(self.enroll_list):
            self.set_status("✅ Enrollment complete!", GREEN)
            self.stop_camera()
            return
        emp_id, name = self.enroll_list[self.enroll_idx]
        self.set_status(f"📷 {name} ka face capture karo\n's' = Save  |  'k' = Skip", BLUE)
        # Keys sirf ek baar bind karo
        self._unbind_keys()
        self._bind_keys()
        self.root.after(500, self._camera_loop)

    def _process_enroll_frame(self, frame):
        if self.enroll_idx >= len(self.enroll_list):
            return frame
        emp_id, name = self.enroll_list[self.enroll_idx]
        cv2.putText(frame, f"Employee: {name}", (10, 38),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        cv2.putText(frame, "s = Save  |  k = Skip  |  q = Quit", (10, 72),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
        # ⚠️ Yahan bind NAHI — _next_enroll mein hota hai
        return frame

    def _enroll_save(self):
        if not self.running or self.mode != "enroll" or self.cam is None:
            return
        self._unbind_keys()

        ret, frame = self.cam.read()
        if not ret:
            self.set_status("Frame nahi mili! Dobara try karo.", RED)
            self.root.after(500, self._next_enroll)
            return

        rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        encs = face_recognition.face_encodings(rgb)

        if not encs:
            self.set_status("Chehra nahi dikh raha! Adjust karo.", RED)
            self._bind_keys()
            return

        if len(encs) > 1:
            self.set_status("Ek se zyada chehra! Akele aao.", RED)
            self._bind_keys()
            return

        emp_id, name = self.enroll_list[self.enroll_idx]
        blob = pickle.dumps(encs[0])

        def save_to_db():
            conn = get_connection()
            cur  = conn.cursor()
            cur.execute("UPDATE employees SET face_encoding=%s WHERE id=%s", (blob, emp_id))
            conn.commit()
            conn.close()
            self.info_var.set(f"✅ {name} enrolled!")
            self.set_status(f"✅ {name} enrolled!", GREEN)
            self.enroll_idx += 1
            self.root.after(800, self._next_enroll)

        threading.Thread(target=save_to_db, daemon=True).start()

    def _enroll_skip(self):
        if not self.running or self.mode != "enroll":
            return
        self._unbind_keys()
        _, name = self.enroll_list[self.enroll_idx]
        self.set_status(f"{name} skip ho gaya.", GRAY)
        self.enroll_idx += 1
        self.root.after(800, self._next_enroll)

    # ══════════════════════════════════════════════
    #  STOP / EXIT
    # ══════════════════════════════════════════════
    def stop_camera(self):
        self.running = False
        self._unbind_keys()
        if self.cam:
            self.cam.release()
            self.cam = None
        self.mode = None
        self.canvas.delete("all")
        self.canvas.create_text(
            self.canvas.winfo_width() // 2 or 320,
            self.canvas.winfo_height() // 2 or 240,
            text="📷  Camera yahan dikhega\nCheckin / Checkout button dabao",
            fill=GRAY, font=("Arial", 16), justify="center"
        )
        self.status_var.set("Mode chuno — Checkin ya Checkout")

    def confirm_exit(self):
        if messagebox.askyesno("Exit", "Kya sach mein band karna hai?"):
            self.stop_camera()
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app  = AttendanceApp(root)
    root.mainloop()
