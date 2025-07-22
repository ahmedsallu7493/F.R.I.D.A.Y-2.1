import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

# --- Configuration ---
CAM_WIDTH, CAM_HEIGHT = 640, 480
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
SMOOTHING_FACTOR = 0.5
CLICK_DISTANCE_THRESHOLD = 30
CLICK_HOLD_TIME = 0.4

# --- Setup ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)

# --- State Variables ---
prev_x = prev_y = 0
dragging = False
pinch_active = False
pinch_start_time = 0
click_ready = False

print("🖱️ Finger Mouse Running... Press 'q' to quit.")

while True:
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)
    h, w, _ = img.shape
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)

        # Get fingertip coordinates
        index = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
        thumb = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]

        x_index, y_index = int(index.x * w), int(index.y * h)
        x_thumb, y_thumb = int(thumb.x * w), int(thumb.y * h)

        # Draw fingertip
        cv2.circle(img, (x_index, y_index), 10, (255, 0, 255), -1)

        # Map to screen
        screen_x = np.interp(x_index, (0, w), (0, SCREEN_WIDTH))
        screen_y = np.interp(y_index, (0, h), (0, SCREEN_HEIGHT))
        smooth_x = prev_x + (screen_x - prev_x) * SMOOTHING_FACTOR
        smooth_y = prev_y + (screen_y - prev_y) * SMOOTHING_FACTOR
        pyautogui.moveTo(smooth_x, smooth_y)
        prev_x, prev_y = smooth_x, smooth_y

        # Distance between index and thumb
        distance = np.hypot(x_index - x_thumb, y_index - y_thumb)

        if distance < CLICK_DISTANCE_THRESHOLD:
            # Pinch started
            if not pinch_active:
                pinch_active = True
                pinch_start_time = time.time()
                click_ready = True  # Assume click unless held too long

            # If held too long, treat as drag
            if time.time() - pinch_start_time > CLICK_HOLD_TIME:
                if not dragging:
                    dragging = True
                    pyautogui.mouseDown()
                    click_ready = False
                    print("🖱️ Drag Start")
        else:
            # Pinch released
            if pinch_active:
                pinch_active = False
                pinch_duration = time.time() - pinch_start_time

                if dragging:
                    dragging = False
                    pyautogui.mouseUp()
                    print("🖱️ Drag End")
                elif click_ready and pinch_duration < CLICK_HOLD_TIME:
                    pyautogui.click()
                    print("🖱️ Click")
                click_ready = False

    cv2.imshow("Finger Mouse - Click vs Drag", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
print("👋 Program Ended")
