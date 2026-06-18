import cv2
import face_recognition
import pickle
import numpy as np
from datetime import datetime
from db_config import get_connection

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

def mark_checkin(emp_id, name):
    conn = get_connection()
    cursor = conn.cursor()

    today = datetime.now().strftime('%Y-%m-%d')
    now_time = datetime.now().strftime('%I:%M %p')
    
    # Check if check-in is after 10:45
    current_hour = datetime.now().hour
    current_minute = datetime.now().minute
    is_after_1045 = (current_hour > 10) or (current_hour == 10 and current_minute > 45)
    
    # Set status: 1 for normal, 2 for "other" (after 10:45)
    status = 2 if is_after_1045 else 1
    # Set type: "other" for late check-in, "face_recognition" for normal
    att_type = "Other" if is_after_1045 else "face_recognition"

    cursor.execute("""
        SELECT id FROM attendances 
        WHERE employee_id=%s AND date=%s
    """, (emp_id, today))

    if cursor.fetchone():
        print(f"  {name} aaj already present hai!")
    else:
        cursor.execute("""
            INSERT INTO attendances (date, employee_id, checkin, status, type)
            VALUES (%s, %s, %s, %s, %s)
        """, (today, emp_id, now_time, status, att_type))
        conn.commit()
        status_text = "Other (after 10:45)" if is_after_1045 else "Present"
        print(f"  ✓ {name} - Checkin: {now_time} - Status: {status_text}")

    conn.close()

def run_attendance():
    print("Database se faces load ho rahe hain...")
    known_encodings, known_info = load_known_faces()
    print(f"{len(known_info)} employees loaded.\n")
    print("Camera shuru ho raha hai... 'q' dabao band karne ke liye.\n")

    cam = cv2.VideoCapture(0)
    marked_today = set()

    while True:
        ret, frame = cam.read()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        locations = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, locations)

        for enc, loc in zip(encodings, locations):
            matches = face_recognition.compare_faces(known_encodings, enc, tolerance=0.5)
            distances = face_recognition.face_distance(known_encodings, enc)

            label = "Unknown"
            color = (0, 0, 255)

            if True in matches:
                best = np.argmin(distances)
                if matches[best]:
                    emp_id, name = known_info[best]
                    label = name
                    color = (0, 255, 0)
                    if emp_id not in marked_today:
                        mark_checkin(emp_id, name)
                        marked_today.add(emp_id)

            top, right, bottom, left = loc
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, label, (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.imshow("Attendance System - q to quit", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows() 
import cv2
import face_recognition
import pickle
import numpy as np
from datetime import datetime
from db_config import get_connection

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

def open_camera():
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        cam = cv2.VideoCapture(1)
    return cam

# ─── CHECKIN ───────────────────────────────────────
def run_checkin():
    print("Database se faces load ho rahe hain...")
    known_encodings, known_info = load_known_faces()
    print(f"{len(known_info)} employees loaded.")
    print("Camera shuru ho raha hai... 'q' dabao band karne ke liye.\n")

    cam = open_camera()
    marked = set()

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, locations)

        for enc, loc in zip(encodings, locations):
            matches = face_recognition.compare_faces(known_encodings, enc, tolerance=0.5)
            distances = face_recognition.face_distance(known_encodings, enc)

            label = "Unknown"
            color = (0, 0, 255)
            status = ""

            if True in matches:
                best = np.argmin(distances)
                if matches[best]:
                    emp_id, name = known_info[best]
                    label = name
                    color = (0, 255, 0)

                    if emp_id not in marked:
                        today = datetime.now().strftime('%Y-%m-%d')
                        now_time = datetime.now().strftime('%H:%M:%S')

                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT id FROM attendances 
                            WHERE employee_id=%s AND date=%s
                        """, (emp_id, today))

                        if cursor.fetchone():
                            status = "Pehle se Checkin hai!"
                            color = (0, 255, 255)
                        else:
                            cursor.execute("""
                                INSERT INTO attendances 
                                (date, employee_id, checkin, status, type ,note)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (today, emp_id, now_time, 1, 'Present' , 'face_recognition'))
                            conn.commit()
                            status = f"CHECKIN: {now_time}"
                            print(f"  ✓ {name} - Checkin: {now_time}")
                        conn.close()
                        marked.add(emp_id)
                    else:
                        status = "Checkin Ho Gaya!"

            top, right, bottom, left = loc
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom), (right, bottom + 25), color, -1)
            cv2.putText(frame, label, (left + 4, bottom + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            if status:
                cv2.putText(frame, status, (left, top - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        cv2.putText(frame, "CHECKIN MODE | q = Quit", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("Attendance - Checkin", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()

# ─── CHECKOUT ──────────────────────────────────────
def run_checkout():
    print("Database se faces load ho rahe hain...")
    known_encodings, known_info = load_known_faces()
    print(f"{len(known_info)} employees loaded.")
    print("Camera shuru ho raha hai... 'q' dabao band karne ke liye.\n")

    cam = open_camera()
    marked = set()

    while True:
        ret, frame = cam.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb)
        encodings = face_recognition.face_encodings(rgb, locations)

        for enc, loc in zip(encodings, locations):
            matches = face_recognition.compare_faces(known_encodings, enc, tolerance=0.5)
            distances = face_recognition.face_distance(known_encodings, enc)

            label = "Unknown"
            color = (0, 0, 255)
            status = ""

            if True in matches:
                best = np.argmin(distances)
                if matches[best]:
                    emp_id, name = known_info[best]
                    label = name
                    color = (255, 165, 0)

                    if emp_id not in marked:
                        today = datetime.now().strftime('%Y-%m-%d')
                        now_time = datetime.now().strftime('%H:%M:%S')

                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT id, checkin, checkout FROM attendances 
                            WHERE employee_id=%s AND date=%s
                        """, (emp_id, today))
                        record = cursor.fetchone()

                        if not record:
                            status = "Pehle Checkin karo!"
                            color = (0, 0, 255)
                        elif record[2]:
                            status = f"Checkout Ho Chuka: {record[2]}"
                            color = (0, 255, 255)
                        else:
                            cursor.execute("""
                                UPDATE attendances SET checkout=%s 
                                WHERE id=%s
                            """, (now_time, record[0]))
                            conn.commit()
                            status = f"CHECKOUT: {now_time}"
                            print(f"  ✓ {name} - Checkout: {now_time}")
                        conn.close()
                        marked.add(emp_id)
                    else:
                        status = "Checkout Ho Gaya!"

            top, right, bottom, left = loc
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom), (right, bottom + 25), color, -1)
            cv2.putText(frame, label, (left + 4, bottom + 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            if status:
                cv2.putText(frame, status, (left, top - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        cv2.putText(frame, "CHECKOUT MODE | q = Quit", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0), 2)
        cv2.imshow("Attendance - Checkout", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()
