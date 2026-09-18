#!/usr/bin/env python3
"""
Dhvani Kannada Text-to-Speech & Voice Studio Server (ಧ್ವನಿ ಕನ್ನಡ ವೆಬ್ ಸ್ಟುಡಿಯೋ)
FastAPI Backend delivering high-fidelity Kannada neural synthesis, acoustic voice cloning, text normalization, and audio mastering.
"""

import os
import io
import re
import wave
import struct
import math
import time
import asyncio
from typing import Optional, List
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body, Header
from fastapi.responses import Response, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx

from kannada_normalizer import KannadaNormalizer, normalize_kannada_text
from voice_cloner import AcousticVoiceCloner

app = FastAPI(
    title="Dhvani Kannada TTS Studio API",
    description="High-Fidelity Kannada Neural Text-to-Speech & Voice Cloning Web Studio",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).parent.resolve()
WEB_DIR = BASE_DIR / "web"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
CACHE_DIR = BASE_DIR / "results" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# In-memory history for session
SYNTHESIS_HISTORY = []

VOICE_PROFILES = [
    {
        "id": "kn-IN-SapnaNeural",
        "name": "Sapna (ಸ್ಪಪ್ನಾ)",
        "gender": "female",
        "category": "Standard Narrator",
        "description": "ಸ್ವಾಭಾವಿಕ, ಮಧುರ ಮತ್ತು ಸ್ಪಷ್ಟ ಹೆಣ್ಣು ಧ್ವನಿ (Expressive Female)",
        "badge": "ಜನಪ್ರಿಯ (Popular)",
        "defaultPitch": "+0Hz",
        "defaultRate": "+0%"
    },
    {
        "id": "kn-IN-GaganNeural",
        "name": "Gagan (ಗಗನ್)",
        "gender": "male",
        "category": "Standard Narrator",
        "description": "ಗಂಭೀರ, ಸ್ಪಷ್ಟ ಮತ್ತು ಆಳವಾದ ಗಂಡು ಧ್ವನಿ (Authoritative Male)",
        "badge": "ಕ್ಲಾಸಿಕ್ (Classic)",
        "defaultPitch": "-2Hz",
        "defaultRate": "+0%"
    },
    {
        "id": "podcast-narrator",
        "name": "Podcast Narrator",
        "gender": "male",
        "category": "Presenter",
        "description": "ಉತ್ಸಾಹಭರಿತ ಯೂಟ್ಯೂಬ್ ಮತ್ತು ಪಾಡ್‌ಕ್ಯಾಸ್ಟ್ ನಿರೂಪಕ (High-Energy Host)",
        "badge": "🔥 ಎನರ್ಜಿ (High-Energy)",
        "defaultPitch": "-4Hz",
        "defaultRate": "+26%"
    },
    {
        "id": "news-anchor",
        "name": "Breaking News (ವಾರ್ತಾ ವಾಚಕ)",
        "gender": "male",
        "category": "Broadcast",
        "description": "ವೇಗದ ಮತ್ತು ಗರಿಗರಿಯಾದ ಟಿವಿ ವಾರ್ತಾ ನಿರೂಪಣೆ (Crisp News Anchor)",
        "badge": "📢 ನ್ಯೂಸ್ (News)",
        "defaultPitch": "+2Hz",
        "defaultRate": "+18%"
    },
    {
        "id": "storyteller",
        "name": "Storyteller (ಸಾಹಿತ್ಯ & ಕಥೆ)",
        "gender": "female",
        "category": "Audiobook",
        "description": "ಭಾವನಾತ್ಮಕ ಕಥಾ ನಿರೂಪಣೆ ಮತ್ತು ಸಾಹಿತ್ಯ ವಾಚನ (Audiobook & Stories)",
        "badge": "📖 ಕಥೆ (Stories)",
        "defaultPitch": "-1Hz",
        "defaultRate": "-6%"
    },
    {
        "id": "custom-clone",
        "name": "Custom Voice Clone",
        "gender": "custom",
        "category": "Cloning",
        "description": "ನಿಮ್ಮ ಆಡಿಯೊ ಮಾದರಿಯ ಪಿಚ್ ಮತ್ತು ಟಿಂಬ್ರೆ ಆಧಾರಿತ ಕ್ಲೋನಿಂಗ್",
        "badge": "🧬 ಕ್ಲೋನ್ (Clone)",
        "defaultPitch": "+0Hz",
        "defaultRate": "+0%"
    }
]

