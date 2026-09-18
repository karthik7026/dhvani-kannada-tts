/**
 * Dhvani Kannada Text-to-Speech & Delivery Style Studio - Frontend Engine v2.1
 */

document.addEventListener("DOMContentLoaded", () => {
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
        uploadedAudioFile: null,
        deliveryProfile: null,
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
    const standardTTSPanel = document.getElementById("standardTTSPanel");
    const deliveryTransferPanel = document.getElementById("deliveryTransferPanel");

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
    const deliveryAudioInput = document.getElementById("deliveryAudioInput");
    const deliveryFileName = document.getElementById("deliveryFileName");
    const analyzeDeliveryBtn = document.getElementById("analyzeDeliveryBtn");
    const deliveryStatsCard = document.getElementById("deliveryStatsCard");
    const statsFilename = document.getElementById("statsFilename");
    const statPace = document.getElementById("statPace");
    const statPitch = document.getElementById("statPitch");
    const statPause = document.getElementById("statPause");
    const statPunch = document.getElementById("statPunch");
    const generateStyledBtn = document.getElementById("generateStyledBtn");
    const abComparisonBox = document.getElementById("abComparisonBox");
    const playNormalABBtn = document.getElementById("playNormalABBtn");
    const playStyledABBtn = document.getElementById("playStyledABBtn");

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
        standardTTSPanel.classList.remove("hidden");
        deliveryTransferPanel.classList.add("hidden");
        updateStatusMeta();
    });

    tabDeliveryTransfer.addEventListener("click", () => {
        state.mode = "delivery";
        tabDeliveryTransfer.classList.add("active");
        tabNormalTTS.classList.remove("active");
        deliveryTransferPanel.classList.remove("hidden");
        standardTTSPanel.classList.add("hidden");
        updateStatusMeta("Delivery Transfer", "ರೆಫರೆನ್ಸ್ ಶೈಲಿ");
    });

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
    voiceCards.forEach(card => {
        card.addEventListener("click", () => {
            voiceCards.forEach(c => c.classList.remove("active"));
            card.classList.add("active");
            
            const gender = card.dataset.gender;
            const voice = card.dataset.voice;
            const preset = card.dataset.preset;

            state.gender = gender;
            state.voice = voice || "kn-IN-GaganNeural";

            if (preset === "podcast") {
                applyPreset("podcast", -4, 1.26);
            } else if (preset === "news") {
                applyPreset("news", 2, 1.18);
            } else if (gender === "female") {
                applyPreset("natural", 0, 1.0);
            } else if (gender === "male") {
                applyPreset("natural", -2, 1.0);
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
        pitchValue.textContent = `${state.pitch > 0 ? '+' : ''}${state.pitch} Hz`;
        updateStatusMeta();
    });

    rateSlider.addEventListener("input", () => {
        state.rate = parseFloat(rateSlider.value);
        rateValue.textContent = `${state.rate.toFixed(2)}x`;
        updateStatusMeta();
        updateTextMetrics();
    });

    function updateStatusMeta(customName, customPreset) {
        if (state.mode === "delivery") {
            const vName = state.voice.includes("Sapna") ? "Sapna" : "Gagan";
            activeVoiceInfo.textContent = `${vName} • ⚡ ಶೈಲಿ ವರ್ಗಾವಣೆ (Delivery Transfer)`;
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
        updateStatusMeta();
        showToast("ಧ್ವನಿ: Gagan (ಗಗನ್) ಆಯ್ಕೆಯಾಗಿದೆ");
    });

    pickSapnaBtn.addEventListener("click", () => {
        pickSapnaBtn.classList.add("active");
        pickGaganBtn.classList.remove("active");
        state.voice = "kn-IN-SapnaNeural";
        updateStatusMeta();
        showToast("ಧ್ವನಿ: Sapna (ಸ್ಪಪ್ನಾ) ಆಯ್ಕೆಯಾಗಿದೆ");
    });

    deliveryAudioInput.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (file) {
            state.uploadedAudioFile = file;
            deliveryFileName.textContent = `✓ ${file.name}`;
            analyzeDeliveryBtn.disabled = false;
            showToast(`ಆಡಿಯೊ ಫೈಲ್ ಲೋಡ್ ಆಗಿದೆ: ${file.name}`);
        }
    });

    // 5a. Analyze Delivery Prosody Profile
    analyzeDeliveryBtn.addEventListener("click", async () => {
        if (!state.uploadedAudioFile) {
            showToast("ದಯವಿಟ್ಟು ಆಡಿಯೊ ಫೈಲ್ ಆಯ್ಕೆ ಮಾಡಿ");
            return;
        }

        analyzeDeliveryBtn.disabled = true;
        analyzeDeliveryBtn.innerHTML = `<span>ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ...</span>`;

        try {
            const formData = new FormData();
            formData.append("reference_audio", state.uploadedAudioFile);

            const res = await fetch("/api/analyze_delivery", {
                method: "POST",
                body: formData
            });

            if (!res.ok) throw new Error("Delivery analysis failed");

            const profile = await res.json();
            state.deliveryProfile = profile;

            // Render stats card
            statsFilename.textContent = fileBasename(state.uploadedAudioFile.name);
            statPace.textContent = `${profile.speaking_rate.pace_syl_sec} syl/s (${profile.speaking_rate.tempo_category})`;
            statPitch.textContent = `${profile.pitch_dynamics.median_hz} Hz (${profile.pitch_dynamics.span_semitones} st, ${profile.pitch_dynamics.ending_slope})`;
            statPause.textContent = `${profile.pauses.median_ms} ms (Short: ${profile.pauses.distribution.short_pct}%)`;
            statPunch.textContent = `${profile.energy_and_punch.transition_contrast} (${profile.energy_and_punch.crest_factor_db} dB)`;

            deliveryStatsCard.classList.remove("hidden");
            analyzeDeliveryBtn.innerHTML = `<span>✓ ಶೈಲಿ ವಿಶ್ಲೇಷಿಸಲಾಗಿದೆ (Analyzed)</span>`;
            showToast("ರೆಫರೆನ್ಸ್ ಶೈಲಿ ವಿಶ್ಲೇಷಣೆ ಯಶಸ್ವಿಯಾಗಿದೆ!");

        } catch (err) {
            console.error(err);
            analyzeDeliveryBtn.disabled = false;
            analyzeDeliveryBtn.innerHTML = `<span>🔍 ಶೈಲಿ ವಿಶ್ಲೇಷಿಸಿ (Analyze Delivery)</span>`;
            showToast(`ದೋಷ: ${err.message}`);
        }
    });

    function fileBasename(name) {
        return name.length > 25 ? name.substring(0, 22) + "..." : name;
    }

    // 5b. Synthesize with Delivery Prosody
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

            if (state.deliveryProfile) {
                formData.append("profile_json", JSON.stringify(state.deliveryProfile));
            } else if (state.uploadedAudioFile) {
                formData.append("reference_audio", state.uploadedAudioFile);
            }

            const res = await fetch("/api/synthesize_delivery", {
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
            const res = await fetch("/api/synthesize", {
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
            if (state.mode === "delivery") {
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

            const res = await fetch("/api/synthesize", {
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
            const res = await fetch("/api/presets");
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
});
