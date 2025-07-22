import cv2
import numpy as np
import pyautogui
import time
import math
import screeninfo
import os
import subprocess
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import wmi
import mediapipe as mp

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# Initialize system components
class SystemControls:
    def __init__(self):
        # Audio control
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))
        
        # Brightness control (Windows only)
        self.wmi_interface = wmi.WMI(namespace='wmi')
        
        # Screen info
        self.screen_width, self.screen_height = pyautogui.size()
        self.monitor = screeninfo.get_monitors()[0]
        
        # Control parameters
        self.cursor_smoothing = 0.5
        self.scroll_sensitivity = 10
        self.volume_sensitivity = 0.02
        self.brightness_sensitivity = 2
        self.drag_threshold = 30
        self.click_threshold = 5
        self.double_click_delay = 0.3
        
        # State tracking
        self.prev_hand_pos = None
        self.drag_start_pos = None
        self.last_click_time = 0
        self.scroll_mode = False
        self.volume_mode = False
        self.brightness_mode = False
        self.right_click_mode = False
        self.window_control_mode = False

    def move_cursor(self, x, y):
        """Move cursor with smoothing"""
        if self.prev_hand_pos:
            # Apply smoothing
            smoothed_x = x * self.cursor_smoothing + self.prev_hand_pos[0] * (1 - self.cursor_smoothing)
            smoothed_y = y * self.cursor_smoothing + self.prev_hand_pos[1] * (1 - self.cursor_smoothing)
        else:
            smoothed_x, smoothed_y = x, y
        
        # Convert from camera coordinates to screen coordinates
        screen_x = np.interp(smoothed_x, [0, self.monitor.width], [0, self.screen_width])
        screen_y = np.interp(smoothed_y, [0, self.monitor.height], [0, self.screen_height])
        
        pyautogui.moveTo(screen_x, screen_y)
        self.prev_hand_pos = (screen_x, screen_y)

    def left_click(self):
        """Perform left click"""
        current_time = time.time()
        if current_time - self.last_click_time < self.double_click_delay:
            pyautogui.doubleClick()
        else:
            pyautogui.click()
        self.last_click_time = current_time

    def right_click(self):
        """Perform right click"""
        pyautogui.rightClick()

    def start_drag(self):
        """Start dragging"""
        self.drag_start_pos = pyautogui.position()
        pyautogui.mouseDown()

    def end_drag(self):
        """End dragging"""
        pyautogui.mouseUp()
        self.drag_start_pos = None

    def scroll(self, direction):
        """Scroll up or down"""
        pyautogui.scroll(direction * self.scroll_sensitivity)

    def adjust_volume(self, change):
        """Adjust system volume"""
        current_volume = self.volume.GetMasterVolumeLevelScalar()
        new_volume = max(0, min(1, current_volume + change * self.volume_sensitivity))
        self.volume.SetMasterVolumeLevelScalar(new_volume, None)

    def adjust_brightness(self, change):
        """Adjust screen brightness (Windows only)"""
        try:
            brightness = self.wmi_interface.WmiMonitorBrightness()[0].CurrentBrightness
            new_brightness = max(0, min(100, brightness + change * self.brightness_sensitivity))
            
            method = self.wmi_interface.WmiMonitorBrightnessMethods()[0]
            method.WmiSetBrightness(new_brightness, 0)
        except Exception as e:
            print(f"Brightness control error: {e}")

    def minimize_all_windows(self):
        """Minimize all windows"""
        pyautogui.hotkey('win', 'd')

    def restore_down_window(self):
        """Restore down current window"""
        pyautogui.hotkey('win', 'down')

    def maximize_window(self):
        """Maximize current window"""
        pyautogui.hotkey('win', 'up')

