import cv2

for i in range(10):
    cam = cv2.VideoCapture(i, cv2.CAP_DSHOW)
    if cam.isOpened():
        print(f"camera{i} mil gya")
        cam.release()
    else:
        print(f"cmaera {i}is not working")