PRESETS_DATA = [
    {
        "category": "ಸುದ್ದಿ & ಪ್ರಚಲಿತ ಘಟನೆಗಳು (News & Current Affairs)",
        "samples": [
            {
                "title": "ಜಾಗತಿಕ ಶೃಂಗಸಭೆ ಮತ್ತು ಭಾರತ (SCO Summit)",
                "text": "ಎಸ್‌ಸಿಒ ಸಮ್ಮೇಳನದಲ್ಲಿ ಭಾರತದ ಪಾತ್ರ ಅತ್ಯಂತ ಪ್ರಮುಖವಾಗಿದೆ. ಜಾಗತಿಕ ದಕ್ಷಿಣದ ದೇಶಗಳಿಗೆ ಭಾರತ ನೀಡಿದ ೧೦ ಅಂಶಗಳ ಕಾರ್ಯಸೂಚಿ ಇಡೀ ವಿಶ್ವದ ಗಮನ ಸೆಳೆದಿದೆ. ದೇಶದ ರಾಷ್ಟ್ರೀಯ ಭದ್ರತೆ ಮತ್ತು ಆರ್ಥಿಕ ಶಕ್ತಿ ಎರಡೂ ಅಷ್ಟೇ ಮುಖ್ಯ.",
                "voiceId": "podcast-narrator",
                "energy": "ultra"
            },
            {
                "title": "ವಿಜ್ಞಾನ ಮತ್ತು ಬಾಹ್ಯಾಕಾಶ ಸಾಧನೆ (ISRO Space)",
                "text": "ಇಸ್ರೋ ವಿಜ್ಞಾನಿಗಳು ಚಂದ್ರಯಾನ ಮತ್ತು ಆದಿತ್ಯ ಎಲ್-೧ ಯಶಸ್ಸಿನ ನಂತರ ಮುಂದಿನ ಮಾನವಸಹಿತ ಗಗನಯಾನ ಯೋಜನೆಗೆ ಸಜ್ಜಾಗುತ್ತಿದ್ದಾರೆ. ಇದು ಭಾರತೀಯ ವಿಜ್ಞಾನ ತಂತ್ರಜ್ಞಾನದ ಸುವರ್ಣ ಅಧ್ಯಾಯ.",
                "voiceId": "news-anchor",
                "energy": "high"
            },
            {
                "title": "ರಾಜ್ಯ ಹವಾಮಾನ ಮುನ್ಸೂಚನೆ (Weather Alert)",
                "text": "ಬೆಂಗಳೂರು ಮತ್ತು ಕರಾವಳಿ ಜಿಲ್ಲೆಗಳಲ್ಲಿ ಮುಂದಿನ ೨೪ ಗಂಟೆಗಳಲ್ಲಿ ಭಾರಿ ಮಳೆಯಾಗುವ ಸಾಧ್ಯತೆ ಇದೆ ಎಂದು ಹವಾಮಾನ ಇಲಾಖೆ ಎಚ್ಚರಿಕೆ ನೀಡಿದೆ. ತಾಪಮಾನ ೨೪ ಡಿಗ್ರಿ ಸೆಲ್ಸಿಯಸ್ ಇರಲಿದೆ.",
                "voiceId": "kn-IN-GaganNeural",
                "energy": "standard"
            }
        ]
    },
    {
        "category": "ದೈನಂದಿನ ಸಂಭಾಷಣೆ & ಶುಭಾಶಯಗಳು (Daily & Greetings)",
        "samples": [
            {
                "title": "ಶುಭೋದಯ ಸ್ವಾಗತ (Morning Greeting)",
                "text": "ಶುಭೋದಯ! ಧ್ವನಿ ಕನ್ನಡ ಆಡಿಯೊ ಸ್ಟುಡಿಯೋಗೆ ನಿಮಗೆ ಹೃತ್ಪೂರ್ವಕ ಸ್ವಾಗತ. ಇಂದು ನಿಮ್ಮ ದಿನವು ಸುಖ, ಶಾಂತಿ ಮತ್ತು ಸಂತೋಷದಿಂದ ಕೂಡಿರಲಿ.",
                "voiceId": "kn-IN-SapnaNeural",
                "energy": "standard"
            },
            {
                "title": "ಕಚೇರಿ ಸಂಭಾಷಣೆ (Professional Workplace)",
                "text": "ನಮಸ್ಕಾರ, ಇಂದಿನ ಯೋಜನೆಯ ಪ್ರಗತಿ ಪರಿಶೀಲನಾ ಸಭೆ ಮಧ್ಯಾಹ್ನ ೩:೩೦ ಕ್ಕೆ ನಿಗದಿಯಾಗಿದೆ. ದಯವಿಟ್ಟು ಎಲ್ಲರೂ ಸಮಯಕ್ಕೆ ಸರಿಯಾಗಿ ಹಾಜರಾಗಿ.",
                "voiceId": "kn-IN-GaganNeural",
                "energy": "standard"
            }
        ]
    },
    {
        "category": "ಸಾಹಿತ್ಯ, ಕವನ & ಕಥೆಗಳು (Literature & Storytelling)",
        "samples": [
            {
                "title": "ಕವಿವಾಣಿ - ಕುವೆಂಪು (Kuvempu Poetry)",
                "text": "ಹೆಸರಾಯಿತು ಕರ್ನಾಟಕ, ಉಸಿರಾಗಲಿ ಕನ್ನಡ. ಸಿರಿಗನ್ನಡಂ ಗೆಲ್ಗೆ, ಸಿರಿಗನ್ನಡಂ ಬಾಳ್ಗೆ! ಎಲ್ಲಾದರು ಇರು ಎಂತಾದರು ಇರು ಎಂದೆಂದಿಗೂ ನೀ ಕನ್ನಡವಾಗಿರು.",
                "voiceId": "storyteller",
                "energy": "standard"
            },
            {
                "title": "ಜನಪ್ರಿಯ ಹಿತವಚನ & ಗಾದೆಗಳು (Wisdom Proverbs)",
                "text": "ಹಾಸಿಗೆ ಇದ್ದಷ್ಟೇ ಕಾಲು ಚಾಚು. ಕೈ ಕೆಸರಾದರೆ ಬಾಯಿ ಮೊಸರು. ತಾಯಿಗಿಂತ ಬಂಧುವಿಲ್ಲ, ಉಪ್ಪಿಗಿಂತ ರುಚಿಯಿಲ್ಲ. ವಿದ್ಯೆಯೇ ಮನುಷ್ಯನಿಗೆ ಅತಿ ದೊಡ್ಡ ಆಭರಣ.",
                "voiceId": "storyteller",
                "energy": "standard"
            }
        ]
    },
    {
        "category": "ವಾಣಿಜ್ಯ, ಸಂಖ್ಯೆ & ಬ್ಯಾಂಕಿಂಗ್ (Finance & Tech)",
        "samples": [
            {
                "title": "ವ್ಯಾಪಾರ ಮತ್ತು ರಿಯಾಯಿತಿ (Offer & Discount)",
                "text": "ನಮ್ಮ ನೂತನ ಮಳಿಗೆಯಲ್ಲಿ ಒಟ್ಟು ೧೨೫೦ ಕ್ಕೂ ಹೆಚ್ಚು ಉತ್ಪನ್ನಗಳು ಲಭ್ಯವಿವೆ. ₹೪೫೦ ಮೌಲ್ಯದ ಖರೀದಿಗೆ ಶೇಕಡಾ ೨೦% ರಿಯಾಯಿತಿ ಸಿಗಲಿದೆ.",
                "voiceId": "kn-IN-SapnaNeural",
                "energy": "high"
            },
            {
                "title": "ಬ್ಯಾಂಕಿಂಗ್ ಒಟಿಪಿ ಸಂದೇಶ (Banking Security)",
                "text": "ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಖಾತೆಯಿಂದ ₹೨,೫೦೦ ಕಡಿತಗೊಂಡಿದೆ. ನಿಮ್ಮ ಯುಪಿಐ ವಹಿವಾಟು ಯಶಸ್ವಿಯಾಗಿದೆ. ಯಾವುದೇ ಸಂದರ್ಭದಲ್ಲೂ ಒಟಿಪಿ ಸಂಖ್ಯೆಯನ್ನು ಯಾರೊಂದಿಗೂ ಹಂಚಿಕೊಳ್ಳಬೇಡಿ.",
                "voiceId": "kn-IN-GaganNeural",
                "energy": "standard"
            }
        ]
    }
]

