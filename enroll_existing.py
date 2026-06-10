import cv2
import face_recognition
import pickle
from db_config import get_connection

def enroll_existing_employees():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name 
        FROM employees 
        WHERE face_encoding IS NULL AND is_active = 1
    """)
    pending = cursor.fetchall()
    conn.close()

    if not pending:
        print("Sabka face capture ho chuka hai!")
        return

    print(f"{len(pending)} employees pending hain.\n")

    for (emp_id, name) in pending:
        print(f"\n>>> {name} (ID: {emp_id})")
        print("'s' = capture karo | 'k' = skip karo")

        cam = cv2.VideoCapture(0)

        while True:
            ret, frame = cam.read()
            cv2.putText(frame, f"Employee: {name}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            cv2.putText(frame, "s = Save  |  k = Skip", (10, 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
            cv2.imshow("Face Enrollment", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('k'):
                print("  Skipped.")
                break

            elif key == ord('s'):
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                encs = face_recognition.face_encodings(rgb)

                if not encs:
                    print("  Chehra nahi dikh raha! Thoda adjust karo.")
                    continue
                if len(encs) > 1:
                    print("  Ek se zyada chehra! Akele aao frame mein.")
                    continue

                blob = pickle.dumps(encs[0])
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    "UPDATE employees SET face_encoding=%s WHERE id=%s",
                    (blob, emp_id)
                )
                conn.commit()
                conn.close()
                print(f"  ✓ {name} ka face save ho gaya!")
                break

        cam.release()
        cv2.destroyAllWindows()

    print("\n✅ Enrollment complete! Ab attendance.py chalao.")

enroll_existing_employees()