# Hand gesture detector
class HandGestureController:
    def __init__(self):
        self.system = SystemControls()
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 1280)
        self.cap.set(4, 720)
        
        # Mode indicators
        self.mode_colors = {
            'normal': (0, 255, 0),
            'scroll': (255, 0, 0),
            'volume': (0, 0, 255),
            'brightness': (255, 255, 0),
            'right_click': (0, 255, 255),
            'window_control': (255, 0, 255)
        }

        # State tracking
        self.prev_fingertip = None
        self.gesture_history = []
        self.gesture_buffer_size = 5

    def count_fingers(self, landmarks):
        """Count extended fingers using hand landmarks"""
        finger_tips = [8, 12, 16, 20]  # Index, Middle, Ring, Pinky
        finger_mcp = [6, 10, 14, 18]   # Base joints
        
        extended_fingers = 0
        
        # Thumb (special case)
        thumb_tip = landmarks.landmark[4]
        thumb_ip = landmarks.landmark[3]
        if thumb_tip.x < thumb_ip.x:  # For left hand
            if thumb_tip.x < thumb_ip.x - 0.05:
                extended_fingers += 1
        else:  # For right hand
            if thumb_tip.x > thumb_ip.x + 0.05:
                extended_fingers += 1
        
        # Other fingers
        for tip, mcp in zip(finger_tips, finger_mcp):
            tip_y = landmarks.landmark[tip].y
            mcp_y = landmarks.landmark[mcp].y
            if tip_y < mcp_y:  # Finger is extended
                extended_fingers += 1
        
        return extended_fingers

    def run(self):
        """Main control loop"""
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process frame with MediaPipe Hands
            results = hands.process(rgb_frame)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw hand landmarks
                    mp_drawing.draw_landmarks(
                        frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    
                    # Get index finger tip (landmark 8)
                    index_tip = hand_landmarks.landmark[8]
                    h, w, c = frame.shape
                    abs_fx, abs_fy = int(index_tip.x * w), int(index_tip.y * h)
                    
                    # Draw fingertip
                    cv2.circle(frame, (abs_fx, abs_fy), 10, (0, 255, 255), -1)
                    
                    # Count fingers
                    finger_count = self.count_fingers(hand_landmarks)
                    self.gesture_history.append(finger_count)
                    if len(self.gesture_history) > self.gesture_buffer_size:
                        self.gesture_history.pop(0)
                    
                    # Determine mode based on finger count
                    if len(self.gesture_history) == self.gesture_buffer_size:
                        if all(g == 1 for g in self.gesture_history):
                            self.system.scroll_mode = True
                            self.system.volume_mode = False
                            self.system.brightness_mode = False
                            self.system.right_click_mode = False
                            self.system.window_control_mode = False
                        elif all(g == 2 for g in self.gesture_history):
                            self.system.volume_mode = True
                            self.system.scroll_mode = False
                            self.system.brightness_mode = False
                            self.system.right_click_mode = False
                            self.system.window_control_mode = False
                        elif all(g == 3 for g in self.gesture_history):
                            self.system.brightness_mode = True
                            self.system.scroll_mode = False
                            self.system.volume_mode = False
                            self.system.right_click_mode = False
                            self.system.window_control_mode = False
                        elif all(g == 4 for g in self.gesture_history):
                            self.system.right_click_mode = True
                            self.system.scroll_mode = False
                            self.system.volume_mode = False
                            self.system.brightness_mode = False
                            self.system.window_control_mode = False
                        elif all(g == 5 for g in self.gesture_history):
                            self.system.window_control_mode = True
                            self.system.scroll_mode = False
                            self.system.volume_mode = False
                            self.system.brightness_mode = False
                            self.system.right_click_mode = False
                        elif all(g == 0 for g in self.gesture_history):
                            # Reset all modes
                            self.system.scroll_mode = False
                            self.system.volume_mode = False
                            self.system.brightness_mode = False
                            self.system.right_click_mode = False
                            self.system.window_control_mode = False
                    
                    # Control actions based on mode
                    if self.system.scroll_mode:
                        # Scroll based on vertical movement
                        if self.prev_fingertip:
                            dy = abs_fy - self.prev_fingertip[1]
                            if abs(dy) > 5:
                                self.system.scroll(1 if dy < 0 else -1)
                    
                    elif self.system.volume_mode:
                        # Adjust volume based on vertical movement
                        if self.prev_fingertip:
                            dy = abs_fy - self.prev_fingertip[1]
                            if abs(dy) > 5:
                                self.system.adjust_volume(1 if dy < 0 else -1)
                    
                    elif self.system.brightness_mode:
                        # Adjust brightness based on vertical movement
                        if self.prev_fingertip:
                            dy = abs_fy - self.prev_fingertip[1]
                            if abs(dy) > 5:
                                self.system.adjust_brightness(1 if dy < 0 else -1)
                    
                    elif self.system.right_click_mode:
                        # Right click when finger stops moving
                        if self.prev_fingertip:
                            dist = math.hypot(abs_fx - self.prev_fingertip[0], abs_fy - self.prev_fingertip[1])
                            if dist < self.system.click_threshold:
                                self.system.right_click()
                    
                    elif self.system.window_control_mode:
                        # Window management gestures
                        if self.prev_fingertip:
                            dist = math.hypot(abs_fx - self.prev_fingertip[0], abs_fy - self.prev_fingertip[1])
                            if dist < self.system.click_threshold:
                                # Swipe left to minimize all
                                if abs_fx < self.prev_fingertip[0] - 50:
                                    self.system.minimize_all_windows()
                                # Swipe right to maximize
                                elif abs_fx > self.prev_fingertip[0] + 50:
                                    self.system.maximize_window()
                                # Swipe down to restore down
                                elif abs_fy > self.prev_fingertip[1] + 50:
                                    self.system.restore_down_window()
                    
                    else:
                        # Normal cursor mode
                        self.system.move_cursor(abs_fx, abs_fy)
                        
                        # Detect click (finger stops moving)
                        if self.prev_fingertip:
                            dist = math.hypot(abs_fx - self.prev_fingertip[0], abs_fy - self.prev_fingertip[1])
                            if dist < self.system.click_threshold:
                                if self.system.drag_start_pos:
                                    current_pos = pyautogui.position()
                                    drag_dist = math.hypot(
                                        current_pos[0] - self.system.drag_start_pos[0],
                                        current_pos[1] - self.system.drag_start_pos[1]
                                    )
                                    if drag_dist > self.system.drag_threshold:
                                        self.system.end_drag()
                                    else:
                                        self.system.left_click()
                                else:
                                    self.system.left_click()
                            elif dist > self.system.drag_threshold and not self.system.drag_start_pos:
                                self.system.start_drag()
                    
                    self.prev_fingertip = (abs_fx, abs_fy)
            
            # Display mode information
            mode_text = "Normal Mode"
            mode_color = self.mode_colors['normal']
            if self.system.scroll_mode:
                mode_text = "Scroll Mode"
                mode_color = self.mode_colors['scroll']
            elif self.system.volume_mode:
                mode_text = "Volume Control"
                mode_color = self.mode_colors['volume']
            elif self.system.brightness_mode:
                mode_text = "Brightness Control"
                mode_color = self.mode_colors['brightness']
            elif self.system.right_click_mode:
                mode_text = "Right Click Mode"
                mode_color = self.mode_colors['right_click']
            elif self.system.window_control_mode:
                mode_text = "Window Control Mode"
                mode_color = self.mode_colors['window_control']
            
            cv2.putText(frame, mode_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, mode_color, 2)
            
            # Display instructions
            instructions = [
                "1 finger: Scroll mode",
                "2 fingers: Volume control",
                "3 fingers: Brightness control",
                "4 fingers: Right click mode",
                "5 fingers: Window controls",
                "Fist: Normal mode",
                "Press 'q' to quit"
            ]
            
            for i, text in enumerate(instructions):
                cv2.putText(frame, text, (10, 70 + i*30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1)
            
            cv2.imshow('Hand Gesture Control', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        hands.close()
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # Install required packages:
    # pip install opencv-python numpy pyautogui screeninfo comtypes pycaw wmi mediapipe
    
    controller = HandGestureController()
    controller.run()