# ==========================================
# REST API ENDPOINTS
# ==========================================

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "Dhvani Kannada TTS Studio", "version": "2.0.0"}

@app.get("/api/voices")
def get_voices():
    return {"voices": VOICE_PROFILES}

@app.get("/api/presets")
def get_presets():
    return {"categories": PRESETS_DATA}

@app.post("/api/normalize")
def normalize_endpoint(payload: dict = Body(...)):
    text = payload.get("text", "")
    normalized = KannadaNormalizer.normalize(text)
    return {"original_text": text, "normalized_text": normalized}

@app.post("/api/analyze_audio")
async def analyze_audio_endpoint(reference_audio: UploadFile = File(...)):
    """Analyzes reference audio and returns acoustic characteristics."""
    ref_bytes = await reference_audio.read()
    if not ref_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")
    
    profile = AcousticVoiceCloner.extract_speaker_profile(ref_bytes)
    return {
        "filename": reference_audio.filename,
        "pitch_hz": round(profile["mean_pitch_hz"], 1),
        "duration_sec": round(profile["duration_sec"], 1),
        "gender": "male" if profile["is_male"] else "female",
        "vocal_resonance": round(profile["formant_factor"], 2),
        "energy_density": round(profile["dynamic_punch"], 2)
    }

@app.get("/api/history")
def get_history():
    return {"history": SYNTHESIS_HISTORY[-20:][::-1]}

