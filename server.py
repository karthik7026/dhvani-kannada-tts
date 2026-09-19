#!/usr/bin/env python3
"""
Dhvani Kannada Text-to-Speech & Voice Delivery Studio Server (ಧ್ವನಿ ಕನ್ನಡ ವೆಬ್ ಸ್ಟುಡಿಯೋ) v3.0
FastAPI Backend delivering high-fidelity Kannada neural synthesis, delivery/prosody style transfer,
configurable pronunciation dictionary, text normalization, and broadcast mastering.
"""

import os
import io
import re
import json
import wave
import struct
import math
import time
import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body, Header, Query
from fastapi.responses import Response, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx

from pronunciation_engine import KannadaPronunciationEngine, normalize_kannada_text
from kannada_normalizer import KannadaNormalizer
from voice_cloner import AcousticVoiceCloner
from delivery_profiler import DeliveryProfiler
from prosody_mapper import KannadaProsodyMapper
from indic_f5_engine import IndicF5Engine

app = FastAPI(
    title="Dhvani Kannada TTS Studio API",
    description="High-Fidelity Kannada Neural Text-to-Speech & Reference Delivery Style Studio with Pronunciation Optimization",
    version="3.0.0"
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
        "category": "ವಾಣಿಜ್ಯ, ಡಿಜಿಟಲ್ ಪಾವತಿ & ತಂತ್ರಜ್ಞಾನ (FinTech & Tech)",
        "samples": [
            {
                "title": "ಡಿಜಿಟಲ್ ಪಾವತಿ & MDR (Digital Payment & MDR)",
                "text": "ನಮ್ಮ ದೇಶದಲ್ಲಿ UPI ಮೂಲಕ digital payment ಕ್ರಾಂತಿ ಸೃಷ್ಟಿಯಾಗಿದೆ. ಸಣ್ಣ ವ್ಯಾಪಾರಿಗಳಿಗೆ MDR ಶೇಕಡಾ 1% ಗಿಂತ ಕಡಿಮೆ ಇರಲಿದ್ದು, ₹1000 ಖರೀದಿಗೆ ₹10 ಕ್ಯಾಶ್‌ಬ್ಯಾಕ್ ಸಿಗಲಿದೆ.",
                "voiceId": "podcast-narrator",
                "energy": "high"
            },
            {
                "title": "ಕೃತಕ ಬುದ್ಧಿಮತ್ತೆ & API (AI & APIs)",
                "text": "YouTube ಮತ್ತು ChatGPT ನಲ್ಲಿ AI ತಂತ್ರಜ್ಞಾನದ ಬಗ್ಗೆ ಮಾಹಿತಿ ಲಭ್ಯವಿದೆ. ನೂತನ TTS API ಬಳಸಿ ಸುಲಭವಾಗಿ ಕನ್ನಡ ಆಡಿಯೋ ರಚಿಸಬಹುದು.",
                "voiceId": "podcast-narrator",
                "energy": "high"
            },
            {
                "title": "ಬ್ಯಾಂಕಿಂಗ್ ಒಟಿಪಿ ಸಂದೇಶ (Banking Security)",
                "text": "ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಖಾತೆಯಿಂದ ₹೨,೫೦೦ ಕಡಿತಗೊಂಡಿದೆ. ನಿಮ್ಮ ಯುಪಿಐ ವಹಿವಾಟು ಯಶಸ್ವಿಯಾಗಿದೆ. ಯಾವುದೇ ಸಂದರ್ಭದಲ್ಲೂ ಒಟಿಪಿ ಸಂಖ್ಯೆಯನ್ನು ಯಾರೊಂದಿಗೂ ಹಂಚಿಕೊಳ್ಳಬೇಡಿ.",
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
    }
]

# ==========================================
# REST API ENDPOINTS
# ==========================================

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "Dhvani Kannada TTS Studio", "version": "3.0.0"}

@app.get("/api/voices")
def get_voices():
    return {"voices": VOICE_PROFILES}

@app.get("/api/presets")
def get_presets():
    return {"categories": PRESETS_DATA}

@app.get("/api/history")
def get_history():
    return {"history": SYNTHESIS_HISTORY[-20:][::-1]}

# -------------------------------------------------------------
# PRONUNCIATION & NORMALIZATION ENDPOINTS
# -------------------------------------------------------------

@app.post("/api/normalize")
def normalize_endpoint(payload: dict = Body(...)):
    """Normalizes input text and returns full pronunciation debug breakdown."""
    text = payload.get("text", "")
    debug_info = KannadaPronunciationEngine.get_debug_breakdown(text)
    return debug_info

@app.post("/api/pronunciation_debug")
def pronunciation_debug_endpoint(payload: dict = Body(...)):
    """
    3-Stage Pronunciation Debug Mode:
    - Original text (display_text)
    - Normalized intermediate text
    - Final speech text (sent to Edge-TTS)
    - Transformation audit logs
    """
    text = payload.get("text", "")
    return KannadaPronunciationEngine.get_debug_breakdown(text)

@app.get("/api/dictionary")
def get_dictionary_endpoint():
    """Returns the user-configurable pronunciation dictionary."""
    return KannadaPronunciationEngine.load_dictionary()

