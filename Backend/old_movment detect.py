import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time

class FingerMouseController:
    def __init__(self,
                 cam_width=640,
                 cam_height=480,
                 frame_reduction=50,
                 smoothing_factor=0.5,
                 click_threshold=30):

        self.cam_width = cam_width
        self.cam_height = cam_height
        self.frame_reduction = frame_reduction
        self.smoothing_factor = smoothing_factor
        self.click_threshold = click_threshold

        self.screen_w, self.screen_h = pyautogui.size()

        # MediaPipe setup
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils

        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.cam_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.cam_height)

        self.prev_x, self.prev_y = 0, 0
        self.click_cooldown = 0

    def start(self):
        if not self.cap.isOpened():
            print("❌ Webcam not found.")
            return

        print("🖐️ Mouse Control = Index Finger | Click = Thumb + Middle Finger")
        print("🟣 Exit = Thumb + Pinky (Little Finger)")

        while True:
            success, img = self.cap.read()
            if not success:
                break

            img = cv2.flip(img, 1)
            h, w, _ = img.shape
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = self.hands.process(img_rgb)

            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                landmarks = hand_landmarks.landmark
                self.mp_draw.draw_landmarks(img, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

                # Get finger coordinates
                index_tip = landmarks[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
                middle_tip = landmarks[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
                thumb_tip = landmarks[self.mp_hands.HandLandmark.THUMB_TIP]
                pinky_tip = landmarks[self.mp_hands.HandLandmark.PINKY_TIP]

                x_index, y_index = int(index_tip.x * w), int(index_tip.y * h)
                x_middle, y_middle = int(middle_tip.x * w), int(middle_tip.y * h)
                x_thumb, y_thumb = int(thumb_tip.x * w), int(thumb_tip.y * h)
                x_pinky, y_pinky = int(pinky_tip.x * w), int(pinky_tip.y * h)

                # Draw pointer
                cv2.circle(img, (x_index, y_index), 10, (255, 0, 255), -1)

                # Cursor control box
                cx, cy = w // 2, h // 2
                x1, y1 = cx - self.frame_reduction, cy - self.frame_reduction
                x2, y2 = cx + self.frame_reduction, cy + self.frame_reduction
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

                # Move pointer using index finger
                mapped_x = np.interp(x_index, (x1, x2), (0, self.screen_w))
                mapped_y = np.interp(y_index, (y1, y2), (0, self.screen_h))
                curr_x = self.prev_x + (mapped_x - self.prev_x) * self.smoothing_factor
                curr_y = self.prev_y + (mapped_y - self.prev_y) * self.smoothing_factor
                pyautogui.moveTo(curr_x, curr_y)
                self.prev_x, self.prev_y = curr_x, curr_y

                # Click: thumb + middle
                mid_thumb_dist = np.hypot(x_middle - x_thumb, y_middle - y_thumb)
                if mid_thumb_dist < self.click_threshold and time.time() - self.click_cooldown > 0.6:
                    pyautogui.click()
                    self.click_cooldown = time.time()
                    print("🖱️ Click (Thumb + Middle)")

                # Exit: thumb + pinky
                pinky_thumb_dist = np.hypot(x_pinky - x_thumb, y_pinky - y_thumb)
                if pinky_thumb_dist < self.click_threshold:
                    cv2.putText(img, "👋 Exit Detected", (10, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                    cv2.imshow("Finger Mouse", img)
                    print("👋 Thumb + Pinky = Exit")
                    time.sleep(1)
                    break

            cv2.imshow("Finger Mouse", img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("🛑 Quit via Keyboard")
                break

        self.cap.release()
        cv2.destroyAllWindows()
        print("🎯 Controller stopped.")

# # # --- Run ---
if __name__ == "__main__":
    controller = FingerMouseController()
    controller.start()  