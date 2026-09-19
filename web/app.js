/**
 * Dhvani Kannada Text-to-Speech & Delivery Style Studio - Frontend Engine v2.1
 */

document.addEventListener("DOMContentLoaded", () => {
    // Relative assets work from file://; API requests still target the local
    // server when the HTML file is opened directly.
    const apiUrl = (path) => window.location.protocol === "file:"
        ? `http://127.0.0.1:8000${path}`
        : path;

    // Studio State
    const state = {
        mode: "standard",   // "standard" or "delivery"
        gender: "male",
        voice: "kn-IN-GaganNeural",
        pitch: 0,           // in Hz (-30 to +30)
        rate: 1.0,          // 0.5x to 2.0x
        volume: 100,        // 0 to 100%
        preset: "natural",
        playbackSpeed: 1.0,
        isTranslitOn: false,
        isPlaying: false,
        isLoading: false,
        currentAudioUrl: null,
        normalAudioUrl: null,
        styledAudioUrl: null,
        theme: "dark",
        history: []
    };

    // DOM Elements - Navigation & Modes
    const tabNormalTTS = document.getElementById("tabNormalTTS");
    const tabDeliveryTransfer = document.getElementById("tabDeliveryTransfer");
    const tabIndicF5 = document.getElementById("tabIndicF5");
    const standardTTSPanel = document.getElementById("standardTTSPanel");
    const deliveryTransferPanel = document.getElementById("deliveryTransferPanel");
    const indicF5Panel = document.getElementById("indicF5Panel");
    const indicF5DeviceBadge = document.getElementById("indicF5DeviceBadge");

    // IndicF5 Elements
    const f5AudioDropzone = document.getElementById("f5AudioDropzone");
    const f5AudioFileInput = document.getElementById("f5AudioFileInput");
    const f5DropzonePrompt = document.getElementById("f5DropzonePrompt");
    const f5LoadedBox = document.getElementById("f5LoadedBox");
    const f5LoadedFilename = document.getElementById("f5LoadedFilename");
    const f5LoadedMeta = document.getElementById("f5LoadedMeta");
    const f5RemoveAudioBtn = document.getElementById("f5RemoveAudioBtn");
    const f5TranscriptInput = document.getElementById("f5TranscriptInput");
    const generateF5Btn = document.getElementById("generateF5Btn");

    let f5UploadedFile = null;

    // Text Input & Normalizer
    const kannadaInput = document.getElementById("kannadaInput");
    const charCount = document.getElementById("charCount");
    const wordCount = document.getElementById("wordCount");
    const estimatedDuration = document.getElementById("estimatedDuration");
    const translitToggleBtn = document.getElementById("translitToggleBtn");
    const translitLabel = document.getElementById("translitLabel");
    const clearTextBtn = document.getElementById("clearTextBtn");
    const copyTextBtn = document.getElementById("copyTextBtn");
    const normalizedPreview = document.getElementById("normalizedPreview");

    // Standard Mode Elements
    const voiceCards = document.querySelectorAll(".voice-card");
    const pitchSlider = document.getElementById("pitchSlider");
    const pitchValue = document.getElementById("pitchValue");
    const rateSlider = document.getElementById("rateSlider");
    const rateValue = document.getElementById("rateValue");

    // Delivery Transfer Mode Elements
    const pickGaganBtn = document.getElementById("pickGaganBtn");
    const pickSapnaBtn = document.getElementById("pickSapnaBtn");
    const generateStyledBtn = document.getElementById("generateStyledBtn");
    const abComparisonBox = document.getElementById("abComparisonBox");
    const playNormalABBtn = document.getElementById("playNormalABBtn");
    const playStyledABBtn = document.getElementById("playStyledABBtn");

    // Real-Time Delivery Modifiers
    const energyModeChips = document.querySelectorAll("#energyModeChips .chip-btn");
    const pitchDepthSlider = document.getElementById("pitchDepthSlider");
    const pitchDepthVal = document.getElementById("pitchDepthVal");
    const burstPaceSlider = document.getElementById("burstPaceSlider");
    const burstPaceVal = document.getElementById("burstPaceVal");
    const pauseStyleChips = document.querySelectorAll("#pauseStyleChips .chip-btn");
    const livePhrasesCount = document.getElementById("livePhrasesCount");
    const livePhraseContainer = document.getElementById("livePhraseContainer");

    // Real-Time Modifier State
    const deliveryState = {
        energyMode: "high_energy",
        pitchDepth: 1.0,
        pacingMultiplier: 1.0,
        pauseStyle: "snappy"
    };

    // Audio Player Bar
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

    // Modals & Drawers
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
    // 1. MODE SWITCHER TABS
    // ==========================================
    tabNormalTTS.addEventListener("click", () => {
        state.mode = "standard";
        tabNormalTTS.classList.add("active");
        tabDeliveryTransfer.classList.remove("active");
        tabIndicF5.classList.remove("active");
        standardTTSPanel.classList.remove("hidden");
        deliveryTransferPanel.classList.add("hidden");
        indicF5Panel.classList.add("hidden");
        updateStatusMeta();
    });

    tabDeliveryTransfer.addEventListener("click", () => {
        state.mode = "delivery";
        tabDeliveryTransfer.classList.add("active");
        tabNormalTTS.classList.remove("active");
        tabIndicF5.classList.remove("active");
        deliveryTransferPanel.classList.remove("hidden");
        standardTTSPanel.classList.add("hidden");
        indicF5Panel.classList.add("hidden");
        updateStatusMeta("Expressive Voice", "ಅಂತರ್ನಿರ್ಮಿತ ಶೈಲಿ");
        updateLivePhraseBreakdown();
    });

    tabIndicF5.addEventListener("click", () => {
        state.mode = "indic_f5";
        tabIndicF5.classList.add("active");
        tabNormalTTS.classList.remove("active");
        tabDeliveryTransfer.classList.remove("active");
        indicF5Panel.classList.remove("hidden");
        standardTTSPanel.classList.add("hidden");
        deliveryTransferPanel.classList.add("hidden");
        updateStatusMeta("IndicF5 Zero-Shot", "AI4Bharat F5");
        fetchIndicF5Status();
    });

    async function fetchIndicF5Status() {
        try {
            const res = await fetch(apiUrl("/api/indic_f5/status"));
            if (res.ok) {
                const data = await res.json();
                if (indicF5DeviceBadge) {
                    indicF5DeviceBadge.textContent = `${data.device.toUpperCase()}`;
                }
            }
        } catch (e) {}
    }

    // ==========================================
    // 2. TEXT METRICS & NORMALIZATION PREVIEW
    // ==========================================
    function updateTextMetrics() {
        const text = kannadaInput.value;
        charCount.textContent = `${text.length} ಅಕ್ಷರಗಳು`;
        const words = text.trim() ? text.trim().split(/\s+/).length : 0;
        wordCount.textContent = `${words} ಶಬ್ದಗಳು`;
        
        const estSec = (text.length * 0.08 / Math.max(0.5, state.rate)).toFixed(1);
        estimatedDuration.textContent = `~${estSec} ಸೆಕೆಂಡುಗಳು`;

        clearTimeout(window._normTimeout);
        window._normTimeout = setTimeout(fetchNormalization, 250);

        clearTimeout(window._phraseTimeout);
        window._phraseTimeout = setTimeout(updateLivePhraseBreakdown, 200);
    }

    async function fetchNormalization() {
        const text = kannadaInput.value;
        if (!text.trim()) {
            normalizedPreview.textContent = "(ಖಾಲಿ)";
            return;
        }
        try {
            const res = await fetch(apiUrl("/api/normalize"), {
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
    // 3. KANNADA PHONETIC TRANSLITERATION ENGINE
    // ==========================================
    translitToggleBtn.addEventListener("click", () => {
        state.isTranslitOn = !state.isTranslitOn;
        translitToggleBtn.classList.toggle("active", state.isTranslitOn);
        translitLabel.textContent = state.isTranslitOn ? "ಲಿಪ್ಯಂತರಣ En ➔ ಕ [ON]" : "ಲಿಪ್ಯಂತರಣ En ➔ ಕ [OFF]";
        showToast(state.isTranslitOn ? "ಕನ್ನಡ ಲಿಪ್ಯಂತರಣ ಸಕ್ರಿಯವಾಗಿದೆ (Transliteration ON)" : "ಲಿಪ್ಯಂತರಣ ನಿಷ್ಕ್ರಿಯವಾಗಿದೆ (OFF)");
    });

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

    kannadaInput.addEventListener("keydown", (e) => {
        if (!state.isTranslitOn) return;
        if (e.key === " " || e.key === "Enter") {
            const pos = kannadaInput.selectionStart;
            const full = kannadaInput.value;
            const before = full.slice(0, pos);
            const after = full.slice(pos);

            const match = before.match(/([a-zA-Z]+)$/);
            if (match) {
                const word = match[1].toLowerCase();
                const converted = PHONETIC_DICT[word] || word;
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
    // 4. STANDARD TTS VOICE & SLIDER CONTROLS
    // ==========================================
    function invalidateGeneratedAudio() {
        audioPlayer.pause();
        audioPlayer.removeAttribute("src");
        audioPlayer.load();
        for (const url of new Set([state.currentAudioUrl, state.normalAudioUrl, state.styledAudioUrl])) {
            if (url) URL.revokeObjectURL(url);
        }
        state.currentAudioUrl = null;
        state.normalAudioUrl = null;
        state.styledAudioUrl = null;
        setPlaybackState("stopped");
    }

    voiceCards.forEach(card => {
        card.addEventListener("click", () => {
            voiceCards.forEach(c => c.classList.remove("active"));
            card.classList.add("active");
            
            const gender = card.dataset.gender;
            const voice = card.dataset.voice;
            const preset = card.dataset.preset;

            state.gender = gender;
            state.voice = voice || "kn-IN-GaganNeural";
            invalidateGeneratedAudio();

            if (preset === "podcast") {
                applyPreset("podcast", -4, 1.26);
            } else if (preset === "news") {
                applyPreset("news", 2, 1.18);
            } else if (gender === "female") {
                applyPreset("natural", 2, 1.0);
            } else if (gender === "male") {
                applyPreset("natural", -5, 0.95);
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

    pitchSlider.addEventListener("input", () => {
        state.pitch = parseInt(pitchSlider.value);
        invalidateGeneratedAudio();
        pitchValue.textContent = `${state.pitch > 0 ? '+' : ''}${state.pitch} Hz`;
        updateStatusMeta();
    });

    rateSlider.addEventListener("input", () => {
        state.rate = parseFloat(rateSlider.value);
        invalidateGeneratedAudio();
        rateValue.textContent = `${state.rate.toFixed(2)}x`;
        updateStatusMeta();
        updateTextMetrics();
    });

    function updateStatusMeta(customName, customPreset) {
        if (state.mode === "delivery") {
            const vName = state.voice.includes("Sapna") ? "Sapna" : "Gagan";
            activeVoiceInfo.textContent = `${vName} • ⚡ ವ್ಯಕ್ತಿತ್ವದ ಧ್ವನಿ (Expressive Voice)`;
        } else {
            const activeCard = document.querySelector(".voice-card.active");
            const voiceName = customName || (activeCard ? activeCard.querySelector(".voice-name").textContent : "Gagan");
            activeVoiceInfo.textContent = `${voiceName} • ${state.pitch}Hz • ${state.rate.toFixed(2)}x`;
        }
    }

    // ==========================================
    // 5. DELIVERY PROSODY STYLE TRANSFER ACTIONS
    // ==========================================
    pickGaganBtn.addEventListener("click", () => {
        pickGaganBtn.classList.add("active");
        pickSapnaBtn.classList.remove("active");
        state.voice = "kn-IN-GaganNeural";
        invalidateGeneratedAudio();
        updateStatusMeta();
        updateLivePhraseBreakdown();
        showToast("ಧ್ವನಿ: Gagan (ಗಗನ್) ಆಯ್ಕೆಯಾಗಿದೆ");
    });

    pickSapnaBtn.addEventListener("click", () => {
        pickSapnaBtn.classList.add("active");
        pickGaganBtn.classList.remove("active");
        state.voice = "kn-IN-SapnaNeural";
        invalidateGeneratedAudio();
        updateStatusMeta();
        updateLivePhraseBreakdown();
        showToast("ಧ್ವನಿ: Sapna (ಸ್ಪಪ್ನಾ) ಆಯ್ಕೆಯಾಗಿದೆ");
    });

    // 5a. Real-Time Attribute Modifiers Listeners
    energyModeChips.forEach(chip => {
        chip.addEventListener("click", () => {
            energyModeChips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            deliveryState.energyMode = chip.dataset.energy;
            updateLivePhraseBreakdown();
            showToast(`ಎನರ್ಜಿ ಮೋಡ್: ${chip.textContent.trim()}`);
        });
    });

    if (pitchDepthSlider) {
        pitchDepthSlider.addEventListener("input", () => {
            const val = parseFloat(pitchDepthSlider.value);
            deliveryState.pitchDepth = val;
            const spanHz = Math.round(82.9 * val);
            pitchDepthVal.textContent = `${val.toFixed(1)}x (~${spanHz} Hz)`;
            updateLivePhraseBreakdown();
        });
    }

    if (burstPaceSlider) {
        burstPaceSlider.addEventListener("input", () => {
            const val = parseFloat(burstPaceSlider.value);
            deliveryState.pacingMultiplier = val;
            const sylSec = (8.5 * val).toFixed(1);
            const deltaPct = Math.round((val * 1.38 - 1.0) * 100);
            burstPaceVal.textContent = `${sylSec} syl/s (+${deltaPct}%)`;
            updateLivePhraseBreakdown();
        });
    }

    pauseStyleChips.forEach(chip => {
        chip.addEventListener("click", () => {
            pauseStyleChips.forEach(c => c.classList.remove("active"));
            chip.classList.add("active");
            deliveryState.pauseStyle = chip.dataset.pause;
            updateLivePhraseBreakdown();
            showToast(`ವಿರಾಮ ಶೈಲಿ: ${chip.textContent.trim()}`);
        });
    });

    // 5b. Real-Time Live Phrase Breakdown Calculator (Applicable to Any Kannada Text)
    async function updateLivePhraseBreakdown() {
        const text = kannadaInput.value.trim();
        if (!text || !livePhraseContainer) return;

        try {
            const res = await fetch(apiUrl("/api/preview_prosody_plan"), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    text,
                    voice: state.voice,
                    energy_mode: deliveryState.energyMode,
                    pitch_depth: deliveryState.pitchDepth,
                    pacing_multiplier: deliveryState.pacingMultiplier,
                    pause_style: deliveryState.pauseStyle
                })
            });

            if (!res.ok) return;
            const plan = await res.json();

            if (livePhrasesCount) {
                livePhrasesCount.textContent = `${plan.total_phrases} ವಾಕ್ಯಖಂಡಗಳು (~${plan.estimated_total_sec}s)`;
            }

            livePhraseContainer.innerHTML = "";
            if (!plan.phrases || plan.phrases.length === 0) {
                livePhraseContainer.innerHTML = `<div class="empty-phrase-hint">(ಯಾವುದೇ ಪಠ್ಯವಿಲ್ಲ)</div>`;
                return;
            }

            plan.phrases.forEach(p => {
                const item = document.createElement("div");
                item.className = "live-phrase-item";
                item.innerHTML = `
                    <div class="phrase-left">
                        <span class="phrase-num">${p.phrase_index}</span>
                        <span class="phrase-text-preview" title="${p.text}">"${p.text}"</span>
                    </div>
                    <div class="phrase-meta-pills">
                        <span class="pill-tag pill-pitch">${p.pitch}</span>
                        <span class="pill-tag pill-rate">${p.rate}</span>
                        <span class="pill-tag pill-pause">${p.pause_after_ms}ms</span>
                        <span class="pill-tag">${p.tag}</span>
                    </div>
                `;
                livePhraseContainer.appendChild(item);
            });

        } catch (e) {
            console.error("Live phrase preview error:", e);
        }
    }

    // 5c. Synthesize with current real-time delivery attributes
    generateStyledBtn.addEventListener("click", () => {
        synthesizeDeliveryStyled();
    });

    async function synthesizeDeliveryStyled() {
        const text = kannadaInput.value.trim();
        if (!text) {
            showToast("ದಯವಿಟ್ಟು ಪಠ್ಯವನ್ನು ನಮೂದಿಸಿ");
            return;
        }

        setPlaybackState("loading");

        try {
            const formData = new FormData();
            formData.append("text", text);
            formData.append("voice", state.voice);
            formData.append("energy_mode", deliveryState.energyMode);
            formData.append("pitch_depth", deliveryState.pitchDepth);
            formData.append("pacing_multiplier", deliveryState.pacingMultiplier);
            formData.append("pause_style", deliveryState.pauseStyle);

            const res = await fetch(apiUrl("/api/synthesize_delivery"), {
                method: "POST",
                body: formData
            });

            if (!res.ok) throw new Error("Delivery synthesis failed");

            const blob = await res.blob();
            if (state.styledAudioUrl) URL.revokeObjectURL(state.styledAudioUrl);
            state.styledAudioUrl = URL.createObjectURL(blob);
            state.currentAudioUrl = state.styledAudioUrl;

            audioPlayer.src = state.currentAudioUrl;
            audioPlayer.playbackRate = state.playbackSpeed;
            audioPlayer.play();

            setPlaybackState("playing");
            abComparisonBox.classList.remove("hidden");
            playStyledABBtn.classList.add("active");
            playNormalABBtn.classList.remove("active");

            showToast("ಶೈಲಿ ವರ್ಗಾವಣೆಯೊಂದಿಗೆ ನುಡಿಸಲಾಗುತ್ತಿದೆ (Delivery Styled Playing)!");

        } catch (err) {
            console.error(err);
            setPlaybackState("stopped");
            showToast(`ದೋಷ: ${err.message}`);
        }
    }

    // 5c. A/B Comparison Switcher
    playNormalABBtn.addEventListener("click", async () => {
        playNormalABBtn.classList.add("active");
        playStyledABBtn.classList.remove("active");

        // Synthesize normal if not cached
        if (!state.normalAudioUrl) {
            setPlaybackState("loading");
            const res = await fetch(apiUrl("/api/synthesize"), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    text: kannadaInput.value.trim(),
                    voice: state.voice,
                    pitch: "+0Hz",
                    rate: "+0%"
                })
            });
            const blob = await res.blob();
            state.normalAudioUrl = URL.createObjectURL(blob);
        }

        state.currentAudioUrl = state.normalAudioUrl;
        audioPlayer.src = state.currentAudioUrl;
        audioPlayer.play();
        setPlaybackState("playing");
        showToast("🔊 Normal Voice ನುಡಿಸಲಾಗುತ್ತಿದೆ");
    });

    playStyledABBtn.addEventListener("click", () => {
        if (!state.styledAudioUrl) {
            synthesizeDeliveryStyled();
            return;
        }
        playStyledABBtn.classList.add("active");
        playNormalABBtn.classList.remove("active");

        state.currentAudioUrl = state.styledAudioUrl;
        audioPlayer.src = state.currentAudioUrl;
        audioPlayer.play();
        setPlaybackState("playing");
        showToast("⚡ Delivery Styled ನುಡಿಸಲಾಗುತ್ತಿದೆ");
    });

    // ==========================================
    // 5d. AI4BHARAT INDICF5 CLONING ACTIONS
    // ==========================================
    if (f5AudioDropzone) {
        f5AudioDropzone.addEventListener("click", (e) => {
            if (e.target !== f5RemoveAudioBtn) {
                f5AudioFileInput.click();
            }
        });

        f5AudioFileInput.addEventListener("change", (e) => {
            const file = e.target.files[0];
            if (file) handleF5AudioFile(file);
        });

        f5AudioDropzone.addEventListener("dragover", (e) => {
            e.preventDefault();
            f5AudioDropzone.classList.add("drag-over");
        });

        f5AudioDropzone.addEventListener("dragleave", () => {
            f5AudioDropzone.classList.remove("drag-over");
        });

        f5AudioDropzone.addEventListener("drop", (e) => {
            e.preventDefault();
            f5AudioDropzone.classList.remove("drag-over");
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith("audio/")) {
                handleF5AudioFile(file);
            }
        });
    }

    function handleF5AudioFile(file) {
        f5UploadedFile = file;
        f5LoadedFilename.textContent = file.name;
        f5LoadedMeta.textContent = `${(file.size / (1024 * 1024)).toFixed(2)} MB • ರೆಫರೆನ್ಸ್ ಸಿದ್ಧವಾಗಿದೆ`;
        f5DropzonePrompt.classList.add("hidden");
        f5LoadedBox.classList.remove("hidden");
        showToast(`ರೆಫರೆನ್ಸ್ ಕ್ಲಿಪ್ ಲೋಡ್ ಆಗಿದೆ: ${file.name}`);
    }

    if (f5RemoveAudioBtn) {
        f5RemoveAudioBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            f5UploadedFile = null;
            f5AudioFileInput.value = "";
            f5DropzonePrompt.classList.remove("hidden");
            f5LoadedBox.classList.add("hidden");
            showToast("ರೆಫರೆನ್ಸ್ ಆಡಿಯೊ ತೆಗೆದುಹಾಕಲಾಗಿದೆ");
        });
    }

    if (generateF5Btn) {
        generateF5Btn.addEventListener("click", () => {
            synthesizeIndicF5();
        });
    }

    async function synthesizeIndicF5() {
        const text = kannadaInput.value.trim();
        if (!text) {
            showToast("ದಯವಿಟ್ಟು ಪಠ್ಯವನ್ನು ನಮೂದಿಸಿ");
            return;
        }

        setPlaybackState("loading");

        try {
            const formData = new FormData();
            formData.append("text", text);
            if (f5TranscriptInput && f5TranscriptInput.value.trim()) {
                formData.append("ref_transcript", f5TranscriptInput.value.trim());
            }
            if (f5UploadedFile) {
                formData.append("reference_audio", f5UploadedFile);
            }

            const res = await fetch(apiUrl("/api/indic_f5/synthesize"), {
                method: "POST",
                body: formData
            });

            if (!res.ok) throw new Error("IndicF5 synthesis failed");

            const blob = await res.blob();
            if (state.currentAudioUrl) URL.revokeObjectURL(state.currentAudioUrl);
            state.currentAudioUrl = URL.createObjectURL(blob);

            audioPlayer.src = state.currentAudioUrl;
            audioPlayer.playbackRate = state.playbackSpeed;
            audioPlayer.play();

            setPlaybackState("playing");
            showToast("🧬 IndicF5 ಧ್ವನಿ ತಯಾರಾಗಿದೆ! ನುಡಿಸಲಾಗುತ್ತಿದೆ...");

        } catch (err) {
            console.error(err);
            setPlaybackState("stopped");
            showToast(`ದೋಷ: ${err.message}`);
        }
    }

    // ==========================================
    // 6. SYNTHESIS & PLAYBACK DISPATCHER
    // ==========================================
    playBtn.addEventListener("click", () => {
        if (state.isPlaying) {
            audioPlayer.pause();
            setPlaybackState("paused");
        } else if (audioPlayer.src && audioPlayer.currentTime > 0 && !audioPlayer.ended && audioPlayer.paused) {
            audioPlayer.play();
            setPlaybackState("playing");
        } else {
            if (state.mode === "indic_f5") {
                synthesizeIndicF5();
            } else if (state.mode === "delivery") {
                synthesizeDeliveryStyled();
            } else {
                synthesizeStandardTTS();
            }
        }
    });

    stopBtn.addEventListener("click", () => {
        audioPlayer.pause();
        audioPlayer.currentTime = 0;
        setPlaybackState("stopped");
    });

    async function synthesizeStandardTTS() {
        const text = kannadaInput.value.trim();
        if (!text) {
            showToast("ದಯವಿಟ್ಟು ಪಠ್ಯವನ್ನು ನಮೂದಿಸಿ");
            return;
        }

        setPlaybackState("loading");

        try {
            const pitchStr = `${state.pitch >= 0 ? '+' : ''}${state.pitch}Hz`;
            const rateDelta = Math.round((state.rate - 1.0) * 100);
            const rateStr = `${rateDelta >= 0 ? '+' : ''}${rateDelta}%`;

            const res = await fetch(apiUrl("/api/synthesize"), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    text,
                    voice: state.voice,
                    pitch: pitchStr,
                    rate: rateStr
                })
            });

            if (!res.ok) throw new Error("Synthesis failed");

            const blob = await res.blob();
            if (state.currentAudioUrl) URL.revokeObjectURL(state.currentAudioUrl);
            state.currentAudioUrl = URL.createObjectURL(blob);
            state.normalAudioUrl = state.currentAudioUrl;

            audioPlayer.src = state.currentAudioUrl;
            audioPlayer.playbackRate = state.playbackSpeed;
            audioPlayer.play();

            setPlaybackState("playing");
            showToast("ಧ್ವನಿ ಸಿದ್ಧವಾಗಿದೆ! ನುಡಿಸಲಾಗುತ್ತಿದೆ...");

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

    playbackSpeedBtn.addEventListener("click", () => {
        const speeds = [1.0, 1.25, 1.5, 2.0];
        const nextIdx = (speeds.indexOf(state.playbackSpeed) + 1) % speeds.length;
        state.playbackSpeed = speeds[nextIdx];
        audioPlayer.playbackRate = state.playbackSpeed;
        playbackSpeedBtn.textContent = `${state.playbackSpeed.toFixed(1)}x`;
        showToast(`ಪ್ಲೇಬ್ಯಾಕ್ ವೇಗ: ${state.playbackSpeed}x`);
    });

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
    // 7. DUAL-CHANNEL CANVAS VISUALIZER
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
            grad.addColorStop(0, state.mode === "delivery" ? "#0284c7" : "#f97316");
            grad.addColorStop(1, state.mode === "delivery" ? "#38bdf8" : "#ec4899");

            canvasCtx.fillStyle = grad;
            canvasCtx.beginPath();
            canvasCtx.roundRect(x, y, barWidth, height, 2);
            canvasCtx.fill();
        }
    }
    drawVisualizer();

    // ==========================================
    // 8. PRESETS & HISTORY
    // ==========================================
    async function loadPresets() {
        try {
            const res = await fetch(apiUrl("/api/presets"));
            if (res.ok) {
                const data = await res.json();
                renderPresets(data.categories);
            }
        } catch (e) {
            console.warn("Could not load presets");
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
        if (categories.length > 0) renderSamples(categories[0].samples);
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
                presetsModal.classList.add("hidden");
                showToast(`"${item.title}" ಲೋಡ್ ಆಗಿದೆ!`);
            });
            modalSamplesList.appendChild(div);
        });
    }

    openPresetsBtn.addEventListener("click", () => {
        loadPresets();
        presetsModal.classList.remove("hidden");
    });
    closePresetsBtn.addEventListener("click", () => presetsModal.classList.add("hidden"));
    presetsModal.addEventListener("click", (e) => {
        if (e.target === presetsModal) presetsModal.classList.add("hidden");
    });

    // Theme Switcher
    themeToggleBtn.addEventListener("click", () => {
        state.theme = state.theme === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-theme", state.theme);
        showToast(state.theme === "dark" ? "ಡಾರ್ಕ್ ಮೋಡ್" : "ಲೈಟ್ ಮೋಡ್");
    });

    // Keyboard Shortcuts
    document.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
            e.preventDefault();
            playBtn.click();
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
    updateLivePhraseBreakdown();
    fetchIndicF5Status();
});