@app.post("/api/dictionary")
def update_dictionary_endpoint(payload: dict = Body(...)):
    """Updates the user pronunciation dictionary and hot-reloads it in memory."""
    success = KannadaPronunciationEngine.save_dictionary(payload)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save dictionary")
    return {"status": "success", "dictionary": KannadaPronunciationEngine.load_dictionary()}

@app.post("/api/dictionary/entry")
def add_dictionary_entry_endpoint(payload: dict = Body(...)):
    """Adds or updates a single word/acronym entry in the dictionary."""
    category = payload.get("category") or payload.get("type", "words")
    key = payload.get("key", "").strip()
    value = payload.get("value", "").strip()

    if not key or not value:
        raise HTTPException(status_code=400, detail="Key and value cannot be empty")

    success = KannadaPronunciationEngine.add_dictionary_entry(key, value, category)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save dictionary entry")
    return {"status": "success", "added": {key: value}, "category": category}

@app.delete("/api/dictionary/entry")
def delete_dictionary_entry_endpoint(
    category: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    key: str = Query(...)
):
    """Deletes an entry from words or acronyms."""
    cat = category or type or "words"
    success = KannadaPronunciationEngine.remove_dictionary_entry(key, cat)
    if success:
        return {"status": "deleted", "key": key, "category": cat}
    raise HTTPException(status_code=404, detail="Entry not found")

# -------------------------------------------------------------
# DELIVERY PROSODY STYLE TRANSFER ENDPOINTS
# -------------------------------------------------------------

@app.post("/api/analyze_delivery")
async def analyze_delivery_endpoint(reference_audio: UploadFile = File(...)):
    """Extracts language-agnostic Delivery Prosody statistics from reference audio."""
    audio_bytes = await reference_audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty reference audio")
    
    profile = DeliveryProfiler.extract_prosody_profile(audio_bytes, max_duration_sec=60.0)
    profile["filename"] = reference_audio.filename
    return profile

@app.post("/api/preview_prosody_plan")
def preview_prosody_plan_endpoint(payload: dict = Body(...)):
    """Returns real-time phrase segmentation with pronunciation-optimized speech text."""
    text = payload.get("text", "").strip()
    voice = payload.get("voice", "kn-IN-GaganNeural")
    energy_mode = payload.get("energy_mode", "high_energy")
    pitch_depth = float(payload.get("pitch_depth", 1.0))
    pacing_multiplier = float(payload.get("pacing_multiplier", 1.0))
    pause_style = payload.get("pause_style", "snappy")
    profile = payload.get("profile", None)

    plan = KannadaProsodyMapper.get_realtime_prosody_plan(
        kannada_text=text,
        voice=voice,
        energy_mode=energy_mode,
        pitch_depth=pitch_depth,
        pacing_multiplier=pacing_multiplier,
        pause_style=pause_style,
        prosody_profile=profile
    )
    return plan

