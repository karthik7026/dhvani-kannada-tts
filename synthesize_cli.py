#!/usr/bin/env python3
"""
Dhvani Kannada TTS Audio Test CLI 🎙️
Synthesize and play Kannada speech directly from the command line with full pronunciation optimization.

Usage:
  python3 synthesize_cli.py "ನಾವು ₹1000 ಡಿಜಿಟಲ್ ಪೇಮೆಂಟ್ ಮಾಡಿದಾಗ, ವ್ಯಾಪಾರಿ 1% MDR ಕಡಿತಗೊಳಿಸುತ್ತಾನೆ."
  python3 synthesize_cli.py --voice kn-IN-SapnaNeural "ಶುಭೋದಯ! ಧ್ವನಿ ಆಡಿಯೊ ಸ್ಟುಡಿಯೋಗೆ ಸುಸ್ವಾಗತ."
  python3 synthesize_cli.py --mode delivery "YouTube ಮತ್ತು ChatGPT ನಲ್ಲಿ AI ಬಗ್ಗೆ ಸಂಪೂರ್ಣ ಮಾಹಿತಿ ಇದೆ."
"""

import sys
import os
import time
import asyncio
import argparse
import subprocess
from pronunciation_engine import KannadaPronunciationEngine

async def synthesize_text(
    text: str,
    voice: str = "kn-IN-GaganNeural",
    mode: str = "standard",
    out_file: str = "output_speech.mp3",
    auto_play: bool = True
):
    print("=" * 65)
    print("  DHVANI KANNADA TTS - AUDIO SYNTHESIZER 🎙️")
    print("=" * 65)

    # 1. Pronunciation Engine Preprocessing
    display_text, speech_text, transforms = KannadaPronunciationEngine.process_pronunciation(text)
    debug_info = KannadaPronunciationEngine.get_debug_breakdown(text)

    print("\n🔍 3-Stage Pronunciation Inspection:")
    print(f"  1. [Display Text]   : {display_text}")
    print(f"  2. [Normalized Text]: {debug_info['normalized_text']}")
    print(f"  3. [Speech for TTS] : {speech_text}")
    
    if transforms:
        print(f"\n⚡ Applied Rules ({len(transforms)}):")
        for t in transforms:
            print(f"  * [{t['stage']}] {t['rule']}")
    else:
        print("\n⚡ Applied Rules: Pure Kannada script (no special replacement needed)")

    # 2. Synthesis
    print(f"\n🎙️ Synthesizing using voice: {voice} (Mode: {mode})...")
    t0 = time.time()

    try:
        if mode == "delivery":
            from prosody_mapper import KannadaProsodyMapper
            audio_bytes, meta = await KannadaProsodyMapper.synthesize_with_delivery_style(
                kannada_text=text,
                voice=voice,
                energy_mode="high_energy"
            )
            out_file = out_file.replace(".mp3", ".wav")
            with open(out_file, "wb") as f:
                f.write(audio_bytes)
        else:
            import edge_tts
            actual_voice = "kn-IN-SapnaNeural" if "sapna" in voice.lower() or "female" in voice.lower() else "kn-IN-GaganNeural"
            rate = "+24%" if voice == "podcast-narrator" else "+0%"
            pitch = "-3Hz" if voice == "podcast-narrator" else "+0Hz"

            communicate = edge_tts.Communicate(
                text=speech_text,
                voice=actual_voice,
                pitch=pitch,
                rate=rate
            )
            await communicate.save(out_file)

        elapsed = time.time() - t0
        file_size = os.path.getsize(out_file) / 1024
        print(f"✅ Audio generated in {elapsed:.2f}s -> {out_file} ({file_size:.1f} KB)")

        # 3. macOS Auto-play
        if auto_play and sys.platform == "darwin":
            print(f"🔊 Playing audio via macOS afplay...")
            subprocess.run(["afplay", out_file])

    except ImportError as e:
        print(f"\n⚠️ Missing dependency: {e}")
        print("To install required packages, run:")
        print("  pip install -r requirements.txt")
    except Exception as e:
        print(f"\n❌ Synthesis error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Dhvani Kannada TTS Audio Test CLI")
    parser.add_argument("text", nargs="?", default="ನಾವು ₹1000 ಡಿಜಿಟಲ್ ಪೇಮೆಂಟ್ ಮಾಡಿದಾಗ, ವ್ಯಾಪಾರಿ 1% MDR ಕಡಿತಗೊಳಿಸುತ್ತಾನೆ.", help="Kannada text to speak")
    parser.add_argument("--voice", default="kn-IN-GaganNeural", help="Voice ID (kn-IN-GaganNeural / kn-IN-SapnaNeural / podcast-narrator)")
    parser.add_argument("--mode", default="standard", choices=["standard", "delivery"], help="Synthesis mode")
    parser.add_argument("--out", default="output_speech.mp3", help="Output audio file path")
    parser.add_argument("--no-play", action="store_true", help="Do not auto-play audio after synthesis")

    args = parser.parse_args()
    asyncio.run(synthesize_text(
        text=args.text,
        voice=args.voice,
        mode=args.mode,
        out_file=args.out,
        auto_play=not args.no_play
    ))

if __name__ == "__main__":
    main()
