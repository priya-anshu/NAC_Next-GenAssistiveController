# Next-Gen Assistive Controller (NAC)

An AI-powered desktop assistant that enables users with partial or complete motor disabilities to control their computer via **voice**, **hand gestures**, **eye-tracking**, or even in the future, **brain–computer interfaces (BCI)**.  

---

## Features

- **Voice Control**  
  - English (`en-US`) & Hindi (`hi-IN`) via Google Speech API  
  - Open apps, perform web searches, get the time, custom commands  

- **Gesture Control**  
  - Cursor movement with right-hand index finger  
  - Left-hand pinch for left/right click  
  - Continuous scroll via finger-extension  

- **Eye-Tracking Control**  
  - Absolute gaze→cursor mapping using MediaPipe Face Mesh + iris landmarks  
  - Automatic corner-based calibration & per-profile sensitivity settings  
  - Smooth, low-latency cursor control

- **Hybrid Mode**  
  - Runs voice, gesture & eye threads in parallel  
  - Central event-bus with priority: **voice > gesture > eye**

- **Profiles & Settings**  
  - Multi-profile JSON manager (click thresholds, scroll sensitivity, eye parameters, voice language)  
  - GUI for creating/managing profiles, adjusting thresholds & sensitivities  
  - “Calibrate Eye Range…” wizard built into the Settings dialog

---

## Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/priya-anshu/NAC_Next-GenAssistiveController.git
   cd NAC
