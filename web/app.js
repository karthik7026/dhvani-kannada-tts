/**
 * Dhvani Kannada Text-to-Speech Studio - Frontend Engine v2.0
 */

document.addEventListener("DOMContentLoaded", () => {
    // Studio State
    const state = {
        gender: "female",
        voice: "kn-IN-SapnaNeural",
        pitch: 0,           // in Hz (-30 to +30)
        rate: 1.0,          // 0.5x to 2.0x
        volume: 100,        // 0 to 100%
        preset: "natural",
        energyMode: "ultra",// "ultra", "high", "standard"
        eqFilter: "natural",// "natural", "presence", "broadcast", "warm"
        playbackSpeed: 1.0,
        isTranslitOn: false,
        uploadedAudioFile: null,
        isPlaying: false,
        isLoading: false,
        currentAudioUrl: null,
        theme: "dark",
        history: []
    };

    // DOM Elements
    const kannadaInput = document.getElementById("kannadaInput");
    const charCount = document.getElementById("charCount");
    const wordCount = document.getElementById("wordCount");
    const estimatedDuration = document.getElementById("estimatedDuration");
    const translitToggleBtn = document.getElementById("translitToggleBtn");
    const translitLabel = document.getElementById("translitLabel");
    const clearTextBtn = document.getElementById("clearTextBtn");
    const copyTextBtn = document.getElementById("copyTextBtn");
    const normalizedPreview = document.getElementById("normalizedPreview");

    const voiceCards = document.querySelectorAll(".voice-card");
    const voiceCloneUploader = document.getElementById("voiceCloneUploader");
    const audioFileInput = document.getElementById("audioFileInput");
    const uploadFileName = document.getElementById("uploadFileName");
    const refAudioPreviewCard = document.getElementById("refAudioPreviewCard");
    const refAudioPlayer = document.getElementById("refAudioPlayer");
    const refAudioMeta = document.getElementById("refAudioMeta");
    const analysisDetails = document.getElementById("analysisDetails");
    const directCloneBtn = document.getElementById("directCloneBtn");

    const eqChips = document.querySelectorAll(".eq-chip");
    const energyChips = document.querySelectorAll(".energy-chip");
    const pitchSlider = document.getElementById("pitchSlider");
    const pitchValue = document.getElementById("pitchValue");
    const rateSlider = document.getElementById("rateSlider");
    const rateValue = document.getElementById("rateValue");
    const volumeSlider = document.getElementById("volumeSlider");
    const volumeValue = document.getElementById("volumeValue");

    const audioPlayer = document.getElementById("audioPlayer");
    const playBtn = document.getElementById("playBtn");
    const playIcon = document.getElementById("playIcon");
    const pauseIcon = document.getElementById("pauseIcon");
    const loadingSpinner = document.getElementById("loadingSpinner");
    const stopBtn = document.getElementById("stopBtn");
    const downloadBtn = document.getElementById("downloadBtn");
    const playbackSpeedBtn = document.getElementById("playbackSpeedBtn");
    const statusText = document.getElementById("statusText");
    const activeVoiceInfo = document.getElementById("activeVoiceInfo");
    const audioScrubber = document.getElementById("audioScrubber");
    const currentTimeEl = document.getElementById("currentTime");
    const durationTimeEl = document.getElementById("durationTime");

    const waveformCanvas = document.getElementById("waveformCanvas");
    const canvasCtx = waveformCanvas.getContext("2d");

    const presetsModal = document.getElementById("presetsModal");
    const openPresetsBtn = document.getElementById("openPresetsBtn");
    const closePresetsBtn = document.getElementById("closePresetsBtn");
    const modalCategories = document.getElementById("modalCategories");
    const modalSamplesList = document.getElementById("modalSamplesList");

    const historyDrawer = document.getElementById("historyDrawer");
    const openHistoryBtn = document.getElementById("openHistoryBtn");
    const closeHistoryBtn = document.getElementById("closeHistoryBtn");
    const historyList = document.getElementById("historyList");

    const themeToggleBtn = document.getElementById("themeToggleBtn");
    const toast = document.getElementById("toast");

    // ==========================================
    // 1. TEXT METRICS & NORMALIZATION PREVIEW
    // ==========================================
    function updateTextMetrics() {
        const text = kannadaInput.value;
        charCount.textContent = `${text.length} ಅಕ್ಷರಗಳು`;
        const words = text.trim() ? text.trim().split(/\s+/).length : 0;
        wordCount.textContent = `${words} ಶಬ್ದಗಳು`;
        
        // Approx duration calculation: ~3.5 aksharas per sec / 1.0x rate
        const estSec = (text.length * 0.08 / Math.max(0.5, state.rate)).toFixed(1);
        estimatedDuration.textContent = `~${estSec} ಸೆಕೆಂಡುಗಳು`;

        clearTimeout(window._normTimeout);
        window._normTimeout = setTimeout(fetchNormalization, 250);
    }

    async function fetchNormalization() {
        const text = kannadaInput.value;
        if (!text.trim()) {
            normalizedPreview.textContent = "(ಖಾಲಿ)";
            return;
        }
        try {
            const res = await fetch("/api/normalize", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text })
            });
            if (res.ok) {
                const data = await res.json();
                normalizedPreview.textContent = data.normalized_text;
            }
        } catch (e) {
            normalizedPreview.textContent = text;
        }
    }

    kannadaInput.addEventListener("input", updateTextMetrics);

    clearTextBtn.addEventListener("click", () => {
        kannadaInput.value = "";
        updateTextMetrics();
        kannadaInput.focus();
    });

    copyTextBtn.addEventListener("click", () => {
        if (!kannadaInput.value.trim()) return;
        navigator.clipboard.writeText(kannadaInput.value);
        showToast("ಪಠ್ಯವನ್ನು ನಕಲಿಸಲಾಗಿದೆ (Copied)!");
    });

    // ==========================================
    // 2. KANNADA PHONETIC TRANSLITERATION ENGINE
    // ==========================================
    translitToggleBtn.addEventListener("click", () => {
        state.isTranslitOn = !state.isTranslitOn;
        translitToggleBtn.classList.toggle("active", state.isTranslitOn);
        translitLabel.textContent = state.isTranslitOn ? "ಲಿಪ್ಯಂತರಣ En ➔ ಕ [ON]" : "ಲಿಪ್ಯಂತರಣ En ➔ ಕ [OFF]";
        showToast(state.isTranslitOn ? "ಕನ್ನಡ ಲಿಪ್ಯಂತರಣ ಸಕ್ರಿಯವಾಗಿದೆ (Transliteration ON)" : "ಲಿಪ್ಯಂತರಣ ನಿಷ್ಕ್ರಿಯವಾಗಿದೆ (OFF)");
    });

    // Comprehensive Phonetic Transliteration Rules
    const PHONETIC_DICT = {
        'namaskara': 'ನಮಸ್ಕಾರ', 'namaste': 'ನಮಸ್ತೆ', 'kannada': 'ಕನ್ನಡ', 'karnataka': 'ಕರ್ನಾಟಕ',
        'bengaluru': 'ಬೆಂಗಳೂರು', 'mysuru': 'ಮೈಸೂರು', 'shubhodaya': 'ಶುಭೋದಯ', 'shubhadina': 'ಶುಭದಿನ',
        'hegiddeera': 'ಹೇಗಿದ್ದೀರ', 'hegiddira': 'ಹೇಗಿದ್ದೀರಾ', 'chennagiddene': 'ಚೆನ್ನಾಗಿದ್ದೇನೆ',
        'dhanyavada': 'ಧನ್ಯವಾದ', 'dhanyavadagalu': 'ಧನ್ಯವಾದಗಳು', 'bharata': 'ಭಾರತ', 'desha': 'ದೇಶ',
        'vidya': 'ವಿದ್ಯಾ', 'shala': 'ಶಾಲೆ', 'pustaka': 'ಪುಸ್ತಕ', 'swagata': 'ಸ್ವಾಗತ', 'surya': 'ಸೂರ್ಯ',
        'chandra': 'ಚಂದ್ರ', 'preeti': 'ಪ್ರೀತಿ', 'sneha': 'ಸ್ನೇಹ', 'santosha': 'ಸಂತೋಷ', 'karya': 'ಕಾರ್ಯ',
        'janapriya': 'ಜನಪ್ರಿಯ', 'varte': 'ವಾರ್ತೆ', 'suddi': 'ಸುದ್ದಿ', 'havamana': 'ಹವಾಮಾನ',
        'kaala': 'ಕಾಲ', 'samaya': 'ಸಮಯ', 'rajya': 'ರಾಜ್ಯ', 'deshada': 'ದೇಶದ', 'nanna': 'ನನ್ನ',
        'nimma': 'ನಿಮ್ಮ', 'hesaru': 'ಹೆಸರು', 'yaaru': 'ಯಾರು', 'yenu': 'ಏನು', 'yelli': 'ಎಲ್ಲಿ',
        'hege': 'ಹೇಗೆ', 'yaake': 'ಯಾಕೆ', 'houdu': 'ಹೌದು', 'illa': 'ಇಲ್ಲ', 'beeku': 'ಬೇಕು', 'beda': 'ಬೇಡ'
    };

    function transliteratePhonetic(input) {
        const lower = input.toLowerCase();
        if (PHONETIC_DICT[lower]) return PHONETIC_DICT[lower];

        // Rule-based fallback converter
        const vowels = {
            'aa': 'ಾ', 'a': '', 'ee': 'ೀ', 'ii': 'ೀ', 'i': 'ಿ', 'oo': 'ೂ', 'uu': 'ೂ', 'u': 'ು',
            'ai': 'ೈ', 'au': 'ೌ', 'e': 'ೆ', 'o': 'ೊ'
        };
        const initialVowels = {
            'aa': 'ಆ', 'a': 'ಅ', 'ee': 'ಈ', 'ii': 'ಈ', 'i': 'ಇ', 'oo': 'ಊ', 'uu': 'ಊ', 'u': 'ಉ',
            'ai': 'ಐ', 'au': 'ಔ', 'e': 'ಎ', 'o': 'ಒ', 'ru': 'ಋ'
        };
        const consonants = {
            'kh': 'ಖ', 'k': 'ಕ', 'gh': 'ಘ', 'g': 'ಗ', 'ch': 'ಚ', 'chh': 'ಛ', 'j': 'ಜ', 'jh': 'ಝ',
            'th': 'ಥ', 't': 'ತ', 'dh': 'ಧ', 'd': 'ದ', 'ph': 'ಫ', 'p': 'ಪ', 'bh': 'ಭ', 'b': 'ಬ',
            'm': 'ಮ', 'y': 'ಯ', 'r': 'ರ', 'l': 'ಲ', 'v': 'ವ', 'w': 'ವ', 'sh': 'ಶ', 's': 'ಸ', 'h': 'ಹ',
            'n': 'ನ', 'ng': 'ಂ', 'ny': 'ಞ'
        };

        // If direct match not in dict, return input for now
        return input;
    }

    kannadaInput.addEventListener("keydown", (e) => {
        if (!state.isTranslitOn) return;
        if (e.key === " " || e.key === "Enter") {
            const pos = kannadaInput.selectionStart;
            const full = kannadaInput.value;
            const before = full.slice(0, pos);
            const after = full.slice(pos);

            const match = before.match(/([a-zA-Z]+)$/);
            if (match) {
                const word = match[1];
                const converted = transliteratePhonetic(word);
                if (converted !== word) {
                    e.preventDefault();
                    const newBefore = before.slice(0, before.length - word.length) + converted + (e.key === "Enter" ? "\n" : " ");
                    kannadaInput.value = newBefore + after;
                    kannadaInput.selectionStart = kannadaInput.selectionEnd = newBefore.length;
                    updateTextMetrics();
                }
            }
        }
    });

    // ==========================================
    // 3. VOICE SELECTION & PRESETS
    // ==========================================
    voiceCards.forEach(card => {
        card.addEventListener("click", () => {
            voiceCards.forEach(c => c.classList.remove("active"));
            card.classList.add("active");
            
            const gender = card.dataset.gender;
            const voice = card.dataset.voice;
            const preset = card.dataset.preset;

            state.gender = gender;
            state.voice = voice || "kn-IN-SapnaNeural";

            if (gender === "custom") {
                voiceCloneUploader.classList.remove("hidden");
                state.preset = "custom";
                updateStatusMeta("Voice Clone", "ಕಸ್ಟಮ್ ಆಡಿಯೊ");
            } else {
                voiceCloneUploader.classList.add("hidden");
                if (preset === "podcast") {
                    applyPreset("podcast", -4, 1.26);
                } else if (preset === "news") {
                    applyPreset("news", 2, 1.18);
                } else if (preset === "storyteller") {
                    applyPreset("storyteller", -1, 0.94);
                } else if (gender === "female") {
                    applyPreset("natural", 0, 1.0);
                } else if (gender === "male") {
                    applyPreset("natural", -2, 1.0);
                }
            }
        });
    });

    function applyPreset(presetKey, pitchVal, rateVal) {
        state.preset = presetKey;
        state.pitch = pitchVal;
        state.rate = rateVal;

        pitchSlider.value = pitchVal;
        pitchValue.textContent = `${pitchVal > 0 ? '+' : ''}${pitchVal} Hz`;

        rateSlider.value = rateVal.toFixed(2);
        rateValue.textContent = `${rateVal.toFixed(2)}x`;

        updateStatusMeta();
        updateTextMetrics();
    }

    // Mastering & EQ Chips
    eqChips.forEach(chip => {
        chip.addEventListener("click", () => {
            eqChips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            state.eqFilter = chip.dataset.eq;
            showToast(`ಆಡಿಯೊ ಇಕ್ವಲೈಜರ್: ${chip.textContent.trim()}`);
        });
    });

    // Vocal Energy Chips
    energyChips.forEach(chip => {
        chip.addEventListener("click", () => {
            energyChips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            state.energyMode = chip.dataset.energy;
            showToast(`ಎನರ್ಜಿ ಮೋಡ್: ${chip.textContent.trim()}`);
            updateStatusMeta();
        });
    });

    // Sliders
    pitchSlider.addEventListener("input", () => {
        state.pitch = parseInt(pitchSlider.value);
        pitchValue.textContent = `${state.pitch > 0 ? '+' : ''}${state.pitch} Hz`;
        updateStatusMeta();
    });

    rateSlider.addEventListener("input", () => {
        state.rate = parseFloat(rateSlider.value);
        rateValue.textContent = `${state.rate.toFixed(2)}x`;
        updateStatusMeta();
        updateTextMetrics();
    });

    volumeSlider.addEventListener("input", () => {
        state.volume = parseInt(volumeSlider.value);
        volumeValue.textContent = `${state.volume}%`;
        audioPlayer.volume = state.volume / 100;
    });

    function updateStatusMeta(customName, customPreset) {
        const activeCard = document.querySelector(".voice-card.active");
        const voiceName = customName || (activeCard ? activeCard.querySelector(".voice-name").textContent : "Sapna");
        activeVoiceInfo.textContent = `${voiceName} • ${state.pitch}Hz • ${state.rate.toFixed(2)}x`;
    }

    // ==========================================
    // 4. AUDIO FILE UPLOAD & CLONING
    // ==========================================
    audioFileInput.addEventListener("change", async (e) => {
        const file = e.target.files[0];
        if (file) {
            state.uploadedAudioFile = file;
            uploadFileName.textContent = `✓ ${file.name}`;
            
            const fileUrl = URL.createObjectURL(file);
            refAudioPlayer.src = fileUrl;
            refAudioPreviewCard.classList.remove("hidden");
            directCloneBtn.disabled = false;
            
            analysisDetails.textContent = "ಧ್ವನಿ ಮಾದರಿಯನ್ನು ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ...";
            try {
                const formData = new FormData();
                formData.append("reference_audio", file);
                const res = await fetch("/api/analyze_audio", {
                    method: "POST",
                    body: formData
                });
                if (res.ok) {
                    const data = await res.json();
                    refAudioMeta.textContent = `${data.duration_sec}s • ${data.pitch_hz} Hz`;
                    analysisDetails.textContent = `ವಿಶ್ಲೇಷಣೆ: ${data.gender === 'male' ? 'ಪುರುಷ' : 'ಮಹಿಳಾ'} ಧ್ವನಿ • ಪಿಚ್: ${data.pitch_hz} Hz • ರೆಸೋನೆನ್ಸ್: ${data.vocal_resonance}x`;
                    showToast(`"${file.name}" ವಿಶ್ಲೇಷಣೆ ಯಶಸ್ವಿಯಾಗಿದೆ!`);
                }
            } catch (err) {
                refAudioMeta.textContent = `${file.name}`;
                analysisDetails.textContent = "ಆಡಿಯೊ ಮಾದರಿ ಸಿದ್ಧವಾಗಿದೆ.";
            }
        }
    });

    directCloneBtn.addEventListener("click", () => {
        if (!state.uploadedAudioFile) {
            showToast("ದಯವಿಟ್ಟು ಮೊದಲು ಆಡಿಯೊ ಫೈಲ್ ಆಯ್ಕೆ ಮಾಡಿ");
            return;
        }
        synthesizeAndPlay();
    });

    // ==========================================
    // 5. SYNTHESIS & PLAYBACK
    // ==========================================
    playBtn.addEventListener("click", () => {
        if (state.isPlaying) {
            audioPlayer.pause();
            setPlaybackState("paused");
        } else if (audioPlayer.src && audioPlayer.currentTime > 0 && !audioPlayer.ended && audioPlayer.paused) {
            audioPlayer.play();
            setPlaybackState("playing");
        } else {
            synthesizeAndPlay();
        }
    });

    stopBtn.addEventListener("click", () => {
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        setPlaybackState("stopped");
    });

    // Playback Speed Switcher
    playbackSpeedBtn.addEventListener("click", () => {
        const speeds = [1.0, 1.25, 1.5, 2.0];
        const nextIdx = (speeds.indexOf(state.playbackSpeed) + 1) % speeds.length;
        state.playbackSpeed = speeds[nextIdx];
        audioPlayer.playbackRate = state.playbackSpeed;
        playbackSpeedBtn.textContent = `${state.playbackSpeed.toFixed(1)}x`;
        showToast(`ಪ್ಲೇಬ್ಯಾಕ್ ವೇಗ: ${state.playbackSpeed}x`);
    });

    async function synthesizeAndPlay() {
        const text = kannadaInput.value.trim();
        if (!text) {
            showToast("ದಯವಿಟ್ಟು ಪಠ್ಯವನ್ನು ನಮೂದಿಸಿ");
            return;
        }

        setPlaybackState("loading");

        try {
            let res;
            if (state.gender === "custom" && state.uploadedAudioFile) {
                const formData = new FormData();
                formData.append("text", text);
                formData.append("pitch", (1.0 + state.pitch / 50).toString());
                formData.append("rate", state.rate.toString());
                formData.append("energy_level", state.energyMode);
                formData.append("reference_audio", state.uploadedAudioFile);

                res = await fetch("/api/clone_voice", {
                    method: "POST",
                    body: formData
                });
            } else {
                const pitchStr = `${state.pitch >= 0 ? '+' : ''}${state.pitch}Hz`;
                const rateDelta = Math.round((state.rate - 1.0) * 100);
                const rateStr = `${rateDelta >= 0 ? '+' : ''}${rateDelta}%`;

                res = await fetch("/api/synthesize", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        text,
                        voice: state.voice,
                        pitch: pitchStr,
                        rate: rateStr,
                        energy_mode: state.energyMode,
                        eq_filter: state.eqFilter,
                        volume: "+0%"
                    })
                });
            }

            if (!res.ok) {
                throw new Error("ಸಂಶ್ಲೇಷಣೆ ವಿಫಲವಾಗಿದೆ (Synthesis failed)");
            }

            const blob = await res.blob();
            if (state.currentAudioUrl) {
                URL.revokeObjectURL(state.currentAudioUrl);
            }
            state.currentAudioUrl = URL.createObjectURL(blob);
            audioPlayer.src = state.currentAudioUrl;
            audioPlayer.volume = state.volume / 100;
            audioPlayer.playbackRate = state.playbackSpeed;
            audioPlayer.play();

            setPlaybackState("playing");
            showToast("ಧ್ವನಿ ಸಿದ್ಧವಾಗಿದೆ! ನುಡಿಸಲಾಗುತ್ತಿದೆ...");

            // Add to session history
            state.history.unshift({
                time: new Date().toLocaleTimeString(),
                text: text,
                voice: state.voice,
                url: state.currentAudioUrl
            });

        } catch (err) {
            console.error(err);
            setPlaybackState("stopped");
            showToast(`ದೋಷ: ${err.message}`);
        }
    }

    function setPlaybackState(status) {
        state.isPlaying = (status === "playing");
        state.isLoading = (status === "loading");

        playIcon.classList.toggle("hidden", state.isPlaying || state.isLoading);
        pauseIcon.classList.toggle("hidden", !state.isPlaying);
        loadingSpinner.classList.toggle("hidden", !state.isLoading);

        if (status === "playing") statusText.textContent = "ನುಡಿಸಲಾಗುತ್ತಿದೆ (Playing)";
        else if (status === "paused") statusText.textContent = "ವಿರಾಮಗೊಳಿಸಲಾಗಿದೆ (Paused)";
        else if (status === "loading") statusText.textContent = "ಧ್ವನಿ ತಯಾರಾಗುತ್ತಿದೆ...";
        else statusText.textContent = "ಸಿದ್ಧವಾಗಿದೆ (Ready)";
    }

    // Audio Progress & Scrubber
    audioPlayer.addEventListener("timeupdate", () => {
        if (!audioPlayer.duration) return;
        const progress = (audioPlayer.currentTime / audioPlayer.duration) * 100;
        audioScrubber.value = progress;
        currentTimeEl.textContent = formatTime(audioPlayer.currentTime);
        durationTimeEl.textContent = formatTime(audioPlayer.duration);
    });

    audioPlayer.addEventListener("ended", () => {
        setPlaybackState("stopped");
        audioScrubber.value = 0;
        currentTimeEl.textContent = "0:00";
    });

    audioScrubber.addEventListener("input", () => {
        if (audioPlayer.duration) {
            audioPlayer.currentTime = (audioScrubber.value / 100) * audioPlayer.duration;
        }
    });

    function formatTime(secs) {
        if (isNaN(secs)) return "0:00";
        const m = Math.floor(secs / 60);
        const s = Math.floor(secs % 60);
        return `${m}:${s < 10 ? '0' : ''}${s}`;
    }

    // Download MP3
    downloadBtn.addEventListener("click", () => {
        if (!state.currentAudioUrl) {
            showToast("ಮೊದಲು ಆಡಿಯೊ ಸಂಶ್ಲೇಷಿಸಿ ನಂತರ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ");
            return;
        }
        const a = document.createElement("a");
        a.href = state.currentAudioUrl;
        a.download = `dhvani_kannada_${Date.now()}.mp3`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        showToast("ಆಡಿಯೊ MP3 ಡೌನ್‌ಲೋಡ್ ಆಗಿದೆ!");
    });

    // ==========================================
    // 6. DUAL-CHANNEL CANVAS VISUALIZER
    // ==========================================
    function drawVisualizer() {
        requestAnimationFrame(drawVisualizer);
        canvasCtx.clearRect(0, 0, waveformCanvas.width, waveformCanvas.height);

        const bars = 18;
        const barWidth = 4;
        const spacing = 3;
        const startX = 6;

        for (let i = 0; i < bars; i++) {
            let height = 4;
            if (state.isPlaying) {
                const wave1 = Math.sin(Date.now() * 0.009 + i * 0.5) * 10;
                const wave2 = Math.cos(Date.now() * 0.006 + i * 0.8) * 6;
                height = Math.max(4, Math.floor(wave1 + wave2 + 16));
            }
            const x = startX + i * (barWidth + spacing);
            const y = (waveformCanvas.height - height) / 2;

            const grad = canvasCtx.createLinearGradient(0, waveformCanvas.height, 0, 0);
            grad.addColorStop(0, "#f97316");
            grad.addColorStop(1, "#ec4899");

            canvasCtx.fillStyle = grad;
            canvasCtx.beginPath();
            canvasCtx.roundRect(x, y, barWidth, height, 2);
            canvasCtx.fill();
        }
    }
    drawVisualizer();

    // ==========================================
    // 7. PRESETS & HISTORY DRAWERS
    // ==========================================
    async function loadPresetsFromApi() {
        try {
            const res = await fetch("/api/presets");
            if (res.ok) {
                const data = await res.json();
                renderPresets(data.categories);
            }
        } catch (e) {
            console.warn("Could not load API presets, using fallback");
        }
    }

    function renderPresets(categories) {
        modalCategories.innerHTML = "";
        categories.forEach((cat, idx) => {
            const btn = document.createElement("button");
            btn.className = `category-pill ${idx === 0 ? 'active' : ''}`;
            btn.textContent = cat.category;
            btn.addEventListener("click", () => {
                document.querySelectorAll(".category-pill").forEach(p => p.classList.remove("active"));
                btn.classList.add("active");
                renderSamples(cat.samples);
            });
            modalCategories.appendChild(btn);
        });
        if (categories.length > 0) {
            renderSamples(categories[0].samples);
        }
    }

    function renderSamples(samples) {
        modalSamplesList.innerHTML = "";
        samples.forEach(item => {
            const div = document.createElement("div");
            div.className = "sample-item";
            div.innerHTML = `
                <div class="sample-title">${item.title}</div>
                <div class="sample-text">${item.text}</div>
            `;
            div.addEventListener("click", () => {
                kannadaInput.value = item.text;
                updateTextMetrics();

                if (item.voiceId) {
                    const targetCard = Array.from(voiceCards).find(c => c.dataset.voice === item.voiceId);
                    if (targetCard) targetCard.click();
                }

                presetsModal.classList.add("hidden");
                showToast(`"${item.title}" ಲೋಡ್ ಆಗಿದೆ!`);
            });
            modalSamplesList.appendChild(div);
        });
    }

    openPresetsBtn.addEventListener("click", () => {
        loadPresetsFromApi();
        presetsModal.classList.remove("hidden");
    });

    closePresetsBtn.addEventListener("click", () => presetsModal.classList.add("hidden"));
    presetsModal.addEventListener("click", (e) => {
        if (e.target === presetsModal) presetsModal.classList.add("hidden");
    });

    // History Drawer
    openHistoryBtn.addEventListener("click", () => {
        renderHistory();
        historyDrawer.classList.remove("hidden");
    });

    closeHistoryBtn.addEventListener("click", () => historyDrawer.classList.add("hidden"));
    historyDrawer.addEventListener("click", (e) => {
        if (e.target === historyDrawer) historyDrawer.classList.add("hidden");
    });

    function renderHistory() {
        historyList.innerHTML = "";
        if (state.history.length === 0) {
            historyList.innerHTML = '<p class="normalizer-tip" style="text-align:center;padding:20px;">ಯಾವುದೇ ಇತಿಹಾಸವಿಲ್ಲ (No recent clips)</p>';
            return;
        }
        state.history.forEach((h, i) => {
            const div = document.createElement("div");
            div.className = "history-item";
            div.innerHTML = `
                <div class="history-title">⏱️ ${h.time} • ${h.voice}</div>
                <div class="history-text">${h.text}</div>
            `;
            div.addEventListener("click", () => {
                kannadaInput.value = h.text;
                updateTextMetrics();
                audioPlayer.src = h.url;
                audioPlayer.play();
                setPlaybackState("playing");
                historyDrawer.classList.add("hidden");
                showToast("ಇತಿಹಾಸದಿಂದ ಮರು-ನುಡಿಸಲಾಗುತ್ತಿದೆ...");
            });
            historyList.appendChild(div);
        });
    }

    // Theme Switcher
    themeToggleBtn.addEventListener("click", () => {
        state.theme = state.theme === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", state.theme);
        showToast(state.theme === "dark" ? "ಡಾರ್ಕ್ ಮೋಡ್ (Dark Mode)" : "ಲೈಟ್ ಮೋಡ್ (Light Mode)");
    });

    // Keyboard Shortcuts (Ctrl+Enter to Play, Esc to Stop)
    document.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            e.preventDefault();
            synthesizeAndPlay();
        } else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
            e.preventDefault();
            openPresetsBtn.click();
        } else if (e.key === "Escape") {
            presetsModal.classList.add("hidden");
            historyDrawer.classList.add("hidden");
            stopBtn.click();
        }
    });

    function showToast(msg) {
        toast.textContent = msg;
        toast.classList.remove("hidden");
        clearTimeout(window._toastTimer);
        window._toastTimer = setTimeout(() => {
            toast.classList.add("hidden");
        }, 2500);
    }

    // Init
    updateTextMetrics();
    updateStatusMeta();
});
