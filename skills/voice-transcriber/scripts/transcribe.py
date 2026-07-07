#!/tmp/whisper_venv/bin/python3
"""
Voice Transcriber - 本地语音转写

用法:
    python transcribe.py <audio_file> [--language zh|en]

使用 faster-whisper base 模型，CPU int8 精度。
"""

import sys
import os

# Ensure whisper_venv packages are importable
WHISPER_VENV = "/tmp/whisper_venv"
if WHISPER_VENV not in sys.path:
    site_pkg = os.path.join(
        WHISPER_VENV, "lib",
        os.listdir(os.path.join(WHISPER_VENV, "lib"))[0],
        "site-packages"
    )
    if os.path.exists(site_pkg) and site_pkg not in sys.path:
        sys.path.insert(0, site_pkg)


def transcribe_audio(audio_path: str, language: str = "zh") -> str:
    """
    Transcribe audio file to text using faster-whisper.

    Args:
        audio_path: Path to audio file (ogg, mp3, wav, etc.)
        language: Language code (zh, en, ja, etc.)

    Returns:
        Transcribed text string
    """
    from faster_whisper import WhisperModel

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    text_parts = []
    for seg in segments:
        text_parts.append(seg.text.strip())

    return " ".join(text_parts)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: transcribe.py <audio_file> [--language zh|en]", file=sys.stderr)
        sys.exit(1)

    audio_file = sys.argv[1]
    lang = "zh"
    if "--language" in sys.argv:
        idx = sys.argv.index("--language")
        if idx + 1 < len(sys.argv):
            lang = sys.argv[idx + 1]

    try:
        result = transcribe_audio(audio_file, lang)
        print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
