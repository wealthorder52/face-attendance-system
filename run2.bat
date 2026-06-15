@echo off
cd /d d:\face-attendance-system
echo Installing dlib from pre-compiled wheels...
C:\Users\tarun\AppData\Local\Programs\Python\Python310\python.exe -m pip install dlib --prefer-binary -q
echo Installing face_recognition...
C:\Users\tarun\AppData\Local\Programs\Python\Python310\python.exe -m pip install face_recognition -q
echo All packages installed successfully!
echo.
echo Starting Face Attendance System...
echo.
C:\Users\tarun\AppData\Local\Programs\Python\Python310\python.exe main.py
pause
