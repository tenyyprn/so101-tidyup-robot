"""Microphone + Whisper check. Speak a Japanese command after the prompt.

Usage: .venv/bin/python voice_test.py [seconds]
"""
import signal
import subprocess
import sys
import tempfile
import time

import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

SECONDS = float(sys.argv[1]) if len(sys.argv) > 1 else 4
SOURCE = "alsa_input.usb-046d_HD_Pro_Webcam_C920-02.analog-stereo"


def record(seconds: float) -> np.ndarray:
    with tempfile.TemporaryDirectory() as d:
        path = f"{d}/rec.wav"
        proc = subprocess.Popen(
            ["pw-record", "--target", SOURCE, "--rate", "16000", "--channels", "1", path]
        )
        time.sleep(seconds)
        proc.send_signal(signal.SIGINT)  # SIGINT lets pw-record finalize the wav header
        proc.wait()
        audio, _ = sf.read(path, dtype="float32")
    return audio


def main():
    print("Loading Whisper...")
    model = WhisperModel("small", device="cpu", compute_type="int8")
    input(f"Press ENTER, then speak for {SECONDS:.0f} s (e.g. 「赤いスポンジを左の箱に入れて」)")
    print("Recording...")
    audio = record(SECONDS)
    print(f"level: rms={np.sqrt((audio**2).mean()):.4f} peak={abs(audio).max():.3f}")
    t = time.time()
    # vad_filter drops silence so Whisper does not hallucinate text on quiet input
    segments, _ = model.transcribe(audio, language="ja", vad_filter=True)
    text = "".join(s.text for s in segments).strip()
    print(f"text ({time.time() - t:.1f}s): {text or '(no speech detected)'}")


if __name__ == "__main__":
    main()
