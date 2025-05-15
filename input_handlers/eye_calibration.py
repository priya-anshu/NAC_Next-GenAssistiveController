import os
import sys
import cv2
import mediapipe as mp
from config.profile_manager import get_profile, update_default_profile

# ─── Ensure project root in sys.path ───────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# ────────────────────────────────────────────────────────────────────────────

import pyautogui
from collections import defaultdict

# Load profile & defaults
settings = get_profile("default")

# MediaPipe Face Mesh (with iris)
mp_face = mp.solutions.face_mesh
face_mesh = mp_face.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# Iris landmarks
LEFT_IRIS  = [474, 475, 476, 477]
RIGHT_IRIS = [469, 470, 471, 472]

def iris_center(landmarks, indices, w, h):
    xs = [landmarks[i].x * w for i in indices]
    ys = [landmarks[i].y * h for i in indices]
    return sum(xs)/len(xs), sum(ys)/len(ys)

def capture_corner(name):
    """
    Prompt user to look at a corner, press 'c' to capture average iris ratio.
    """
    print(f"\n>> Calibration: look at {name.upper()}, then press 'c'")
    cap = cv2.VideoCapture(0)
    ratios = []
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
            lx, ly = iris_center(lm, LEFT_IRIS,  w, h)
            rx, ry = iris_center(lm, RIGHT_IRIS, w, h)
            cx, cy = (lx+rx)/2, (ly+ry)/2
            # draw text
            cv2.putText(frame, f"Press 'c' to capture {name}",
                        (30,30), cv2.FONT_HERSHEY_SIMPLEX,
                        1, (0,255,0), 2)
            cv2.imshow("Calibration", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('c') and res.multi_face_landmarks:
            # record this frame's ratio
            ratios.append((cx/w, cy/h))
            print(f"  Captured: {(cx/w):.3f}, {(cy/h):.3f}")
            break
        elif key == ord('q'):
            break
    cap.release()
    cv2.destroyWindow("Calibration")
    if ratios:
        # since we captured one sample, return it; could average multiple
        return ratios[-1]
    return None, None

def main():
    corners = ["top-left", "top-right", "bottom-right", "bottom-left"]
    captured = defaultdict(tuple)

    for name in corners:
        rx, ry = capture_corner(name)
        if rx is None:
            print(f"Skipping {name}, no data.")
            continue
        captured[name] = (rx, ry)

    # build min/max from corners
    xs = [v[0] for v in captured.values()]
    ys = [v[1] for v in captured.values()]
    if xs and ys:
        eye_min_x = min(xs)
        eye_max_x = max(xs)
        eye_min_y = min(ys)
        eye_max_y = max(ys)
        print(f"\nSaving calibration:")
        print(f"  eye_min_x = {eye_min_x:.3f}, eye_max_x = {eye_max_x:.3f}")
        print(f"  eye_min_y = {eye_min_y:.3f}, eye_max_y = {eye_max_y:.3f}")

        settings["eye_min_x"] = eye_min_x
        settings["eye_max_x"] = eye_max_x
        settings["eye_min_y"] = eye_min_y
        settings["eye_max_y"] = eye_max_y
        update_default_profile(settings)
        print("Calibration saved to profile.")
    else:
        print("No valid calibration data captured.")

    input("Calibration complete. Press Enter to exit…")

if __name__ == "__main__":
    main()
