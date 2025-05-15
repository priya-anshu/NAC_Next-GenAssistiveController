import os
import sys

# ─── Ensure project root on sys.path ────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
# ────────────────────────────────────────────────────────────────────────────

import speech_recognition as sr
import pyttsx3
import subprocess
import webbrowser
import datetime
from config.profile_manager import get_profile

# Load settings
settings = get_profile("default")
# Example codes: "en-US", "hi-IN"
LANGUAGE = settings.get("language", "en-US")
# Derive base language code for easier checks: "en" or "hi"
BASE_LANG = LANGUAGE.split("-")[0]

# Initialize TTS engine
engine = pyttsx3.init()

def speak(text: str):
    engine.say(text)
    engine.runAndWait()

def listen() -> str:
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print(f"Listening ({LANGUAGE})…")
        recognizer.pause_threshold = 0.8
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
    try:
        query = recognizer.recognize_google(audio, language=LANGUAGE)
        print(f"Recognized: {query}")
        return query.lower().strip()
    except sr.UnknownValueError:
        print("Could not understand audio")
        return ""
    except sr.RequestError as e:
        print(f"API error: {e}")
        return ""

def handle_command(cmd: str):
    if not cmd:
        return

    # English commands
    if BASE_LANG == "en":
        if "open chrome" in cmd:
            subprocess.Popen(["chrome"])
            speak("Opening Google Chrome.")
        elif "open notepad" in cmd:
            subprocess.Popen(["notepad"])
            speak("Opening Notepad.")
        elif cmd.startswith("search "):
            term = cmd.replace("search ", "", 1).strip()
            webbrowser.open(f"https://www.google.com/search?q={term}")
            speak(f"Searching for {term}.")
        elif "time" in cmd:
            now = datetime.datetime.now().strftime("%I:%M %p")
            speak(f"The current time is {now}.")
        elif any(word in cmd for word in ("exit", "quit", "close")):
            speak("Goodbye!")
            sys.exit(0)
        else:
            speak("Sorry, I don't understand that command.")

    # Hindi commands
    elif BASE_LANG == "hi":
        # Chrome
        if "क्रोम" in cmd and ("खोलो" in cmd or "खोलें" in cmd):
            subprocess.Popen(["chrome"])
            speak("क्रोम खोल रहा हूँ।")
        # Notepad
        elif "नोटपैड" in cmd and ("खोलो" in cmd or "खोलें" in cmd):
            subprocess.Popen(["notepad"])
            speak("नोटपैड खोल रहा हूँ।")
        # Search
        elif cmd.startswith("खोजो") or cmd.startswith("खोजें") or cmd.startswith("खोज "):
            # strip any of the Hindi search keywords
            term = cmd
            for kw in ("खोजो", "खोजें", "खोज"):
                if term.startswith(kw):
                    term = term.replace(kw, "", 1).strip()
                    break
            webbrowser.open(f"https://www.google.com/search?q={term}")
            speak(f"{term} के लिए खोज रहा हूँ।")
        # Time
        elif "समय" in cmd:
            now = datetime.datetime.now().strftime("%I:%M %p")
            speak(f"वर्तमान समय है {now}।")
        # Exit
        elif any(phrase in cmd for phrase in ("बाहर निकलो", "बंद करो", "बाहर निकलें")):
            speak("अलविदा!")
            sys.exit(0)
        else:
            speak("माफ़ कीजिए, मैं वह कमांड नहीं समझा।")

def main():
    # Initial greeting
    if BASE_LANG == "en":
        speak("NAC Voice Module activated.")
    else:
        speak("एनएसी वॉयस मॉड्यूल सक्रिय है।")

    while True:
        command = listen()
        handle_command(command)

if __name__ == "__main__":
    main()
    input("Press Enter to exit…")