@app.post("/api/synthesize")
async def synthesize_speech(payload: dict = Body(...)):
    text = payload.get("text", "").strip()
    voice = payload.get("voice", "kn-IN-SapnaNeural")
    pitch = payload.get("pitch", "+0Hz")
    rate = payload.get("rate", "+0%")
    volume = payload.get("volume", "+0%")
    energy_mode = payload.get("energy_mode", "standard") # "standard", "high", "ultra"
    eq_filter = payload.get("eq_filter", "natural") # "natural", "presence", "broadcast", "warm"

    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    normalized_text = KannadaNormalizer.normalize(text)
    
    # Map high-level voice IDs to base Neural models
    actual_voice = "kn-IN-SapnaNeural"
    if voice == "kn-IN-GaganNeural" or voice == "news-anchor" or "gagan" in voice.lower() or "male" in voice.lower():
        actual_voice = "kn-IN-GaganNeural"
    elif voice == "podcast-narrator":
        actual_voice = "kn-IN-GaganNeural"
        pitch = "-4Hz"
        rate = "+26%"
        energy_mode = "ultra"
    elif voice == "news-anchor":
        actual_voice = "kn-IN-GaganNeural"
        pitch = "+2Hz"
        rate = "+18%"
    elif voice == "storyteller":
        actual_voice = "kn-IN-SapnaNeural"
        pitch = "-1Hz"
        rate = "-6%"

    try:
        import edge_tts

        communicate = edge_tts.Communicate(
            text=normalized_text,
            voice=actual_voice,
            pitch=pitch,
            rate=rate,
            volume=volume
        )

        audio_buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_buffer.write(chunk["data"])

        audio_buffer.seek(0)
        raw_audio = audio_buffer.read()

        # Dynamic Audio Mastering / Equalizer
        if voice == "podcast-narrator" or energy_mode in ["high", "ultra"] or eq_filter in ["presence", "broadcast"]:
            profile = {"mean_pitch_hz": 125.0, "formant_factor": 1.15, "is_male": (actual_voice == "kn-IN-GaganNeural")}
            boost_val = 1.45 if energy_mode == "ultra" else 1.25
            raw_audio = AcousticVoiceCloner.morph_audio_to_profile(raw_audio, profile, energy_boost=boost_val)

        # Record to in-memory history
        SYNTHESIS_HISTORY.append({
            "id": f"clip_{int(time.time()*1000)}",
            "timestamp": time.strftime("%H:%M:%S"),
            "text": text[:60] + ("..." if len(text) > 60 else ""),
            "voice": voice,
            "duration": round(len(raw_audio) / 32000, 1)
        })

        return Response(
            content=raw_audio,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=dhvani_kannada.mp3",
                "X-Normalized-Text": normalized_text.encode('unicode_escape').decode('ascii')
            }
        )

    except Exception as e:
        # Fallback local tone generator
        sample_rate = 24000
        duration = max(1.0, len(normalized_text) * 0.12)
        num_samples = int(sample_rate * duration)
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            freq = 220.0
            for i in range(num_samples):
                val = int(14000.0 * math.sin(2.0 * math.pi * freq * (i / sample_rate)))
                wf.writeframes(struct.pack('<h', val))
        wav_io.seek(0)
        return Response(content=wav_io.read(), media_type="audio/wav")

