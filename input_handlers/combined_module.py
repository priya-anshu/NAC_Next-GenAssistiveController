import os
import sys
import threading
import time
import math
import cv2
import mediapipe as mp
import speech_recognition as sr
import pyttsx3
import subprocess
import webbrowser
import datetime
import pyautogui
from queue import Queue, Empty
from collections import deque

# ─── Ensure project root on import path ────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# ────────────────────────────────────────────────────────────────────────────

from config.profile_manager import get_profile
from utils.logger import log_event

# ─── Load settings ─────────────────────────────────────────────────────────
settings        = get_profile("default")
LANGUAGE        = settings.get("language", "en-US")
CLICK_THRESH    = settings.get("click_threshold", 30)
CLICK_COOLDOWN  = settings.get("click_cooldown", 0.5)
SCROLL_SCALE    = settings.get("scroll_scale", 2)
EYE_SMOOTH      = settings.get("eye_smoothing", 5)
EYE_SENSITIVITY = settings.get("eye_sensitivity", 2.0)

pyautogui.FAILSAFE = False
SCREEN_W, SCREEN_H = pyautogui.size()

# ─── Shared exit flag and event queue ───────────────────────────────────────
exit_event = threading.Event()
event_q    = Queue()

# ─── Helper for Iris Center ────────────────────────────────────────────────
def iris_center(landmarks, indices, width, height):
    xs = [landmarks[i].x * width for i in indices]
    ys = [landmarks[i].y * height for i in indices]
    return sum(xs) / len(xs), sum(ys) / len(ys)

# ─── Event Dispatcher ──────────────────────────────────────────────────────
def dispatcher():
    while not exit_event.is_set():
        try:
            src, evt = event_q.get(timeout=0.1)
        except Empty:
            continue

        # Voice (highest priority)
        if src == "voice":
            cmd = evt
            if cmd == "exit":
                exit_event.set()
                break
            handle_voice_command(cmd)
            continue

        # Gesture
        if src == "gesture":
            typ = evt["type"]
            if typ == "move":
                x, y = evt["pos"]
                pyautogui.moveTo(x, y)
            elif typ == "click":
                pyautogui.click(button=evt["button"])
            elif typ == "scroll":
                pyautogui.scroll(evt["amount"])
            continue

        # Eye (lowest priority)
        if src == "eye" and evt["type"] == "move":
            x, y = evt["pos"]
            pyautogui.moveTo(x, y)

# ─── Voice Thread ──────────────────────────────────────────────────────────
def voice_loop():
    recognizer = sr.Recognizer()
    tts        = pyttsx3.init()

    def speak(text):
        tts.say(text)
        tts.runAndWait()

    def listen():
        with sr.Microphone() as src:
            recognizer.pause_threshold = 0.8
            audio = recognizer.listen(src, timeout=5, phrase_time_limit=5)
        try:
            return recognizer.recognize_google(audio, language=LANGUAGE).lower()
        except:
            return ""

    def publish(cmd):
        event_q.put(("voice", cmd))

    # Optional greeting
    publish(f"greet_{LANGUAGE}")

    while not exit_event.is_set():
        cmd = listen()
        if cmd:
            publish(cmd)

def handle_voice_command(cmd):
    log_event("voice_command", cmd)
    # Basic mappings
    if "open chrome" in cmd or "क्रोम" in cmd:
        subprocess.Popen(["chrome"])
    elif "open notepad" in cmd or "नोटपैड" in cmd:
        subprocess.Popen(["notepad"])
    elif cmd.startswith("search ") or cmd.startswith("खोज"):
        term = cmd.split(" ", 1)[1]
        webbrowser.open(f"https://www.google.com/search?q={term}")
    elif "time" in cmd or "समय" in cmd:
        now = datetime.datetime.now().strftime("%I:%M %p")
        pyttsx3.init().say(now); pyttsx3.init().runAndWait()
    elif any(k in cmd for k in ("exit", "quit", "बाहर निकल")):
        event_q.put(("voice", "exit"))
    else:
        pyttsx3.init().say("Command not recognized"); pyttsx3.init().runAndWait()

