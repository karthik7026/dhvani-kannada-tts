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

    // Primary CTA Buttons & Quick Actions
    const primarySynthesizeBtn = document.getElementById("primarySynthesizeBtn");
    const primaryCtaPlayIcon = document.getElementById("primaryCtaPlayIcon");
    const primaryCtaPauseIcon = document.getElementById("primaryCtaPauseIcon");
    const primaryCtaText = document.getElementById("primaryCtaText");
    const randomSampleBtn = document.getElementById("randomSampleBtn");
    const downloadPrimaryBtn = document.getElementById("downloadPrimaryBtn");
    const standardPlayCtaBtn = document.getElementById("standardPlayCtaBtn");
    const voicePresetChips = document.querySelectorAll("#voicePresetChips .voice-preset-chip");

    // Pronunciation Inspector & 3-Stage Debug Elements
    const pronunciationDebugAccordion = document.getElementById("pronunciationDebugAccordion");
    const debugRulesCountBadge = document.getElementById("debugRulesCountBadge");
    const debugDisplayText = document.getElementById("debugDisplayText");
    const debugNormalizedText = document.getElementById("debugNormalizedText");
    const debugSpeechText = document.getElementById("debugSpeechText");
    const transformsList = document.getElementById("transformsList");
    const openDictFromDebugBtn = document.getElementById("openDictFromDebugBtn");
    const openDictBtn = document.getElementById("openDictBtn");

    // Dictionary Modal Elements
    const dictModal = document.getElementById("dictModal");
    const closeDictModalBtn = document.getElementById("closeDictModalBtn");
    const addDictForm = document.getElementById("addDictForm");
    const dictNewKey = document.getElementById("dictNewKey");
    const dictNewValue = document.getElementById("dictNewValue");
    const dictNewType = document.getElementById("dictNewType");
    const addDictEntryBtn = document.getElementById("addDictEntryBtn");
    const dictTabWords = document.getElementById("dictTabWords");
    const dictTabAcronyms = document.getElementById("dictTabAcronyms");
    const dictWordsCountBadge = document.getElementById("dictWordsCountBadge");
    const dictAcronymsCountBadge = document.getElementById("dictAcronymsCountBadge");
    const dictSearchInput = document.getElementById("dictSearchInput");
    const dictEntriesList = document.getElementById("dictEntriesList");
    const dictTotalMeta = document.getElementById("dictTotalMeta");

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

    function escapeHtml(str) {
        if (!str) return "";
        const div = document.createElement("div");
        div.textContent = str;
        return div.innerHTML;
    }

    async function fetchNormalization() {
        const text = kannadaInput.value;
        if (!text.trim()) {
            if (normalizedPreview) normalizedPreview.textContent = "(ಖಾಲಿ)";
            if (debugDisplayText) debugDisplayText.textContent = "(ಖಾಲಿ)";
            if (debugNormalizedText) debugNormalizedText.textContent = "(ಖಾಲಿ)";
            if (debugSpeechText) debugSpeechText.textContent = "(ಖಾಲಿ)";
            if (debugRulesCountBadge) debugRulesCountBadge.textContent = "0 ನಿಯಮಗಳು";
            if (transformsList) {
                transformsList.innerHTML = `<span class="empty-rules-hint">ಯಾವುದೇ ವಿಶೇಷ ನಿಯಮದ ಅಗತ್ಯವಿಲ್ಲ (ಶುದ್ಧ ಕನ್ನಡ ಪದಗಳು)</span>`;
            }
            return;
        }

        try {
            const res = await fetch(apiUrl("/api/pronunciation_debug"), {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text })
            });

            if (res.ok) {
                const data = await res.json();
                if (normalizedPreview) normalizedPreview.textContent = data.normalized_text;
                if (debugDisplayText) debugDisplayText.textContent = data.display_text;
                if (debugNormalizedText) debugNormalizedText.textContent = data.normalized_text;
                if (debugSpeechText) debugSpeechText.textContent = data.speech_text;

                const transforms = data.transformations || data.applied_transforms || [];
                if (debugRulesCountBadge) {
                    debugRulesCountBadge.textContent = `${transforms.length} ನಿಯಮಗಳು`;
                }

                if (transformsList) {
                    if (transforms.length > 0) {
                        transformsList.innerHTML = transforms.map(t => `
                            <div class="transform-chip">
                                <span class="transform-orig">${escapeHtml(t.original)}</span>
                                <span class="transform-arrow">➔</span>
                                <span class="transform-spoken">${escapeHtml(t.replacement || t.spoken)}</span>
                            </div>
                        `).join("");
                    } else {
                        transformsList.innerHTML = `<span class="empty-rules-hint">ಯಾವುದೇ ವಿಶೇಷ ನಿಯಮದ ಅಗತ್ಯವಿಲ್ಲ (ಶುದ್ಧ ಕನ್ನಡ ಪದಗಳು)</span>`;
                    }
                }
            }
        } catch (e) {
            if (normalizedPreview) normalizedPreview.textContent = text;
            if (debugDisplayText) debugDisplayText.textContent = text;
            if (debugNormalizedText) debugNormalizedText.textContent = text;
            if (debugSpeechText) debugSpeechText.textContent = text;
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
            const nameEl = activeCard ? (activeCard.querySelector(".voice-title") || activeCard.querySelector(".voice-name")) : null;
            const voiceName = customName || (nameEl ? nameEl.textContent.split('(')[0].trim() : "Gagan");
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

        if (primaryCtaPlayIcon && primaryCtaPauseIcon) {
            primaryCtaPlayIcon.classList.toggle("hidden", state.isPlaying);
            primaryCtaPauseIcon.classList.toggle("hidden", !state.isPlaying);
        }

        if (primaryCtaText) {
            if (status === "playing") primaryCtaText.textContent = "⏸️ ವಿರಾಮಗೊಳಿಸಿ (Pause)";
            else if (status === "paused") primaryCtaText.textContent = "▶️ ಮುಂದುವರಿಸಿ (Resume)";
            else if (status === "loading") primaryCtaText.textContent = "⏳ ಧ್ವನಿ ತಯಾರಾಗುತ್ತಿದೆ...";
            else primaryCtaText.textContent = "🎙️ ಧ್ವನಿ ರಚಿಸಿ & ನುಡಿಸಿ (Generate & Play)";
        }

        if (status === "playing") statusText.textContent = "ನುಡಿಸಲಾಗುತ್ತಿದೆ (Playing)";
        else if (status === "paused") statusText.textContent = "ವಿರಾಮಗೊಳಿಸಲಾಗಿದೆ (Paused)";
        else if (status === "loading") statusText.textContent = "ಧ್ವನಿ ತಯಾರಾಗುತ್ತಿದೆ...";
        else statusText.textContent = "ಸಿದ್ಧವಾಗಿದೆ (Ready)";
    }

    // Connect Primary CTA Buttons
    if (primarySynthesizeBtn) {
        primarySynthesizeBtn.addEventListener("click", () => playBtn.click());
    }

    if (standardPlayCtaBtn) {
        standardPlayCtaBtn.addEventListener("click", () => synthesizeStandardTTS());
    }

    if (downloadPrimaryBtn) {
        downloadPrimaryBtn.addEventListener("click", () => downloadBtn.click());
    }

    const SAMPLE_TEXTS = [
        "ನಾವು ₹1000 ಡಿಜಿಟಲ್ ಪೇಮೆಂಟ್ ಮಾಡಿದಾಗ, ವ್ಯಾಪಾರಿ 1% MDR ಕಡಿತಗೊಳಿಸುತ್ತಾನೆ. ದಿನಾಂಕ 15/08/1947 ರಂದು ಮಧ್ಯಾಹ್ನ 3:30 PM ಕ್ಕೆ ಆರಂಭವಾದ ಈ ಪದ್ಧತಿಯು ಇಂದು YouTube ಮತ್ತು ChatGPT ನಂತಹ AI ತಂತ್ರಜ್ಞಾನಗಳ ಮೂಲಕ ಲಕ್ಷಾಂತರ ಜನರಿಗೆ ತಲುಪಿದೆ.",
        "ಎಸ್‌ಸಿಒ ಸಮ್ಮೇಳನದಲ್ಲಿ ಭಾರತದ ಪಾತ್ರ ಅತ್ಯಂತ ಪ್ರಮುಖವಾಗಿದೆ. ಜಾಗತಿಕ ದಕ್ಷಿಣದ ದೇಶಗಳಿಗೆ ಭಾರತ ನೀಡಿದ ೧೦ ಅಂಶಗಳ ಕಾರ್ಯಸೂಚಿ ಇಡೀ ವಿಶ್ವದ ಗಮನ ಸೆಳೆದಿದೆ. ದೇಶದ ರಾಷ್ಟ್ರೀಯ ಭದ್ರತೆ ಮತ್ತು ಆರ್ಥಿಕ ಶಕ್ತಿ ಎರಡೂ ಅಷ್ಟೇ ಮುಖ್ಯ.",
        "ನಿಮ್ಮ ಬ್ಯಾಂಕ್ ಖಾತೆಯಿಂದ ₹೨,೫೦೦ ಕಡಿತಗೊಂಡಿದೆ. ನಿಮ್ಮ ಯುಪಿಐ ವಹಿವಾಟು ಯಶಸ್ವಿಯಾಗಿದೆ. ಯಾವುದೇ ಸಂದರ್ಭದಲ್ಲೂ ಒಟಿಪಿ ಸಂಖ್ಯೆಯನ್ನು ಯಾರೊಂದಿಗೂ ಹಂಚಿಕೊಳ್ಳಬೇಡಿ.",
        "ಶುಭೋದಯ! ಧ್ವನಿ ಕನ್ನಡ ಆಡಿಯೊ ಸ್ಟುಡಿಯೋಗೆ ನಿಮಗೆ ಹೃತ್ಪೂರ್ವಕ ಸ್ವಾಗತ. ಇಂದು ನಿಮ್ಮ ದಿನವು ಸುಖ, ಶಾಂತಿ ಮತ್ತು ಸಂತೋಷದಿಂದ ಕೂಡಿರಲಿ.",
        "ಹೆಸರಾಯಿತು ಕರ್ನಾಟಕ, ಉಸಿರಾಗಲಿ ಕನ್ನಡ. ಸಿರಿಗನ್ನಡಂ ಗೆಲ್ಗೆ, ಸಿರಿಗನ್ನಡಂ ಬಾಳ್ಗೆ! ಎಲ್ಲಾದರು ಇರು ಎಂತಾದರು ಇರು ಎಂದೆಂದಿಗೂ ನೀ ಕನ್ನಡವಾಗಿರು."
    ];

    if (randomSampleBtn) {
        randomSampleBtn.addEventListener("click", () => {
            const randomText = SAMPLE_TEXTS[Math.floor(Math.random() * SAMPLE_TEXTS.length)];
            kannadaInput.value = randomText;
            updateTextMetrics();
            showToast("🎲 ಯಾದೃಚ್ಛಿಕ ಮಾದರಿ ಪಠ್ಯ ಲೋಡ್ ಆಗಿದೆ!");
        });
    }

    // Voice Preset Chips
    if (voicePresetChips && voicePresetChips.length > 0) {
        voicePresetChips.forEach(chip => {
            chip.addEventListener("click", () => {
                voicePresetChips.forEach(c => c.classList.remove("active"));
                chip.classList.add("active");
                const pitch = parseInt(chip.dataset.pitch || "0");
                const rate = parseFloat(chip.dataset.rate || "1.0");
                state.pitch = pitch;
                state.rate = rate;
                if (pitchSlider) {
                    pitchSlider.value = pitch;
                    pitchValue.textContent = `${pitch >= 0 ? '+' : ''}${pitch} Hz`;
                }
                if (rateSlider) {
                    rateSlider.value = rate;
                    rateValue.textContent = `${rate.toFixed(2)}x`;
                }
                showToast(`ಶೈಲಿ ಅನ್ವಯಿಸಲಾಗಿದೆ: ${chip.textContent.trim()}`);
            });
        });
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

    // ==========================================
    // 9. PRONUNCIATION DICTIONARY CONTROLLER
    // ==========================================
    let currentDictTab = "words";
    let cachedDictData = { words: {}, acronyms: {} };

    async function loadDictionary() {
        try {
            const res = await fetch(apiUrl("/api/dictionary"));
            if (res.ok) {
                cachedDictData = await res.json();
                if (dictWordsCountBadge) dictWordsCountBadge.textContent = cachedDictData.total_words || 0;
                if (dictAcronymsCountBadge) dictAcronymsCountBadge.textContent = cachedDictData.total_acronyms || 0;
                renderDictionaryList();
            }
        } catch (e) {
            console.warn("Failed to load pronunciation dictionary", e);
        }
    }

    function renderDictionaryList() {
        if (!dictEntriesList) return;
        dictEntriesList.innerHTML = "";
        const query = (dictSearchInput ? dictSearchInput.value : "").trim().toLowerCase();
        const sourceObj = currentDictTab === "words" ? (cachedDictData.words || {}) : (cachedDictData.acronyms || {});
        const entries = Object.entries(sourceObj);

        const filtered = entries.filter(([k, v]) => {
            if (!query) return true;
            return k.toLowerCase().includes(query) || v.toLowerCase().includes(query);
        });

        if (dictTotalMeta) {
            dictTotalMeta.textContent = `ಒಟ್ಟು ${entries.length} ನಮೂದುಗಳು (${filtered.length} ಪ್ರದರ್ಶಿಸಲಾಗುತ್ತಿದೆ)`;
        }

        if (filtered.length === 0) {
            dictEntriesList.innerHTML = `<div class="dict-empty-view">ಯಾವುದೇ ನಮೂದುಗಳು ಕಂಡುಬಂದಿಲ್ಲ (No entries found)</div>`;
            return;
        }

        // Sort alphabetically
        filtered.sort((a, b) => a[0].localeCompare(b[0]));

        filtered.forEach(([k, v]) => {
            const card = document.createElement("div");
            card.className = "dict-entry-card";
            card.innerHTML = `
                <div class="dict-entry-main">
                    <span class="dict-entry-key">${escapeHtml(k)}</span>
                    <span class="dict-entry-val">${escapeHtml(v)}</span>
                </div>
                <div class="dict-entry-actions">
                    <span class="tab-count-badge">${currentDictTab === 'words' ? 'ಪದ' : 'ಸಂಕ್ಷೇಪಣ'}</span>
                    <button class="dict-delete-btn" title="ತೆಗೆದುಹಾಕಿ (Delete)">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                </div>
            `;

            const delBtn = card.querySelector(".dict-delete-btn");
            delBtn.addEventListener("click", async (e) => {
                e.stopPropagation();
                if (!confirm(`"${k}" ನಮೂದನ್ನು ಅಳಿಸಲು ನೀವು ಖಚಿತವಾಗಿದ್ದೀರಾ?`)) return;
                try {
                    const res = await fetch(apiUrl(`/api/dictionary/entry?key=${encodeURIComponent(k)}&type=${currentDictTab === 'words' ? 'word' : 'acronym'}`), {
                        method: "DELETE"
                    });
                    if (res.ok) {
                        showToast(`"${k}" ನಿಘಂಟಿನಿಂದ ತೆಗೆದುಹಾಕಲಾಗಿದೆ`);
                        await loadDictionary();
                        fetchNormalization();
                    } else {
                        const err = await res.json();
                        showToast(`ದೋಷ: ${err.detail || 'ಅಳಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ'}`);
                    }
                } catch (err) {
                    showToast(`ದೋಷ: ${err.message}`);
                }
            });

            dictEntriesList.appendChild(card);
        });
    }

    if (dictTabWords) {
        dictTabWords.addEventListener("click", () => {
            currentDictTab = "words";
            dictTabWords.classList.add("active");
            if (dictTabAcronyms) dictTabAcronyms.classList.remove("active");
            renderDictionaryList();
        });
    }

    if (dictTabAcronyms) {
        dictTabAcronyms.addEventListener("click", () => {
            currentDictTab = "acronyms";
            dictTabAcronyms.classList.add("active");
            if (dictTabWords) dictTabWords.classList.remove("active");
            renderDictionaryList();
        });
    }

    if (dictSearchInput) {
        dictSearchInput.addEventListener("input", renderDictionaryList);
    }

    if (addDictEntryBtn) {
        addDictEntryBtn.addEventListener("click", async () => {
            const key = dictNewKey.value.trim();
            const value = dictNewValue.value.trim();
            const type = dictNewType.value;

            if (!key || !value) {
                showToast("ದಯವಿಟ್ಟು ಪದ ಮತ್ತು ಕನ್ನಡ ಉಚ್ಚಾರಣೆ ಎರಡನ್ನೂ ನಮೂದಿಸಿ");
                return;
            }

            try {
                const res = await fetch(apiUrl("/api/dictionary/entry"), {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ key, value, type })
                });

                if (res.ok) {
                    dictNewKey.value = "";
                    dictNewValue.value = "";
                    showToast(`"${key}" ನಿಘಂಟಿಗೆ ಸೇರಿಸಲಾಗಿದೆ!`);
                    await loadDictionary();
                    fetchNormalization();
                } else {
                    const err = await res.json();
                    showToast(`ದೋಷ: ${err.detail || 'ಉಳಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ'}`);
                }
            } catch (err) {
                showToast(`ದೋಷ: ${err.message}`);
            }
        });
    }

    function openDictionaryModal() {
        loadDictionary();
        if (dictModal) dictModal.classList.remove("hidden");
    }

    function closeDictionaryModal() {
        if (dictModal) dictModal.classList.add("hidden");
    }

    if (openDictBtn) openDictBtn.addEventListener("click", openDictionaryModal);
    if (openDictFromDebugBtn) openDictFromDebugBtn.addEventListener("click", openDictionaryModal);
    if (closeDictModalBtn) closeDictModalBtn.addEventListener("click", closeDictionaryModal);
    if (dictModal) {
        dictModal.addEventListener("click", (e) => {
            if (e.target === dictModal) closeDictionaryModal();
        });
    }

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
            if (presetsModal) presetsModal.classList.add("hidden");
            if (historyDrawer) historyDrawer.classList.add("hidden");
            if (dictModal) dictModal.classList.add("hidden");
            if (stopBtn) stopBtn.click();
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
    loadDictionary();
});
