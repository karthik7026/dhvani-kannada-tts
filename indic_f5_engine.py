#!/usr/bin/env python3
"""
Dhvani Kannada IndicF5 Neural Zero-Shot Engine (ಧ್ವನಿ ಇಂಡಿಕ್-F5 ನರ ಎಂಜಿನ್)
Provides 100% local zero-shot voice cloning and expressive synthesis using AI4Bharat/IndicF5
with automatic device selection (Apple Silicon MPS / CUDA / CPU) and seamless fallback to the local prosody engine.
"""

import os
import io
import time
import wave
import torch
import shutil
import tempfile
import numpy as np
from typing import Optional, Tuple, Dict, Any
from pathlib import Path

try:
    from kannada_normalizer import KannadaNormalizer
except ImportError:
    class KannadaNormalizer:
        @staticmethod
        def normalize(t): return t

try:
    from prosody_mapper import apply_broadcast_mastering
except ImportError:
    def apply_broadcast_mastering(pcm_data, sr=24000, punch=1.35):
        return pcm_data

class IndicF5Engine:
    """
    Singleton Manager for AI4Bharat/IndicF5 Zero-Shot Voice Cloning Model.
    """
    _instance = None
    _model = None
    _device = None
    _status = "unloaded"
    _error_msg = None

    @classmethod
    def get_device(cls) -> str:
        if cls._device is None:
            if torch.backends.mps.is_available():
                cls._device = "mps"
            elif torch.cuda.is_available():
                cls._device = "cuda"
            else:
                cls._device = "cpu"
        return cls._device

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        return {
            "status": cls._status,
            "device": cls.get_device(),
            "model_name": "ai4bharat/IndicF5",
            "is_ready": cls._model is not None,
            "error": cls._error_msg,
            "has_hf_token": bool(os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN"))
        }

    @classmethod
    def load_model(cls, hf_token: Optional[str] = None) -> bool:
        """
        Loads the AI4Bharat/IndicF5 model weights locally into memory.
        """
        if cls._model is not None:
            return True

        token = hf_token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        cls._status = "loading"

        try:
            from transformers import AutoModel
            repo_id = "ai4bharat/IndicF5"
            print(f"[IndicF5] Loading {repo_id} onto {cls.get_device()}...")
            
            cls._model = AutoModel.from_pretrained(
                repo_id,
                trust_remote_code=True,
                token=token
            )
            cls._status = "ready"
            cls._error_msg = None
            print("[IndicF5] Model loaded successfully!")
            return True

        except Exception as e:
            cls._status = "error"
            err_str = str(e)
            if "gated repo" in err_str.lower() or "restricted" in err_str.lower():
                cls._error_msg = "IndicF5 is a free gated model on Hugging Face. Please accept terms at https://huggingface.co/ai4bharat/IndicF5 and provide your free HF_TOKEN."
            else:
                cls._error_msg = err_str
            print(f"[IndicF5] Load notice: {cls._error_msg}")
            return False

    @classmethod
    async def synthesize(
        cls,
        kannada_text: str,
        ref_audio_path_or_bytes: Optional[Any] = None,
        ref_transcript: Optional[str] = None,
        hf_token: Optional[str] = None
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Synthesizes Kannada speech using IndicF5 Zero-Shot Cloning.
        If model is unavailable or HF token is pending, seamlessly falls back to
        the high-impact local prosody engine (preserving zero downtime).
        """
        norm_text = KannadaNormalizer.normalize(kannada_text.strip())
        t0 = time.time()

        # Try loading IndicF5 if not yet loaded
        if cls._model is None:
            cls.load_model(hf_token=hf_token)

        if cls._model is not None:
            temp_ref_path = None
            try:
                if isinstance(ref_audio_path_or_bytes, bytes):
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                        f.write(ref_audio_path_or_bytes)
                        temp_ref_path = f.name
                elif isinstance(ref_audio_path_or_bytes, str) and os.path.exists(ref_audio_path_or_bytes):
                    temp_ref_path = ref_audio_path_or_bytes
                else:
                    # Default built-in presenter reference
                    default_ref = "uploads/ref_vidssave.com ✊🏼INDIA🇮🇳vs PAK at SCO summit💥 720P.mp3"
                    temp_ref_path = default_ref if os.path.exists(default_ref) else None

                audio_output = cls._model(
                    text=norm_text,
                    ref_audio_path=temp_ref_path,
                    ref_text=ref_transcript or "Transcript of reference audio"
                )

                pcm_data = np.array(audio_output, dtype=np.float32)
                sr = 24000

                # Master audio for broadcast clarity
                mastered = apply_broadcast_mastering(pcm_data, sr=sr, punch=1.35)
                out_int16 = (mastered * 32767).astype(np.int16)

                buf = io.BytesIO()
                with wave.open(buf, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(sr)
                    wf.writeframes(out_int16.tobytes())

                duration = round(len(out_int16) / sr, 2)
                metadata = {
                    "engine": "AI4Bharat/IndicF5",
                    "device": cls.get_device(),
                    "duration_sec": duration,
                    "synthesis_time_sec": round(time.time() - t0, 2),
                    "zero_shot_cloned": bool(temp_ref_path)
                }

                return buf.getvalue(), metadata

            finally:
                if temp_ref_path and temp_ref_path.startswith(tempfile.gettempdir()):
                    try:
                        os.remove(temp_ref_path)
                    except Exception:
                        pass

        # Seamless Fallback to Local Prosody Delivery Engine
        from prosody_mapper import KannadaProsodyMapper
        audio_bytes, meta = await KannadaProsodyMapper.synthesize_with_delivery_style(
            kannada_text=norm_text,
            voice="kn-IN-GaganNeural"
        )
        meta["engine"] = "Dhvani Hybrid Prosody Engine (Local Fallback)"
        meta["fallback_reason"] = cls._error_msg or "IndicF5 token pending"
        return audio_bytes, meta
