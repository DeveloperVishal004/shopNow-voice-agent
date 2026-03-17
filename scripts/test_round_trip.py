import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.stt import transcribe_audio
from backend.services.tts import text_to_speech

def test_round_trip(audio_file_path: str):
    print("\n--- STEP 1: STT ---")
    stt_result = transcribe_audio(audio_file_path)
    
    if not stt_result["success"]:
        print(f"STT failed: {stt_result['error']}")
        return
    
    print(f"Transcribed text : {stt_result['text']}")
    print(f"Detected language: {stt_result['language']}")

    print("\n--- STEP 2: TTS ---")
    tts_result = text_to_speech(
        text=stt_result["text"],
        language=stt_result["language"]
    )

    if not tts_result["success"]:
        print(f"TTS failed: {tts_result['error']}")
        return

    print(f"Audio saved to: {tts_result['audio_path']}")
    print(f"Voice used    : {tts_result['voice']}")
    print("\n--- ROUND TRIP COMPLETE ---")
    print("Play the output audio file to verify it sounds correct")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_round_trip.py <path_to_audio_file>")
        print("Example: python scripts/test_round_trip.py data/test.mp3")
        sys.exit(1)

    test_round_trip(sys.argv[1])