@app.post("/api/synthesize_delivery")
async def synthesize_delivery_endpoint(
    text: str = Form(...),
    voice: str = Form("kn-IN-GaganNeural"),
    energy_mode: str = Form("high_energy"),
    pitch_depth: float = Form(1.0),
    pacing_multiplier: float = Form(1.0),
    pause_style: str = Form("snappy"),
    profile_json: Optional[str] = Form(None),
    reference_audio: Optional[UploadFile] = File(None)
):
    """
    Synthesizes Kannada text with expressive reference delivery while
    strictly preserving 100% of the selected speaker identity (Gagan or Sapna)
    and optimizing pronunciation via KannadaPronunciationEngine.
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    prosody_profile = None
    if reference_audio is not None:
        audio_bytes = await reference_audio.read()
        if audio_bytes:
            prosody_profile = DeliveryProfiler.extract_prosody_profile(audio_bytes, max_duration_sec=60.0)
    
    if prosody_profile is None and profile_json:
        try:
            prosody_profile = json.loads(profile_json)
        except Exception:
            pass

    try:
        audio_bytes, meta = await KannadaProsodyMapper.synthesize_with_delivery_style(
            kannada_text=text,
            voice=voice,
            energy_mode=energy_mode,
            pitch_depth=pitch_depth,
            pacing_multiplier=pacing_multiplier,
            pause_style=pause_style,
            prosody_profile=prosody_profile
        )

        SYNTHESIS_HISTORY.append({
            "id": f"clip_{int(time.time()*1000)}",
            "timestamp": time.strftime("%H:%M:%S"),
            "text": text[:60] + ("..." if len(text) > 60 else ""),
            "voice": f"{voice} [Delivery Styled - {energy_mode.upper()}]",
            "duration": meta.get("duration_sec", 0.0)
        })

        media_type = "audio/wav" if audio_bytes.startswith(b"RIFF") else "audio/mpeg"
        filename = "dhvani_delivery_styled.wav" if audio_bytes.startswith(b"RIFF") else "dhvani_delivery_styled.mp3"
        return Response(
            content=audio_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-Delivery-Meta": json.dumps({
                    "voice": meta.get("voice_used"),
                    "duration": meta.get("duration_sec"),
                    "phrase_count": meta.get("phrase_count"),
                    "energy_mode": meta.get("energy_mode"),
                    "overall_pace": meta.get("overall_pace")
                }, ensure_ascii=True)
            }
        )

    except Exception as e:
        print(f"Error in synthesize_delivery: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------------------------------------------
# STANDARD NORMAL TTS SYNTHESIS WITH PRONUNCIATION PREPROCESSING
# -------------------------------------------------------------

@app.post("/api/synthesize")
async def synthesize_speech(payload: dict = Body(...)):
    text = payload.get("text", "").strip()
    voice = payload.get("voice", "kn-IN-SapnaNeural")
    pitch = payload.get("pitch", "+0Hz")
    rate = payload.get("rate", "+0%")
    volume = payload.get("volume", "+0%")
    energy_mode = payload.get("energy_mode", "standard")
    eq_filter = payload.get("eq_filter", "natural")

    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    display_text, speech_text, transforms = KannadaPronunciationEngine.process_pronunciation(text)
    
    actual_voice = "kn-IN-SapnaNeural"
    if voice == "podcast-narrator":
        actual_voice = "kn-IN-GaganNeural"
        pitch = "-4Hz"
        rate = "+26%"
        energy_mode = "ultra"
    elif voice == "news-anchor":
        actual_voice = "kn-IN-GaganNeural"
        pitch = "+2Hz"
        rate = "+18%"
    elif voice == "kn-IN-GaganNeural" or "gagan" in voice.lower() or "male" in voice.lower():
        actual_voice = "kn-IN-GaganNeural"
    elif voice == "storyteller":
        actual_voice = "kn-IN-SapnaNeural"
        pitch = "-1Hz"
        rate = "-6%"

    try:
        import edge_tts

        communicate = edge_tts.Communicate(
            text=speech_text,
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

        SYNTHESIS_HISTORY.append({
            "id": f"clip_{int(time.time()*1000)}",
            "timestamp": time.strftime("%H:%M:%S"),
            "text": display_text[:60] + ("..." if len(display_text) > 60 else ""),
            "voice": f"{actual_voice} [Normal Mode]",
            "duration": round(len(raw_audio) / 32000, 1)
        })

        return Response(
            content=raw_audio,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=dhvani_kannada.mp3",
                "X-Display-Text": display_text.encode('unicode_escape').decode('ascii'),
                "X-Speech-Text": speech_text.encode('unicode_escape').decode('ascii')
            }
        )

    except Exception as e:
        print(f"Edge TTS synthesis failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Kannada speech service is unavailable. Check your internet connection and try again."
        ) from e

# -------------------------------------------------------------
# AI4BHARAT INDICF5 LOCAL ZERO-SHOT CLONING ENDPOINTS
# -------------------------------------------------------------

@app.get("/api/indic_f5/status")
def indic_f5_status_endpoint():
    return IndicF5Engine.get_status()

@app.post("/api/indic_f5/synthesize")
async def indic_f5_synthesize_endpoint(
    text: str = Form(...),
    ref_transcript: Optional[str] = Form(None),
    hf_token: Optional[str] = Form(None),
    reference_audio: Optional[UploadFile] = File(None)
):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    ref_audio_bytes = None
    if reference_audio is not None:
        ref_audio_bytes = await reference_audio.read()

    try:
        audio_bytes, meta = await IndicF5Engine.synthesize(
            kannada_text=text,
            ref_audio_path_or_bytes=ref_audio_bytes,
            ref_transcript=ref_transcript,
            hf_token=hf_token
        )

        SYNTHESIS_HISTORY.append({
            "id": f"clip_{int(time.time()*1000)}",
            "timestamp": time.strftime("%H:%M:%S"),
            "text": text[:60] + ("..." if len(text) > 60 else ""),
            "voice": f"IndicF5 Zero-Shot [{meta.get('device', 'cpu').upper()}]",
            "duration": meta.get("duration_sec", 0.0)
        })

        media_type = "audio/wav" if audio_bytes.startswith(b"RIFF") else "audio/mpeg"
        filename = "dhvani_indic_f5.wav" if audio_bytes.startswith(b"RIFF") else "dhvani_indic_f5.mp3"

        return Response(
            content=audio_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "X-IndicF5-Meta": json.dumps(meta, ensure_ascii=True)
            }
        )

    except Exception as e:
        print(f"Error in indic_f5_synthesize: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# STATIC FILES & WEB STUDIO MOUNT
# ==========================================

@app.get("/")
def serve_index():
    index_file = WEB_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Dhvani Kannada TTS Studio API Running."}

@app.get("/styles.css")
def serve_css():
    return FileResponse(WEB_DIR / "styles.css", media_type="text/css")

@app.get("/app.js")
def serve_js():
    return FileResponse(WEB_DIR / "app.js", media_type="application/javascript")

if __name__ == "__main__":
    print("================================================================")
    print("  ಧ್ವನಿ KANNADA TEXT-TO-SPEECH WEB STUDIO v3.0 IS RUNNING!       ")
    print("  Open in browser: http://localhost:8000                         ")
    print("================================================================")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
