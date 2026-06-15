@echo off
cd /d d:\face-attendance-system
echo Installing face_recognition and dependencies...
C:\Users\tarun\AppData\Local\Programs\Python\Python310\python.exe -m pip install --only-binary :all: face_recognition
C:\Users\tarun\AppData\Local\Programs\Python\Python310\python.exe -m pip install pymysql pillow
echo.
echo Starting Face Attendance System...
echo.
C:\Users\tarun\AppData\Local\Programs\Python\Python310\python.exe main.py
pause