# ─── Gesture Thread ─────────────────────────────────────────────────────────
def gesture_loop():
    mp_hands = mp.solutions.hands
    hands    = mp_hands.Hands(
        max_num_hands=2,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    )
    last_time = time.time()
    cap       = cv2.VideoCapture(0)

    def pinch(a, b):
        return math.hypot(a.x - b.x, a.y - b.y) < (CLICK_THRESH / 100)

    while not exit_event.is_set():
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.flip(frame, 1)
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res   = hands.process(rgb)

        if res.multi_hand_landmarks and res.multi_handedness:
            for idx, hand_hm in enumerate(res.multi_handedness):
                label = hand_hm.classification[0].label
                lm    = res.multi_hand_landmarks[idx].landmark

                # Right hand → move
                if label == "Right":
                    x = int(lm[8].x * SCREEN_W)
                    y = int(lm[8].y * SCREEN_H)
                    event_q.put(("gesture", {"type": "move", "pos": (x, y)}))

                # Left hand → click / scroll
                if label == "Left":
                    now = time.time()
                    # left click
                    if pinch(lm[4], lm[8]) and now - last_time > CLICK_COOLDOWN:
                        event_q.put(("gesture", {"type": "click", "button": "left"}))
                        last_time = now
                    # right click
                    elif pinch(lm[4], lm[12]) and now - last_time > CLICK_COOLDOWN:
                        event_q.put(("gesture", {"type": "click", "button": "right"}))
                        last_time = now
                    # scroll
                    elif lm[8].y < lm[6].y and lm[12].y < lm[10].y:
                        amt = int((lm[6].y - lm[8].y) * SCROLL_SCALE * 100)
                        event_q.put(("gesture", {"type": "scroll", "amount": amt}))

        if cv2.waitKey(1) & 0xFF == ord('q'):
            exit_event.set()
            break

    cap.release()
    cv2.destroyAllWindows()

# ─── Eye Thread ─────────────────────────────────────────────────────────────
def eye_loop():
    mp_face   = mp.solutions.face_mesh
    mesh      = mp_face.FaceMesh(refine_landmarks=True)
    smoothing = deque(maxlen=EYE_SMOOTH)
    cap       = cv2.VideoCapture(0)

    LEFT_IRIS  = [474, 475, 476, 477]
    RIGHT_IRIS = [469, 470, 471, 472]

    while not exit_event.is_set():
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res  = mesh.process(rgb)

        if res.multi_face_landmarks:
            lm = res.multi_face_landmarks[0].landmark
            lx, ly = iris_center(lm, LEFT_IRIS, w, h)
            rx, ry = iris_center(lm, RIGHT_IRIS, w, h)
            cx, cy = (lx + rx) / 2, (ly + ry) / 2

            nx, ny = cx / w, cy / h
            ax = (nx - 0.5) * EYE_SENSITIVITY + 0.5
            ay = (ny - 0.5) * EYE_SENSITIVITY + 0.5
            ax, ay = max(0.0, min(ax, 1.0)), max(0.0, min(ay, 1.0))

            smoothing.append((ax, ay))
            avg_x = sum(p[0] for p in smoothing) / len(smoothing)
            avg_y = sum(p[1] for p in smoothing) / len(smoothing)

            x = int(avg_x * SCREEN_W)
            y = int(avg_y * SCREEN_H)
            event_q.put(("eye", {"type": "move", "pos": (x, y)}))

        if cv2.waitKey(1) & 0xFF == ord('q'):
            exit_event.set()
            break

    cap.release()
    cv2.destroyAllWindows()

# ─── Main ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # start all three threads
    threading.Thread(target=voice_loop,   daemon=True).start()
    threading.Thread(target=gesture_loop, daemon=True).start()
    threading.Thread(target=eye_loop,     daemon=True).start()
    # start dispatcher in main thread (blocks)
    dispatcher()
