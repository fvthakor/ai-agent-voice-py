import subprocess
import sounddevice as sd
import soundfile as sf
import tempfile
import re
import os

# ---------------- CONFIG ----------------
WHISPER_PATH = r"D:\python\ai-agent-call-real-freeapi\whisper\Release\whisper-cli.exe"
WHISPER_MODEL = r"D:\python\ai-agent-call-real-freeapi\whisper\Release\ggml-base.en.bin"
OLLAMA_MODEL = "llama3"
TTS_MODEL = "tts_models/en/vctk/vits"  # Multi-speaker with GST
DEFAULT_SPEAKER_IDX = "p225"           # Works on Windows TTS
DEFAULT_EMOTION = "happy"              # happy, sad, neutral, angry, etc.

# ---------------- FUNCTIONS ----------------
def record_audio(filename, duration=5):
    print("\n🎤 Speak now...")
    samplerate = 16000
    audio = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='float32')
    sd.wait()
    sf.write(filename, audio, samplerate)

def transcribe_audio(filename):
    print("📝 Transcribing...")
    try:
        result = subprocess.check_output(
            [WHISPER_PATH, "-m", WHISPER_MODEL, "-f", filename, "--no-timestamps"],
            text=True
        )
        transcript = result.strip().splitlines()[-1]  # last line
        print("🗣 You said:", transcript)
        return transcript
    except subprocess.CalledProcessError:
        print("[!] Whisper failed to transcribe audio.")
        return ""

def ask_ollama(prompt):
    print("🤖 Thinking...")
    try:
        result = subprocess.check_output(["ollama", "run", OLLAMA_MODEL], input=prompt, text=True)
        response = result.strip()
        print("💬 AI says:", response)
        return response
    except subprocess.CalledProcessError:
        print("[!] Ollama failed to generate a response.")
        return "Sorry, I couldn't think of a reply."

def clean_text(text):
    """Remove unsupported characters for TTS."""
    return re.sub(r"[^\w\s.,!?]", "", text)

def speak_text(text, speaker_idx=DEFAULT_SPEAKER_IDX, emotion=DEFAULT_EMOTION):
    text = clean_text(text)
    print(f"🎭 Speaking ({emotion}): {text}")
    tmpfile = tempfile.mktemp(suffix=".wav")
    try:
        subprocess.run([
            "tts",
            "--text", text,
            "--model_name", TTS_MODEL,
            "--speaker_idx", speaker_idx,  # Use string like "p225"
            "--gst_style", emotion,
            "--out_path", tmpfile
        ], check=True)
        data, samplerate = sf.read(tmpfile)
        sd.play(data, samplerate)
        sd.wait()
    except subprocess.CalledProcessError:
        print("[!] TTS failed to generate audio.")
    except Exception as e:
        print(f"[!] Audio playback error: {e}")
    finally:
        if os.path.exists(tmpfile):
            os.remove(tmpfile)

# ---------------- MAIN LOOP ----------------
if __name__ == "__main__":
    conversation_history = "You are a friendly young woman. Speak warmly with emotions.\n"

    while True:
        wav_file = "input.wav"
        record_audio(wav_file, duration=5)

        transcript = transcribe_audio(wav_file)
        if transcript.lower() in ["exit", "quit", "bye"]:
            print("👋 Ending conversation.")
            break

        conversation_history += f"User: {transcript}\nGirl:"
        response = ask_ollama(conversation_history)

        # Speak response with correct speaker_idx and emotion
        speak_text(response, speaker_idx=DEFAULT_SPEAKER_IDX, emotion=DEFAULT_EMOTION)

        conversation_history += f" {response}\n"
