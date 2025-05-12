import speech_recognition as sr
import pyttsx3
import subprocess
import webbrowser
import datetime
import sys
from config.profile_manager import get_profile

# Load settings
settings = get_profile("default")
LANGUAGE = settings.get("language", "en-US")

# Initialize text-to-speech engine
engine = pyttsx3.init()

def speak(text: str):
    engine.say(text)
    engine.runAndWait()

def listen() -> str:
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.pause_threshold = 0.8
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
    try:
        query = recognizer.recognize_google(audio, language=LANGUAGE)
        print(f"You said: {query}")
        return query.lower()
    except sr.UnknownValueError:
        print("Sorry, I didn't catch that.")
        return ""
    except sr.RequestError as e:
        print(f"API error: {e}")
        return ""

def handle_command(cmd: str):
    if "open chrome" in cmd:
        subprocess.Popen(["chrome"])
        speak("Opening Google Chrome.")
    elif "open notepad" in cmd:
        subprocess.Popen(["notepad"])
        speak("Opening Notepad.")
    elif cmd.startswith("search "):
        query = cmd.replace("search ", "").strip()
        webbrowser.open(f"https://www.google.com/search?q={query}")
        speak(f"Searching for {query}.")
    elif "time" in cmd:
        now = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The current time is {now}.")
    elif cmd in ("exit", "quit", "close"):
        speak("Goodbye!")
        sys.exit(0)
    else:
        speak("Sorry, I don't understand that command.")

def main():
    speak("NAC Voice Module activated.")
    while True:
        command = listen()
        if command:
            handle_command(command)

if __name__ == "__main__":
    main()
    input("Press Enter to exit…")
