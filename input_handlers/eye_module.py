import os
import sys
import cv2
import mediapipe as mp
import pyautogui
from collections import deque

# ─── Project‐root import hack ───────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# ────────────────────────────────────────────────────────────────────────────

from config.profile_manager import get_profile, update_default_profile
from utils.logger import log_event

# ─── Load profile & defaults ───────────────────────────────────────────────
settings      = get_profile("default")
SMOOTHING     = settings.get("eye_smoothing", 5)
SENSITIVITY   = settings.get("eye_sensitivity", 2.0)
# calibration bounds (will be written back if missing)
EYE_MIN_X     = settings.get("eye_min_x", None)
EYE_MAX_X     = settings.get("eye_max_x", None)
EYE_MIN_Y     = settings.get("eye_min_y", None)
EYE_MAX_Y     = settings.get("eye_max_y", None)
# ────────────────────────────────────────────────────────────────────────────

pyautogui.FAILSAFE = False
SCREEN_W, SCREEN_H = pyautogui.size()

# MediaPipe Face Mesh + Iris
mp_face   = mp.solutions.face_mesh
face_mesh = mp_face.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw   = mp.solutions.drawing_utils

LEFT_IRIS  = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

def iris_center(lms, idxs, w, h):
    xs = [lms[i].x * w for i in idxs]
    ys = [lms[i].y * h for i in idxs]
    return sum(xs)/len(xs), sum(ys)/len(ys)

def capture_corner(label):
    """
    Show a camera window prompting “Look at {label} and press C”,
    return the normalized (x,y) of iris-centroid for that frame.
    """
    cap = cv2.VideoCapture(0)
    print(f"\n→ Calibration: look at {label} and press C")
    cx_c, cy_c = None, None

    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = face_mesh.process(rgb)

        if res.multi_face_landmarks:
            lm = res.multi_face_landmarks[0].landmark
            lx, ly = iris_center(lm, LEFT_IRIS, w, h)
            rx, ry = iris_center(lm, RIGHT_IRIS, w, h)
            cx, cy = (lx+rx)/2, (ly+ry)/2
            cv2.putText(frame, f"Press C to capture {label}",
                        (30,30), cv2.FONT_HERSHEY_SIMPLEX,
                        1.0, (0,255,0), 2)
        cv2.imshow("Eye Calibration", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('c') and res.multi_face_landmarks:
            cx_c, cy_c = cx/w, cy/h
            print(f"  Captured {label}: ({cx_c:.3f}, {cy_c:.3f})")
            break
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyWindow("Eye Calibration")
    return cx_c, cy_c

def run_calibration():
    """If any of the four corner bounds are missing, run them now."""
    global EYE_MIN_X, EYE_MAX_X, EYE_MIN_Y, EYE_MAX_Y
    if None not in (EYE_MIN_X, EYE_MAX_X, EYE_MIN_Y, EYE_MAX_Y):
        return

    # capture each corner
    corners = ["top-left", "top-right", "bottom-right", "bottom-left"]
    pts = []
    for c in corners:
        xy = capture_corner(c)
        if xy[0] is not None:
            pts.append(xy)

    if len(pts) < 2:
        print("Calibration aborted; not enough data.")
        return

    xs, ys = zip(*pts)
    EYE_MIN_X, EYE_MAX_X = min(xs), max(xs)
    EYE_MIN_Y, EYE_MAX_Y = min(ys), max(ys)

    # save back into profile
    settings["eye_min_x"] = EYE_MIN_X
    settings["eye_max_x"] = EYE_MAX_X
    settings["eye_min_y"] = EYE_MIN_Y
    settings["eye_max_y"] = EYE_MAX_Y
    update_default_profile(settings)
    print(f"Saved calibration: X∈[{EYE_MIN_X:.3f},{EYE_MAX_X:.3f}], "
          f"Y∈[{EYE_MIN_Y:.3f},{EYE_MAX_Y:.3f}]")

def main():
    log_event("module_start", "eye_module_auto_calib")
    # 1) If needed, run calibration
    run_calibration()

    # 2) Tracking loop
    cap       = cv2.VideoCapture(0)
    smoothing = deque(maxlen=SMOOTHING)
    print("NAC Eye Module active (auto‐calibrated). Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        frame = cv2.flip(frame, 1)
        h, w = frame.shape[:2]
        rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res  = face_mesh.process(rgb)

        if res.multi_face_landmarks:
            lm = res.multi_face_landmarks[0].landmark
            lx, ly = iris_center(lm, LEFT_IRIS, w, h)
            rx, ry = iris_center(lm, RIGHT_IRIS, w, h)
            cx, cy = (lx+rx)/2, (ly+ry)/2

            # raw norm
            nx = cx/w; ny = cy/h
            # apply calibration bounds
            if EYE_MAX_X > EYE_MIN_X:
                nx = (nx - EYE_MIN_X)/(EYE_MAX_X - EYE_MIN_X)
            if EYE_MAX_Y > EYE_MIN_Y:
                ny = (ny - EYE_MIN_Y)/(EYE_MAX_Y - EYE_MIN_Y)
            nx, ny = max(0, min(nx,1)), max(0, min(ny,1))

            # sensitivity
            ax = (nx - 0.5)*SENSITIVITY + 0.5
            ay = (ny - 0.5)*SENSITIVITY + 0.5
            ax, ay = max(0, min(ax,1)), max(0, min(ay,1))

            # smoothing
            smoothing.append((ax, ay))
            mx = sum(p[0] for p in smoothing)/len(smoothing)
            my = sum(p[1] for p in smoothing)/len(smoothing)

            # move
            pyautogui.moveTo(int(mx*SCREEN_W), int(my*SCREEN_H))

            # debug draw
            mp_draw.draw_landmarks(
                frame,
                res.multi_face_landmarks[0],
                mp_face.FACEMESH_IRISES,
                mp_draw.DrawingSpec((0,255,0),1,1),
                mp_draw.DrawingSpec((255,0,0),1,1)
            )

        cv2.imshow("NAC Eye Control", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
    input("Press Enter to exit…")
