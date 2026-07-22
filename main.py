import ctypes
import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
from collections import deque

# Enable debug prints for cursor movement troubleshooting
DEBUG = True

# Windows fallback for cursor movement in case pyautogui does not move reliably.
user32 = ctypes.windll.user32

def win_move_cursor(x: int, y: int) -> None:
    user32.SetCursorPos(x, y)

# Disable PyAutoGUI fail-safe because the app moves the cursor from hand gestures.
# Be careful: moving the mouse to a corner will no longer abort the program automatically.
pyautogui.FAILSAFE = False

# Initialize webcam (prefer DirectShow on Windows to avoid backend issues)
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

# If the first device failed, try a few fallback indices
if not cap.isOpened():
    for i in range(1, 4):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            print(f"Opened camera index {i}")
            break

# Use a lower default resolution to avoid large frame allocations
if cap.isOpened():
    cap.set(3, 640)
    cap.set(4, 480)
else:
    raise RuntimeError("Could not open any camera. Close other apps using the camera or check permissions.")

# MediaPipe Hands setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

# Screen dimensions
screen_w, screen_h = pyautogui.size()

# Virtual keyboard removed — this build only provides gesture-based mouse control.

# Camera-to-screen mapping range
CAMERA_X_MIN = 0.02
CAMERA_X_MAX = 0.95
CAMERA_Y_MIN = 0.02
CAMERA_Y_MAX = 0.95

# Control parameters
CLICK_DISTANCE = 0.03
COOLDOWN = 0.2
SMOOTHING_FACTOR = 0.6
DEADZONE_RADIUS = 1
POSITION_BUFFER_SIZE = 3

# Scrolling parameters
SCROLL_GAP_THRESHOLD = 0.06  # distance in normalized units
SCROLL_MOVE_THRESHOLD = 0.005  # how much Y has to move to trigger scroll
last_scroll_y = None
scroll_mode = False

# State variables
last_click_time = 0
cursor_locked = False
locked_position = (0, 0)
smoothed_pos = (0, 0)
position_buffer = deque(maxlen=POSITION_BUFFER_SIZE)


# Note: keyboard drawing and typing helpers removed

while True:
    try:
        success, frame = cap.read()
    except cv2.error as e:
        print("OpenCV error while reading from camera:", e)
        print("Possible causes: camera in use, unsupported backend, or insufficient memory.")
        break

    if not success or frame is None:
        # If frame grab fails repeatedly, give actionable hints and continue briefly
        print("Warning: camera read returned no frame. Retrying...")
        time.sleep(0.1)
        continue

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    current_time = time.time()
    hand_detected = False

    if results.multi_hand_landmarks:
        hand_detected = True
        hand = results.multi_hand_landmarks[0]
        landmarks = hand.landmark

        # Get key landmarks
        index = landmarks[8]
        thumb = landmarks[4]
        middle = landmarks[12]

        # Convert coordinates to screen space using a tuned camera range.
        # This maps the visible hand range more fully to the screen width.
        raw_x = np.interp(index.x, [CAMERA_X_MIN, CAMERA_X_MAX], [0, screen_w - 1])
        raw_y = np.interp(index.y, [CAMERA_Y_MIN, CAMERA_Y_MAX], [0, screen_h - 1])

        # Add raw position to buffer and average recent positions for smoother movement
        position_buffer.append((raw_x, raw_y))
        avg_x = sum(p[0] for p in position_buffer) / len(position_buffer)
        avg_y = sum(p[1] for p in position_buffer) / len(position_buffer)

        # Exponential smoothing for cursor
        if not cursor_locked:
            smoothed_x = smoothed_pos[0] * SMOOTHING_FACTOR + avg_x * (1 - SMOOTHING_FACTOR)
            smoothed_y = smoothed_pos[1] * SMOOTHING_FACTOR + avg_y * (1 - SMOOTHING_FACTOR)
            smoothed_pos = (smoothed_x, smoothed_y)

        # Distance calculations
        ti_dist = np.hypot(thumb.x - index.x, thumb.y - index.y)
        tm_dist = np.hypot(thumb.x - middle.x, thumb.y - middle.y)
        im_dist = np.hypot(index.x - middle.x, index.y - middle.y)

        # SCROLLING MODE (index and middle fingers close + vertical movement)
        if im_dist < SCROLL_GAP_THRESHOLD:
            scroll_mode = True
            avg_y = (index.y + middle.y) / 2

            if last_scroll_y is not None:
                diff = avg_y - last_scroll_y
                if abs(diff) > SCROLL_MOVE_THRESHOLD:
                    pyautogui.scroll(-int(np.sign(diff) * 5))  # Negative = scroll up
                    last_scroll_y = avg_y
            else:
                last_scroll_y = avg_y
        else:
            scroll_mode = False
            last_scroll_y = None

        # Cursor follows the smoothed index position directly.
        cursor_locked = False
        final_x, final_y = smoothed_pos

        # Clamp cursor within screen bounds.
        final_x = min(max(final_x, 0), screen_w - 1)
        final_y = min(max(final_y, 0), screen_h - 1)

        if DEBUG:
            print(f"raw: ({raw_x:.1f},{raw_y:.1f}) avg: ({avg_x:.1f},{avg_y:.1f})")
            print(f"smoothed: ({smoothed_pos[0]:.1f},{smoothed_pos[1]:.1f}) final: ({final_x:.1f},{final_y:.1f})")

        try:
            pyautogui.moveTo(int(final_x), int(final_y), _pause=False)
        except Exception:
            win_move_cursor(int(final_x), int(final_y))

        # Left click detection (keyboard removed — always perform a click)
        if ti_dist < CLICK_DISTANCE and current_time - last_click_time > COOLDOWN:
            pyautogui.click()
            last_click_time = current_time
            time.sleep(0.1)

        # Right click detection
        if tm_dist < CLICK_DISTANCE and current_time - last_click_time > COOLDOWN:
            pyautogui.rightClick()
            last_click_time = current_time
            time.sleep(0.1)

        # Visual feedback
        h, w, _ = frame.shape
        cv2.circle(frame, (int(index.x * w), int(index.y * h)),
                   15, (0, 255, 0) if cursor_locked else (0, 0, 255), -1)
        cv2.putText(frame, f"Locked: {cursor_locked} | Scroll: {scroll_mode}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

    # Reset when no hand
    if not hand_detected:
        smoothed_pos = pyautogui.position()
        last_scroll_y = None
        scroll_mode = False
        if DEBUG:
            print(f"No hand detected — mouse at {pyautogui.position()}")

    cv2.imshow("Gesture Control", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()