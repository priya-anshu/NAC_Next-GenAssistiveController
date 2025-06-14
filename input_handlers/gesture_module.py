import os
import sys

# Ensure project root (one level up) is on the import path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


import cv2
import mediapipe as mp
import pyautogui
import time
import math
from config.profile_manager import get_profile
from utils.logger import log_event

# Disable PyAutoGUI failsafe
pyautogui.FAILSAFE = False

# Load settings
settings        = get_profile("default")
CLICK_THRESHOLD = settings.get("click_threshold", 30)
CLICK_COOLDOWN  = settings.get("click_cooldown", 0.5)
SCROLL_SCALE    = settings.get("scroll_scale", 2)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

screen_w, screen_h = pyautogui.size()

last_click_time = 0.0
scroll_active   = False
prev_scroll_y   = None

def is_pinch(lm1, lm2, cam_w, cam_h, threshold) -> bool:
    x1, y1 = lm1.x * cam_w, lm1.y * cam_h
    x2, y2 = lm2.x * cam_w, lm2.y * cam_h
    return math.hypot(x2 - x1, y2 - y1) < threshold

def fingers_extended(lms, cam_h) -> bool:
    return (
        lms[8].y * cam_h < lms[6].y * cam_h and
        lms[12].y * cam_h < lms[10].y * cam_h
    )

def main():
    global last_click_time, scroll_active, prev_scroll_y

    cap = cv2.VideoCapture(0)
    cam_w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    cam_h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

    log_event("module_start", "gesture_module")
    print("NAC Gesture Module active. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        if result.multi_hand_landmarks and result.multi_handedness:
            for idx, hand_hm in enumerate(result.multi_handedness):
                label = hand_hm.classification[0].label  # "Left" or "Right"
                lms   = result.multi_hand_landmarks[idx].landmark
                mp_draw.draw_landmarks(
                    frame,
                    result.multi_hand_landmarks[idx],
                    mp_hands.HAND_CONNECTIONS
                )

                if label == "Right":
                    x = int(lms[8].x * screen_w)
                    y = int(lms[8].y * screen_h)
                    pyautogui.moveTo(x, y)

                elif label == "Left":
                    now    = time.time()
                    thumb  = lms[4]
                    index  = lms[8]
                    middle = lms[12]

                    # Left-click
                    if is_pinch(thumb, index, cam_w, cam_h, CLICK_THRESHOLD):
                        if now - last_click_time > CLICK_COOLDOWN:
                            pyautogui.click(button="left")
                            log_event("gesture_click", "left")
                            last_click_time = now
                            scroll_active   = False
                            prev_scroll_y   = None

                    # Right-click
                    elif is_pinch(thumb, middle, cam_w, cam_h, CLICK_THRESHOLD):
                        if now - last_click_time > CLICK_COOLDOWN:
                            pyautogui.click(button="right")
                            log_event("gesture_click", "right")
                            last_click_time = now
                            scroll_active   = False
                            prev_scroll_y   = None

                    # Continuous scroll
                    elif fingers_extended(lms, cam_h):
                        cur_y = lms[8].y * cam_h
                        if not scroll_active:
                            scroll_active = True
                            prev_scroll_y = cur_y
                        else:
                            delta = prev_scroll_y - cur_y
                            amount = int(delta * SCROLL_SCALE)
                            if amount:
                                pyautogui.scroll(amount)
                                log_event("gesture_scroll", str(amount))
                                prev_scroll_y = cur_y

                    else:
                        scroll_active = False
                        prev_scroll_y = None

        cv2.imshow("NAC Gesture Control", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
    input("Press Enter to exit…")
