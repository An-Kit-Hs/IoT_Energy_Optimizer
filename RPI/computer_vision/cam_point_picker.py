import cv2

points = []

def mouse_callback(event, x, y, flags, param):
    global points

    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        print(f"Point {len(points)}: {x}, {y}")

cap = cv2.VideoCapture(0)

cv2.namedWindow("Click 4 floor corners")
cv2.setMouseCallback("Click 4 floor corners", mouse_callback)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Draw clicked points
    for p in points:
        cv2.circle(frame, p, 5, (0,255,0), -1)

    # Draw lines between them
    if len(points) >= 2:
        for i in range(len(points)-1):
            cv2.line(frame, points[i], points[i+1], (255,0,0), 2)

    if len(points) == 4:
        cv2.line(frame, points[3], points[0], (255,0,0), 2)

    cv2.imshow("Click 4 floor corners", frame)

    key = cv2.waitKey(1)
    if key == 27:   # ESC
        break

cap.release()
cv2.destroyAllWindows()

print("\nFINAL CAM_POINTS =")
print(points)