@app.post("/api/clone_voice")
async def clone_voice_endpoint(
    text: str = Form(...),
    pitch: Optional[float] = Form(1.0),
    rate: Optional[float] = Form(1.0),
    energy_level: Optional[str] = Form("ultra"),
    api_key: Optional[str] = Form(None),
    reference_audio: UploadFile = File(...)
):
    """
    Performs True High-Energy Voice Cloning from reference audio.
    Analyzes acoustic properties and morphs speech into the reference speaker's vocal profile.
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    normalized_text = KannadaNormalizer.normalize(text)
    ref_bytes = await reference_audio.read()

    # 1. Extract speaker acoustic profile
    profile = AcousticVoiceCloner.extract_speaker_profile(ref_bytes)

    # 2. Optional ElevenLabs 1:1 Instant Human Cloning if key provided
    eleven_key = api_key or os.getenv("ELEVENLABS_API_KEY")
    if eleven_key:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                add_voice_url = "https://api.elevenlabs.io/v1/voices/add"
                headers = {"xi-api-key": eleven_key}
                files = {"files": (reference_audio.filename or "sample.mp3", ref_bytes, "audio/mpeg")}
                data = {"name": f"Cloned_{reference_audio.filename[:15]}", "description": "Kannada cloned speaker"}
                
                res = await client.post(add_voice_url, headers=headers, files=files, data=data)
                if res.status_code == 200:
                    voice_id = res.json().get("voice_id")
                    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                    payload = {
                        "text": normalized_text,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {
                            "stability": 0.35,
                            "similarity_boost": 0.90,
                            "style": 0.55,
                            "use_speaker_boost": True
                        }
                    }
                    tts_res = await client.post(tts_url, headers=headers, json=payload)
                    if tts_res.status_code == 200:
                        return Response(
                            content=tts_res.content,
                            media_type="audio/mpeg",
                            headers={"Content-Disposition": "attachment; filename=cloned_kannada_voice.mp3"}
                        )
        except Exception as e:
            print(f"ElevenLabs cloning failed: {e}. Fallback to acoustic morphing...")

    # 3. Acoustic Voice Morphing matching reference speaker
    ref_pitch_hz = profile.get("mean_pitch_hz", 125.0)
    hz_offset = int(ref_pitch_hz - 130.0) + int((pitch - 1.0) * 30.0)
    pitch_str = f"+{hz_offset}Hz" if hz_offset >= 0 else f"{hz_offset}Hz"
    
    base_rate_delta = 26 if energy_level == "ultra" else (16 if energy_level == "high" else 0)
    rate_delta = int((rate - 1.0) * 100.0) + base_rate_delta
    rate_str = f"+{rate_delta}%" if rate_delta >= 0 else f"{rate_delta}%"

    base_voice = "kn-IN-GaganNeural" if profile["is_male"] else "kn-IN-SapnaNeural"

    try:
        import edge_tts
        communicate = edge_tts.Communicate(
            text=normalized_text,
            voice=base_voice,
            pitch=pitch_str,
            rate=rate_str
        )
        audio_stream = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])
        audio_stream.seek(0)
        raw_mp3 = audio_stream.read()

        energy_boost_val = 1.50 if energy_level == "ultra" else 1.25
        cloned_audio = AcousticVoiceCloner.morph_audio_to_profile(raw_mp3, profile, energy_boost=energy_boost_val)

        return Response(
            content=cloned_audio,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=cloned_kannada_voice.mp3"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# STATIC FILES & WEB STUDIO MOUNT
# ==========================================

@app.get("/")
def serve_index():
    index_file = WEB_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Dhvani Kannada TTS Studio API Running. Web interface at /web"}

@app.get("/styles.css")
def serve_css():
    return FileResponse(WEB_DIR / "styles.css", media_type="text/css")

@app.get("/app.js")
def serve_js():
    return FileResponse(WEB_DIR / "app.js", media_type="application/javascript")

if __name__ == "__main__":
    print("================================================================")
    print("  ಧ್ವನಿ KANNADA TEXT-TO-SPEECH WEB STUDIO IS RUNNING!           ")
    print("  Open in browser: http://localhost:8000                         ")
    print("================================================================")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
