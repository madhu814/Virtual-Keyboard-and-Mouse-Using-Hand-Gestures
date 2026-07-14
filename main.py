import cv2
import mediapipe as mp
import pyautogui
import numpy as np
import time
from collections import deque

# Disable PyAutoGUI fail-safe because the app moves the cursor from hand gestures.
# Be careful: moving the mouse to a corner will no longer abort the program automatically.
pyautogui.FAILSAFE = False

# Initialize webcam
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

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

# Virtual keyboard layout
KEYBOARD_LAYOUT = [
    [("Q", 1), ("W", 1), ("E", 1), ("R", 1), ("T", 1), ("Y", 1), ("U", 1), ("I", 1), ("O", 1), ("P", 1)],
    [("A", 1), ("S", 1), ("D", 1), ("F", 1), ("G", 1), ("H", 1), ("J", 1), ("K", 1), ("L", 1)],
    [("Z", 1), ("X", 1), ("C", 1), ("V", 1), ("B", 1), ("N", 1), ("M", 1), ("SPACE", 3)]
]
KEYBOARD_TOP_FRACTION = 0.60
KEYBOARD_HEIGHT_FRACTION = 0.32
KEYBOARD_MARGIN = 0.02
KEYBOARD_GAP = 0.01

# Camera-to-screen mapping range
CAMERA_X_MIN = 0.02
CAMERA_X_MAX = 0.95
CAMERA_Y_MIN = 0.02
CAMERA_Y_MAX = 0.95

# Control parameters
CLICK_DISTANCE = 0.0475
LOCK_DISTANCE = 0.085
COOLDOWN = 0.2
SMOOTHING_FACTOR = 0.85
DEADZONE_RADIUS = 15
POSITION_BUFFER_SIZE = 5

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


def get_keyboard_rects(frame_w, frame_h):
    top = int(frame_h * KEYBOARD_TOP_FRACTION)
    key_h = int(frame_h * 0.09)
    margin = int(frame_w * KEYBOARD_MARGIN)
    gap = int(frame_w * KEYBOARD_GAP)

    rects = []
    for row_index, row in enumerate(KEYBOARD_LAYOUT):
        row_top = top + row_index * (key_h + gap)
        row_units = sum(width for _, width in row)
        total_gap = gap * (len(row) - 1)
        available_width = frame_w - margin * 2 - total_gap
        unit = available_width / row_units
        x = margin

        for key, width in row:
            key_w = int(unit * width)
            rects.append((key, x, row_top, x + key_w, row_top + key_h))
            x += key_w + gap

    return rects


def get_key_at_position(index_x, index_y, frame_w, frame_h):
    px = int(index_x * frame_w)
    py = int(index_y * frame_h)
    for key, x1, y1, x2, y2 in get_keyboard_rects(frame_w, frame_h):
        if x1 <= px <= x2 and y1 <= py <= y2:
            return key
    return None


def draw_keyboard(frame, selected_key=None):
    frame_h, frame_w = frame.shape[:2]
    for key, x1, y1, x2, y2 in get_keyboard_rects(frame_w, frame_h):
        is_selected = key == selected_key
        color = (0, 160, 0) if is_selected else (50, 50, 50)
        border_color = (255, 255, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, cv2.FILLED)
        cv2.rectangle(frame, (x1, y1), (x2, y2), border_color, 2)

        label = "SPACE" if key == "SPACE" else key
        text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        text_x = x1 + (x2 - x1 - text_size[0]) // 2
        text_y = y1 + (y2 - y1 + text_size[1]) // 2
        cv2.putText(frame, label, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.putText(frame, "Virtual Keyboard: hover over a key and pinch to type", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
    return frame

while True:
    success, frame = cap.read()
    if not success:
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

        # Lock position logic
        if ti_dist < LOCK_DISTANCE:
            if not cursor_locked:
                cursor_locked = True
                locked_position = smoothed_pos
            final_x, final_y = locked_position
        else:
            cursor_locked = False
            final_x, final_y = smoothed_pos

        # Clamp cursor within screen bounds and move cursor if not locked or outside deadzone
        final_x = min(max(final_x, 0), screen_w - 1)
        final_y = min(max(final_y, 0), screen_h - 1)

        if not cursor_locked or (abs(final_x - pyautogui.position()[0]) > DEADZONE_RADIUS or
                                 abs(final_y - pyautogui.position()[1]) > DEADZONE_RADIUS):
            pyautogui.moveTo(final_x, final_y, _pause=False)

        # Determine virtual keyboard selection
        selected_key = get_key_at_position(index.x, index.y, frame.shape[1], frame.shape[0])

        # Left click detection
        if ti_dist < CLICK_DISTANCE and current_time - last_click_time > COOLDOWN:
            if selected_key:
                if selected_key == "SPACE":
                    pyautogui.write(" ")
                else:
                    pyautogui.write(selected_key)
            else:
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
        frame = draw_keyboard(frame, selected_key)

    # Reset when no hand
    if not hand_detected:
        smoothed_pos = pyautogui.position()
        last_scroll_y = None
        scroll_mode = False

    cv2.imshow("Gesture Control", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()